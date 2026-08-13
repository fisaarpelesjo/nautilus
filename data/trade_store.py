import csv

from data.csv_utils import ensure_csv
from data.paths import TRADES_FILE

TRADE_HEADERS = [
    "opened_at", "closed_at", "symbol", "side", "entry_price",
    "exit_price", "quantity", "pnl_usdt", "pnl_pct", "exit_reason",
    "balance_after", "client_order_id",
]


def log_trade(trade: dict):
    ensure_csv(TRADES_FILE, TRADE_HEADERS)
    with open(TRADES_FILE, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=TRADE_HEADERS)
        w.writerow({k: trade.get(k, "") for k in TRADE_HEADERS})
