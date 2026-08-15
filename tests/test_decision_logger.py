from trading import decision_logger


class _FakeSignal:
    def __init__(self, signal, reason="test"):
        self.signal = signal
        self.reason = reason


def test_log_decision_snapshot_includes_regime_field(monkeypatch):
    from strategy.base import Signal
    from strategy.ema_rsi import EmaRsiStrategy

    logged = []
    monkeypatch.setattr(decision_logger, "log_decision", lambda decision: logged.append(decision))
    indicators = {
        "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1000.0,
        "ema_fast": 10.0, "ema_slow": 9.0, "ema_trend": 8.0, "rsi": 50.0, "macd": 0.1,
        "atr": 1.0, "volume_ma": 900.0, "bb_upper": 105.0, "bb_middle": 100.0, "bb_lower": 95.0,
        "regime": "trending",
    }
    row = {"decision": "compra aberta", "blockers": ""}

    decision_logger.log_decision_snapshot(
        1, "BTC/USDT", _FakeSignal(Signal.BUY), indicators, None, 100.0, row, strategy=EmaRsiStrategy(),
    )

    assert logged[0]["regime"] == "trending"
