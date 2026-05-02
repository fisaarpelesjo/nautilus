from pathlib import Path

TRADES_FILE = "data/trades.csv"
SIGNALS_FILE = "data/signals.csv"
DECISIONS_FILE = "data/decisions.csv"
STATE_FILE = "data/state.json"
OHLCV_DIR = "data/ohlcv"

Path(OHLCV_DIR).mkdir(parents=True, exist_ok=True)
