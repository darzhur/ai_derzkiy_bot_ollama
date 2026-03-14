import subprocess
import time
import requests
import os
import sys

# 1. Старт Ollama сервер
print("Запускаем Ollama...")
ollama_process = subprocess.Popen(["ollama", "serve"])

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# 2. Ждем, пока Ollama станет доступна
while True:
    try:
        r = requests.get(OLLAMA_URL)
        if r.status_code == 200:
            print("Ollama доступна, запускаем бот...")
            break
    except requests.exceptions.ConnectionError:
        print("Ждем Ollama...")
        time.sleep(1)

# 3. Запуск бота
os.execvp("python3", ["python3", "bot.py"])