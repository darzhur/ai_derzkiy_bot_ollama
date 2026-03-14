#!/usr/bin/env python3
"""
Быстрый старт Telegram бота с ChatGPT.
Этот скрипт проводит вас через установку и запуск.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Выполняет команду и показывает статус."""
    print(f"\n🔄 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Ошибка: {result.stderr}")
        return False
    print(f"✅ {description} - готово")
    return True


def setup():
    """Главная функция установки."""
    print("=" * 50)
    print("  Telegram бот с ChatGPT - Быстрый старт")
    print("=" * 50)
    
    # Проверка Python
    print("\n📦 Проверка Python...")
    py_version = subprocess.run([sys.executable, '--version'], capture_output=True, text=True)
    print(f"   {py_version.stdout.strip()}")
    
    # Проверка и создание .env
    if not Path('.env').exists():
        print("\n🔑 Файл .env не найден")
        print("   Копирую .env.example -> .env...")
        subprocess.run("cp .env.example .env", shell=True)
        
        print("\n⚠️  ВАЖНО! Отредактируйте файл .env:")
        print("   1. Откройте файл .env в текстовом редакторе")
        print("   2. Добавьте ваш Telegram токен (от @BotFather)")
        print("   3. Добавьте ваш OpenAI API ключ")
        
        input("\n   Нажмите Enter после редактирования .env файла...")
    else:
        print("✅ Файл .env найден")
    
    # Создание виртуального окружения
    if not Path('venv').exists():
        if not run_command(f'"{sys.executable}" -m venv venv', "Создание виртуального окружения"):
            sys.exit(1)
    else:
        print("\n✅ Виртуальное окружение уже создано")
    
    # Определение команды активации (зависит от ОС)
    if sys.platform == "win32":
        activate_cmd = "venv\\Scripts\\activate"
        pip_path = "venv\\Scripts\\pip"
    else:
        activate_cmd = "source venv/bin/activate"
        pip_path = "./venv/bin/pip"
    
    # Install requirements
    if not run_command(f'{pip_path} install --upgrade pip', "Обновление pip"):
        sys.exit(1)
    
    if not run_command(f'{pip_path} install -r requirements.txt', "Установка зависимостей"):
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✨ Установка завершена!")
    print("=" * 50)
    
    print("\n🚀 Для запуска бота выполните:")
    if sys.platform == "win32":
        print("   venv\\Scripts\\activate")
        print("   python bot.py")
    else:
        print("   chmod +x run.sh")
        print("   ./run.sh")
        print("   или")
        print("   source venv/bin/activate")
        print("   python3 bot.py")
    
    print("\n💡 Подсказки:")
    print("   - Боту нужны ваши Telegram и OpenAI токены")
    print("   - Отредактируйте .env перед запуском")
    print("   - Используйте Ctrl+C для остановки бота")
    print("   - Логи видны в терминале")


if __name__ == '__main__':
    setup()
