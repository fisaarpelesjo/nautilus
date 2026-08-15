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
        "rsi": 50.0, "volume": 150.0, "volume_ma": 100.0, "bb_upper": 120.0,
        "adx": 25.0, "regime": "trending", "atr": 1.0, "atr_ratio": 0.01,
    }


def _buy_row(atr_ratio=0.01):
    return {
        "close": 110.0, "ema_fast": 12.0, "ema_slow": 10.0, "ema_trend": 95.0,
        "rsi": 55.0, "volume": 150.0, "volume_ma": 100.0, "bb_upper": 120.0,
        "adx": 25.0, "regime": "trending", "atr": 110.0 * atr_ratio, "atr_ratio": atr_ratio,
    }


def test_calculate_indicators_adds_atr_ratio_column():
    strategy = EmaRsiStrategy()
    n = 100
    closes = [100.0 + i * 0.2 for i in range(n)]
    df = pd.DataFrame({
        "open":   closes,
        "high":   [c + 1.0 for c in closes],
        "low":    [c - 1.0 for c in closes],
        "close":  closes,
        "volume": [1000.0] * n,
    }, index=pd.date_range("2024-01-01", periods=n, freq="4h"))

    result = strategy.calculate_indicators(df)

    assert "atr_ratio" in result.columns
    assert (result["atr_ratio"] >= 0).all()


def test_generate_signal_ignores_high_volatility_when_filter_disabled(monkeypatch):
    from strategy import ema_rsi
    monkeypatch.setattr(ema_rsi, "HIGH_VOLATILITY_FILTER_ENABLED", False)
    strategy = _strategy_with_indicators(monkeypatch, [_prev_row(), _buy_row(atr_ratio=0.20)])

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.BUY


def test_generate_signal_blocks_buy_when_atr_ratio_above_threshold_and_filter_enabled(monkeypatch):
    from strategy import ema_rsi
    monkeypatch.setattr(ema_rsi, "HIGH_VOLATILITY_FILTER_ENABLED", True)
    monkeypatch.setattr(ema_rsi, "HIGH_VOLATILITY_ATR_RATIO", 0.05)
    strategy = _strategy_with_indicators(monkeypatch, [_prev_row(), _buy_row(atr_ratio=0.20)])

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.HOLD
    assert "volatil" in signal.reason.lower()


def test_generate_signal_does_not_block_sell_when_volatility_filter_enabled(monkeypatch):
    # Regressao (mesma classe de achado do filtro de regime): volatilidade
    # elevada so deve bloquear novas entradas, nunca a saida de uma posicao.
    from strategy import ema_rsi
    monkeypatch.setattr(ema_rsi, "HIGH_VOLATILITY_FILTER_ENABLED", True)
    monkeypatch.setattr(ema_rsi, "HIGH_VOLATILITY_ATR_RATIO", 0.05)
    sell_prev = {
        "close": 110.0, "ema_fast": 12.0, "ema_slow": 10.0, "ema_trend": 90.0,
        "rsi": 50.0, "volume": 150.0, "volume_ma": 100.0, "bb_upper": 120.0,
        "adx": 25.0, "regime": "trending", "atr": 22.0, "atr_ratio": 0.20,
    }
    sell_curr = {
        "close": 100.0, "ema_fast": 9.0, "ema_slow": 10.0, "ema_trend": 90.0,
        "rsi": 45.0, "volume": 150.0, "volume_ma": 100.0, "bb_upper": 120.0,
        "adx": 25.0, "regime": "trending", "atr": 20.0, "atr_ratio": 0.20,
    }
    strategy = _strategy_with_indicators(monkeypatch, [sell_prev, sell_curr])

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.SELL


def test_calculate_indicators_atr_ratio_is_nan_not_inf_when_close_is_zero():
    # Regressao (achado de code-review): atr/close sem guarda vira +inf
    # quando close==0 (candle invalido/par congelado) -- +inf nao e removido
    # por dropna() (so NaN e), furando o caminho de "dado desconhecido" que
    # o filtro de volatilidade elevada espera. A linha inteira deve ser
    # descartada pelo dropna() ja existente, nao sobreviver com atr_ratio=inf.
    strategy = EmaRsiStrategy()
    n = 100
    closes = [100.0 + i * 0.2 for i in range(n)]
    closes[-1] = 0.0  # ultimo candle invalido
    df = pd.DataFrame({
        "open":   [100.0] * n,
        "high":   [c + 1.0 for c in closes],
        "low":    [max(c - 1.0, 0.0) for c in closes],
        "close":  closes,
        "volume": [1000.0] * n,
    }, index=pd.date_range("2024-01-01", periods=n, freq="4h"))

    result = strategy.calculate_indicators(df)

    assert not (result["atr_ratio"] == float("inf")).any()
    # candle com close==0 foi descartado pelo dropna(), nao sobrevive com
    # indicadores invalidos.
    assert 0.0 not in result["close"].values


def test_generate_signal_allows_buy_when_atr_ratio_within_normal_range(monkeypatch):
    from strategy import ema_rsi
    monkeypatch.setattr(ema_rsi, "HIGH_VOLATILITY_FILTER_ENABLED", True)
    monkeypatch.setattr(ema_rsi, "HIGH_VOLATILITY_ATR_RATIO", 0.05)
    strategy = _strategy_with_indicators(monkeypatch, [_prev_row(), _buy_row(atr_ratio=0.01)])

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.BUY
