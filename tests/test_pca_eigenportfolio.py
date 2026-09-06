import numpy as np
import pandas as pd
import pytest

from backtesting import pca_eigenportfolio as mod
from strategy.base import Signal


def test_componentes_pca_recupera_estrutura_de_fator_dominante():
    rng = np.random.default_rng(0)
    n, m = 500, 6
    fator = rng.normal(0, 1, n)
    loadings = np.array([1.0, 0.9, 1.1, 0.8, 1.2, 0.95])
    ruido = rng.normal(0, 0.05, (n, m))
    retornos = np.outer(fator, loadings) + ruido
    df = pd.DataFrame(retornos, columns=[f"A{i}" for i in range(m)])
    padronizado = (df - df.mean()) / df.std()

    autovetores, variancia = mod._componentes_pca(padronizado)

    # um unico fator domina os retornos por construcao -- poucos
    # componentes ja devem explicar >=55% da variancia (D2)
    assert autovetores.shape[1] <= 2
    assert variancia >= mod.VARIANCIA_ALVO


def test_ajustar_ou_recupera_parametros_de_serie_sintetica():
    rng = np.random.default_rng(1)
    n = 2000
    b_verdadeiro = 0.9
    media_verdadeira = 5.0
    a_verdadeiro = media_verdadeira * (1 - b_verdadeiro)
    x = np.zeros(n)
    x[0] = media_verdadeira
    for t in range(1, n):
        x[t] = a_verdadeiro + b_verdadeiro * x[t - 1] + rng.normal(0, 0.5)

    resultado = mod._ajustar_ou(x)

    assert resultado is not None
    media, sigma_eq = resultado
    assert media == pytest.approx(media_verdadeira, abs=0.5)
    assert sigma_eq > 0


def test_ajustar_ou_none_para_serie_explosiva():
    rng = np.random.default_rng(2)
    n = 300
    x = np.zeros(n)
    x[0] = 1.0
    for t in range(1, n):
        x[t] = 1.05 * x[t - 1] + rng.normal(0, 0.1)  # explosivo, b>1 -- nunca estacionario

    assert mod._ajustar_ou(x) is None


def test_ajustar_ou_none_para_serie_curta_demais():
    assert mod._ajustar_ou(np.array([1.0, 2.0])) is None


def test_precompute_signals_buy_no_cruzamento_de_entrada_sell_no_de_saida():
    idx = pd.date_range("2026-01-01", periods=6, freq="4h")
    candles = pd.DataFrame({"close": [1.0] * 6}, index=idx)
    # cruza entrada entre indice 1 (-1.0, acima do limiar) e 2 (-1.3, <=-1.25) -> BUY em 2
    # fica esticado em 3 (-1.3) sem novo cruzamento -> HOLD
    # cruza saida entre indice 4 (-0.6, abaixo do limiar) e 5 (-0.4, >=-0.5) -> SELL em 5
    s_score = pd.Series([0.0, -1.0, -1.3, -1.3, -0.6, -0.4], index=idx)

    sinais = mod.precompute_signals(candles, s_score)

    assert sinais.iloc[2] == Signal.BUY
    assert sinais.iloc[3] == Signal.HOLD
    assert sinais.iloc[5] == Signal.SELL


def test_teste_sanidade_zero_trades_sobre_s_score_constante():
    assert mod.teste_sanidade() is True


def test_gerar_resultado_par_custo_zero_remove_fee_e_slippage(monkeypatch):
    capturado = {}

    def _fake_simulate_backtest(df, strategy, fee_rate, slippage_pct, precomputed_signals=None):
        capturado["fee_rate"] = fee_rate
        capturado["slippage_pct"] = slippage_pct
        return "resultado-fake"

    monkeypatch.setattr(mod, "simulate_backtest", _fake_simulate_backtest)

    candles = mod._candles_s_score_constante()
    s_score = pd.Series(0.0, index=candles.index)

    resultado = mod.gerar_resultado_par(candles, True, s_score)

    assert resultado == "resultado-fake"
    assert capturado["fee_rate"] == 0.0
    assert capturado["slippage_pct"] == 0.0

    mod.gerar_resultado_par(candles, False, s_score)
    assert capturado["fee_rate"] > 0.0
    assert capturado["slippage_pct"] > 0.0


def _ohlcv_sintetico(n: int, closes: np.ndarray) -> pd.DataFrame:
    idx = pd.date_range("2026-01-01", periods=n, freq="4h")
    return pd.DataFrame({
        "open": closes, "high": closes * 1.001, "low": closes * 0.999,
        "close": closes, "volume": 1000.0,
    }, index=idx)


