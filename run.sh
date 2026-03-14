#!/bin/bash

# Скрипт для запуска Telegram бота на macOS/Linux

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "Python 3 не установлен!"
    exit 1
fi

# Проверяем наличие виртуального окружения
if [ ! -d "venv" ]; then
    echo "Виртуальное окружение не найдено."
    echo "Создаю виртуальное окружение..."
    python3 -m venv venv
    
    echo "Активирую виртуальное окружение..."
    source venv/bin/activate
    
    echo "Установка зависимостей..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "Активирую виртуальное окружение..."
    source venv/bin/activate
fi

# Проверяем конфигурацию
echo ""
echo "Проверка конфигурации..."
python3 config.py

# Если проверка прошла успешно, запускаем бота
if [ $? -eq 0 ]; then
    echo "Запуск бота..."
    python3 bot.py
fi
