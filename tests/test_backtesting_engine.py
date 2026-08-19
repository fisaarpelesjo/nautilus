import pandas as pd
import pytest

from backtesting import engine
from backtesting.engine import (
    Trade,
    _annualized_return_pct,
    _calculate_advanced_metrics,
    edge_score_band,
    print_report,
    run_backtest,
    simulate_backtest,
)
from strategy.ema_rsi import EmaRsiStrategy
from utils.display import _fmt_price
from strategy.base import BaseStrategy, Signal, TradeSignal


class SequenceStrategy:
    def __init__(self, signals):
        self.signals = list(signals)

    def generate_signal(self, _df):
        if self.signals:
            return TradeSignal(self.signals.pop(0), 100.0, "test")
        return TradeSignal(Signal.HOLD, 100.0, "test")


def _df(rows):
    index = pd.date_range("2026-01-01", periods=len(rows), freq="h")
    return pd.DataFrame(rows, index=index)


def test_simulate_backtest_applies_fees_and_slippage_on_take_profit():
    data = _df([
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0},
        {"open": 100.0, "high": 107.0, "low": 99.0, "close": 105.0, "volume": 1.0},
        {"open": 108.0, "high": 112.0, "low": 107.0, "close": 110.0, "volume": 1.0},
    ])
    strategy = SequenceStrategy([Signal.BUY, Signal.HOLD])

    result = simulate_backtest(
        data,
        strategy,
        initial_capital=1000.0,
        start_index=1,
        fee_rate=0.001,
        slippage_pct=0.001,
    )

    assert result.total_trades == 1
    trade = result.trades[0]
    assert trade.exit_reason == "Take Profit"
    assert trade.entry_price > 105.0
    assert trade.exit_price < trade.entry_price * 1.06
    assert trade.fees > 0


def test_simulate_backtest_caps_atr_stop_loss_at_max_stop_loss_pct(monkeypatch):
    # Achado de auditoria: _stop_price() tinha seu proprio piso independente
    # (entry_price * 0.5), desalinhado do teto MAX_STOP_LOSS_PCT que
    # risk/manager.py calculate_risk() aplica em paper/live -- um backtest
    # simulava o bot sobrevivendo a quedas bem piores do que o bot real
    # toleraria num par de ATR largo, distorcendo o veredito de aprovacao.
    monkeypatch.setattr(engine, "MAX_STOP_LOSS_PCT", 0.08)
    data = _df([
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0, "atr": 13.3},
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0, "atr": 13.3},
        {"open": 90.0, "high": 95.0, "low": 85.0, "close": 90.0, "volume": 1.0, "atr": 13.3},
    ])
    strategy = SequenceStrategy([Signal.BUY, Signal.HOLD])

    # ATR_SL_MULTIPLIER default (1.5) x atr=13.3 colocaria o stop em ~80.05 (-20%),
    # que o low=85 do candle de saida NAO alcancaria -- so o teto de 8% (stop=92)
    # faz esse trade fechar por Stop Loss neste candle.
    result = simulate_backtest(data, strategy, start_index=1, fee_rate=0.0, slippage_pct=0.0)

    assert result.total_trades == 1
    trade = result.trades[0]
    assert trade.exit_reason == "Stop Loss"
    assert trade.exit_price == pytest.approx(92.0)


def test_simulate_backtest_closes_open_position_at_period_end():
    data = _df([
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0},
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0},
        {"open": 102.0, "high": 103.0, "low": 101.0, "close": 102.0, "volume": 1.0},
    ])
    strategy = SequenceStrategy([Signal.BUY, Signal.HOLD])

    result = simulate_backtest(data, strategy, start_index=1, fee_rate=0.0, slippage_pct=0.0)

    assert result.total_trades == 1
    assert result.trades[0].exit_reason == "Fim do periodo"


def test_simulate_backtest_calculates_advanced_metrics():
    data = _df([
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0},
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0},
        {"open": 100.0, "high": 101.0, "low": 98.0, "close": 99.0, "volume": 1.0},
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0},
        {"open": 100.0, "high": 107.0, "low": 99.0, "close": 106.0, "volume": 1.0},
    ])
    strategy = SequenceStrategy([Signal.BUY, Signal.HOLD, Signal.BUY, Signal.HOLD])

    result = simulate_backtest(
        data,
        strategy,
        initial_capital=1000.0,
        start_index=1,
        fee_rate=0.0,
        slippage_pct=0.0,
    )

    assert result.total_trades == 2
    assert result.profit_factor == 4.0
    assert result.expectancy == 2.25
    assert result.average_win == 6.0
    assert result.average_loss == -1.5
    assert result.largest_win == 6.0
    assert result.largest_loss == -1.5
    assert result.max_losing_streak == 1
    assert round(result.exposure_pct, 2) == 66.67
    assert result.sharpe > 0
    assert result.expectancy_pct > 0
    assert result.payoff_ratio == 4.0


