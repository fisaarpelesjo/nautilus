"""Rotulagem por barreira tripla e atributos declarados (spec 027, H14)."""
import numpy as np
import pandas as pd
import pytest

from strategy.barreira_tripla import (
    ATRIBUTOS,
    ParametrosBarreira,
    distribuicao_classes,
    extrair_atributos,
    razao_de_chances,
    rotular,
)


def _serie(closes, atr=1.0, altas=None, baixas=None):
    n = len(closes)
    c = np.array(closes, dtype=float)
    return pd.DataFrame({
        "open": c,
        "close": c,
        "high": c if altas is None else np.array(altas, dtype=float),
        "low": c if baixas is None else np.array(baixas, dtype=float),
        "atr": np.full(n, atr, dtype=float),
    }, index=pd.date_range("2026-01-01", periods=n, freq="4h"))


P = ParametrosBarreira(sl_mult=1.0, tp_mult=2.0, limite_velas=5)


# ---------------------------------------------------------------- T004 rótulos

def test_alvo_tocado_primeiro_rotula_positivo():
    # Entrada em 100, alvo 102, stop 99. A máxima chega a 102 na vela 2.
    r = rotular(_serie([100, 100.5, 102.5, 100, 100], altas=[100, 100.5, 102.5, 100, 100],
                       baixas=[100, 100.5, 102.5, 100, 100]), P)

    assert r["rotulo_bruto"].iloc[0] == 1
    assert r["rotulo"].iloc[0] == 1


def test_stop_tocado_primeiro_rotula_negativo():
    r = rotular(_serie([100, 99.5, 98.5, 105, 105], altas=[100, 99.5, 98.5, 105, 105],
                       baixas=[100, 99.5, 98.5, 105, 105]), P)

    assert r["rotulo_bruto"].iloc[0] == -1
    assert r["rotulo"].iloc[0] == 0, "o bot so opera comprado: stop e classe negativa"


def test_nenhuma_barreira_tocada_rotula_tempo():
    r = rotular(_serie([100, 100.2, 99.8, 100.1, 100.3, 100.2], altas=None, baixas=None), P)

    assert r["rotulo_bruto"].iloc[0] == 0
    assert r["rotulo"].iloc[0] == 0


def test_stop_tem_precedencia_quando_ambos_no_mesmo_candle():
    """Conservador: uma vela que toca as duas barreiras conta como stop.

    Não é possível saber, com OHLC agregado, qual foi tocada primeiro dentro da
    vela. Assumir o alvo produziria rótulos otimistas por construção.
    """
    r = rotular(_serie([100, 100], altas=[100, 103], baixas=[100, 98]), P)

    assert r["rotulo_bruto"].iloc[0] == -1


# ============================================== T005 CAUSALIDADE (US1, FR-004)

def test_preco_anterior_ao_evento_nao_altera_o_rotulo():
    """FR-004 — o rótulo olha para a frente. Se um preço passado o muda, a
    rotulagem está lendo o que não deveria."""
    base = [100, 100, 100.5, 102.5, 100, 100]
    original = rotular(_serie(base, altas=base, baixas=base), P)

    mexido = list(base)
    mexido[0] = 80.0  # vela ANTERIOR ao evento de indice 1
    alterado = rotular(_serie(mexido, altas=mexido, baixas=mexido), P)

    assert original["rotulo_bruto"].iloc[1] == alterado["rotulo_bruto"].iloc[1]
    assert original["fim_horizonte"].iloc[1] == alterado["fim_horizonte"].iloc[1]


def test_preco_dentro_do_horizonte_altera_o_rotulo():
    """A contrapartida: se nada dentro do horizonte muda o rótulo, a rotulagem
    não está olhando para lugar nenhum."""
    base = [100, 100.5, 100.5, 100.5, 100.5, 100.5]
    original = rotular(_serie(base, altas=base, baixas=base), P)

    mexido = list(base)
    mexido[2] = 97.0  # dentro do horizonte do evento 0, abaixo do stop 99
    alterado = rotular(_serie(mexido, altas=mexido, baixas=mexido), P)

    assert original["rotulo_bruto"].iloc[0] == 0
    assert alterado["rotulo_bruto"].iloc[0] == -1


def test_rotulo_nao_usa_velas_alem_do_limite():
    """Uma barreira tocada depois do limite de tempo não conta."""
    p = ParametrosBarreira(sl_mult=1.0, tp_mult=2.0, limite_velas=2)
    base = [100, 100, 100, 105, 105]
    r = rotular(_serie(base, altas=base, baixas=base), p)

    assert r["rotulo_bruto"].iloc[0] == 0, "o alvo so aparece na vela 3, fora do limite 2"


