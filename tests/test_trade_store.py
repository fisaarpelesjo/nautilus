from data import trade_store


def test_load_recent_trades_returns_empty_list_when_file_missing(tmp_path):
    missing_path = str(tmp_path / "trades.csv")

    result = trade_store.load_recent_trades(path=missing_path)

    assert result == []


def test_load_recent_trades_reads_last_n_rows(tmp_path):
    path = tmp_path / "trades.csv"
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=trade_store.TRADE_HEADERS)
        w.writeheader()
        for i in range(5):
            w.writerow({
                "opened_at": f"2026-01-0{i+1}", "closed_at": f"2026-01-0{i+1}",
                "symbol": "BTC/USDT", "side": "long", "entry_price": "100",
                "exit_price": "110", "quantity": "1", "pnl_usdt": str(i),
                "pnl_pct": "1.0", "exit_reason": "take profit",
                "balance_after": "1000", "client_order_id": "", "close_client_order_id": "",
            })

    result = trade_store.load_recent_trades(n=2, path=str(path))

    assert len(result) == 2
    assert result[-1]["pnl_usdt"] == "4"  # ultima linha do arquivo
