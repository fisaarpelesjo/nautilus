
import pandas as pd

from strategy.base import Signal
from strategy.ema_rsi import EmaRsiStrategy, _classify_regime


def _strategy_with_indicators(monkeypatch, rows):
    strategy = EmaRsiStrategy()
    df = pd.DataFrame(rows)
    monkeypatch.setattr(strategy, "calculate_indicators", lambda _df: df)
    return strategy


def _buy_row(regime="trending"):
    return {
        "close": 110.0,
        "ema_fast": 12.0,
        "ema_slow": 10.0,
        "ema_trend": 95.0,
        "rsi": 55.0,
        "volume": 150.0,
        "volume_ma": 100.0,
        "bb_upper": 120.0,
        "adx": 25.0,
        "regime": regime,
        "atr": 1.0,
        "atr_ratio": 0.01,
    }


def _prev_row():
    return {
        "close": 100.0,
        "ema_fast": 9.0,
        "ema_slow": 10.0,
        "ema_trend": 90.0,
        "rsi": 50.0,
        "volume": 150.0,
        "volume_ma": 100.0,
        "bb_upper": 120.0,
        "adx": 25.0,
        "regime": "trending",
        "atr": 1.0,
        "atr_ratio": 0.01,
    }


def test_classify_regime_trending_when_adx_at_or_above_threshold():
    assert _classify_regime(20.0, threshold=20.0) == "trending"
    assert _classify_regime(30.0, threshold=20.0) == "trending"


def test_classify_regime_sideways_when_adx_below_threshold():
    assert _classify_regime(19.9, threshold=20.0) == "sideways"
    assert _classify_regime(0.0, threshold=20.0) == "sideways"


def test_classify_regime_indefinido_when_adx_is_nan():
    assert _classify_regime(float("nan"), threshold=20.0) == "indefinido"
    assert _classify_regime(None, threshold=20.0) == "indefinido"


def test_calculate_indicators_adds_adx_and_regime_columns():
    strategy = EmaRsiStrategy()
    n = 120
    # serie com tendencia clara de alta -- suficiente para o ADX estabilizar
    # apos o periodo de warmup (janela 14 + suavizacao).
    closes = [100.0 + i * 0.8 for i in range(n)]
    df = pd.DataFrame({
        "open":   closes,
        "high":   [c + 1.0 for c in closes],
        "low":    [c - 1.0 for c in closes],
        "close":  closes,
        "volume": [1000.0] * n,
    }, index=pd.date_range("2024-01-01", periods=n, freq="4h"))

    result = strategy.calculate_indicators(df)

    assert "adx" in result.columns
    assert "regime" in result.columns
    assert result["regime"].isin(["trending", "sideways", "indefinido"]).all()


def test_generate_signal_ignores_regime_when_filter_disabled(monkeypatch):
    from strategy import ema_rsi
    monkeypatch.setattr(ema_rsi, "REGIME_FILTER_ENABLED", False)
    strategy = _strategy_with_indicators(monkeypatch, [_prev_row(), _buy_row(regime="sideways")])

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.BUY


def test_generate_signal_blocks_buy_in_sideways_regime_when_filter_enabled(monkeypatch):
    from strategy import ema_rsi
    monkeypatch.setattr(ema_rsi, "REGIME_FILTER_ENABLED", True)
    strategy = _strategy_with_indicators(monkeypatch, [_prev_row(), _buy_row(regime="sideways")])

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.HOLD
    assert "regime" in signal.reason.lower() or "lateraliz" in signal.reason.lower()


def test_generate_signal_blocks_buy_in_indefinido_regime_when_filter_enabled(monkeypatch):
    from strategy import ema_rsi
    monkeypatch.setattr(ema_rsi, "REGIME_FILTER_ENABLED", True)
    strategy = _strategy_with_indicators(monkeypatch, [_prev_row(), _buy_row(regime="indefinido")])

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.HOLD


def test_generate_signal_does_not_block_sell_when_regime_filter_enabled(monkeypatch):
    # Regressao (achado de code-review): o filtro de regime bloqueava HOLD
    # para QUALQUER sinal (inclusive venda) quando o regime era sideways/
    # indefinido -- FR-002/FR-005 escopam o bloqueio a "novas entradas", nao
    # a saida de uma posicao ja aberta.
    from strategy import ema_rsi
    monkeypatch.setattr(ema_rsi, "REGIME_FILTER_ENABLED", True)
    sell_prev = {
        "close": 110.0, "ema_fast": 12.0, "ema_slow": 10.0, "ema_trend": 90.0,
        "rsi": 50.0, "volume": 150.0, "volume_ma": 100.0, "bb_upper": 120.0,
        "adx": 10.0, "regime": "sideways", "atr": 1.0, "atr_ratio": 0.01,
    }
    sell_curr = {
        "close": 100.0, "ema_fast": 9.0, "ema_slow": 10.0, "ema_trend": 90.0,
        "rsi": 45.0, "volume": 150.0, "volume_ma": 100.0, "bb_upper": 120.0,
        "adx": 10.0, "regime": "sideways", "atr": 1.0, "atr_ratio": 0.01,
    }
    strategy = _strategy_with_indicators(monkeypatch, [sell_prev, sell_curr])

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.SELL


def test_generate_signal_allows_buy_in_trending_regime_when_filter_enabled(monkeypatch):
    from strategy import ema_rsi
    monkeypatch.setattr(ema_rsi, "REGIME_FILTER_ENABLED", True)
    strategy = _strategy_with_indicators(monkeypatch, [_prev_row(), _buy_row(regime="trending")])

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.BUY
