import pandas as pd
import pytest

from backtesting.engine import (
    Trade,
    _annualized_return_pct,
    _calculate_advanced_metrics,
    edge_score_band,
    print_report,
    simulate_backtest,
)
from utils.display import _fmt_price
from strategy.base import Signal, TradeSignal


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
