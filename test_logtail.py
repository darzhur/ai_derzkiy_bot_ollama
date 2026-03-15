import logging
from logtail import LogtailHandler
import time
import os

SOURCE_TOKEN = os.getenv("SRC_TOKEN")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if SOURCE_TOKEN:
    logger.addHandler(LogtailHandler(source_token=SOURCE_TOKEN))

logger.info("Тестовое сообщение для Logtail")

# Ждём 2 секунды, чтобы лог успел отправиться
time.sleep(2)