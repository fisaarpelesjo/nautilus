import csv

from data import signal_store


def test_load_recent_signals_returns_empty_list_when_file_missing(tmp_path):
    missing_path = str(tmp_path / "signals.csv")

    result = signal_store.load_recent_signals(path=missing_path)

    assert result == []


def test_load_recent_signals_reads_last_n_rows(tmp_path):
    path = tmp_path / "signals.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=signal_store.SIGNAL_HEADERS)
        w.writeheader()
        for i in range(5):
            w.writerow({
                "timestamp": f"2026-01-0{i+1}", "symbol": "BTC/USDT", "timeframe": "4h",
                "price": str(100 + i), "signal": "BUY", "ema_fast": "1", "ema_slow": "1",
                "ema_trend": "1", "rsi": "50", "macd": "0.1", "reason": "test",
            })

    result = signal_store.load_recent_signals(n=2, path=str(path))

    assert len(result) == 2
    assert result[-1]["price"] == "104"
