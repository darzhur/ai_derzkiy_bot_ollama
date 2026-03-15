from logtail import LogtailHandler
import logging
import os

SOURCE_TOKEN = os.getenv("SRC_TOKEN")
logger = logging.getLogger("test_logger")
logger.setLevel(logging.INFO)

if SOURCE_TOKEN:
    logger.addHandler(LogtailHandler(source_token=SOURCE_TOKEN))

logger.info("Тестовое сообщение в BetterStack")