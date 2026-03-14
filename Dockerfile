# Используем Python 3.11 slim
FROM python:3.11-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем все файлы проекта
COPY . /app

# Устанавливаем системные зависимости для python и Ollama (если нужны)
RUN apt-get update && \
    apt-get install -y curl git && \
    rm -rf /var/lib/apt/lists/*

# Создаём виртуальное окружение и устанавливаем зависимости
RUN python3 -m venv venv
RUN /bin/bash -c "source venv/bin/activate && pip install --no-cache-dir --upgrade pip"
RUN /bin/bash -c "source venv/bin/activate && pip install --no-cache-dir -r requirements.txt"

# Порт для локальной Ollama (если бот будет обращаться к локальной LLM)
EXPOSE 11434

# Команда запуска бота
CMD ["/bin/bash", "-c", "source venv/bin/activate && python bot.py"]