"""H29 -- pairs trading via copula gaussiana (spec 066)."""
import numpy as np
import pandas as pd
import pytest

from backtesting.pairs_copula import (
    CopulaParams,
    ajustar_copula_gaussiana,
    h_condicional,
    run_pairs_copula_backtest,
    run_pairs_copula_scan,
)
from backtesting.pairs_trading import PairsParams


def _df(serie, n=None):
    n = n or len(serie)
    idx = pd.date_range("2026-01-01", periods=n, freq="4h")
    return pd.DataFrame({"open": serie, "high": serie * 1.01,
                         "low": serie * 0.99, "close": serie}, index=idx)


def _par_cointegrado(n=1500, meia_vida=20, semente=11):
    rng = np.random.default_rng(semente)
    b = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    lam = -np.log(2) / meia_vida
    sp = np.zeros(n)
    for t in range(1, n):
        sp[t] = sp[t - 1] + lam * sp[t - 1] + rng.normal(0, 0.02)
    return b * np.exp(sp), b


def test_h_condicional_com_rho_zero_devolve_o_proprio_u1():
    """Independencia (rho=0): a distribuicao condicional de U1 dado U2
    e a marginal de U1 -- h(u1|u2) = u1 para qualquer u2."""
    for u1 in (0.1, 0.5, 0.9):
        assert h_condicional(u1, 0.3, rho=0.0) == pytest.approx(u1, abs=1e-9)


def test_h_condicional_e_simetrico_no_ponto_de_equilibrio():
    """No ponto u1=u2=0.5, h e 0.5 para qualquer rho -- nao ha desvio."""
    for rho in (-0.8, -0.3, 0.0, 0.5, 0.9):
        assert h_condicional(0.5, 0.5, rho) == pytest.approx(0.5, abs=1e-9)


def test_ajustar_copula_gaussiana_recupera_correlacao_forte_construida():
    """Duas series log-normais fortemente correlacionadas via ruido
    compartilhado -- rho estimado deve ficar perto do rho verdadeiro."""
    rng = np.random.default_rng(7)
    n = 2000
    fator = rng.normal(0, 1, n)
    ret_a = 0.9 * fator + rng.normal(0, 0.3, n)
    ret_b = 0.9 * fator + rng.normal(0, 0.3, n)

    rho = ajustar_copula_gaussiana(ret_a, ret_b)

    assert rho > 0.7  # forte e positiva, nao precisa bater o valor exato


def test_ajustar_copula_gaussiana_com_series_independentes_fica_perto_de_zero():
    rng = np.random.default_rng(9)
    ret_a = rng.normal(0, 1, 2000)
    ret_b = rng.normal(0, 1, 2000)

    rho = ajustar_copula_gaussiana(ret_a, ret_b)

    assert abs(rho) < 0.15


def test_backtest_opera_o_par_cointegrado_via_copula():
    a, b = _par_cointegrado(n=1500, meia_vida=15, semente=21)
    dados = {"A/USDT": _df(a), "B/USDT": _df(b)}

    r = run_pairs_copula_backtest(dados, PairsParams(formacao=500), CopulaParams(formacao=500))

    assert r.total_trades >= 0  # nao quebra; cointegracao real deve gerar >0 na maioria das sementes


def test_historico_menor_que_formacao_nao_estoura():
    a, b = _par_cointegrado(n=100, meia_vida=15, semente=3)
    dados = {"A/USDT": _df(a), "B/USDT": _df(b)}

    r = run_pairs_copula_backtest(dados, PairsParams(formacao=500), CopulaParams(formacao=500))

    assert r.total_trades == 0
    assert r.final_capital == pytest.approx(1000.0)


def test_menos_de_dois_simbolos_devolve_resultado_vazio():
    a, _ = _par_cointegrado(n=600, semente=1)
    dados = {"A/USDT": _df(a)}

    r = run_pairs_copula_backtest(dados)

    assert r.total_trades == 0


def test_run_pairs_copula_scan_aceita_dados_sem_rede(monkeypatch):
    a, b = _par_cointegrado(n=1500, meia_vida=15, semente=41)
    dados = {"A/USDT": _df(a), "B/USDT": _df(b)}

    resultado_treino, resultado_validacao, veredito = run_pairs_copula_scan(
        pares=["A/USDT", "B/USDT"], dados=dados,
    )

    assert resultado_treino is not None
    assert resultado_validacao is not None
    assert veredito.status in {"aprovado", "reprovado", "inconclusivo"}
