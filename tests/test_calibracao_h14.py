"""Calibracao do classificador de H14 (spec 055).

A linha de overlays de risco (specs 040-047) fechou apontando para o
classificador de entrada em si. Esta spec pergunta se o subconjunto ja
decidido em producao tem uma cauda de alta confianca explorável: um corte
mais estrito concentra qualidade (razao sobe), ou so reduz a amostra?
"""
import pandas as pd
import pytest


def test_faixas_por_corte_conta_alvo_stop_tempo_pelo_rotulo_bruto():
    from backtesting.calibracao_h14 import _faixas_por_corte
    from backtesting.modelo import ParametrosBarreira

    prev = pd.Series([0.2, 0.4, 0.4, 0.6, 0.6, 0.6])
    rot = pd.Series([1, -1, -1, 1, 1, 0])  # alvo, stop, stop, alvo, alvo, tempo

    faixas = _faixas_por_corte(prev, rot, cortes=[0.3], limiar=0.5,
                                params=ParametrosBarreira())

    f = faixas[0]
    assert f.corte == 0.3
    assert f.n == 5  # tudo menos o 0.2
    assert f.alvo == 2
    assert f.stop == 2
    assert f.tempo == 1
    assert f.razao == pytest.approx(1.0)


def test_corte_zero_e_sentinela_para_o_limiar_real():
    """0.0 nao filtra em prob>0 -- resolve para limiar_de_decisao real."""
    from backtesting.calibracao_h14 import _faixas_por_corte
    from backtesting.modelo import ParametrosBarreira

    prev = pd.Series([0.1, 0.4, 0.6])
    rot = pd.Series([-1, 1, 1])

    faixas = _faixas_por_corte(prev, rot, cortes=[0.0], limiar=0.5,
                                params=ParametrosBarreira())

    assert faixas[0].corte == 0.5
    assert faixas[0].n == 1  # so 0.6 > 0.5


def test_stop_zero_produz_razao_infinita_sem_quebrar():
    from backtesting.calibracao_h14 import _faixas_por_corte
    from backtesting.modelo import ParametrosBarreira

    prev = pd.Series([0.6, 0.7])
    rot = pd.Series([1, 1])

    faixas = _faixas_por_corte(prev, rot, cortes=[0.5], limiar=0.5,
                                params=ParametrosBarreira())

    assert faixas[0].razao == float("inf")
    assert faixas[0].supera_empate is False  # sem stop, supera_empate_com_confianca nao roda


def test_amostra_grande_e_razao_alta_supera_empate_com_confianca():
    """Espelha o achado real medido (n~2500, razao~0.70 > empate 0.50)."""
    from backtesting.calibracao_h14 import _faixas_por_corte
    from backtesting.modelo import ParametrosBarreira

    n_alvo, n_stop = 968, 1378
    prev = pd.Series([0.6] * (n_alvo + n_stop))
    rot = pd.Series([1] * n_alvo + [-1] * n_stop)

    faixas = _faixas_por_corte(prev, rot, cortes=[0.5], limiar=0.5,
                                params=ParametrosBarreira())

    assert faixas[0].supera_empate is True


def test_amostra_pequena_com_razao_alta_nao_supera_por_falta_de_evidencia():
    """Mesma razao da faixa anterior, amostra pequena -- IC nao sobrevive.

    Mesma licao de M9/M13 (registro de hipoteses): ponto estimado bom nao
    e evidencia sem banda de confianca.
    """
    from backtesting.calibracao_h14 import _faixas_por_corte
    from backtesting.modelo import ParametrosBarreira

    prev = pd.Series([0.6] * 10)
    rot = pd.Series([1] * 6 + [-1] * 4)  # razao 1.5, folgadamente > empate 0.5

    faixas = _faixas_por_corte(prev, rot, cortes=[0.5], limiar=0.5,
                                params=ParametrosBarreira())

    assert faixas[0].razao == pytest.approx(1.5)
    assert faixas[0].supera_empate is False


def test_avaliar_calibracao_sem_previsoes_devolve_faixas_vazias():
    from backtesting.calibracao_h14 import avaliar_calibracao
    import backtesting.calibracao_h14 as mod

    def _sem_dado(pares, params):
        return None, None

    orig = mod._previsoes_pooladas
    mod._previsoes_pooladas = _sem_dado
    try:
        resultado = avaliar_calibracao(pares=["BTC/USDT"])
    finally:
        mod._previsoes_pooladas = orig

    assert resultado.faixas == []
    assert resultado.n_pares == 0


def test_avaliar_calibracao_usa_pares_e_params_passados(monkeypatch):
    from backtesting.calibracao_h14 import avaliar_calibracao
    import backtesting.calibracao_h14 as mod
    from backtesting.modelo import ParametrosBarreira

    chamada = {}

    def _fake_pooladas(pares, params):
        chamada["pares"] = list(pares)
        chamada["params"] = params
        prev = pd.Series([0.6, 0.6, 0.2])
        rot = pd.Series([1, -1, 1])
        return prev, rot

    monkeypatch.setattr(mod, "_previsoes_pooladas", _fake_pooladas)

    p = ParametrosBarreira()
    resultado = avaliar_calibracao(pares=["ETH/USDT", "SOL/USDT"], params=p,
                                    cortes=[0.5])

    assert chamada["pares"] == ["ETH/USDT", "SOL/USDT"]
    assert chamada["params"] is p
    assert resultado.n_pares == 2
    assert len(resultado.faixas) == 1
    assert resultado.faixas[0].n == 2  # so os dois 0.6 > 0.5
