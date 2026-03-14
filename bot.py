import os
import logging
import time
import telebot
import openai
import requests
from typing import List, Dict
from dotenv import load_dotenv
from yandex_ai_studio_sdk import AIStudio

# Загрузка переменных окружения
load_dotenv()

# Логи
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    """
    Вызывает функцию модели с обработкой ошибок и таймаутом.
    Если модель зависает или падает — возвращает сообщение об ошибке.
    """
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
# новый вариант с таймаутом 10 секунд
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
        f"Привет! 👋\nЯ дерзкий бот. Модель: {user_models.get(message.from_user.id, DEFAULT_MODEL).upper()}\n"
        "Просто отправь сообщение, я отвечу."
    )
    bot.send_message(message.chat.id, welcome_text)

@bot.message_handler(commands=['models'])
def handle_models(message):
    text = (
        "Доступные модели:\n1️⃣ ChatGPT/ProxyAPI\n2️⃣ YandexGPT\n3️⃣ Ollama\n"
        f"Текущая модель: {user_models.get(message.from_user.id, DEFAULT_MODEL).upper()}"
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['model'])
def handle_model(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("ChatGPT", callback_data="model_chatgpt"),
        telebot.types.InlineKeyboardButton("YandexGPT", callback_data="model_yandex"),
        telebot.types.InlineKeyboardButton("Ollama", callback_data="model_ollama")
    )
    bot.send_message(message.chat.id, "Выберите модель:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_model_choice(call):
    logger.info(f"Callback data: {call.data}")  # <-- логируем данные кнопки
    user_id = call.from_user.id
    if call.data == "model_chatgpt":
        user_models[user_id] = 'chatgpt'
    elif call.data == "model_yandex":
        user_models[user_id] = 'yandex'
    elif call.data == "model_ollama":
        user_models[user_id] = 'ollama'

    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Модель изменена на: {user_models[user_id].upper()}"
        )
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения кнопки: {e}")
        bot.send_message(call.message.chat.id, f"Модель изменена на: {user_models[user_id].upper()}")

@bot.message_handler(content_types=['text'])
def handle_text_message(message):
    user_id = message.from_user.id
    response = get_response(message.text, user_id)
    bot.reply_to(message, response)

@bot.message_handler(content_types=['photo', 'video', 'audio', 'document', 'voice'])
def handle_non_text_message(message):
    bot.reply_to(message, "Работаю только с текстом.")

# ====================== Main ======================

if __name__ == '__main__':
    logger.info("Бот запущен")
    # Очистка старых апдейтов
    try:
        updates = bot.get_updates()
        if updates:
            logger.info(f"Очищено {len(updates)} старых апдейтов")
    except Exception as e:
        logger.warning(f"Не удалось очистить старые апдейты: {e}")
    bot.infinity_polling()