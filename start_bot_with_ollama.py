import os
import requests
import time

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Ждем доступности Ollama
while True:
    try:
        r = requests.get(OLLAMA_URL)
        if r.status_code == 200:
            print("Ollama доступна, запускаем бота...")
            break
    except requests.exceptions.ConnectionError:
        print("Ждем Ollama...")
        time.sleep(1)

os.execvp("python3", ["python3", "bot.py"])