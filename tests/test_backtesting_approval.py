from types import SimpleNamespace

from backtesting.approval import diagnose_profile, evaluate_approval, ranking_key
from backtesting.engine import BacktestResult


def _result(total_trades, total_return_pct, buy_hold_return_pct, profit_factor, max_drawdown_pct,
            expectancy=0.0):
    return BacktestResult(
        trades=[],
        initial_capital=1000.0,
        final_capital=1000.0 * (1 + total_return_pct / 100),
        total_return_pct=total_return_pct,
        win_rate=0.0,
        total_trades=total_trades,
        max_drawdown_pct=max_drawdown_pct,
        profit_factor=profit_factor,
        expectancy=expectancy,
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
        sortino=0.0,
        calmar=0.0,
        annualized_return_pct=0.0,
        return_per_exposure_pct=None,
    )


def test_evaluate_approval_approves_when_all_criteria_pass():
    result = _result(total_trades=15, total_return_pct=20.0, buy_hold_return_pct=5.0,
                      profit_factor=1.5, max_drawdown_pct=8.0)

    verdict = evaluate_approval(result)

    assert verdict.status == "aprovado"
    assert verdict.reasons == []


def test_evaluate_approval_rejects_when_profit_factor_below_minimum():
    result = _result(total_trades=15, total_return_pct=20.0, buy_hold_return_pct=5.0,
                      profit_factor=1.1, max_drawdown_pct=8.0)

    verdict = evaluate_approval(result)

    assert verdict.status == "reprovado"
    assert any("profit factor" in r for r in verdict.reasons)


def test_evaluate_approval_rejects_when_return_does_not_beat_buy_and_hold():
    result = _result(total_trades=15, total_return_pct=4.0, buy_hold_return_pct=5.0,
                      profit_factor=1.5, max_drawdown_pct=8.0)

    verdict = evaluate_approval(result)

    assert verdict.status == "reprovado"
    assert any("buy-and-hold" in r for r in verdict.reasons)


def test_evaluate_approval_rejects_when_drawdown_too_high():
    result = _result(total_trades=15, total_return_pct=20.0, buy_hold_return_pct=5.0,
                      profit_factor=1.5, max_drawdown_pct=15.0)

    verdict = evaluate_approval(result)

    assert verdict.status == "reprovado"
    assert any("drawdown" in r for r in verdict.reasons)


def test_evaluate_approval_rejects_when_too_few_trades():
    result = _result(total_trades=3, total_return_pct=20.0, buy_hold_return_pct=5.0,
                      profit_factor=1.5, max_drawdown_pct=8.0)

    verdict = evaluate_approval(result)

    assert verdict.status == "reprovado"
    assert any("trades" in r for r in verdict.reasons)


def test_evaluate_approval_is_inconclusive_when_result_missing():
    verdict = evaluate_approval(None)

    assert verdict.status == "inconclusivo"
    assert verdict.reasons


def test_diagnose_profile_flags_defensive_when_low_drawdown_positive_expectancy_below_buy_hold():
    result = _result(total_trades=15, total_return_pct=4.0, buy_hold_return_pct=20.0,
                      profit_factor=1.5, max_drawdown_pct=3.0, expectancy=1.0)

    diagnosis = diagnose_profile(result)

    assert diagnosis is not None
    assert "defensivo" in diagnosis


def test_diagnose_profile_is_none_when_drawdown_too_high():
    result = _result(total_trades=15, total_return_pct=4.0, buy_hold_return_pct=20.0,
                      profit_factor=1.5, max_drawdown_pct=15.0, expectancy=1.0)

    assert diagnose_profile(result) is None


def test_diagnose_profile_is_none_when_expectancy_not_positive():
    result = _result(total_trades=15, total_return_pct=4.0, buy_hold_return_pct=20.0,
                      profit_factor=1.5, max_drawdown_pct=3.0, expectancy=0.0)

    assert diagnose_profile(result) is None


