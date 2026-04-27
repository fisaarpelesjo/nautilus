import logging
from datetime import datetime
import os

os.makedirs("logs", exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # sem output no terminal — tudo vai pro arquivo
    file_handler = logging.FileHandler(f"logs/{datetime.now().strftime('%Y-%m-%d')}.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))

    logger.addHandler(file_handler)
    return logger
