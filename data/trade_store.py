import csv
from pathlib import Path
from typing import List

from data.csv_utils import ensure_csv
from data.paths import TRADES_FILE

TRADE_HEADERS = [
    "opened_at", "closed_at", "symbol", "side", "entry_price",
    "exit_price", "quantity", "pnl_usdt", "pnl_pct", "exit_reason",
    "balance_after", "client_order_id", "close_client_order_id",
]


def log_trade(trade: dict):
    ensure_csv(TRADES_FILE, TRADE_HEADERS)
    with open(TRADES_FILE, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=TRADE_HEADERS)
        w.writerow({k: trade.get(k, "") for k in TRADE_HEADERS})


def load_recent_trades(n: int = 10, path: str = TRADES_FILE) -> List[dict]:
    """Ultimas `n` linhas de trades.csv, mais antiga primeiro. Arquivo
    ausente/vazio vira lista vazia, nunca erro -- mesmo padrao ja usado em
    data/decisions_analysis.py _load_decisions()."""
    if not Path(path).exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[-n:]
