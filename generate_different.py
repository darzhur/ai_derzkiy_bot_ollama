#!/usr/bin/env python3
"""
Скрипт для демонстрации различных способов работы с YandexGPT API.
Поддерживает несколько вариантов взаимодействия с моделью.
"""

from __future__ import annotations
import time
import os
import sys
import logging
from dotenv import load_dotenv
from yandex_ai_studio_sdk import AIStudio

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Константы
SYSTEM_PROMPT = "Ты — дерзкий, ворчливый и саркастичный помощник. Отвечай на вопросы кратко"
DEFAULT_QUESTION = "Как устроена Луна?"


def initialize_sdk() -> AIStudio:
    """
    Инициализирует SDK с параметрами из переменных окружения.
    
    Returns:
        AIStudio: Инициализированный SDK
        
    Raises:
        ValueError: Если отсутствуют необходимые переменные окружения
    """
    folder_id = os.getenv('YANDEX_FOLDER_ID')
    auth_token = os.getenv('YANDEX_AUTH_TOKEN')
    
    if not folder_id or not auth_token:
        logger.error("Отсутствуют YANDEX_FOLDER_ID или YANDEX_AUTH_TOKEN в .env файле")
        raise ValueError("Необходимо установить YANDEX_FOLDER_ID и YANDEX_AUTH_TOKEN")
    
    try:
        sdk = AIStudio(
            folder_id=folder_id,
            auth=auth_token,
        )
        logger.info("SDK успешно инициализирован")
        return sdk
    except Exception as e:
        logger.error(f"Ошибка при инициализации SDK: {str(e)}")
        raise


def variant_1_deferred(sdk: AIStudio, question: str) -> None:
    """
    Вариант 1: Отложенное выполнение с проверкой статуса каждые 5 секунд.
    
    Args:
        sdk: Инициализированный SDK
        question: Вопрос для модели
    """
    logger.info("Запуск Variant 1: Deferred операция с ожиданием (5 сек)")
    print("\n" + "="*60)
    print("Variant 1: Отложенное выполнение (ожидание каждые 5 сек)")
    print("="*60)
    
    try:
        model = sdk.models.completions("yandexgpt")
        
        messages = [
            {"role": "system", "text": SYSTEM_PROMPT},
            {"role": "user", "text": question},
        ]
        
        operation = model.configure(temperature=0.5).run_deferred(messages)
        
        status = operation.get_status()
        while status.is_running:
            logger.info(f"Операция выполняется... ({status})")
            time.sleep(5)
            status = operation.get_status()
        
        result = operation.get_result()
        print(f"\n✅ Ответ:\n{result}\n")
        logger.info("Variant 1 успешно выполнен")
        
    except Exception as e:
        logger.error(f"Ошибка в Variant 1: {str(e)}")
        print(f"\n❌ Ошибка: {str(e)}\n")


def variant_2_fast(sdk: AIStudio, question: str) -> None:
    """
    Вариант 2: Отложенное выполнение с более частой проверкой статуса (1 сек).
    
    Args:
        sdk: Инициализированный SDK
        question: Вопрос для модели
    """
    logger.info("Запуск Variant 2: Deferred операция с ожиданием (1 сек)")
    print("\n" + "="*60)
    print("Variant 2: Отложенное выполнение (ожидание каждые 1 сек)")
    print("="*60)
    
    try:
        model = sdk.models.completions("yandexgpt")
        
        messages = [
            {"role": "system", "text": SYSTEM_PROMPT},
            {"role": "user", "text": question},
        ]
        
        operation = model.configure(temperature=0.7).run_deferred(messages)
        
        status = operation.get_status()
        iterations = 0
        while status.is_running:
            iterations += 1
            logger.debug(f"Проверка статуса #{iterations}")
            time.sleep(1)
            status = operation.get_status()
        
        result = operation.get_result()
        print(f"\n✅ Ответ (всего проверок: {iterations}):\n{result}\n")
        logger.info(f"Variant 2 успешно выполнен (проверок: {iterations})")
        
    except Exception as e:
        logger.error(f"Ошибка в Variant 2: {str(e)}")
        print(f"\n❌ Ошибка: {str(e)}\n")


def main():
    """
    Главная функция. Запускает несколько вариантов работы с YandexGPT.
    """
    # Получение вопроса из аргументов командной строки или использование по умолчанию
    question = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_QUESTION
    
    logger.info(f"Вопрос: {question}")
    print(f"\n🤖 Использование YandexGPT")
    print(f"❓ Вопрос: {question}\n")
    
    try:
        # Инициализация SDK
        sdk = initialize_sdk()
        
        # Запуск вариантов
        variant_1_deferred(sdk, question)
        variant_2_fast(sdk, question)
        
        logger.info("Все варианты успешно выполнены")
        
    except ValueError as e:
        logger.error(f"Ошибка конфигурации: {str(e)}")
        print(f"❌ {str(e)}")
        print("\n💡 Убедитесь, что в файле .env установлены:")
        print("   - YANDEX_FOLDER_ID")
        print("   - YANDEX_AUTH_TOKEN")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}")
        print(f"\n❌ Неожиданная ошибка: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()