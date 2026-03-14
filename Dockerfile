FROM python:3.11-slim

WORKDIR /app

# Копируем все файлы проекта
COPY . /app

# Системные зависимости
RUN apt-get update && \
    apt-get install -y curl git && \
    rm -rf /var/lib/apt/lists/*

# Установка Python-зависимостей
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Запуск бота
# CMD ["python3", "bot.py"]

# Установка Ollama (если можно) и запуск сервера в фоне
RUN ollama pull llama3.2  # если модель ещё не загружена

# Фоновый запуск Ollama
CMD ollama serve & python3 bot.py