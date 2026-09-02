from pathlib import Path

TRADES_FILE = "data/trades.csv"
SIGNALS_FILE = "data/signals.csv"
DECISIONS_FILE = "data/decisions.csv"
STATE_FILE = "data/state.json"
KILLSWITCH_FILE = "data/killswitch.json"
ARBITRAGEM_FILE = "data/arbitragem.jsonl"
OHLCV_DIR = "data/ohlcv"

Path(OHLCV_DIR).mkdir(parents=True, exist_ok=True)
