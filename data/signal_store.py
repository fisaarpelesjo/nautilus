import csv

from data.csv_utils import ensure_csv
from data.paths import SIGNALS_FILE

SIGNAL_HEADERS = [
    "timestamp", "symbol", "timeframe", "price", "signal",
    "ema_fast", "ema_slow", "ema_trend", "rsi", "macd", "reason",
]


def log_signal(signal: dict):
    ensure_csv(SIGNALS_FILE, SIGNAL_HEADERS)
    with open(SIGNALS_FILE, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SIGNAL_HEADERS)
        w.writerow({k: signal.get(k, "") for k in SIGNAL_HEADERS})
