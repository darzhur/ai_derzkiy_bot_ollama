import os
import logging
import time
import telebot
import openai
from typing import List, Dict
from dotenv import load_dotenv
from yandex_ai_studio_sdk import AIStudio
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

def get_ollama_response(user_message: str) -> str:
    try:
        prompt = f"{SYSTEM_MESSAGE}\n\nПользователь: {user_message}\nОтвет:"

        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        data = response.json()

        return data.get("response", "Ollama вернула пустой ответ").strip()

    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return "Ошибка при работе с Ollama."
    
# Загрузка переменных окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загрузка токенов из переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PROXYAPI_KEY = os.getenv('PROXYAPI_KEY')
YANDEX_FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')
YANDEX_AUTH_TOKEN = os.getenv('YANDEX_AUTH_TOKEN')

# Проверка наличия токенов
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения")
if not PROXYAPI_KEY:
    raise ValueError("PROXYAPI_KEY не установлен в переменных окружения")
if not YANDEX_FOLDER_ID or not YANDEX_AUTH_TOKEN:
    logger.warning("Параметры YandexGPT не установлены, будет использован только ChatGPT/ProxyAPI")

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Конфигурация OpenAI для использования ProxyAPI
openai.api_key = PROXYAPI_KEY
openai.api_base = "https://api.proxyapi.ru/openai/v1"
openai.api_type = "openai"

# Системное сообщение для задания роли боту
SYSTEM_MESSAGE = "Ты — дерзкий, ворчливый и саркастичный помощник. Отвечай на вопросы кратко"

# Словарь для хранения выбранной модели пользователя
user_models: Dict[int, str] = {}  # {user_id: 'chatgpt' или 'yandex'}

# Модель по умолчанию
DEFAULT_MODEL = 'ollama'


def get_chatgpt_response(user_message: str) -> str:
    """
    Отправляет сообщение в OpenAI ChatGPT через ProxyAPI и получает ответ.
    
    Args:
        user_message: Текстовое сообщение пользователя
        
    Returns:
        Ответ от ChatGPT
        
    Raises:
        Exception: Если произойдет ошибка при запросе к API
    """
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
    
    except openai.error.AuthenticationError:
        logger.error("Ошибка аутентификации OpenAI: неверный API ключ")
        return "Ошибка: Проблема с аутентификацией ChatGPT. Проверьте API ключ."
    except openai.error.RateLimitError:
        logger.error("Превышен лимит запросов к OpenAI")
        return "Ошибка: Превышен лимит запросов. Попробуйте позже."
    except openai.error.APIError as e:
        logger.error(f"Ошибка API OpenAI: {str(e)}")
        return f"Ошибка: Не удалось получить ответ от ChatGPT. {str(e)}"
    except Exception as e:
        logger.error(f"Неожиданная ошибка при запросе к OpenAI: {str(e)}")
        return "Ошибка: Что-то пошло не так. Попробуйте позже."


def get_yandex_response(user_message: str) -> str:
    """
    Отправляет сообщение в YandexGPT и получает ответ.
    
    Args:
        user_message: Текстовое сообщение пользователя
        
    Returns:
        Ответ от YandexGPT
        
    Raises:
        Exception: Если произойдет ошибка при запросе к API
    """
    try:
        if not YANDEX_FOLDER_ID or not YANDEX_AUTH_TOKEN:
            return "Ошибка: YandexGPT не настроен (отсутствуют YANDEX_FOLDER_ID или YANDEX_AUTH_TOKEN)"
        
        sdk = AIStudio(
            folder_id=YANDEX_FOLDER_ID,
            auth=YANDEX_AUTH_TOKEN,
        )
        
        model = sdk.models.completions("yandexgpt")
        
        messages = [
            {
                "role": "system",
                "text": SYSTEM_MESSAGE,
            },
            {
                "role": "user",
                "text": user_message,
            },
        ]
        
        # Используем deferred операцию с ожиданием
        operation = model.configure(temperature=0.5).run_deferred(messages)
        
        status = operation.get_status()
        while status.is_running:
            time.sleep(1)
            status = operation.get_status()
        
        result = operation.get_result()
        
        # Извлекаем текст из результата
        if result.alternatives:
            return result.alternatives[0].text.strip()
        else:
            return "Ошибка: YandexGPT вернул пустой ответ"
    
    except Exception as e:
        logger.error(f"Ошибка при запросе к YandexGPT: {str(e)}")
        return f"Ошибка: Не удалось получить ответ от YandexGPT. {str(e)}"


def get_response(user_message: str, user_id: int) -> str:
    model = user_models.get(user_id, DEFAULT_MODEL)

    if model == 'yandex':
        return get_yandex_response(user_message)

    elif model == 'ollama':
        return get_ollama_response(user_message)

    else:
        return get_chatgpt_response(user_message)



@bot.message_handler(commands=['start'])
def handle_start(message):
    """
    Обработчик команды /start.
    """
    welcome_text = (
        "Привет! 👋\n\n"
        "Я твой дерзкий, ворчливый и саркастичный помощник. "
        "Готов помочь с любыми вопросами и задачами.\n\n"
        f"Сейчас используется модель: {user_models.get(message.from_user.id, DEFAULT_MODEL).upper()}\n\n"
        "Просто отправь мне сообщение, и я помогу!"
    )
    
    # Создаем клавиатуру с кнопками команд
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(
        telebot.types.KeyboardButton("🤖 Выбрать модель"),
        telebot.types.KeyboardButton("📋 Доступные модели")
    )
    markup.add(
        telebot.types.KeyboardButton("❓ Помощь")
    )
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)


