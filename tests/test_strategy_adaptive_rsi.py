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


def _overbought_crossover_row(rsi=85.0, volume=250.0, volume_ma=100.0):
    # Crossover valido (ema_fast 12 > ema_slow 10, prev era 9 < 10), preco nao
    # esticado (close 110 <= bb_upper 115), acima da tendencia (ema_trend 95).
    return {
        "close": 110.0, "ema_fast": 12.0, "ema_slow": 10.0, "ema_trend": 95.0,
        "rsi": rsi, "volume": volume, "volume_ma": volume_ma, "bb_upper": 115.0,
        "adx": 25.0, "regime": "trending", "atr": 1.0, "atr_ratio": 0.01,
    }


def test_generate_signal_blocks_overbought_crossover_when_adaptive_rsi_disabled(monkeypatch):
    from strategy import ema_rsi
    monkeypatch.setattr(ema_rsi, "ADAPTIVE_RSI_ENABLED", False)
    # volume 250 >= 100*2.0 (teria confirmado se o filtro estivesse ligado)
    strategy = _strategy_with_indicators(monkeypatch, [_prev_row(), _overbought_crossover_row()])

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.HOLD


def test_generate_signal_allows_overbought_crossover_with_strong_volume(monkeypatch):
    from strategy import ema_rsi
    monkeypatch.setattr(ema_rsi, "ADAPTIVE_RSI_ENABLED", True)
    monkeypatch.setattr(ema_rsi, "ADAPTIVE_RSI_VOLUME_RATIO", 2.0)
    # rsi=85 (acima do RSI_OVERBOUGHT=70 default), volume 250 = 2.5x a media (100)
    strategy = _strategy_with_indicators(monkeypatch, [_prev_row(), _overbought_crossover_row(rsi=85.0, volume=250.0, volume_ma=100.0)])

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.BUY


def test_generate_signal_blocks_overbought_crossover_without_strong_enough_volume(monkeypatch):
    from strategy import ema_rsi
    monkeypatch.setattr(ema_rsi, "ADAPTIVE_RSI_ENABLED", True)
    monkeypatch.setattr(ema_rsi, "ADAPTIVE_RSI_VOLUME_RATIO", 2.0)
    # volume 120 passa no volume_ok normal (>= 1.0x) mas nao no teto adaptativo (>= 2.0x)
    strategy = _strategy_with_indicators(monkeypatch, [_prev_row(), _overbought_crossover_row(rsi=85.0, volume=120.0, volume_ma=100.0)])

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.HOLD


def test_adaptive_rsi_does_not_relax_pullback_rsi_ceiling(monkeypatch):
    # Decisao de design: ADAPTIVE_RSI_ENABLED so afeta o crossover, nao o
    # pullback (cenario diferente -- recuo controlado numa tendencia ja
    # estabelecida, nao um pico vertical). Pullback com RSI acima do teto
    # continua bloqueado mesmo com volume forte e o filtro ligado.
    from strategy import ema_rsi
    monkeypatch.setattr(ema_rsi, "ADAPTIVE_RSI_ENABLED", True)
    monkeypatch.setattr(ema_rsi, "ADAPTIVE_RSI_VOLUME_RATIO", 2.0)
    row = {
        # Tendencia estabelecida (fast > slow > trend) sem crossover neste candle.
        "close": 100.5, "ema_fast": 11.0, "ema_slow": 10.0, "ema_trend": 9.0,
        "rsi": 85.0,  # acima do RSI_OVERBOUGHT (70) e do teto de pullback
        "volume": 250.0, "volume_ma": 100.0, "bb_upper": 115.0,
        "adx": 25.0, "regime": "trending", "atr": 1.0, "atr_ratio": 0.01,
        "low": 99.0, "open": 99.5,
    }
    prev = dict(row, ema_fast=11.0, ema_slow=10.0)  # sem crossover (fast ja estava acima)
    strategy = _strategy_with_indicators(monkeypatch, [prev, row])

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.HOLD
