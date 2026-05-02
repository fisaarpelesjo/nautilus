import csv

from data.csv_utils import ensure_csv
from data.paths import DECISIONS_FILE

DECISION_HEADERS = [
    "timestamp", "cycle_id", "symbol", "timeframe", "price", "signal",
    "decision", "in_position", "entry_opened", "blockers", "mtf_checked",
    "mtf_ok", "position_pnl_pct", "open", "high", "low", "close", "volume",
    "ema_fast", "ema_slow", "ema_trend", "rsi", "macd", "atr", "atr_pct",
    "volume_ma", "volume_ratio", "bb_upper", "bb_middle", "bb_lower",
    "trend_gap_pct", "bullish_cross", "bearish_cross", "trend_ok", "rsi_ok",
    "volume_ok", "bb_ok", "pullback_entry", "reason",
]


def log_decision(decision: dict):
    ensure_csv(DECISIONS_FILE, DECISION_HEADERS)
    with open(DECISIONS_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=DECISION_HEADERS)
        w.writerow({k: decision.get(k, "") for k in DECISION_HEADERS})