# ------------------------------------------------------- T006 fim_horizonte

def test_fim_horizonte_e_o_instante_da_barreira_tocada():
    base = [100, 100.5, 102.5, 100, 100]
    df = _serie(base, altas=base, baixas=base)
    r = rotular(df, P)

    assert r["fim_horizonte"].iloc[0] == df.index[2]


def test_fim_horizonte_e_o_limite_quando_nenhuma_barreira_e_tocada():
    base = [100, 100.1, 100.2, 100.1, 100.2, 100.1, 100.2]
    df = _serie(base, altas=base, baixas=base)
    r = rotular(df, P)

    assert r["fim_horizonte"].iloc[0] == df.index[P.limite_velas]


# ------------------------------------------------------------- T007 ATR ruim

@pytest.mark.parametrize("valor", [0.0, -1.0, np.nan, np.inf])
def test_atr_invalido_produz_evento_sem_rotulo(valor):
    base = [100, 101, 102, 103, 104, 105]
    df = _serie(base, altas=base, baixas=base)
    df.loc[df.index[0], "atr"] = valor

    r = rotular(df, P)

    assert pd.isna(r["rotulo_bruto"].iloc[0])


def test_atr_ausente_e_recusado():
    base = [100, 101, 102]
    df = _serie(base).drop(columns=["atr"])

    with pytest.raises(ValueError, match="atr"):
        rotular(df, P)


# ------------------------------------------------ T008 atributos declarados

def _df_indicadores(n=200, semente=1):
    from backtesting.horizonte import preparar
    from strategy.ema_rsi import EmaRsiStrategy

    rng = np.random.default_rng(semente)
    p = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.01, n)))
    df = pd.DataFrame({
        "open": p, "close": p, "high": p * 1.01, "low": p * 0.99,
        "volume": rng.uniform(1e4, 1e6, n),
    }, index=pd.date_range("2026-01-01", periods=n, freq="4h"))
    return preparar(df, EmaRsiStrategy())


def test_conjunto_de_atributos_e_exatamente_o_declarado():
    """FR-003 — o conjunto é fixo. Buscar atributos reintroduziria o problema
    de testes múltiplos que a metodologia existe para conter."""
    x = extrair_atributos(_df_indicadores())

    assert list(x.columns) == ATRIBUTOS
    assert len(ATRIBUTOS) == 5


def test_atributos_sao_adimensionais_ou_normalizados():
    """Pré-condição para agrupar pares de preços muito diferentes (D4): dois
    pares com o mesmo comportamento e preços 100x distintos produzem os mesmos
    atributos."""
    barato = _df_indicadores()
    caro = barato.copy()
    for col in ("open", "close", "high", "low", "ema_fast", "ema_slow",
                "ema_trend", "bb_upper", "bb_lower", "bb_middle", "atr", "macd"):
        if col in caro:
            caro[col] = caro[col] * 100

    xb = extrair_atributos(barato).dropna()
    xc = extrair_atributos(caro).dropna()

    for col in ATRIBUTOS:
        assert np.allclose(xb[col].values, xc[col].values, rtol=1e-9), col


def test_rsi_e_dist_ema_fast_ficaram_de_fora():
    """Descartados por colinearidade medida: 0,901 e 0,959 contra
    `dist_ema_slow`. Correlação nesse nível desestabiliza a estimação."""
    assert "rsi" not in ATRIBUTOS
    assert "dist_ema_fast" not in ATRIBUTOS
    assert "dist_ema_trend" not in ATRIBUTOS
    assert "pos_bb" not in ATRIBUTOS


# ------------------------------------- T015 distribuição e razão de chances

def test_distribuicao_de_classes():
    r = pd.Series([1, 1, -1, -1, -1, 0])

    d = distribuicao_classes(r)

    assert d["alvo"] == pytest.approx(2 / 6 * 100)
    assert d["stop"] == pytest.approx(3 / 6 * 100)
    assert d["tempo"] == pytest.approx(1 / 6 * 100)


def test_razao_de_chances_alvo_sobre_stop():
    assert razao_de_chances(pd.Series([1, 1, -1, -1, -1, -1])) == pytest.approx(0.5)


def test_razao_de_chances_sem_stop_e_infinita_nao_zero():
    """Nenhum stop significa razão indefinida por divisão por zero. Devolver 0,0
    a leria como o pior caso possível, que é o oposto do observado."""
    assert razao_de_chances(pd.Series([1, 1, 0])) == float("inf")


def test_razao_de_chances_de_amostra_vazia_e_none():
    assert razao_de_chances(pd.Series([], dtype=float)) is None
