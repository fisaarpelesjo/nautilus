import pandas as pd

from backtesting.engine import BacktestResult, precompute_signals
from backtesting.validation import evaluate_validation, split_train_validation
from strategy.base import Signal
from strategy.ema_rsi import EmaRsiParams, EmaRsiStrategy


def _synthetic_df(n):
    index = pd.date_range("2026-01-01", periods=n, freq="h")
    return pd.DataFrame({"close": range(n)}, index=index)


def test_split_train_validation_is_contiguous_non_overlapping_and_unshuffled():
    df = _synthetic_df(500)

    train, validation = split_train_validation(df, validation_ratio=0.3)

    assert validation is not None
    assert len(train) + len(validation) == len(df)
    assert train.index[-1] < validation.index[0]
    assert abs(len(validation) / len(df) - 0.3) < 0.01
    pd.testing.assert_frame_equal(pd.concat([train, validation]), df)


def test_split_train_validation_returns_none_when_insufficient_data():
    df = _synthetic_df(100)  # menor que a janela minima exigida para as duas fatias

    train, validation = split_train_validation(df, validation_ratio=0.3)

    assert validation is None
    assert len(train) == len(df)


def test_signals_sliced_after_full_df_precompute_detect_boundary_crossover():
    # Cruzamento de EMA que acontece exatamente no primeiro candle da fatia de
    # validacao (split_idx). Se os sinais forem recomputados so sobre a fatia
    # (em vez de calculados no df inteiro e so entao fatiados), o .shift(1)
    # perde o contexto da linha anterior (do lado do treino) e o cruzamento
    # some -- exatamente o bug do achado da rodada de review desta US3.
    n = 10
    split_idx = 5
    index = pd.date_range("2026-01-01", periods=n, freq="h")
    ema_fast = [9.0] * split_idx + [11.0] * (n - split_idx)
    ema_slow = [10.0] * n
    df = pd.DataFrame({
        "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0,
        "volume": 10.0, "volume_ma": 5.0,
        "ema_fast": ema_fast, "ema_slow": ema_slow, "ema_trend": 90.0,
        "bb_upper": 200.0, "rsi": 50.0,
    }, index=index)

    strategy = EmaRsiStrategy(EmaRsiParams(pullback_entry_enabled=False))

    signals_full = precompute_signals(df, strategy)
    validation_df = df.iloc[split_idx:]
    sliced_from_full = signals_full.loc[validation_df.index]
    recomputed_from_slice = precompute_signals(validation_df, strategy)

    assert sliced_from_full.iloc[0] == Signal.BUY
    assert recomputed_from_slice.iloc[0] == Signal.HOLD  # o bug que a correcao evita


def _result(total_trades, total_return_pct, buy_hold_return_pct, profit_factor, max_drawdown_pct):
    return BacktestResult(
        trades=[],
        initial_capital=1000.0,
        final_capital=1000.0 * (1 + total_return_pct / 100),
        total_return_pct=total_return_pct,
        win_rate=0.0,
        total_trades=total_trades,
        max_drawdown_pct=max_drawdown_pct,
        profit_factor=profit_factor,
        expectancy=0.0,
        average_win=0.0,
        average_loss=0.0,
        largest_win=0.0,
        largest_loss=0.0,
        max_losing_streak=0,
        exposure_pct=0.0,
        sharpe=0.0,
        expectancy_pct=0.0,
        payoff_ratio=0.0,
        buy_hold_return_pct=buy_hold_return_pct,
        edge_return_pct=total_return_pct - buy_hold_return_pct,
        edge_score=0.0,
    )


def test_evaluate_validation_approves_when_all_criteria_pass_out_of_sample():
    result = _result(total_trades=15, total_return_pct=20.0, buy_hold_return_pct=5.0,
                      profit_factor=1.5, max_drawdown_pct=8.0)

    verdict = evaluate_validation(result)

    assert verdict.status == "aprovado"
    assert verdict.reasons == []


def test_evaluate_validation_rejects_when_profit_factor_below_minimum():
    result = _result(total_trades=15, total_return_pct=20.0, buy_hold_return_pct=5.0,
                      profit_factor=1.1, max_drawdown_pct=8.0)

    verdict = evaluate_validation(result)

    assert verdict.status == "reprovado"
    assert any("profit factor" in r for r in verdict.reasons)


def test_evaluate_validation_rejects_when_return_does_not_beat_buy_and_hold():
    result = _result(total_trades=15, total_return_pct=4.0, buy_hold_return_pct=5.0,
                      profit_factor=1.5, max_drawdown_pct=8.0)

    verdict = evaluate_validation(result)

    assert verdict.status == "reprovado"
    assert any("buy-and-hold" in r for r in verdict.reasons)


def test_evaluate_validation_rejects_when_drawdown_too_high():
    result = _result(total_trades=15, total_return_pct=20.0, buy_hold_return_pct=5.0,
                      profit_factor=1.5, max_drawdown_pct=15.0)

    verdict = evaluate_validation(result)

    assert verdict.status == "reprovado"
    assert any("drawdown" in r for r in verdict.reasons)


def test_evaluate_validation_rejects_when_too_few_trades():
    result = _result(total_trades=3, total_return_pct=20.0, buy_hold_return_pct=5.0,
                      profit_factor=1.5, max_drawdown_pct=8.0)

    verdict = evaluate_validation(result)

    assert verdict.status == "reprovado"
    assert any("trades" in r for r in verdict.reasons)


def test_evaluate_validation_is_inconclusive_when_validation_window_missing():
    verdict = evaluate_validation(None)

    assert verdict.status == "inconclusivo"
    assert verdict.reasons
