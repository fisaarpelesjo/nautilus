import csv
import json
import os
from datetime import datetime
from pathlib import Path

TRADES_FILE  = "data/trades.csv"
SIGNALS_FILE = "data/signals.csv"
DECISIONS_FILE = "data/decisions.csv"
STATE_FILE   = "data/state.json"
OHLCV_DIR    = "data/ohlcv"

Path(OHLCV_DIR).mkdir(parents=True, exist_ok=True)

TRADE_HEADERS  = ["opened_at", "closed_at", "symbol", "side", "entry_price",
                  "exit_price", "quantity", "pnl_usdt", "pnl_pct", "exit_reason",
                  "balance_after"]
SIGNAL_HEADERS = ["timestamp", "symbol", "timeframe", "price", "signal",
                  "ema_fast", "ema_slow", "ema_trend", "rsi", "macd", "reason"]
DECISION_HEADERS = [
    "timestamp", "cycle_id", "symbol", "timeframe", "price", "signal",
    "decision", "in_position", "entry_opened", "blockers", "mtf_checked",
    "mtf_ok", "position_pnl_pct", "open", "high", "low", "close", "volume",
    "ema_fast", "ema_slow", "ema_trend", "rsi", "macd", "atr", "atr_pct",
    "volume_ma", "volume_ratio", "bb_upper", "bb_middle", "bb_lower",
    "trend_gap_pct", "bullish_cross", "bearish_cross", "trend_ok", "rsi_ok",
    "volume_ok", "bb_ok", "pullback_entry", "reason",
]

def _ensure_csv(path: str, headers: list):
    if not os.path.exists(path):
        with open(path, "w", newline="") as f:
            csv.writer(f).writerow(headers)

def log_trade(trade: dict):
    _ensure_csv(TRADES_FILE, TRADE_HEADERS)
    with open(TRADES_FILE, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=TRADE_HEADERS)
        w.writerow({k: trade.get(k, "") for k in TRADE_HEADERS})

def log_signal(signal: dict):
    _ensure_csv(SIGNALS_FILE, SIGNAL_HEADERS)
    with open(SIGNALS_FILE, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SIGNAL_HEADERS)
        w.writerow({k: signal.get(k, "") for k in SIGNAL_HEADERS})

def log_decision(decision: dict):
    _ensure_csv(DECISIONS_FILE, DECISION_HEADERS)
    with open(DECISIONS_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=DECISION_HEADERS)
        w.writerow({k: decision.get(k, "") for k in DECISION_HEADERS})

def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)

def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE) as f:
        return json.load(f)

def save_ohlcv(symbol: str, timeframe: str, df):
    import pandas as pd
    safe = symbol.replace("/", "")
    path = f"{OHLCV_DIR}/{safe}_{timeframe}.csv"
    if os.path.exists(path):
        existing = pd.read_csv(path, index_col="timestamp", parse_dates=True)
        df = pd.concat([existing, df])
        df = df[~df.index.duplicated(keep="last")].sort_index()
    df.to_csv(path)
