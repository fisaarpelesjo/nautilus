import sys

import main


def test_debug_command_is_registered():
    assert "debug" in main.COMMANDS


def test_cmd_debug_prints_full_diagnosis_for_pair(monkeypatch):
    import pandas as pd

    monkeypatch.setattr(sys, "argv", ["main.py", "debug", "BTC/USDT"])

    n = 120
    closes = [100.0 + i * 0.1 for i in range(n)]
    df = pd.DataFrame({
        "open": closes, "high": [c + 1.0 for c in closes], "low": [c - 1.0 for c in closes],
        "close": closes, "volume": [1000.0] * n,
    }, index=pd.date_range("2024-01-01", periods=n, freq="4h"))

    monkeypatch.setattr("data.fetcher.fetch_ohlcv", lambda symbol, timeframe: df)
    monkeypatch.setattr("trading.position_lifecycle.mtf_confirmed", lambda symbol, price, strategy: True)

    from execution import order_manager
    monkeypatch.setattr(order_manager, "TRADING_MODE", "paper")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})

    printed = []
    from utils import display
    monkeypatch.setattr(display.console, "print", lambda *args, **kwargs: printed.append(str(args)))

    main.cmd_debug()

    joined = " ".join(printed)
    assert "BTC/USDT" in joined
