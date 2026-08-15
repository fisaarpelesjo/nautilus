import pandas as pd

from strategy.base import Signal
from strategy.ema_rsi import EmaRsiStrategy


def _strategy_with_indicators(monkeypatch, rows):
    strategy = EmaRsiStrategy()
    df = pd.DataFrame(rows)
    monkeypatch.setattr(strategy, "calculate_indicators", lambda _df: df)
    return strategy


def _prev_row():
    return {
        "close": 100.0, "ema_fast": 9.0, "ema_slow": 10.0, "ema_trend": 90.0,
        "rsi": 50.0, "volume": 150.0, "volume_ma": 100.0, "bb_upper": 105.0,
        "adx": 25.0, "regime": "trending", "atr": 1.0, "atr_ratio": 0.01,
    }


def _overextended_buy_row(volume=150.0, volume_ma=100.0, ema_trend=95.0):
    # preco (110) acima de bb_upper (105) -- "esticado" pelo filtro fixo atual.
    return {
        "close": 110.0, "ema_fast": 12.0, "ema_slow": 10.0, "ema_trend": ema_trend,
        "rsi": 55.0, "volume": volume, "volume_ma": volume_ma, "bb_upper": 105.0,
        "adx": 25.0, "regime": "trending", "atr": 1.0, "atr_ratio": 0.01,
    }


def test_generate_signal_blocks_overextended_buy_when_adaptive_bb_disabled(monkeypatch):
    from strategy import ema_rsi
    monkeypatch.setattr(ema_rsi, "ADAPTIVE_BOLLINGER_ENABLED", False)
    strategy = _strategy_with_indicators(monkeypatch, [_prev_row(), _overextended_buy_row()])

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.HOLD


def test_generate_signal_allows_overextended_buy_with_strong_trend_and_volume(monkeypatch):
    from strategy import ema_rsi
    monkeypatch.setattr(ema_rsi, "ADAPTIVE_BOLLINGER_ENABLED", True)
    # above_trend: close(110) > ema_trend(95); volume_ok: 150 >= 100*1.0
    strategy = _strategy_with_indicators(monkeypatch, [_prev_row(), _overextended_buy_row(volume=150.0, volume_ma=100.0, ema_trend=95.0)])

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.BUY


def test_generate_signal_blocks_overextended_buy_without_strong_trend(monkeypatch):
    from strategy import ema_rsi
    monkeypatch.setattr(ema_rsi, "ADAPTIVE_BOLLINGER_ENABLED", True)
    # above_trend falso: close(110) <= ema_trend(150)
    strategy = _strategy_with_indicators(monkeypatch, [_prev_row(), _overextended_buy_row(ema_trend=150.0)])

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.HOLD


def test_generate_signal_blocks_overextended_buy_without_strong_volume(monkeypatch):
    from strategy import ema_rsi
    monkeypatch.setattr(ema_rsi, "ADAPTIVE_BOLLINGER_ENABLED", True)
    # volume_ok falso: 50 < 100*1.0
    strategy = _strategy_with_indicators(monkeypatch, [_prev_row(), _overextended_buy_row(volume=50.0, volume_ma=100.0)])

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.HOLD


def test_high_volatility_block_takes_precedence_over_adaptive_bollinger_permission(monkeypatch):
    # Edge Case do spec.md: bloqueio de risco (volatilidade elevada) tem
    # precedencia sobre permissao de oportunidade (rompimento adaptativo).
    from strategy import ema_rsi
    monkeypatch.setattr(ema_rsi, "ADAPTIVE_BOLLINGER_ENABLED", True)
    monkeypatch.setattr(ema_rsi, "HIGH_VOLATILITY_FILTER_ENABLED", True)
    monkeypatch.setattr(ema_rsi, "HIGH_VOLATILITY_ATR_RATIO", 0.05)
    row = _overextended_buy_row(volume=150.0, volume_ma=100.0, ema_trend=95.0)
    row["atr_ratio"] = 0.20  # bem acima do limiar de 0.05
    strategy = _strategy_with_indicators(monkeypatch, [_prev_row(), row])

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.HOLD
    assert "volatil" in signal.reason.lower()
