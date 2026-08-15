import csv
from pathlib import Path
from typing import List

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


def load_recent_signals(n: int = 10, path: str = SIGNALS_FILE) -> List[dict]:
    """Ultimas `n` linhas de signals.csv, mais antiga primeiro. Arquivo
    ausente/vazio vira lista vazia, nunca erro -- mesmo padrao ja usado em
    data/decisions_analysis.py _load_decisions()."""
    if not Path(path).exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[-n:]