def test_simulate_backtest_calculates_buy_hold_and_edge_metrics():
    data = _df([
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0},
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0},
        {"open": 120.0, "high": 121.0, "low": 119.0, "close": 120.0, "volume": 1.0},
    ])
    strategy = SequenceStrategy([Signal.HOLD, Signal.HOLD])

    result = simulate_backtest(data, strategy, start_index=1, fee_rate=0.0, slippage_pct=0.0)

    assert result.total_return_pct == 0.0
    assert result.buy_hold_return_pct == 20.0
    assert result.edge_return_pct == -20.0
    assert result.edge_score < 0


def test_print_report_records_edge_metrics(caplog):
    data = _df([
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0},
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0},
        {"open": 120.0, "high": 121.0, "low": 119.0, "close": 120.0, "volume": 1.0},
    ])
    result = simulate_backtest(data, SequenceStrategy([Signal.HOLD, Signal.HOLD]), start_index=1)

    print_report(result)

    output = caplog.text
    assert "RESULTADO DO BACKTEST" in output
    assert "Expectativa %" in output
    assert "Buy & hold" in output
    assert "Edge vs B&H" in output
    assert "Edge score" in output


def test_price_formatter_keeps_small_crypto_prices_visible():
    assert _fmt_price(0.00234567) == "$0.00234567"


def test_annualized_return_pct_uses_compound_interest_over_365_days():
    start = pd.Timestamp("2026-01-01")
    end = start + pd.Timedelta(days=365)

    result = _annualized_return_pct(10.0, start, end)

    assert result == pytest.approx(10.0, abs=0.01)  # exatamente 1 ano -> retorno = anualizado


def test_annualized_return_pct_compounds_short_period_up():
    start = pd.Timestamp("2026-01-01")
    end = start + pd.Timedelta(days=100)

    result = _annualized_return_pct(10.0, start, end)

    expected = ((1 + 10.0 / 100) ** (365 / 100) - 1) * 100
    assert result == pytest.approx(expected, abs=0.01)


def test_annualized_return_pct_is_zero_when_period_not_positive():
    same_instant = pd.Timestamp("2026-01-01")

    assert _annualized_return_pct(10.0, same_instant, same_instant) == 0.0
    assert _annualized_return_pct(10.0, None, None) == 0.0


def test_annualized_return_pct_handles_overflow_from_short_period_large_return():
    # Achado de /code-review medium: TIMEFRAME=1m + poucas horas de historico +
    # retorno acumulado grande faz growth_factor ** (365/period_days) estourar o
    # range de float (OverflowError), derrubando `python main.py backtest` sem
    # try/except nenhum no caminho.
    start = pd.Timestamp("2026-01-01")
    end = start + pd.Timedelta(minutes=1900)

    result = _annualized_return_pct(1300.0, start, end)

    assert result == float("inf")


def test_annualized_return_pct_handles_total_loss_without_complex_number():
    # 1 + (-150/100) = -0.5 <= 0 -- potencia fracionaria de base negativa vira
    # numero complexo silenciosamente em Python se nao tratado.
    start = pd.Timestamp("2026-01-01")
    end = start + pd.Timedelta(days=100)

    result = _annualized_return_pct(-150.0, start, end)

    assert result == -100.0
    assert isinstance(result, float)


def _trade(pnl_pct):
    now = pd.Timestamp("2026-01-01")
    return Trade(
        entry_price=100.0, exit_price=100.0 + pnl_pct, quantity=1.0, pnl=pnl_pct, pnl_pct=pnl_pct,
        fees=0.0, entry_time=now, exit_time=now, exit_reason="test",
    )


_PERIOD_START = pd.Timestamp("2026-01-01")
_PERIOD_END = _PERIOD_START + pd.Timedelta(days=100)


def test_sortino_uses_only_downside_deviation_differing_from_sharpe():
    # ganhos com alta variancia, perdas com baixa variancia -- Sharpe (desvio
    # geral) e Sortino (desvio so do downside) devem divergir.
    trades = [_trade(p) for p in [9.0, -1.0, 2.0, -1.2, 8.0, -0.8]]

    metrics = _calculate_advanced_metrics(
        trades, max_drawdown_pct=5.0, period_start=_PERIOD_START, period_end=_PERIOD_END,
    )

    assert metrics["sortino"] != pytest.approx(metrics["sharpe"])


