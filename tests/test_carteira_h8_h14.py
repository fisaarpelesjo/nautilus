from backtesting import carteira_h8_h14 as mod
from backtesting.engine import BacktestResult
from backtesting.funding_carry import ResultadoFundingPar


def _resultado_h14(annualized_return_pct=-17.0, max_drawdown_pct=28.66):
    return BacktestResult(
        trades=[], initial_capital=1000.0, final_capital=900.0, total_return_pct=-10.0,
        win_rate=40.0, total_trades=50, max_drawdown_pct=max_drawdown_pct, profit_factor=0.72,
        expectancy=-1.0, average_win=1.0, average_loss=-1.0, largest_win=1.0, largest_loss=-1.0,
        max_losing_streak=3, exposure_pct=50.0, sharpe=-0.5, expectancy_pct=-0.5, payoff_ratio=1.0,
        buy_hold_return_pct=100.0, edge_return_pct=-110.0, edge_score=-50.0, sortino=-0.5, calmar=-0.6,
        annualized_return_pct=annualized_return_pct, return_per_exposure_pct=-20.0,
    )


def _resultado_h8(par, liquido_aa_capital_implantado):
    return ResultadoFundingPar(
        par=par, dias_cobertos=365, n_pagamentos=1095, pct_negativos=30.0,
        bruto_aa=liquido_aa_capital_implantado * 2 + 0.01, liquido_aa_nocional=liquido_aa_capital_implantado * 2,
        liquido_aa_capital_implantado=liquido_aa_capital_implantado,
        supera_benchmark=liquido_aa_capital_implantado > 0.05,
    )


def test_avaliar_combinado_none_quando_h14_nao_produz_resultado(monkeypatch):
    monkeypatch.setattr(mod, "simular_carteira", lambda pares: None)
    monkeypatch.setattr(mod, "avaliar_universo_h8", lambda pares: [])

    assert mod.avaliar_combinado(pares=["BTC/USDT"]) is None


def test_avaliar_combinado_blend_50_50_dos_retornos_anualizados(monkeypatch):
    monkeypatch.setattr(mod, "simular_carteira", lambda pares: _resultado_h14(annualized_return_pct=-17.0))
    monkeypatch.setattr(mod, "avaliar_universo_h8", lambda pares: [
        _resultado_h8("BTC/USDT", 0.03), _resultado_h8("ETH/USDT", 0.05),
    ])

    resultado = mod.avaliar_combinado(alocacao_h14=0.5, pares=["BTC/USDT", "ETH/USDT"])

    assert resultado is not None
    # pooled H8 = (0.03+0.05)/2 = 0.04 -> 4% a.a.
    assert resultado.taxa_carry_pooled_aa == 0.04
    # combinado = 0.5*(-17.0) + 0.5*(0.04*100) = -8.5 + 2.0 = -6.5
    assert resultado.retorno_combinado_aa == -6.5


def test_avaliar_combinado_drawdown_escalado_pela_alocacao_h14(monkeypatch):
    monkeypatch.setattr(mod, "simular_carteira", lambda pares: _resultado_h14(max_drawdown_pct=28.66))
    monkeypatch.setattr(mod, "avaliar_universo_h8", lambda pares: [])

    resultado = mod.avaliar_combinado(alocacao_h14=0.5, pares=["BTC/USDT"])

    assert resultado.drawdown_combinado_aproximado_pct == 14.33


def test_avaliar_combinado_sem_pares_h8_validos_usa_taxa_zero(monkeypatch):
    monkeypatch.setattr(mod, "simular_carteira", lambda pares: _resultado_h14())
    monkeypatch.setattr(mod, "avaliar_universo_h8", lambda pares: [])

    resultado = mod.avaliar_combinado(pares=["BTC/USDT"])

    assert resultado.taxa_carry_pooled_aa == 0.0
    assert resultado.resultados_h8 == []


def test_avaliar_combinado_usa_universo_h11_por_padrao(monkeypatch):
    capturado = {}

    def _fake_simular(pares):
        capturado["pares_h14"] = pares
        return _resultado_h14()

    def _fake_h8(pares):
        capturado["pares_h8"] = pares
        return []

    monkeypatch.setattr(mod, "simular_carteira", _fake_simular)
    monkeypatch.setattr(mod, "avaliar_universo_h8", _fake_h8)

    mod.avaliar_combinado()

    assert capturado["pares_h14"] == list(mod.UNIVERSO_H11)
    assert capturado["pares_h8"] == list(mod.UNIVERSO_H11)
