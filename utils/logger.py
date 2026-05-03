import logging
import json
from datetime import datetime
import os

LOG_DIR = "logs"

os.makedirs(LOG_DIR, exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # sem output no terminal — tudo vai pro arquivo
    file_handler = logging.FileHandler(f"{LOG_DIR}/{datetime.now().strftime('%Y-%m-%d')}.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))

    logger.addHandler(file_handler)
    return logger


def log_event(event: str, **fields):
    os.makedirs(LOG_DIR, exist_ok=True)
    payload = {
        "timestamp": datetime.now().isoformat(),
        "event": event,
        **fields,
    }
    path = f"{LOG_DIR}/events-{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