def test_diagnose_profile_flags_defensive_when_return_exactly_matches_buy_and_hold():
    # Fronteira: evaluate_approval() reprova com "<=" (retorno == buy-hold conta
    # como nao superar); diagnose_profile() precisa usar o mesmo limiar, senao
    # um resultado reprovado por essa razao especifica fica sem diagnostico.
    result = _result(total_trades=15, total_return_pct=20.0, buy_hold_return_pct=20.0,
                      profit_factor=1.5, max_drawdown_pct=3.0, expectancy=1.0)

    assert diagnose_profile(result) is not None


def test_diagnose_profile_is_none_when_return_beats_buy_and_hold():
    result = _result(total_trades=15, total_return_pct=25.0, buy_hold_return_pct=20.0,
                      profit_factor=1.5, max_drawdown_pct=3.0, expectancy=1.0)

    assert diagnose_profile(result) is None


def test_diagnose_profile_flags_aggressive_when_high_drawdown_and_return_well_above_buy_hold():
    result = _result(total_trades=15, total_return_pct=45.0, buy_hold_return_pct=20.0,
                      profit_factor=1.5, max_drawdown_pct=15.0, expectancy=1.0)

    diagnosis = diagnose_profile(result)

    assert diagnosis is not None
    assert "agressivo" in diagnosis


def test_diagnose_profile_is_none_when_drawdown_high_but_return_not_well_above_buy_hold():
    # drawdown alto (reprova o perfil defensivo), mas retorno so um pouco acima
    # do buy-hold (< 1.5x) -- nao deve ser rotulado agressivo so por ter tido
    # drawdown alto, senao qualquer resultado ruim com drawdown alto vira
    # "agressivo" por omissao.
    result = _result(total_trades=15, total_return_pct=25.0, buy_hold_return_pct=20.0,
                      profit_factor=1.5, max_drawdown_pct=15.0, expectancy=1.0)

    assert diagnose_profile(result) is None


def test_diagnose_profile_is_none_when_buy_hold_negative_and_strategy_just_lost_less():
    # Achado de /code-review medium: `buy_hold * 1.5` inverte o limiar quando o
    # buy-hold e negativo (bear market). Estrategia perdeu 20% mas o
    # buy-and-hold perdeu 30% -- perder menos que um benchmark negativo nao e
    # "retorno bem acima do buy-and-hold", nao pode virar "perfil agressivo".
    result = _result(total_trades=15, total_return_pct=-20.0, buy_hold_return_pct=-30.0,
                      profit_factor=0.9, max_drawdown_pct=15.0, expectancy=-1.0)

    assert diagnose_profile(result) is None


def _rankable(edge_score, profit_factor=1.0, trades=15):
    return SimpleNamespace(edge_score=edge_score, profit_factor=profit_factor, trades=trades)


def test_ranking_key_prevents_tiny_sample_from_topping_a_robust_result():
    # Achado do /code-review high desta spec: um "1 trade sortudo" com edge_score
    # muito alto nao pode superar um resultado robusto com amostra decente, mesmo
    # que o numero bruto do edge_score seja maior -- mesma protecao que o
    # ScanResult.score antigo tinha (trades < 3 vira exclusao dura).
    lucky_one_trade = _rankable(edge_score=187.0, profit_factor=float("inf"), trades=1)
    robust = _rankable(edge_score=19.0, profit_factor=1.3, trades=25)

    ranked = sorted([lucky_one_trade, robust], key=ranking_key, reverse=True)

    assert ranked == [robust, lucky_one_trade]


def test_ranking_key_uses_edge_score_when_sample_is_large_enough():
    a = _rankable(edge_score=10.0, trades=10)
    b = _rankable(edge_score=5.0, trades=10)

    ranked = sorted([b, a], key=ranking_key, reverse=True)

    assert ranked == [a, b]
