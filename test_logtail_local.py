from logtail import LogtailHandler
import logging
import os
from dotenv import load_dotenv

load_dotenv()
SRC_TOKEN = os.getenv("SRC_TOKEN")

logger = logging.getLogger("test")
logger.setLevel(logging.INFO)

if SRC_TOKEN:
    handler = LogtailHandler(source_token=SRC_TOKEN)
    logger.addHandler(handler)
    logger.info("Тестовое сообщение Logtail")
    print("Лог должен отправиться в BetterStack")
else:
    print("SRC_TOKEN не найден")