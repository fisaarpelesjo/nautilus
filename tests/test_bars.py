"""Testes da construção de barras dirigidas por informação (spec 026, H13)."""
import numpy as np
import pandas as pd
import pytest

from data.bars import (
    TIPOS,
    ParametrosBarra,
    calibrar_limiar,
    construir_barras,
    diagnostico,
)


def _serie(n=400, semente=3, freq="1h"):
    rng = np.random.default_rng(semente)
    preco = 100 * np.exp(np.cumsum(rng.normal(0.0002, 0.01, n)))
    return pd.DataFrame({
        "open": preco, "close": preco,
        "high": preco * 1.01, "low": preco * 0.99,
        "volume": rng.uniform(1e4, 1e6, n),
    }, index=pd.date_range("2026-01-01", periods=n, freq=freq))


# ------------------------------------------------------------------ T002 fumaça

def test_api_publica_existe():
    assert TIPOS == ("dollar", "cusum")
    assert ParametrosBarra().tipo == "dollar"


# ------------------------------------------------------- T004 regras de agregação

def test_agregacao_usa_primeiro_maximo_minimo_ultimo_e_soma():
    df = pd.DataFrame({
        "open": [10.0, 11.0, 12.0, 13.0],
        "high": [10.5, 15.0, 12.5, 13.5],
        "low": [9.0, 10.8, 7.0, 12.9],
        "close": [10.2, 11.9, 12.1, 13.2],
        "volume": [100.0, 100.0, 100.0, 100.0],
    }, index=pd.date_range("2026-01-01", periods=4, freq="1h"))

    # Limiar que fecha exatamente a cada 2 candles (~1100 e ~1200 de nocional).
    barras = construir_barras(df, "dollar", limiar=2000.0)

    assert len(barras) == 2
    primeira = barras.iloc[0]
    assert primeira["open"] == 10.0          # open do PRIMEIRO
    assert primeira["high"] == 15.0          # maximo do grupo
    assert primeira["low"] == 9.0            # minimo do grupo
    assert primeira["close"] == 11.9         # close do ULTIMO
    assert primeira["volume"] == 200.0       # soma
    assert primeira["candles_origem"] == 2


# ------------------------------------------------ T005 índice é o fechamento

def test_indice_da_barra_e_o_instante_do_ultimo_candle():
    """Indexar pela abertura dataria a barra num momento em que seu conteúdo
    ainda era desconhecido — vazamento de futuro por convenção de índice."""
    df = _serie(n=60)
    barras = construir_barras(df, "dollar", limiar=calibrar_limiar(
        df, "dollar", ParametrosBarra(tipo="dollar", barras_alvo=10)))

    assert len(barras) > 0
    for ts in barras.index:
        assert ts in df.index
    # O primeiro instante da série só pode ser índice de barra se a primeira
    # barra tiver exatamente um candle.
    if barras.iloc[0]["candles_origem"] > 1:
        assert barras.index[0] != df.index[0]


# ==================================================== T006 CAUSALIDADE (US3)

def test_causalidade_reconstrucao_incremental_e_identica():
    """FR-003 — o teste mais importante desta spec.

    Barras construídas prefixo a prefixo, como o bot as veria ao vivo, têm de
    ser idênticas às construídas sobre a série completa. Se diferirem, alguma
    decisão de fronteira está usando informação futura.

    É a classe de defeito de M2, que passou meses despercebida no projeto: um
    filtro que comparava preço histórico contra indicador corrente. Uma barra
    que conhece o próprio total futuro produziria o resultado mais convincente
    e mais falso possível.
    """
    df = _serie(n=300, semente=11)
    limiar = calibrar_limiar(df, "dollar", ParametrosBarra(barras_alvo=40))

    completo = construir_barras(df, "dollar", limiar=limiar)

    # Reconstrói vendo apenas o prefixo disponível em cada instante.
    for corte in (50, 120, 200, 300):
        prefixo = construir_barras(df.iloc[:corte], "dollar", limiar=limiar)
        n = len(prefixo)
        if n == 0:
            continue
        assert prefixo.index.tolist() == completo.index[:n].tolist(), corte
        for col in ("open", "high", "low", "close", "volume", "candles_origem"):
            assert prefixo[col].tolist() == completo[col].iloc[:n].tolist(), (corte, col)


def test_causalidade_vale_para_cusum():
    df = _serie(n=300, semente=5)
    limiar = calibrar_limiar(df, "cusum", ParametrosBarra(tipo="cusum", barras_alvo=40))

    completo = construir_barras(df, "cusum", limiar=limiar)
    prefixo = construir_barras(df.iloc[:150], "cusum", limiar=limiar)

    n = len(prefixo)
    assert n > 0
    assert prefixo.index.tolist() == completo.index[:n].tolist()
    assert prefixo["close"].tolist() == completo["close"].iloc[:n].tolist()


# ------------------------------------------------- T007 barra incompleta cai