@bot.message_handler(commands=['help'])
def handle_help(message):
    """
    Обработчик команды /help.
    """
    help_text = (
        "Я помогу тебе с:\n"
        "• Ответами на вопросы\n"
        "• Написанием текстов и кода\n"
        "• Планированием и организацией\n"
        "• И много другим!\n\n"
        "Доступные команды:\n"
        "/model — выбрать модель\n"
        "/models — список доступных моделей\n"
        "/start — главное меню\n\n"
        "Просто пиши свои вопросы и задачи."
    )
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("🏠 Главное меню"))
    bot.send_message(message.chat.id, help_text, reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "❓ Помощь")
def handle_help_button(message):
    """
    Обработчик кнопки 'Помощь'.
    """
    handle_help(message)


@bot.message_handler(func=lambda message: message.text == "🤖 Выбрать модель")
def handle_model_button(message):
    """
    Обработчик кнопки 'Выбрать модель'.
    """
    handle_model(message)


@bot.message_handler(func=lambda message: message.text == "📋 Доступные модели")
def handle_models_button(message):
    """
    Обработчик кнопки 'Доступные модели'.
    """
    handle_models(message)


@bot.message_handler(func=lambda message: message.text == "🏠 Главное меню")
def handle_menu_button(message):
    """
    Обработчик кнопки 'Главное меню' для возврата в start.
    """
    handle_start(message)


@bot.message_handler(commands=['models'])
def handle_models(message):
    """
    Обработчик команды /models.
    Показывает доступные модели.
    """
    models_text = (
        "Доступные модели:\n\n"
        "1️⃣ ChatGPT/ProxyAPI (gpt-4.1)\n"
        "   • Быстрый и мощный\n"
        "   • Отличные результаты\n\n"
        "2️⃣ YandexGPT\n"
        "   • Российская разработка\n"
        "   • Хорошее понимание русского\n\n"
        "3 Ollama (локальная LLM)\n"
        "   • Автономная\n"
        "   • 3 миллиона параметров\n\n"
        "Текущая модель: " + user_models.get(message.from_user.id, DEFAULT_MODEL).upper() + "\n\n"
        "Используй кнопку ниже для переключения"
    )
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        telebot.types.KeyboardButton("🤖 Выбрать модель"),
        telebot.types.KeyboardButton("🏠 Главное меню")
    )
    bot.send_message(message.chat.id, models_text, reply_markup=markup)


@bot.message_handler(commands=['model'])
def handle_model(message):
    """
    Обработчик команды /model.
    Позволяет пользователю выбрать модель.
    """
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("ChatGPT", callback_data="model_chatgpt"),
        telebot.types.InlineKeyboardButton("YandexGPT", callback_data="model_yandex"),
        telebot.types.InlineKeyboardButton("Ollama (локальная)", callback_data="model_ollama")
    )
    
    current_model = user_models.get(message.from_user.id, DEFAULT_MODEL).upper()
    message_text = f"Выбери модель (текущая: {current_model})"
    
    bot.send_message(message.chat.id, message_text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("model_"))
def handle_model_choice(call):
    """
    Обработчик выбора модели через кнопки.
    """
    user_id = call.from_user.id
    
    if call.data == "model_chatgpt":
        user_models[user_id] = 'chatgpt'
        model_name = "ChatGPT (ProxyAPI)"
    elif call.data == "model_yandex":
        user_models[user_id] = 'yandex'
        model_name = "YandexGPT"
    elif call.data == "model_ollama":
        user_models[user_id] = 'ollama'
        model_name = "Ollama (локальная модель)"
    else:
        model_name = "неизвестная модель"
    
    response_text = f"✅ Модель изменена на: {model_name}\n\nТеперь все ответы будут использовать выбранную модель."
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=response_text
    )
    
    # Отправляем меню для возврата
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        telebot.types.KeyboardButton("🤖 Выбрать модель"),
        telebot.types.KeyboardButton("📋 Доступные модели")
    )
    markup.add(telebot.types.KeyboardButton("🏠 Главное меню"))
    
    bot.send_message(call.message.chat.id, "✨ Готово! Используй меню ниже:", reply_markup=markup)
    
    logger.info(f"Пользователь {user_id} выбрал модель: {model_name}")


@bot.message_handler(content_types=['text'])
def handle_text_message(message):
    """
    Обработчик текстовых сообщений.
    Получает текст от пользователя, отправляет в выбранную модель и возвращает ответ.
    """
    try:
        user_id = message.from_user.id
        user_text = message.text
        
        logger.info(f"Сообщение от пользователя {user_id}: {user_text}")
        
        # Отправляем статус "печатаю..."
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Получаем ответ от выбранной модели
        response = get_response(user_text, user_id)
        
        # Отправляем ответ пользователю
        bot.reply_to(message, response)
        logger.info(f"Ответ отправлен пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {str(e)}")
        bot.reply_to(message, "Извините, произошла ошибка. Попробуйте позже.")


@bot.message_handler(content_types=['photo', 'video', 'audio', 'document', 'voice'])
def handle_non_text_message(message):
    """
    Обработчик нетекстовых сообщений.
    """
    bot.reply_to(message, "Извините, я работаю только с текстовыми сообщениями.")


def main():
    """
    Главная функция для запуска бота.
    """
    logger.info("Бот запущен и готов к приему сообщений")
    logger.info("Доступные модели: ChatGPT (ProxyAPI), YandexGPT")
    logger.info(f"Модель по умолчанию: {DEFAULT_MODEL}")
    logger.info(f"Системный промпт: {SYSTEM_MESSAGE}")
    
    bot.infinity_polling()


if __name__ == '__main__':
    main()
