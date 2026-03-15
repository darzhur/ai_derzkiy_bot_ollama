import os
import logging
import time
import telebot
import openai
import requests
from typing import List, Dict
from dotenv import load_dotenv
from yandex_ai_studio_sdk import AIStudio
from telebot import types
import os

# Загрузка переменных окружения
load_dotenv()

# Логи
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SOURCE_TOKEN = os.getenv("SRC_TOKEN")

from logtail import LogtailHandler

if SOURCE_TOKEN:
    logtail_handler = LogtailHandler(source_token=SOURCE_TOKEN)
    logger.addHandler(logtail_handler)
    logger.info("Logtail интегрирован и готов к отправке логов")
else:
    logger.warning("SOURCE_TOKEN не найден — логи не будут уходить в BetterStack")

# Переменные окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PROXYAPI_KEY = os.getenv('PROXYAPI_KEY')
YANDEX_FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')
YANDEX_AUTH_TOKEN = os.getenv('YANDEX_AUTH_TOKEN')
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

if not TELEGRAM_TOKEN or not PROXYAPI_KEY:
    raise ValueError("TELEGRAM_BOT_TOKEN или PROXYAPI_KEY не установлены")

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=True, skip_pending=True)

# Настройка OpenAI ProxyAPI
openai.api_key = PROXYAPI_KEY
openai.api_base = "https://api.proxyapi.ru/openai/v1"
openai.api_type = "openai"

# Системное сообщение
SYSTEM_MESSAGE = "Ты — дерзкий, ворчливый и саркастичный помощник. Отвечай кратко"

# Словарь выбранной модели пользователя
user_models: Dict[int, str] = {}
DEFAULT_MODEL = 'ollama'

# Проверка доступности Ollama
try:
    r = requests.get(OLLAMA_URL, timeout=5)
    if r.status_code == 200:
        logger.info("Ollama доступна")
    else:
        logger.warning(f"Ollama вернула статус {r.status_code}")
except requests.exceptions.RequestException:
    logger.warning("Ollama недоступна при старте")

# ====================== Функции для моделей ======================

def get_ollama_response(user_message: str) -> str:
    try:
        payload = {"model": OLLAMA_MODEL, "prompt": f"{SYSTEM_MESSAGE}\n\nПользователь: {user_message}\nОтвет:", "stream": False}
        r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("response", "Ollama вернула пустой ответ").strip()
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return "Ошибка при работе с Ollama."

def get_chatgpt_response(user_message: str) -> str:
    try:
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": user_message}
        ]
        response = openai.ChatCompletion.create(
            model="gpt-4.1",
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"ChatGPT error: {e}")
        return "Ошибка при работе с ChatGPT."

def get_yandex_response(user_message: str) -> str:
    try:
        if not YANDEX_FOLDER_ID or not YANDEX_AUTH_TOKEN:
            return "YandexGPT не настроен"
        sdk = AIStudio(folder_id=YANDEX_FOLDER_ID, auth=YANDEX_AUTH_TOKEN)
        model = sdk.models.completions("yandexgpt")
        messages = [{"role": "system", "text": SYSTEM_MESSAGE}, {"role": "user", "text": user_message}]
        operation = model.configure(temperature=0.5).run_deferred(messages)
        status = operation.get_status()
        while status.is_running:
            time.sleep(1)
            status = operation.get_status()
        result = operation.get_result()
        if result.alternatives:
            return result.alternatives[0].text.strip()
        return "YandexGPT вернул пустой ответ"
    except Exception as e:
        logger.error(f"YandexGPT error: {e}")
        return "Ошибка при работе с YandexGPT."

# ====================== Safe call для моделей ======================
def safe_model_call(func, *args, timeout_sec=60):
    import threading
    result = ["Модель временно недоступна"]

    def target():
        try:
            result[0] = func(*args)
        except Exception as e:
            logger.error(f"Ошибка модели {func.__name__}: {e}")
            result[0] = f"Ошибка работы модели {func.__name__}"

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout=timeout_sec)
    if thread.is_alive():
        logger.warning(f"Таймаут {timeout_sec} секунд для модели {func.__name__}")
        return f"{func.__name__} не ответила за {timeout_sec} секунд"
    return result[0]

def get_response(user_message: str, user_id: int) -> str:
    model = user_models.get(user_id, DEFAULT_MODEL)
    if model == 'yandex':
        return safe_model_call(get_yandex_response, user_message, timeout_sec=60)
    elif model == 'ollama':
        return safe_model_call(get_ollama_response, user_message, timeout_sec=60)
    else:
        return safe_model_call(get_chatgpt_response, user_message, timeout_sec=60)

# ====================== Хэндлеры Telegram ======================

@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome_text = (
        f"Привет! 👋\nЯ ОЧЕНЬ дерзкий бот. Модель: {user_models.get(message.from_user.id, DEFAULT_MODEL).upper()}\n"
        "Нажми /model для выбора модели.\n"
        "Или просто отправь сообщение, я отвечу."
    )
    markup = types.ReplyKeyboardRemove()  # убираем старые кнопки
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(commands=['menu'])
def handle_menu(message):
    text = (
        "Главное меню:\n"
        "/model — выбрать модель\n"
    )
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(commands=['choose_model'])
def handle_choose_model(message):
    text = (
        "Выбор модели:\n"
        "/model_chatgpt — ChatGPT\n"
        "/model_yandex — YandexGPT\n"
        "/model_ollama — Ollama\n"
        f"Текущая модель: {user_models.get(message.from_user.id, DEFAULT_MODEL).upper()}"
    )
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(commands=['model'])
def handle_model(message):
    text = (
        "Выбери модель командой:\n"
        "/model_chatgpt — ChatGPT\n"
        "/model_yandex — YandexGPT\n"
        "/model_ollama — Ollama\n"
        f"Текущая модель: {user_models.get(message.from_user.id, DEFAULT_MODEL).upper()}"
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['model_chatgpt'])
def set_chatgpt_model(message):
    user_models[message.from_user.id] = 'chatgpt'
    bot.reply_to(message, "Модель изменена на ChatGPT")

@bot.message_handler(commands=['model_yandex'])
def set_yandex_model(message):
    user_models[message.from_user.id] = 'yandex'
    bot.reply_to(message, "Модель изменена на YandexGPT")

@bot.message_handler(commands=['model_ollama'])
def set_ollama_model(message):
    user_models[message.from_user.id] = 'ollama'
    bot.reply_to(message, "Модель изменена на Ollama")

# Текстовые сообщения отдельно
@bot.message_handler(content_types=['text'])
def handle_text_message(message):
    user_id = message.from_user.id
    try:
        response = get_response(message.text, user_id)
        bot.reply_to(message, response)

        if SOURCE_TOKEN:
            logger.info(
                "User message",
                extra={
                    "user_id": user_id,
                    "username": message.from_user.username,
                    "message_text": message.text
                }
            )
    except Exception as e:
        logger.exception("Ошибка при обработке сообщения")
        bot.reply_to(message, "Произошла ошибка при обработке вашего сообщения.")

@bot.message_handler(content_types=['photo', 'video', 'audio', 'document', 'voice'])
def handle_non_text_message(message):
    bot.reply_to(message, "Работаю только с текстом.")

# ====================== Main ======================

if __name__ == '__main__':
    logger.info("Бот запущен")
    try:
        updates = bot.get_updates()
        if updates:
            logger.info(f"Очищено {len(updates)} старых апдейтов")
    except Exception as e:
        logger.warning(f"Не удалось очистить старые апдейты: {e}")
    bot.infinity_polling()