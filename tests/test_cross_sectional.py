import numpy as np
import pandas as pd
import pytest

from backtesting.cross_sectional import (
    CrossSectionalParams,
    _alinhar,
    run_cross_sectional_backtest,
)


def _serie(tendencia, n=400, semente=0, inicio="2026-01-01"):
    rng = np.random.default_rng(semente)
    idx = pd.date_range(inicio, periods=n, freq="4h")
    p = 100 * np.exp(np.cumsum(tendencia + rng.normal(0, 0.008, n)))
    return pd.DataFrame({"open": p, "high": p * 1.01, "low": p * 0.99, "close": p}, index=idx)


def _universo(tendencias, n=400):
    return {f"P{i}/USDT": _serie(t, n=n, semente=i) for i, t in enumerate(tendencias)}


def test_escolhe_o_par_que_sobe_entre_pares_que_caem():
    # Se o ranking funciona, a carteira fica com o unico par em alta e termina
    # acima do buy-and-hold da carteira inteira (que carrega os que caem).
    dados = _universo([0.005, -0.003, -0.003, -0.003])
    r = run_cross_sectional_backtest(dados, CrossSectionalParams(lookback=30, top_k=1, rebalance_every=6))

    assert r.total_trades > 0
    assert r.total_return_pct > 0
    assert r.edge_return_pct > 0


def test_rebalanceamento_mais_frequente_paga_mais_taxa():
    # O parametro mais sensivel do transversal e a frequencia de giro: cada
    # rebalanceamento paga taxa e slippage nas duas pontas.
    dados = _universo([0.002, 0.001, -0.001, -0.002])
    raro = run_cross_sectional_backtest(dados, CrossSectionalParams(lookback=30, top_k=2, rebalance_every=48))
    frequente = run_cross_sectional_backtest(dados, CrossSectionalParams(lookback=30, top_k=2, rebalance_every=4))

    assert frequente.total_trades > raro.total_trades
    assert sum(t.fees for t in frequente.trades) > sum(t.fees for t in raro.trades)


def test_custo_zero_rende_mais_que_custo_real():
    dados = _universo([0.003, 0.001, -0.001, -0.002])
    p = CrossSectionalParams(lookback=30, top_k=2, rebalance_every=6)
    com_custo = run_cross_sectional_backtest(dados, p)
    sem_custo = run_cross_sectional_backtest(dados, p, fee_rate=0.0, slippage_pct=0.0)

    assert sem_custo.total_return_pct > com_custo.total_return_pct


def test_min_momentum_impede_entrada_em_universo_todo_em_queda():
    # Com todos caindo e min_momentum=0, nao ha nada acima do limiar: a
    # estrategia fica em caixa em vez de comprar o "menos pior".
    dados = _universo([-0.004, -0.005, -0.006, -0.007])
    r = run_cross_sectional_backtest(
        dados, CrossSectionalParams(lookback=30, top_k=2, rebalance_every=6, min_momentum=0.0)
    )

    assert r.total_trades == 0
    assert r.total_return_pct == pytest.approx(0.0, abs=1e-9)


def test_historico_curto_devolve_resultado_vazio_sem_estourar():
    dados = _universo([0.001, -0.001], n=20)
    r = run_cross_sectional_backtest(dados, CrossSectionalParams(lookback=30))

    assert r.total_trades == 0
    assert r.final_capital == r.initial_capital


def test_alinhar_usa_interseccao_e_nao_preenche_buraco():
    # Simbolos listados em datas diferentes: a matriz alinhada tem que ficar do
    # tamanho da interseccao. Preencher para tras faria o rank comparar preco
    # real com preco repetido.
    longo = _serie(0.001, n=300)
    curto = _serie(0.001, n=100, semente=1, inicio="2026-01-20")
    precos = _alinhar({"A/USDT": longo, "B/USDT": curto})

    assert list(precos.columns) == ["A/USDT", "B/USDT"]
    assert len(precos) <= 100
    assert not precos.isna().any().any()


def test_universo_vazio_nao_quebra():
    r = run_cross_sectional_backtest({}, CrossSectionalParams())

    assert r.total_trades == 0
    assert r.final_capital == r.initial_capital
