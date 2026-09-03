"""H30 -- fator de tamanho/iliquidez, cesta iliquida vs liquida (spec 067)."""
import numpy as np
import pandas as pd
import pytest

from backtesting.fator_tamanho import (
    ResultadoCesta,
    avaliar_fator_tamanho,
    selecionar_cesta,
    simular_cesta,
)


def _serie(n, semente, sigma=0.01, inicio=100.0):
    rng = np.random.default_rng(semente)
    return inicio * np.exp(np.cumsum(rng.normal(0, sigma, n)))


def _df(n, semente, volume_medio, sigma=0.01):
    idx = pd.date_range("2026-01-01", periods=n, freq="4h")
    close = _serie(n, semente, sigma=sigma)
    rng = np.random.default_rng(semente + 1)
    volume = rng.normal(volume_medio, volume_medio * 0.05, n).clip(min=volume_medio * 0.5)
    return pd.DataFrame({"close": close, "volume": volume}, index=idx)


def test_selecionar_cesta_menor_volume_pega_os_de_menor_volume_medio():
    dados = {
        "A": _df(50, 1, volume_medio=1000),
        "B": _df(50, 2, volume_medio=100),
        "C": _df(50, 3, volume_medio=10000),
    }
    cesta = selecionar_cesta(dados, n=2, criterio="menor_volume")
    assert cesta == ["B", "A"]


def test_selecionar_cesta_maior_volume_pega_os_de_maior_volume_medio():
    dados = {
        "A": _df(50, 1, volume_medio=1000),
        "B": _df(50, 2, volume_medio=100),
        "C": _df(50, 3, volume_medio=10000),
    }
    cesta = selecionar_cesta(dados, n=2, criterio="maior_volume")
    assert cesta == ["C", "A"]


def test_simular_cesta_devolve_capital_inicial_sem_rebalanceamento_e_precos_constantes():
    idx = pd.date_range("2026-01-01", periods=10, freq="4h")
    dados = {
        "A": pd.DataFrame({"close": [100.0] * 10, "volume": [1000.0] * 10}, index=idx),
        "B": pd.DataFrame({"close": [50.0] * 10, "volume": [1000.0] * 10}, index=idx),
    }
    r = simular_cesta(dados, ["A", "B"], "menor_volume", capital_inicial=1000.0,
                       rebalance_a_cada=5, fee_rate=0.0, slippage_pct=0.0)

    assert r.capital_final == pytest.approx(1000.0, rel=1e-6)
    assert r.retorno_pct == pytest.approx(0.0, abs=1e-4)
    assert r.drawdown_max_pct == pytest.approx(0.0, abs=1e-4)


def test_simular_cesta_paga_custo_no_rebalanceamento():
    idx = pd.date_range("2026-01-01", periods=10, freq="4h")
    dados = {
        "A": pd.DataFrame({"close": [100.0] * 10, "volume": [1000.0] * 10}, index=idx),
        "B": pd.DataFrame({"close": [50.0] * 10, "volume": [1000.0] * 10}, index=idx),
    }
    r = simular_cesta(dados, ["A", "B"], "menor_volume", capital_inicial=1000.0,
                       rebalance_a_cada=5, fee_rate=0.001, slippage_pct=0.0005)

    assert r.custo_total_turnover > 0
    assert r.capital_final < 1000.0  # precos constantes, so custo consumido


def test_simular_cesta_captura_valorizacao_de_um_ativo():
    idx = pd.date_range("2026-01-01", periods=3, freq="4h")
    dados = {
        "A": pd.DataFrame({"close": [100.0, 200.0, 200.0], "volume": [1000.0] * 3}, index=idx),
        "B": pd.DataFrame({"close": [100.0, 100.0, 100.0], "volume": [1000.0] * 3}, index=idx),
    }
    r = simular_cesta(dados, ["A", "B"], "menor_volume", capital_inicial=1000.0,
                       rebalance_a_cada=100, fee_rate=0.0, slippage_pct=0.0)

    assert r.retorno_pct > 20  # A dobrou, metade da carteira -- retorno > 20% antes do rebalance


def test_multiplicador_de_slippage_maior_reduz_capital_final():
    idx = pd.date_range("2026-01-01", periods=20, freq="4h")
    dados = {
        "A": pd.DataFrame({"close": _serie(20, 1), "volume": [1000.0] * 20}, index=idx),
        "B": pd.DataFrame({"close": _serie(20, 2), "volume": [1000.0] * 20}, index=idx),
    }
    r_1x = simular_cesta(dados, ["A", "B"], "menor_volume", rebalance_a_cada=3,
                          multiplicador_slippage=1.0)
    r_5x = simular_cesta(dados, ["A", "B"], "menor_volume", rebalance_a_cada=3,
                          multiplicador_slippage=5.0)

    assert r_5x.custo_total_turnover > r_1x.custo_total_turnover
    assert r_5x.capital_final < r_1x.capital_final


def test_simular_cesta_sem_pares_validos_devolve_resultado_neutro():
    r = simular_cesta({}, ["X"], "menor_volume", capital_inicial=500.0)
    assert r.capital_final == 500.0
    assert r.retorno_pct == 0.0
    assert r.pares == []


def test_avaliar_fator_tamanho_usa_dados_passados_sem_rede():
    dados = {
        f"P{i}": _df(800, i, volume_medio=100.0 * (i + 1))
        for i in range(6)
    }
    resultados = avaliar_fator_tamanho(pares=list(dados.keys()), n=2,
                                        rebalance_a_cada=200, dados=dados)

    assert ("treino", "menor_volume", 1.0) in resultados
    assert ("validacao", "maior_volume", 5.0) in resultados
    for r in resultados.values():
        assert isinstance(r, ResultadoCesta)
        assert len(r.pares) <= 2