def test_sortino_is_inf_without_losing_trades_and_positive_mean():
    trades = [_trade(p) for p in [5.0, 3.0, 4.0]]

    metrics = _calculate_advanced_metrics(
        trades, max_drawdown_pct=0.0, period_start=_PERIOD_START, period_end=_PERIOD_END,
    )

    assert metrics["sortino"] == float("inf")


def test_sortino_is_zero_with_single_losing_trade_and_nonpositive_mean():
    # 1 trade com prejuizo nao e suficiente para calcular desvio padrao (precisa
    # de >= 2 pontos) -- cai no fallback, igual profit_factor/payoff_ratio.
    trades = [_trade(p) for p in [-1.0]]

    metrics = _calculate_advanced_metrics(
        trades, max_drawdown_pct=1.0, period_start=_PERIOD_START, period_end=_PERIOD_END,
    )

    assert metrics["sortino"] == 0.0


def test_calmar_ratio_divides_annualized_return_by_max_drawdown():
    trades = [_trade(p) for p in [5.0, -2.0, 3.0]]

    metrics = _calculate_advanced_metrics(
        trades, total_return_pct=6.0, max_drawdown_pct=4.0,
        period_start=_PERIOD_START, period_end=_PERIOD_END,
    )

    expected_annualized = _annualized_return_pct(6.0, _PERIOD_START, _PERIOD_END)
    assert metrics["calmar"] == pytest.approx(expected_annualized / 4.0)


def test_calmar_ratio_is_inf_without_drawdown_and_positive_return():
    trades = [_trade(p) for p in [5.0, 3.0]]

    metrics = _calculate_advanced_metrics(
        trades, total_return_pct=8.0, max_drawdown_pct=0.0,
        period_start=_PERIOD_START, period_end=_PERIOD_END,
    )

    assert metrics["calmar"] == float("inf")


def test_calmar_ratio_is_zero_without_drawdown_and_nonpositive_return():
    trades = [_trade(p) for p in [-1.0, -2.0]]

    metrics = _calculate_advanced_metrics(
        trades, total_return_pct=0.0, max_drawdown_pct=0.0,
        period_start=_PERIOD_START, period_end=_PERIOD_END,
    )

    assert metrics["calmar"] == 0.0


def test_backtest_result_annualized_return_matches_shared_helper():
    trades = [_trade(p) for p in [5.0, -2.0, 3.0]]

    metrics = _calculate_advanced_metrics(
        trades, total_return_pct=6.0, max_drawdown_pct=4.0,
        period_start=_PERIOD_START, period_end=_PERIOD_END,
    )

    expected = _annualized_return_pct(6.0, _PERIOD_START, _PERIOD_END)
    assert metrics["annualized_return_pct"] == pytest.approx(expected)


def test_return_per_exposure_pct_divides_by_exposure_fraction():
    now = _PERIOD_START
    trades = [Trade(
        entry_price=100.0, exit_price=110.0, quantity=1.0, pnl=10.0, pnl_pct=10.0, fees=0.0,
        entry_time=now, exit_time=now + pd.Timedelta(days=10), exit_reason="test",
    )]

    metrics = _calculate_advanced_metrics(
        trades, total_return_pct=10.0, max_drawdown_pct=2.0,
        period_start=_PERIOD_START, period_end=_PERIOD_END,
    )

    assert metrics["exposure_pct"] > 0
    expected = 10.0 / (metrics["exposure_pct"] / 100)
    assert metrics["return_per_exposure_pct"] == pytest.approx(expected)


def test_return_per_exposure_pct_is_none_when_no_exposure():
    metrics = _calculate_advanced_metrics(
        [], total_return_pct=0.0, max_drawdown_pct=0.0,
        period_start=_PERIOD_START, period_end=_PERIOD_END,
    )

    assert metrics["exposure_pct"] == 0.0
    assert metrics["return_per_exposure_pct"] is None


def test_edge_score_band_matches_documented_thresholds():
    assert edge_score_band(20.0) == "Forte"
    assert edge_score_band(50.0) == "Forte"
    assert edge_score_band(19.99) == "Médio"
    assert edge_score_band(0.0) == "Médio"
    assert edge_score_band(-0.01) == "Fraco"
    assert edge_score_band(-20.0) == "Fraco"
    assert edge_score_band(-20.01) == "Reprovado"
    assert edge_score_band(-100.0) == "Reprovado"


