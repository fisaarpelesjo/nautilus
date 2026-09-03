"""H26 -- reversao contra funding extremo (spec 063)."""
import numpy as np
import pandas as pd
import pytest

from backtesting import funding_reversao


def _preco_prep(n, atr=2.0, freq="4h", semente=1):
    idx = pd.date_range("2026-01-01", periods=n, freq=freq)
    rng = np.random.default_rng(semente)
    close = list(100 * np.exp(np.cumsum(rng.normal(0, 0.002, n))))
    high = [c * 1.001 for c in close]
    low = [c * 0.999 for c in close]
    return pd.DataFrame({"close": close, "high": high, "low": low, "atr": [atr] * n}, index=idx)


def _funding_serie(idx, valores):
    """Serie de funding sobre o MESMO indice dos candles (simplifica os
    testes -- o forward-fill em cima de indices iguais e identidade)."""
    return pd.Series(valores, index=idx, name="fundingRate")


def test_avaliar_par_none_sem_funding(monkeypatch):
    monkeypatch.setattr(funding_reversao, "fetch_funding_rate_history",
                         lambda par, dias=funding_reversao.DIAS_FUNDING: pd.DataFrame(columns=["fundingRate"]))

    assert funding_reversao.avaliar_par("SEMPERP/USDT") is None


def test_limiar_calibrado_so_no_treino_nao_muda_com_a_validacao(monkeypatch):
    """Mesma fatia de treino, duas fatias de validacao DIFERENTES -- o
    limiar de extremo (calculado so no treino) deve ser identico nas
    duas chamadas."""
    n = 100
    prep = _preco_prep(n)

    def _fake_preparar(df, estrategia):
        return prep

    monkeypatch.setattr(funding_reversao, "preparar", _fake_preparar)
    monkeypatch.setattr(funding_reversao, "fetch_ohlcv", lambda par, tf, limit: pd.DataFrame(index=prep.index))

    rng = np.random.default_rng(7)
    valores_funding = rng.normal(0, 0.0005, n)

    limiares = []
    for _semente_validacao in (1, 2):
        funding_df = pd.DataFrame({"fundingRate": valores_funding}, index=prep.index)
        monkeypatch.setattr(funding_reversao, "fetch_funding_rate_history",
                             lambda par, dias=None, _fd=funding_df: _fd)
        monkeypatch.setattr(funding_reversao, "rotular",
                             lambda p, params, _n=n: pd.DataFrame(
                                 {"rotulo_bruto": [0.0] * _n}, index=p.index))

        r = funding_reversao.avaliar_par("BTC/USDT")
        limiares.append(r.limiar_extremo)

    assert limiares[0] == pytest.approx(limiares[1])


def test_alinhamento_forward_fill_causal(monkeypatch):
    """Candles entre duas leituras de funding herdam a leitura ANTERIOR,
    nunca a seguinte."""
    idx_funding = pd.date_range("2026-01-01", periods=3, freq="8h")
    funding = pd.Series([-0.01, 0.02, -0.01], index=idx_funding)

    idx_candles = pd.date_range("2026-01-01", periods=6, freq="4h")
    alinhado = funding.reindex(idx_candles, method="ffill")

    # candle em 04:00 (entre 00:00 e 08:00) deve herdar o valor de 00:00 (-0.01),
    # nunca o de 08:00 (0.02)
    assert alinhado.loc[idx_candles[1]] == pytest.approx(-0.01)


def test_eventos_extremos_filtra_abaixo_do_limiar():
    idx = pd.date_range("2026-01-01", periods=5, freq="4h")
    funding = pd.Series([-0.02, -0.005, 0.01, -0.03, 0.0], index=idx)

    eventos = funding_reversao._eventos_extremos(idx, funding, limiar_extremo=-0.01)

    assert list(eventos) == [idx[0], idx[3]]  # so -0.02 e -0.03 ficam abaixo de -0.01


def test_agregar_pooled_soma_entre_pares_e_delega_significancia():
    r1 = funding_reversao.ResultadoParH26(
        par="A/USDT", limiar_extremo=-0.01, n_treino=70, n_eventos_treino=5,
        n_validacao=30, n_eventos_validacao=10, alvo_validacao=6, stop_validacao=4,
        razao_validacao=1.5, supera_empate_validacao=True,
    )
    r2 = funding_reversao.ResultadoParH26(
        par="B/USDT", limiar_extremo=-0.02, n_treino=70, n_eventos_treino=3,
        n_validacao=30, n_eventos_validacao=8, alvo_validacao=2, stop_validacao=6,
        razao_validacao=0.33, supera_empate_validacao=False,
    )

    agregado = funding_reversao.agregar_pooled([r1, r2])

    assert agregado["n_pares"] == 2
    assert agregado["n_alvo"] == 8
    assert agregado["n_stop"] == 10
    assert agregado["razao"] == pytest.approx(0.8)
    assert agregado["empate"] == pytest.approx(0.5)
    # razao pontual (0.8) > empate (0.5), mas n=18 e pequeno demais para o
    # limite inferior do IC de Wilson superar a fracao de empate -- mesma
    # licao de M9/M13, delegada a supera_empate_com_confianca sem reimplementar.
    assert agregado["supera_empate"] is False


def test_agregar_pooled_sem_resultados_nao_quebra():
    agregado = funding_reversao.agregar_pooled([])

    assert agregado["n_pares"] == 0
    assert agregado["n_alvo"] == 0
    assert agregado["n_stop"] == 0
    assert agregado["razao"] == float("inf")
    assert agregado["supera_empate"] is False


def test_avaliar_universo_pula_pares_sem_resultado(monkeypatch):
    def _fake_avaliar_par(par, params=None):
        if par == "SEMPERP/USDT":
            return None
        return funding_reversao.ResultadoParH26(
            par=par, limiar_extremo=-0.01, n_treino=70, n_eventos_treino=5,
            n_validacao=30, n_eventos_validacao=10, alvo_validacao=6, stop_validacao=4,
            razao_validacao=1.5, supera_empate_validacao=True,
        )

    monkeypatch.setattr(funding_reversao, "avaliar_par", _fake_avaliar_par)

    resultados = funding_reversao.avaliar_universo(["BTC/USDT", "SEMPERP/USDT", "ETH/USDT"])

    assert [r.par for r in resultados] == ["BTC/USDT", "ETH/USDT"]
