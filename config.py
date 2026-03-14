#!/usr/bin/env python3
"""
Утилита для загрузки переменных окружения из .env файла
и проверки конфигурации перед запуском бота.
"""

import os
import sys
from pathlib import Path


def load_env_file():
    """Загружает переменные окружения из .env файла."""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ Файл .env не найден!")
        print("   Создайте его из .env.example:")
        print("   cp .env.example .env")
        print("   Затем отредактируйте .env и добавьте ваши токены.")
        sys.exit(1)
    
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def check_configuration():
    """Проверяет наличие всех необходимых переменных окружения."""
    required_vars = ['TELEGRAM_BOT_TOKEN', 'PROXYAPI_KEY']
    optional_vars = ['YANDEX_FOLDER_ID', 'YANDEX_AUTH_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Отсутствуют обязательные переменные окружения:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nОтредактируйте файл .env и добавьте недостающие значения.")
        sys.exit(1)
    
    # Дополнительная проверка значений
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    proxyapi_key = os.getenv('PROXYAPI_KEY')
    
    if telegram_token == 'your_telegram_bot_token_here':
        print("❌ TELEGRAM_BOT_TOKEN содержит значение по умолчанию!")
        print("   Замените на реальный токен в файле .env")
        sys.exit(1)
    
    if proxyapi_key == 'your_proxyapi_key_here':
        print("❌ PROXYAPI_KEY содержит значение по умолчанию!")
        print("   Замените на реальный ключ в файле .env")
        sys.exit(1)
    
    # Проверка YandexGPT параметров (опционально)
    yandex_folder = os.getenv('YANDEX_FOLDER_ID')
    yandex_auth = os.getenv('YANDEX_AUTH_TOKEN')
    
    if yandex_folder and yandex_auth:
        print("✅ YandexGPT параметры найдены")
    else:
        print("⚠️  YandexGPT параметры не установлены (бот будет работать только с ChatGPT)")
    
    print("✅ Конфигурация проверена успешно!")
    print(f"   Telegram токен: {telegram_token[:10]}...")
    print(f"   ProxyAPI ключ: {proxyapi_key[:10]}...")


if __name__ == '__main__':
    load_env_file()
    check_configuration()
    print("\n✨ Все готово. Запускаем бота...\n")
