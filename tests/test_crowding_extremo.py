"""H35 -- crowding via long/short ratio e open interest (spec 071)."""
import numpy as np
import pandas as pd
import pytest

from backtesting import crowding_extremo


def _preco_prep(n, atr=2.0, freq="4h", semente=1):
    idx = pd.date_range("2026-01-01", periods=n, freq=freq)
    rng = np.random.default_rng(semente)
    close = list(100 * np.exp(np.cumsum(rng.normal(0, 0.002, n))))
    high = [c * 1.001 for c in close]
    low = [c * 0.999 for c in close]
    return pd.DataFrame({"close": close, "high": high, "low": low, "atr": [atr] * n}, index=idx)


def _rotular_zeros(p, params):
    return pd.DataFrame({"rotulo_bruto": [0.0] * len(p)}, index=p.index)


def test_avaliar_par_none_sem_long_short_ratio(monkeypatch):
    idx = pd.date_range("2026-01-01", periods=1, freq="4h")
    monkeypatch.setattr(crowding_extremo, "fetch_long_short_ratio_history",
                         lambda par, timeframe=None: pd.DataFrame(columns=["longShortRatio"]))
    monkeypatch.setattr(crowding_extremo, "fetch_open_interest_history",
                         lambda par, timeframe=None: pd.DataFrame({"openInterestValue": [1.0]}, index=idx))

    assert crowding_extremo.avaliar_par("SEMPERP/USDT") is None


def test_avaliar_par_none_sem_open_interest(monkeypatch):
    idx = pd.date_range("2026-01-01", periods=1, freq="4h")
    monkeypatch.setattr(crowding_extremo, "fetch_long_short_ratio_history",
                         lambda par, timeframe=None: pd.DataFrame({"longShortRatio": [1.0]}, index=idx))
    monkeypatch.setattr(crowding_extremo, "fetch_open_interest_history",
                         lambda par, timeframe=None: pd.DataFrame(columns=["openInterestValue"]))

    assert crowding_extremo.avaliar_par("SEMPERP/USDT") is None


def test_candles_confirmados_exige_as_duas_condicoes_simultaneamente():
    idx = pd.date_range("2026-01-01", periods=5, freq="4h")
    # decil baixo (< 1.0): candles 0, 1, 3, 4
    ratio = pd.Series([0.5, 0.5, 2.0, 0.5, 0.5], index=idx)
    # acima da mediana (> 1_000_000): candles 0, 2, 3
    oi = pd.Series([2_000_000.0, 500_000.0, 2_000_000.0, 2_000_000.0, 500_000.0], index=idx)

    confirmados = crowding_extremo._candles_confirmados(idx, ratio, oi, limiar_ratio=1.0, mediana_oi=1_000_000.0)

    # so onde as DUAS condicoes valem simultaneamente: candles 0 e 3
    assert list(confirmados) == [idx[0], idx[3]]


def test_calibracao_so_no_treino_nao_muda_com_a_validacao(monkeypatch):
    """Mesma fatia de treino, duas fatias de validacao DIFERENTES -- o
    limiar de ratio e a mediana de OI (calculados so no treino) devem ser
    identicos nas duas chamadas."""
    n = 100
    prep = _preco_prep(n)

    monkeypatch.setattr(crowding_extremo, "preparar", lambda df, estrategia: prep)
    monkeypatch.setattr(crowding_extremo, "fetch_ohlcv", lambda par, tf, limit: pd.DataFrame(index=prep.index))
    monkeypatch.setattr(crowding_extremo, "rotular", _rotular_zeros)

    corte = int(n * (1 - crowding_extremo.DEFAULT_VALIDATION_RATIO))
    rng = np.random.default_rng(7)
    ratio_treino = rng.normal(1.0, 0.1, corte)
    oi_treino = rng.normal(1_000_000, 100_000, corte)

    limiares, medianas = [], []
    for semente_validacao in (1, 2):
        rng_val = np.random.default_rng(semente_validacao)
        ratio_full = np.concatenate([ratio_treino, rng_val.normal(1.0, 0.1, n - corte)])
        oi_full = np.concatenate([oi_treino, rng_val.normal(1_000_000, 100_000, n - corte)])

        ratio_df = pd.DataFrame({"longShortRatio": ratio_full}, index=prep.index)
        oi_df = pd.DataFrame({"openInterestValue": oi_full}, index=prep.index)
        monkeypatch.setattr(crowding_extremo, "fetch_long_short_ratio_history",
                             lambda par, timeframe=None, _d=ratio_df: _d)
        monkeypatch.setattr(crowding_extremo, "fetch_open_interest_history",
                             lambda par, timeframe=None, _d=oi_df: _d)

        r = crowding_extremo.avaliar_par("BTC/USDT")
        limiares.append(r.limiar_ratio)
        medianas.append(r.mediana_oi)

    assert limiares[0] == pytest.approx(limiares[1])
    assert medianas[0] == pytest.approx(medianas[1])