def test_avaliar_universo_com_universo_pequeno_mockado(monkeypatch):
    """So verifica que a orquestracao roda de ponta a ponta e devolve um
    ResultadoAtivoPCA por par, sem exigir um numero especifico de
    exclusoes -- comportamento estatistico exato depende da realizacao
    aleatoria, o objetivo aqui e a integracao (PCA -> OU -> filtro ->
    bateria), nao um resultado numerico fixo."""
    rng = np.random.default_rng(3)
    n = 1000
    fator = np.cumsum(rng.normal(0, 0.5, n))
    pares = {}
    for i, nome in enumerate(["A/USDT", "B/USDT", "C/USDT", "D/USDT"]):
        preco = 100.0 * np.exp(0.001 * i * np.arange(n) / n) + fator * (0.5 + 0.1 * i) + rng.normal(0, 0.2, n)
        preco = np.abs(preco) + 50.0  # nunca <= 0
        pares[nome] = _ohlcv_sintetico(n, preco)

    monkeypatch.setattr(mod, "fetch_ohlcv", lambda par, tf, limit: pares[par])

    resultados = mod.avaliar_universo(list(pares.keys()))

    assert len(resultados) == len(pares)
    assert {r.par for r in resultados} == set(pares.keys())
    for r in resultados:
        assert r.n_componentes >= 1
        assert 0.0 <= r.variancia_explicada <= 1.0
        if not r.excluido:
            assert r.relatorio is not None
        else:
            assert r.motivo_exclusao is not None


def test_avaliar_universo_distingue_motivo_de_exclusao(monkeypatch):
    """Meia-vida fora da faixa e OU nao-estacionario sao motivos
    DIFERENTES de exclusao -- nao devem ficar atras do mesmo rotulo
    (achado de code-review)."""
    rng = np.random.default_rng(5)
    n = 1000
    fator = np.cumsum(rng.normal(0, 0.5, n))
    pares = {}
    for i, nome in enumerate(["A/USDT", "B/USDT", "C/USDT", "D/USDT"]):
        preco = 100.0 + fator * (0.5 + 0.1 * i) + rng.normal(0, 0.2, n)
        pares[nome] = _ohlcv_sintetico(n, np.abs(preco) + 50.0)
    monkeypatch.setattr(mod, "fetch_ohlcv", lambda par, tf, limit: pares[par])

    # forca meia-vida sempre na faixa (isola o caminho de exclusao por OU
    # nao-estacionario) e OU sempre nao-estacionario (forca a exclusao)
    monkeypatch.setattr(mod, "meia_vida_reversao", lambda spread: 10.0)
    monkeypatch.setattr(mod, "_ajustar_ou", lambda x_treino: None)

    resultados = mod.avaliar_universo(list(pares.keys()))

    assert resultados, "esperava resultado para o teste fazer sentido"
    assert all(r.excluido for r in resultados)
    for r in resultados:
        assert "OU" in r.motivo_exclusao or "estacionario" in r.motivo_exclusao
        assert "meia-vida fora" not in r.motivo_exclusao


def test_avaliar_universo_motivo_de_exclusao_por_meia_vida_fora_da_faixa(monkeypatch):
    rng = np.random.default_rng(6)
    n = 1000
    fator = np.cumsum(rng.normal(0, 0.5, n))
    pares = {}
    for i, nome in enumerate(["A/USDT", "B/USDT", "C/USDT", "D/USDT"]):
        preco = 100.0 + fator * (0.5 + 0.1 * i) + rng.normal(0, 0.2, n)
        pares[nome] = _ohlcv_sintetico(n, np.abs(preco) + 50.0)
    monkeypatch.setattr(mod, "fetch_ohlcv", lambda par, tf, limit: pares[par])

    # meia-vida sempre fora da faixa declarada -- isola o caminho de
    # exclusao por faixa, nunca deve chegar a chamar _ajustar_ou
    monkeypatch.setattr(mod, "meia_vida_reversao", lambda spread: mod.MEIA_VIDA_MAX + 1)

    resultados = mod.avaliar_universo(list(pares.keys()))

    assert resultados
    assert all(r.excluido for r in resultados)
    for r in resultados:
        assert "meia-vida fora" in r.motivo_exclusao


def test_avaliar_universo_devolve_vazio_com_menos_de_tres_pares(monkeypatch):
    n = 500
    preco = 100.0 + np.cumsum(np.random.default_rng(4).normal(0, 0.1, n))
    df = _ohlcv_sintetico(n, np.abs(preco) + 50.0)
    monkeypatch.setattr(mod, "fetch_ohlcv", lambda par, tf, limit: df)

    resultados = mod.avaliar_universo(["A/USDT", "B/USDT"])

    assert resultados == []