def test_barra_incompleta_nao_aparece_na_saida():
    """FR-004 — o `close` de uma barra que não fechou é o preço do instante em
    que os dados acabaram. Tratá-lo como fechamento é transformar um instante
    arbitrário em decisão."""
    df = pd.DataFrame({
        "open": [10.0] * 5, "high": [10.0] * 5, "low": [10.0] * 5,
        "close": [10.0] * 5, "volume": [100.0] * 5,
    }, index=pd.date_range("2026-01-01", periods=5, freq="1h"))

    # Limiar de 2000 => fecha nos candles 1 e 3 (indices 0-based), sobra o 4.
    barras = construir_barras(df, "dollar", limiar=2000.0)

    assert len(barras) == 2
    assert barras.index[-1] == df.index[3]
    assert df.index[4] not in barras.index


def test_nenhuma_barra_quando_o_limiar_nunca_e_cruzado():
    df = _serie(n=50)
    enorme = float((df["close"] * df["volume"]).sum()) * 10

    assert len(construir_barras(df, "dollar", limiar=enorme)) == 0


# --------------------------------------------------- T008 limiar inválido

@pytest.mark.parametrize("limiar", [0.0, -1.0, None])
def test_limiar_nao_positivo_e_recusado(limiar):
    with pytest.raises(ValueError, match="limiar"):
        construir_barras(_serie(n=50), "dollar", limiar=limiar)


def test_tipo_desconhecido_e_recusado():
    with pytest.raises(ValueError, match="tipo de barra"):
        construir_barras(_serie(n=50), "trades", limiar=1.0)


# ------------------------------------------------------- T009 volume ausente

def test_volume_ausente_e_recusado_em_dollar_bars():
    """Volume ausente impede a construção. Recusar é melhor que devolver uma
    barra silenciosamente errada."""
    df = _serie(n=50).drop(columns=["volume"])

    with pytest.raises(ValueError, match="volume"):
        construir_barras(df, "dollar", limiar=1000.0)


def test_volume_totalmente_nulo_e_recusado():
    df = _serie(n=50)
    df["volume"] = 0.0

    with pytest.raises(ValueError, match="volume"):
        construir_barras(df, "dollar", limiar=1000.0)


def test_serie_vazia_e_recusada():
    with pytest.raises(ValueError, match="vazia"):
        construir_barras(_serie(n=10).iloc[0:0], "dollar", limiar=1.0)


# ------------------------------------------------------- T014 calibração (D2)

@pytest.mark.parametrize("tipo", ["dollar", "cusum"])
def test_calibracao_converge_dentro_da_tolerancia(tipo):
    df = _serie(n=2000, semente=7)
    p = ParametrosBarra(tipo=tipo, barras_alvo=200, tolerancia=0.05)

    limiar = calibrar_limiar(df, tipo, p)
    barras = construir_barras(df, tipo, limiar=limiar)

    erro = abs(len(barras) - p.barras_alvo) / p.barras_alvo
    assert erro <= 0.15, f"{tipo}: {len(barras)} barras contra alvo {p.barras_alvo}"


def test_calibracao_nao_consulta_metrica_de_retorno():
    """FR-014 — varrer limiares até um passar é o problema de testes múltiplos
    que a metodologia existe para conter. A calibração é de ESCALA."""
    import ast
    import inspect

    import data.bars as modulo

    fonte = inspect.getsource(modulo.calibrar_limiar)
    arvore = ast.parse(fonte.strip())
    nomes = {n.id for n in ast.walk(arvore) if isinstance(n, ast.Name)}
    nomes |= {n.attr for n in ast.walk(arvore) if isinstance(n, ast.Attribute)}

    proibidos = {"total_return_pct", "profit_factor", "max_drawdown_pct",
                 "edge_score", "simulate_backtest", "evaluate_approval"}
    assert not (nomes & proibidos), nomes & proibidos


def test_calibracao_e_deterministica():
    df = _serie(n=800, semente=2)
    a = calibrar_limiar(df, "dollar", ParametrosBarra(barras_alvo=100))
    b = calibrar_limiar(df, "dollar", ParametrosBarra(barras_alvo=100))

    assert a == b


# ---------------------------------------------------- T015 / T038 diagnóstico

def test_diagnostico_reporta_agrupamento():
    df = _serie(n=1000, semente=4)
    limiar = calibrar_limiar(df, "dollar", ParametrosBarra(barras_alvo=100))
    barras = construir_barras(df, "dollar", limiar=limiar)

    d = diagnostico(barras)

    assert d["barras"] == len(barras)
    assert d["mediana"] >= 1.0
    assert 0.0 <= d["pct_1_candle"] <= 100.0
    assert barras["candles_origem"].sum() <= len(df)


def test_diagnostico_de_serie_vazia_nao_explode():
    assert diagnostico(pd.DataFrame())["barras"] == 0


def test_reamostragem_inerte_e_detectavel_pelo_diagnostico():
    """Limiar baixíssimo faz cada candle virar uma barra. O diagnóstico precisa
    tornar isso visível — foi o que faltou em H12, onde 37 de 48 combinações
    não mediram nada e apareciam como reprovação."""
    df = _serie(n=200)
    barras = construir_barras(df, "dollar", limiar=1e-9)

    d = diagnostico(barras)

    assert d["pct_1_candle"] == 100.0
    assert d["barras"] == len(df)