def test_candles_anteriores_ao_inicio_real_sao_descartados(monkeypatch):
    n = 60
    prep = _preco_prep(n)
    monkeypatch.setattr(crowding_extremo, "preparar", lambda df, estrategia: prep)
    monkeypatch.setattr(crowding_extremo, "fetch_ohlcv", lambda par, tf, limit: pd.DataFrame(index=prep.index))
    monkeypatch.setattr(crowding_extremo, "rotular", _rotular_zeros)

    # ratio/OI so existem a partir do candle 30 -- os 30 primeiros do prep
    # nao tem historico real das duas series (D4).
    idx_curto = prep.index[30:]
    ratio_df = pd.DataFrame({"longShortRatio": [1.0] * len(idx_curto)}, index=idx_curto)
    oi_df = pd.DataFrame({"openInterestValue": [1_000_000.0] * len(idx_curto)}, index=idx_curto)
    monkeypatch.setattr(crowding_extremo, "fetch_long_short_ratio_history", lambda par, timeframe=None: ratio_df)
    monkeypatch.setattr(crowding_extremo, "fetch_open_interest_history", lambda par, timeframe=None: oi_df)

    r = crowding_extremo.avaliar_par("BTC/USDT")

    assert r is not None
    # nunca os 60 candles originais do prep -- so os 30 com historico real
    assert r.n_treino + r.n_validacao == len(idx_curto)


def test_agregar_pooled_soma_entre_pares_e_delega_significancia():
    r1 = crowding_extremo.ResultadoParH35(
        par="A/USDT", retencao_dias=31.0, limiar_ratio=0.8, mediana_oi=1_000_000.0,
        n_treino=70, n_eventos_treino=5, n_validacao=30, n_eventos_validacao=10,
        alvo_validacao=6, stop_validacao=4, razao_validacao=1.5, supera_empate_validacao=True,
    )
    r2 = crowding_extremo.ResultadoParH35(
        par="B/USDT", retencao_dias=31.0, limiar_ratio=0.7, mediana_oi=2_000_000.0,
        n_treino=70, n_eventos_treino=3, n_validacao=30, n_eventos_validacao=8,
        alvo_validacao=2, stop_validacao=6, razao_validacao=0.33, supera_empate_validacao=False,
    )

    agregado = crowding_extremo.agregar_pooled([r1, r2])

    assert agregado["n_pares"] == 2
    assert agregado["n_alvo"] == 8
    assert agregado["n_stop"] == 10
    assert agregado["razao"] == pytest.approx(0.8)
    assert agregado["empate"] == pytest.approx(0.5)
    # mesma licao de M9/M13 (H26): razao pontual > empate, mas n=18 e pequeno
    # demais para o limite inferior do IC de Wilson superar a fracao de empate.
    assert agregado["supera_empate"] is False


def test_agregar_pooled_sem_resultados_nao_quebra():
    agregado = crowding_extremo.agregar_pooled([])

    assert agregado["n_pares"] == 0
    assert agregado["n_alvo"] == 0
    assert agregado["n_stop"] == 0
    assert agregado["razao"] == float("inf")
    assert agregado["supera_empate"] is False


def test_avaliar_universo_pula_pares_sem_resultado(monkeypatch):
    def _fake_avaliar_par(par, params=None):
        if par == "SEMPERP/USDT":
            return None
        return crowding_extremo.ResultadoParH35(
            par=par, retencao_dias=31.0, limiar_ratio=0.8, mediana_oi=1_000_000.0,
            n_treino=70, n_eventos_treino=5, n_validacao=30, n_eventos_validacao=10,
            alvo_validacao=6, stop_validacao=4, razao_validacao=1.5, supera_empate_validacao=True,
        )

    monkeypatch.setattr(crowding_extremo, "avaliar_par", _fake_avaliar_par)

    resultados = crowding_extremo.avaliar_universo(["BTC/USDT", "SEMPERP/USDT", "ETH/USDT"])

    assert [r.par for r in resultados] == ["BTC/USDT", "ETH/USDT"]