def _synthetic_ohlcv(n=150):
    import pandas as pd
    return pd.DataFrame({
        "open": [100.0] * n, "high": [101.0] * n, "low": [99.0] * n,
        "close": [100.0] * n, "volume": [1000.0] * n,
    }, index=pd.date_range("2024-01-01", periods=n, freq="4h"))


class _RecordingStrategy(BaseStrategy):
    """Estrategia minima usada so para confirmar QUAL estrategia run_backtest usou."""
    def calculate_indicators(self, df):
        df = df.copy()
        df["atr"] = 0.0
        return df

    def generate_signal(self, df):
        return TradeSignal(Signal.HOLD, df.iloc[-1]["close"] if len(df) else 0, "recording")


def test_run_backtest_defaults_to_ema_rsi_strategy_when_none_passed(monkeypatch):
    monkeypatch.setattr(engine, "fetch_ohlcv", lambda symbol, timeframe, limit=2000: _synthetic_ohlcv())
    used_strategies = []
    original_simulate = engine.simulate_backtest

    def _spy_simulate(df, strategy, **kwargs):
        used_strategies.append(strategy)
        return original_simulate(df, strategy, **kwargs)

    monkeypatch.setattr(engine, "simulate_backtest", _spy_simulate)
    monkeypatch.setattr(engine, "print_report", lambda result: None)

    run_backtest("BTC/USDT", "4h")

    assert len(used_strategies) == 1
    assert isinstance(used_strategies[0], EmaRsiStrategy)


def test_run_backtest_uses_passed_strategy_instead_of_default(monkeypatch):
    monkeypatch.setattr(engine, "fetch_ohlcv", lambda symbol, timeframe, limit=2000: _synthetic_ohlcv())
    monkeypatch.setattr(engine, "print_report", lambda result: None)
    custom = _RecordingStrategy()

    result = run_backtest("BTC/USDT", "4h", strategy=custom)

    assert result is not None


def test_run_backtest_produces_full_report_with_breakout_strategy(monkeypatch):
    from strategy.breakout import BreakoutStrategy

    # serie com variacao suficiente para produzir alguns rompimentos reais
    # dentro de uma janela de 200 candles.
    n = 260
    closes = [100.0 + (i % 40) * 0.5 - (i // 40) * 0.3 for i in range(n)]
    df = pd.DataFrame({
        "open": closes, "high": [c + 1.0 for c in closes], "low": [c - 1.0 for c in closes],
        "close": closes, "volume": [1000.0] * n,
    }, index=pd.date_range("2024-01-01", periods=n, freq="4h"))
    monkeypatch.setattr(engine, "fetch_ohlcv", lambda symbol, timeframe, limit=2000: df)
    monkeypatch.setattr(engine, "print_report", lambda result: None)

    result = run_backtest("BTC/USDT", "4h", strategy=BreakoutStrategy(window=50))

    assert result is not None
    assert hasattr(result, "edge_score")
    assert hasattr(result, "sortino")


def _prepared_df_for_buy_signal(regime="trending", atr_ratio=0.01):
    # 2 candles com um cruzamento EMA de alta claro no segundo -- replica o
    # mesmo cenario ja usado em tests/test_strategy_ema_rsi.py para BUY.
    index = pd.date_range("2026-01-01", periods=2, freq="h")
    return pd.DataFrame({
        "close":     [100.0, 110.0],
        "open":      [100.0, 105.0],
        "low":       [99.0, 108.0],
        "ema_fast":  [9.0, 12.0],
        "ema_slow":  [10.0, 10.0],
        "ema_trend": [90.0, 95.0],
        "rsi":       [50.0, 55.0],
        "volume":    [150.0, 150.0],
        "volume_ma": [100.0, 100.0],
        "bb_upper":  [120.0, 120.0],
        "regime":    [regime, regime],
        "atr_ratio": [atr_ratio, atr_ratio],
    }, index=index)


def test_precompute_signals_blocks_buy_in_sideways_regime_when_filter_enabled(monkeypatch):
    # Regressao (achado de code-review): precompute_signals() -- caminho
    # vetorizado usado por optimize/backtest --validate/optimize
    # --walk-forward -- nao respeitava REGIME_FILTER_ENABLED, divergindo do
    # caminho por candle (generate_signal) usado por backtest/edge/compare.
    monkeypatch.setattr(engine, "REGIME_FILTER_ENABLED", True)
    df = _prepared_df_for_buy_signal(regime="sideways")
    strategy = EmaRsiStrategy()

    signals = engine.precompute_signals(df, strategy)

    assert signals.iloc[-1] == Signal.HOLD


def test_precompute_signals_allows_buy_in_trending_regime_when_filter_enabled(monkeypatch):
    monkeypatch.setattr(engine, "REGIME_FILTER_ENABLED", True)
    df = _prepared_df_for_buy_signal(regime="trending")
    strategy = EmaRsiStrategy()

    signals = engine.precompute_signals(df, strategy)

    assert signals.iloc[-1] == Signal.BUY


def test_precompute_signals_blocks_buy_on_high_volatility_when_filter_enabled(monkeypatch):
    monkeypatch.setattr(engine, "HIGH_VOLATILITY_FILTER_ENABLED", True)
    monkeypatch.setattr(engine, "HIGH_VOLATILITY_ATR_RATIO", 0.05)
    df = _prepared_df_for_buy_signal(atr_ratio=0.20)
    strategy = EmaRsiStrategy()

    signals = engine.precompute_signals(df, strategy)

    assert signals.iloc[-1] == Signal.HOLD


def _prepared_df_for_overbought_crossover(volume=250.0, volume_ma=100.0, rsi=85.0):
    index = pd.date_range("2026-01-01", periods=2, freq="h")
    return pd.DataFrame({
        "close":     [100.0, 110.0],
        "open":      [100.0, 105.0],
        "low":       [99.0, 108.0],
        "ema_fast":  [9.0, 12.0],
        "ema_slow":  [10.0, 10.0],
        "ema_trend": [90.0, 95.0],
        "rsi":       [50.0, rsi],
        "volume":    [150.0, volume],
        "volume_ma": [100.0, volume_ma],
        "bb_upper":  [120.0, 120.0],
        "regime":    ["trending", "trending"],
        "atr_ratio": [0.01, 0.01],
    }, index=index)


def test_precompute_signals_blocks_overbought_crossover_when_adaptive_rsi_disabled(monkeypatch):
    monkeypatch.setattr(engine, "ADAPTIVE_RSI_ENABLED", False)
    df = _prepared_df_for_overbought_crossover()
    strategy = EmaRsiStrategy()

    signals = engine.precompute_signals(df, strategy)

    assert signals.iloc[-1] == Signal.HOLD


def test_precompute_signals_allows_overbought_crossover_with_strong_volume(monkeypatch):
    monkeypatch.setattr(engine, "ADAPTIVE_RSI_ENABLED", True)
    monkeypatch.setattr(engine, "ADAPTIVE_RSI_VOLUME_RATIO", 2.0)
    df = _prepared_df_for_overbought_crossover(volume=250.0, volume_ma=100.0, rsi=85.0)
    strategy = EmaRsiStrategy()

    signals = engine.precompute_signals(df, strategy)

    assert signals.iloc[-1] == Signal.BUY


def test_precompute_signals_matches_generate_signal_for_adaptive_rsi(monkeypatch):
    # Consistencia entre os dois caminhos (vetorizado e por-candle) -- mesmo
    # cenario coberto em tests/test_strategy_adaptive_rsi.py.
    monkeypatch.setattr(engine, "ADAPTIVE_RSI_ENABLED", True)
    monkeypatch.setattr(engine, "ADAPTIVE_RSI_VOLUME_RATIO", 2.0)
    from strategy import ema_rsi
    monkeypatch.setattr(ema_rsi, "ADAPTIVE_RSI_ENABLED", True)
    monkeypatch.setattr(ema_rsi, "ADAPTIVE_RSI_VOLUME_RATIO", 2.0)
    df = _prepared_df_for_overbought_crossover(volume=250.0, volume_ma=100.0, rsi=85.0)
    strategy = EmaRsiStrategy()
    monkeypatch.setattr(strategy, "calculate_indicators", lambda _df: df)

    vectorized = engine.precompute_signals(df, strategy)
    per_candle = strategy.generate_signal(pd.DataFrame()).signal

    assert vectorized.iloc[-1] == per_candle == Signal.BUY


def test_precompute_signals_matches_generate_signal_when_all_filters_enabled(monkeypatch):
    # Consistencia entre os dois caminhos (vetorizado e por-candle) --
    # exatamente o que divergia antes desta correcao.
    monkeypatch.setattr(engine, "REGIME_FILTER_ENABLED", True)
    from strategy import ema_rsi
    monkeypatch.setattr(ema_rsi, "REGIME_FILTER_ENABLED", True)
    df = _prepared_df_for_buy_signal(regime="sideways")
    strategy = EmaRsiStrategy()
    monkeypatch.setattr(strategy, "calculate_indicators", lambda _df: df)

    vectorized = engine.precompute_signals(df, strategy)
    per_candle = strategy.generate_signal(pd.DataFrame()).signal

    assert vectorized.iloc[-1] == per_candle == Signal.HOLD
