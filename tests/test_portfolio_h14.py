import numpy as np
import pandas as pd
import pytest

from backtesting.portfolio_h14 import (
    UNIVERSO_AMPLO,
    _correlacionado_com_posicao_aberta,
    _simular_carteira_core,
    comparar_drawdown,
)
from config.settings import MAX_CONSECUTIVE_LOSSES, MAX_POSITIONS

LIMIAR = 0.3333


def _prep(index, close, high=None, low=None, atr=2.0, atr_ratio=None):
    n = len(index)
    high = high if high is not None else [c * 1.001 for c in close]
    low = low if low is not None else [c * 0.999 for c in close]
    dados = {"close": close, "high": high, "low": low, "atr": [atr] * n}
    if atr_ratio is not None:
        dados["atr_ratio"] = atr_ratio if hasattr(atr_ratio, "__len__") else [atr_ratio] * n
    return pd.DataFrame(dados, index=index)


def _idx(n, freq="4h"):
    return pd.date_range("2026-01-01", periods=n, freq=freq)


def _serie(n, semente=1, sigma=0.01):
    rng = np.random.default_rng(semente)
    return list(100 * np.exp(np.cumsum(rng.normal(0, sigma, n))))


# ============================================================ T004 — caixa

def test_caixa_abaixo_do_minimo_nao_abre_posicao():
    """Com capital abaixo do piso de $10, nenhuma posicao abre -- o caixa
    fica intacto, nunca negativo (FR-004/FR-011)."""
    idx = _idx(3)
    previsoes = {"A/USDT": pd.Series([1.0, 1.0, 1.0], index=idx)}
    preparados = {"A/USDT": _prep(idx, close=[100.0, 100.0, 100.0])}

    r = _simular_carteira_core(previsoes, preparados, LIMIAR, capital_inicial=5.0)

    assert r.total_trades == 0
    assert r.final_capital == pytest.approx(5.0)


def test_caixa_nunca_excede_o_gasto_com_multiplos_candidatos_simultaneos():
    """Varios pares sinalizam compra no mesmo candle -- a soma do custo de
    entrada das posicoes abertas nunca excede o capital disponivel."""
    idx = _idx(3)
    capital_inicial = 150.0
    previsoes = {
        f"{p}/USDT": pd.Series([1.0, 1.0, 1.0], index=idx) for p in "ABCD"
    }
    preparados = {
        f"{p}/USDT": _prep(idx, close=[100.0, 100.0, 100.0]) for p in "ABCD"
    }

    r = _simular_carteira_core(previsoes, preparados, LIMIAR, capital_inicial=capital_inicial)

    gasto_total = sum(t.quantity * t.entry_price + t.fees for t in r.trades if t.entry_time == idx[0])
    assert gasto_total <= capital_inicial * 1.001


# ===================================================== T005 — MAX_POSITIONS

def test_max_positions_nunca_excedido(monkeypatch):
    monkeypatch.setattr("backtesting.portfolio_h14.MAX_POSITIONS", 2)
    idx = _idx(2)
    previsoes = {f"{p}/USDT": pd.Series([1.0, 1.0], index=idx) for p in "ABCD"}
    preparados = {f"{p}/USDT": _prep(idx, close=[100.0, 100.0]) for p in "ABCD"}

    r = _simular_carteira_core(previsoes, preparados, LIMIAR, capital_inicial=100000.0)

    abertas_no_primeiro_candle = [t for t in r.trades if t.entry_time == idx[0]]
    assert len(abertas_no_primeiro_candle) == 2


# ========================================================== T006 — desempate

def test_desempate_por_maior_probabilidade(monkeypatch):
    """Dois pares sinalizam no mesmo candle, so 1 slot livre -- abre o de
    maior previsao (D4), nunca o outro. Precos distintos por par tornam a
    escolha identificavel sem exigir um campo `par` em `Trade`."""
    monkeypatch.setattr("backtesting.portfolio_h14.MAX_POSITIONS", 1)
    idx = _idx(2)
    previsoes = {
        "ALTO/USDT": pd.Series([0.9, 0.9], index=idx),
        "BAIXO/USDT": pd.Series([0.5, 0.5], index=idx),
    }
    preparados = {
        "ALTO/USDT": _prep(idx, close=[100.0, 100.0]),
        "BAIXO/USDT": _prep(idx, close=[50.0, 50.0]),
    }

    r = _simular_carteira_core(previsoes, preparados, LIMIAR, capital_inicial=100000.0)

    abertas = [t for t in r.trades if t.entry_time == idx[0]]
    assert len(abertas) == 1
    assert abertas[0].entry_price == pytest.approx(100.0, rel=0.01)


# ======================================== T007 — take-profit / stop trailing

def test_fecha_no_take_profit_por_atr():
    idx = _idx(3)
    atr = 2.0
    # Entrada em 100, ATR=2 -> alvo = 100 + ATR_TP_MULTIPLIER*2 (3.0 default = 106)
    close = [100.0, 100.0, 100.0]
    high = [100.0, 107.0, 107.0]
    low = [99.9, 99.9, 99.9]
    previsoes = {"A/USDT": pd.Series([1.0, 0.0, 0.0], index=idx)}
    preparados = {"A/USDT": _prep(idx, close=close, high=high, low=low, atr=atr)}

    r = _simular_carteira_core(previsoes, preparados, LIMIAR, capital_inicial=1000.0)

    assert r.total_trades == 1
    assert r.trades[0].exit_reason == "Take Profit"


def test_fecha_no_stop_trailing():
    idx = _idx(3)
    atr = 2.0
    # Entrada em 100, stop inicial = 100 - ATR_SL_MULTIPLIER*2 (1.5 default = 97)
    close = [100.0, 100.0, 100.0]
    high = [100.0, 100.0, 100.0]
    low = [99.9, 96.0, 96.0]
    previsoes = {"A/USDT": pd.Series([1.0, 0.0, 0.0], index=idx)}
    preparados = {"A/USDT": _prep(idx, close=close, high=high, low=low, atr=atr)}

    r = _simular_carteira_core(previsoes, preparados, LIMIAR, capital_inicial=1000.0)

    assert r.total_trades == 1
    assert r.trades[0].exit_reason == "Stop Loss"


def test_stop_trailing_sobe_e_dispara_em_nivel_que_o_stop_original_nao_tocaria():
    """Preco sobe (stop trailing deve subir de 97 para 102), depois recua
    para 100,9 -- abaixo do stop JA SUBIDO (102), mas acima do original
    (97). Só dispara "Stop Loss" aqui se o trailing realmente subiu."""
    idx = _idx(3)
    atr = 2.0
    close = [100.0, 105.0, 101.0]
    high = [100.0, 105.0, 101.0]
    low = [99.9, 104.9, 100.9]
    previsoes = {"A/USDT": pd.Series([1.0, 0.0, 0.0], index=idx)}
    preparados = {"A/USDT": _prep(idx, close=close, high=high, low=low, atr=atr)}

    r = _simular_carteira_core(previsoes, preparados, LIMIAR, capital_inicial=1000.0)

    assert r.total_trades == 1
    assert r.trades[0].exit_reason == "Stop Loss"
    assert r.trades[0].exit_price == pytest.approx(102.0, abs=0.2)


# ================================================== T008 — fim do periodo

def test_posicao_aberta_no_fim_fecha_com_rotulo_proprio():
    idx = _idx(3)
    previsoes = {"A/USDT": pd.Series([1.0, 0.0, 0.0], index=idx)}
    preparados = {"A/USDT": _prep(idx, close=[100.0, 101.0, 102.0])}

    r = _simular_carteira_core(previsoes, preparados, LIMIAR, capital_inicial=1000.0)

    assert r.total_trades == 1
    assert r.trades[0].exit_reason == "Fim do periodo"
    assert r.trades[0].exit_time == idx[-1]


# ============================================= T009 — evaluate_approval

def test_resultado_aceito_por_evaluate_approval_sem_excecao():
    from backtesting.approval import evaluate_approval

    idx = _idx(3)
    previsoes = {"A/USDT": pd.Series([1.0, 0.0, 0.0], index=idx)}
    preparados = {"A/USDT": _prep(idx, close=[100.0, 101.0, 102.0])}

    r = _simular_carteira_core(previsoes, preparados, LIMIAR, capital_inicial=1000.0)
    veredito = evaluate_approval(r)

    assert veredito.status in {"aprovado", "reprovado", "inconclusivo"}


# ================================================ T012 — buy-and-hold

def test_buy_hold_e_carteira_igualmente_ponderada():
    idx = _idx(2)
    # A dobra de preco (100->200), B cai pela metade (100->50). Igualmente
    # ponderados, o resultado liquido e neutro (nao a media simples dos
    # retornos percentuais, mas o valor final de uma carteira 50/50 real).
    previsoes = {
        "A/USDT": pd.Series([0.0, 0.0], index=idx),
        "B/USDT": pd.Series([0.0, 0.0], index=idx),
    }
    preparados = {
        "A/USDT": _prep(idx, close=[100.0, 200.0]),
        "B/USDT": _prep(idx, close=[100.0, 50.0]),
    }

    r = _simular_carteira_core(previsoes, preparados, LIMIAR, capital_inicial=1000.0)

    # 500 em A vira 1000; 500 em B vira 250; total 1250 -> +25%.
    assert r.buy_hold_return_pct == pytest.approx(25.0, abs=0.01)


def test_evaluate_approval_usa_limiares_ja_existentes_sem_parametro_novo():
    from backtesting.approval import evaluate_approval

    idx = _idx(3)
    previsoes = {"A/USDT": pd.Series([1.0, 0.0, 0.0], index=idx)}
    preparados = {"A/USDT": _prep(idx, close=[100.0, 101.0, 102.0])}

    r = _simular_carteira_core(previsoes, preparados, LIMIAR, capital_inicial=1000.0)

    # Mesma chamada usada em qualquer outra avaliacao do projeto -- sem
    # kwarg extra.
    veredito = evaluate_approval(r)
    assert veredito is not None


# ==================================================== T015 — comparacao

def test_comparar_drawdown_devolve_os_dois_numeros_separados():
    from unittest.mock import MagicMock

    resultado_carteira = MagicMock(max_drawdown_pct=12.5)
    avaliacao_a = MagicMock(par="A/USDT")
    avaliacao_a.modelo.backtest.max_drawdown_pct = 30.0
    avaliacao_b = MagicMock(par="B/USDT")
    avaliacao_b.modelo.backtest.max_drawdown_pct = 45.0

    r = comparar_drawdown(resultado_carteira, [avaliacao_a, avaliacao_b])

    assert r["drawdown_carteira"] == pytest.approx(12.5)
    assert r["maior_drawdown_por_par"] == pytest.approx(45.0)
    assert r["drawdowns_por_par"] == {"A/USDT": 30.0, "B/USDT": 45.0}


# ============================================== spec 040 (universo amplo)

def test_universo_amplo_tem_34_pares_unicos_usdt():
    assert len(UNIVERSO_AMPLO) == 34
    assert len(set(UNIVERSO_AMPLO)) == 34
    assert all(p.endswith("/USDT") for p in UNIVERSO_AMPLO)


def test_universo_amplo_nao_inclui_pegged_excluidos():
    excluidos = {"USD1/USDT", "RLUSD/USDT", "EUR/USDT", "XAUT/USDT", "PAXG/USDT"}
    assert not (excluidos & set(UNIVERSO_AMPLO))


# ==================================== spec 041 (dimensionamento por volatilidade)

def test_default_sem_dimensionamento_vol_ignora_atr_ratio():
    """usar_dimensionamento_vol=False (default) reproduz o mesmo resultado
    independente de atr_ratio estar presente -- regressao do caminho ja
    publicado (FR-004)."""
    idx = _idx(3)
    previsoes = {"A/USDT": pd.Series([1.0, 0.0, 0.0], index=idx)}
    preparados_sem = {"A/USDT": _prep(idx, close=[100.0, 101.0, 102.0])}
    preparados_com_coluna = {"A/USDT": _prep(idx, close=[100.0, 101.0, 102.0], atr_ratio=0.10)}

    r_sem = _simular_carteira_core(previsoes, preparados_sem, LIMIAR, capital_inicial=1000.0)
    r_com_coluna = _simular_carteira_core(previsoes, preparados_com_coluna, LIMIAR, capital_inicial=1000.0)

    assert r_sem.trades[0].quantity == pytest.approx(r_com_coluna.trades[0].quantity)
    assert r_sem.final_capital == pytest.approx(r_com_coluna.final_capital)


def test_atr_ratio_alto_reduz_o_tamanho_da_entrada():
    idx = _idx(3)
    previsoes = {"A/USDT": pd.Series([1.0, 0.0, 0.0], index=idx)}
    preparados_baixo = {"A/USDT": _prep(idx, close=[100.0, 101.0, 102.0], atr_ratio=0.02)}  # = alvo
    preparados_alto = {"A/USDT": _prep(idx, close=[100.0, 101.0, 102.0], atr_ratio=0.10)}  # 5x o alvo

    r_baixo = _simular_carteira_core(
        previsoes, preparados_baixo, LIMIAR, capital_inicial=1000.0, usar_dimensionamento_vol=True,
    )
    r_alto = _simular_carteira_core(
        previsoes, preparados_alto, LIMIAR, capital_inicial=1000.0, usar_dimensionamento_vol=True,
    )

    assert r_alto.trades[0].quantity < r_baixo.trades[0].quantity


def test_atr_ratio_ausente_nao_muda_o_tamanho():
    idx = _idx(3)
    previsoes = {"A/USDT": pd.Series([1.0, 0.0, 0.0], index=idx)}
    preparados = {"A/USDT": _prep(idx, close=[100.0, 101.0, 102.0])}  # sem coluna atr_ratio

    r_sem_flag = _simular_carteira_core(previsoes, preparados, LIMIAR, capital_inicial=1000.0)
    r_com_flag = _simular_carteira_core(
        previsoes, preparados, LIMIAR, capital_inicial=1000.0, usar_dimensionamento_vol=True,
    )

    assert r_sem_flag.trades[0].quantity == pytest.approx(r_com_flag.trades[0].quantity)


# ==================================================== spec 042 (gate de correlacao)

def test_bloqueia_candidato_correlacionado_com_posicao_aberta():
    idx = _idx(30)
    base = _serie(30, semente=1)
    quase_igual = [c * 1.001 for c in base]  # retornos praticamente identicos -> corr ~1.0
    preparados = {
        "A/USDT": _prep(idx, close=base),
        "B/USDT": _prep(idx, close=quase_igual),
    }

    bloqueado_por = _correlacionado_com_posicao_aberta(
        "B/USDT", preparados, ["A/USDT"], idx[-1], lookback=10,
    )

    assert bloqueado_por == "A/USDT"


def test_nao_bloqueia_candidato_descorrelacionado():
    idx = _idx(30)
    preparados = {
        "A/USDT": _prep(idx, close=_serie(30, semente=1)),
        "C/USDT": _prep(idx, close=_serie(30, semente=99)),
    }

    bloqueado_por = _correlacionado_com_posicao_aberta(
        "C/USDT", preparados, ["A/USDT"], idx[-1], lookback=10,
    )

    assert bloqueado_por is None


def test_sem_posicoes_abertas_nunca_bloqueia():
    idx = _idx(10)
    preparados = {"A/USDT": _prep(idx, close=_serie(10))}

    assert _correlacionado_com_posicao_aberta("A/USDT", preparados, [], idx[-1]) is None


def test_amostra_insuficiente_falha_aberta():
    idx = _idx(3)  # bem menor que lookback padrao (50) // 2
    preparados = {
        "A/USDT": _prep(idx, close=[100.0, 101.0, 102.0]),
        "B/USDT": _prep(idx, close=[100.0, 101.0, 102.0]),
    }

    assert _correlacionado_com_posicao_aberta("B/USDT", preparados, ["A/USDT"], idx[-1]) is None


def test_gate_correlacao_desligado_por_padrao_reproduz_resultado_ja_publicado():
    idx = _idx(3)
    previsoes = {"A/USDT": pd.Series([1.0, 0.0, 0.0], index=idx)}
    preparados = {"A/USDT": _prep(idx, close=[100.0, 101.0, 102.0])}

    r_sem_flag = _simular_carteira_core(previsoes, preparados, LIMIAR, capital_inicial=1000.0)
    r_com_flag_false = _simular_carteira_core(
        previsoes, preparados, LIMIAR, capital_inicial=1000.0, usar_gate_correlacao=False,
    )

    assert r_sem_flag.total_return_pct == pytest.approx(r_com_flag_false.total_return_pct)
    assert r_sem_flag.max_drawdown_pct == pytest.approx(r_com_flag_false.max_drawdown_pct)


def test_candidato_bloqueado_nao_impede_o_proximo_candidato_de_abrir():
    """A abre no candle t1. No candle seguinte t2, B (correlacionado com
    A) e C (descorrelacionado) sinalizam -- com o gate ligado, B fica de
    fora e so A e C terminam como trades (2, nunca 3); sem o gate, os
    tres abrem (3)."""
    idx = _idx(30)
    base_a = _serie(30, semente=1)
    base_a[-2:] = [base_a[-3], base_a[-3]]  # preco estavel no fim: A nao bate stop/TP entre t1 e t2
    preparados = {
        "A/USDT": _prep(idx, close=base_a),
        "B/USDT": _prep(idx, close=[c * 1.001 for c in base_a]),  # quase identico a A -> corr ~1.0
        "C/USDT": _prep(idx, close=_serie(30, semente=99)),  # descorrelacionado
    }
    t1, t2 = idx[-2], idx[-1]
    previsoes = {
        "A/USDT": pd.Series([1.0, 0.0], index=[t1, t2]),
        "B/USDT": pd.Series([0.0, 1.0], index=[t1, t2]),
        "C/USDT": pd.Series([0.0, 1.0], index=[t1, t2]),
    }

    r_com_gate = _simular_carteira_core(
        previsoes, preparados, LIMIAR, capital_inicial=1000.0, usar_gate_correlacao=True,
    )
    r_sem_gate = _simular_carteira_core(
        previsoes, preparados, LIMIAR, capital_inicial=1000.0, usar_gate_correlacao=False,
    )

    assert r_com_gate.total_trades == 2  # A e C -- B bloqueado por correlacao
    assert r_sem_gate.total_trades == 3  # A, B e C -- sem o gate, todos abrem


# ============================================== spec 043 (combinacao vol+correlacao)

def test_dimensionamento_vol_e_gate_correlacao_juntos_nao_quebram():
    """As duas flags ligadas ao mesmo tempo produzem um BacktestResult
    valido, sem excecao -- cenario com posicao correlacionada (bloqueada
    pelo gate) e atr_ratio alto (reduzido pelo dimensionamento) na mesma
    simulacao."""
    idx = _idx(30)
    base_a = _serie(30, semente=1)
    base_a[-2:] = [base_a[-3], base_a[-3]]
    preparados = {
        "A/USDT": _prep(idx, close=base_a, atr_ratio=0.10),
        "B/USDT": _prep(idx, close=[c * 1.001 for c in base_a], atr_ratio=0.10),
        "C/USDT": _prep(idx, close=_serie(30, semente=99), atr_ratio=0.10),
    }
    t1, t2 = idx[-2], idx[-1]
    previsoes = {
        "A/USDT": pd.Series([1.0, 0.0], index=[t1, t2]),
        "B/USDT": pd.Series([0.0, 1.0], index=[t1, t2]),
        "C/USDT": pd.Series([0.0, 1.0], index=[t1, t2]),
    }

    r = _simular_carteira_core(
        previsoes, preparados, LIMIAR, capital_inicial=1000.0,
        usar_dimensionamento_vol=True, usar_gate_correlacao=True,
    )

    assert r is not None
    assert r.total_trades == 2  # A e C -- B ainda bloqueado por correlacao com os dois ligados


def test_fator_nunca_amplia_alem_do_teto_ja_existente():
    """atr_ratio muito baixo (bem abaixo do alvo) nao pode fazer a posicao
    ficar MAIOR que sem dimensionamento -- fator_volatilidade ja tem teto
    de 1,0 embutido (D1/FR-003)."""
    idx = _idx(3)
    previsoes = {"A/USDT": pd.Series([1.0, 0.0, 0.0], index=idx)}
    preparados_sem = {"A/USDT": _prep(idx, close=[100.0, 101.0, 102.0])}
    preparados_vol_baixa = {"A/USDT": _prep(idx, close=[100.0, 101.0, 102.0], atr_ratio=0.0001)}

    r_sem = _simular_carteira_core(previsoes, preparados_sem, LIMIAR, capital_inicial=1000.0)
    r_vol_baixa = _simular_carteira_core(
        previsoes, preparados_vol_baixa, LIMIAR, capital_inicial=1000.0, usar_dimensionamento_vol=True,
    )

    assert r_vol_baixa.trades[0].quantity <= r_sem.trades[0].quantity * 1.0001


# ==================================== spec 044 (circuit breaker de perdas consecutivas)

def _cenario_circuit_breaker(com_reset: bool):
    """A abre e bate stop 3x seguidas (perdas_consecutivas -> 3, o
    default de MAX_CONSECUTIVE_LOSSES). C tenta abrir logo depois -- so
    consegue se algo resetar o contador antes. Se `com_reset=True`, B
    abre junto com a 3a entrada de A e bate take-profit depois do
    breaker disparar, resetando o contador antes da tentativa de C."""
    assert MAX_CONSECUTIVE_LOSSES == 3, "cenario assume o default -- ajustar se MAX_CONSECUTIVE_LOSSES mudar"
    idx = _idx(12)
    n = len(idx)

    sinal_a = [0.0] * n
    close_a = [100.0] * n
    high_a = [100.0] * n
    low_a = [99.9] * n
    for entrada in (0, 2, 4):
        sinal_a[entrada] = 1.0
    for saida_stop in (1, 3, 5):
        low_a[saida_stop] = 96.0  # stop = 100 - 1.5*2 = 97 -> dispara

    sinal_c = [0.0] * n
    close_c = [100.0] * n
    high_c = [100.0] * n
    low_c = [99.9] * n
    for t in range(6, n):
        sinal_c[t] = 1.0  # tenta abrir em todo candle a partir do gatilho do breaker

    previsoes = {
        "A/USDT": pd.Series(sinal_a, index=idx),
        "C/USDT": pd.Series(sinal_c, index=idx),
    }
    preparados = {
        "A/USDT": _prep(idx, close=close_a, high=high_a, low=low_a),
        "C/USDT": _prep(idx, close=close_c, high=high_c, low=low_c),
    }

    if com_reset:
        sinal_b = [0.0] * n
        sinal_b[4] = 1.0  # abre junto com a 3a entrada de A (perdas ainda = 2, nao bloqueia)
        close_b = [100.0] * n
        high_b = [100.0] * n
        high_b[7] = 107.0  # alvo = 100 + 3.0*2 = 106 -> take profit em t7, reseta o contador
        low_b = [99.9] * n
        previsoes["B/USDT"] = pd.Series(sinal_b, index=idx)
        preparados["B/USDT"] = _prep(idx, close=close_b, high=high_b, low=low_b)

    return previsoes, preparados


def test_circuit_breaker_bloqueia_apos_perdas_consecutivas_no_limite():
    previsoes, preparados = _cenario_circuit_breaker(com_reset=False)

    r = _simular_carteira_core(
        previsoes, preparados, LIMIAR, capital_inicial=1000.0, usar_circuit_breaker=True,
    )

    assert r.total_trades == 3  # so as 3 perdas de A -- C nunca chega a abrir, nada reseta o contador
    assert all(t.exit_reason == "Stop Loss" for t in r.trades)


def test_circuit_breaker_reseta_no_primeiro_trade_lucrativo():
    previsoes, preparados = _cenario_circuit_breaker(com_reset=True)

    r = _simular_carteira_core(
        previsoes, preparados, LIMIAR, capital_inicial=1000.0, usar_circuit_breaker=True,
    )

    # 3 perdas de A + o lucro de B (que reseta o contador) + C, agora liberado
    assert r.total_trades == 5
    assert sum(1 for t in r.trades if t.exit_reason == "Take Profit") == 1


def test_circuit_breaker_desligado_por_padrao_reproduz_resultado_ja_publicado():
    previsoes, preparados = _cenario_circuit_breaker(com_reset=False)

    r_sem_flag = _simular_carteira_core(previsoes, preparados, LIMIAR, capital_inicial=1000.0)
    r_com_flag_false = _simular_carteira_core(
        previsoes, preparados, LIMIAR, capital_inicial=1000.0, usar_circuit_breaker=False,
    )

    assert r_sem_flag.total_trades == r_com_flag_false.total_trades == 4  # C abre normalmente, sem bloqueio


# ============================== spec 045 (limite de drawdown diario)

CAPITAL_LIMITE_DIARIO = MAX_POSITIONS * 50.0  # $50/slot em media -- bem abaixo do teto
                                               # MAX_ORDER_SIZE_USDT=100, garante que o cap
                                               # nao domina e quase todo o capital e deployado


def _cenario_limite_diario(dias: int):
    """`MAX_POSITIONS` pares (todos os slots) abrem juntos no candle 0 e
    batem stop no candle 1 -- ATR alto o suficiente para o teto
    MAX_STOP_LOSS_PCT (8%) dominar o calculo do stop
    (`backtesting/engine.py::_stop_price`). Perda agregada (~8% de quase
    todo `CAPITAL_LIMITE_DIARIO` deployado) supera 5%
    (`DAILY_DRAWDOWN_LIMIT`) -- dispara o limite ainda dentro do dia 1.
    F (par candidato, fora dos slots ocupados) tenta abrir a partir do
    candle 2 -- so consegue no primeiro candle do dia 2 (candle 6),
    quando o saldo de referencia reseta, MESMO sem nenhum trade
    lucrativo ter fechado."""
    idx = _idx(dias * 6, freq="4h")  # 6 candles de 4h = 1 dia de calendario
    n = len(idx)
    atr_alto = 20.0  # stop nao-capado seria 100-1.5*20=70; MAX_STOP_LOSS_PCT (8%) domina

    sinal_perdedor = [0.0] * n
    sinal_perdedor[0] = 1.0
    close = [100.0] * n
    high = [100.0] * n
    low = [99.9] * n
    low[1] = 65.0  # dispara o stop (capado a 8%) de todos os pares perdedores no candle 1

    sinal_f = [0.0] * n
    for t in range(2, n):
        sinal_f[t] = 1.0

    pares_perdedores = [f"L{i}/USDT" for i in range(MAX_POSITIONS)]
    previsoes = {par: pd.Series(sinal_perdedor, index=idx) for par in pares_perdedores}
    preparados = {
        par: _prep(idx, close=close, high=high, low=low, atr=atr_alto) for par in pares_perdedores
    }
    previsoes["F/USDT"] = pd.Series(sinal_f, index=idx)
    preparados["F/USDT"] = _prep(idx, close=[100.0] * n, high=[100.0] * n, low=[99.9] * n)
    return previsoes, preparados


def test_limite_drawdown_diario_bloqueia_pelo_resto_do_dia():
    previsoes, preparados = _cenario_limite_diario(dias=1)

    r = _simular_carteira_core(
        previsoes, preparados, LIMIAR, capital_inicial=CAPITAL_LIMITE_DIARIO,
        usar_limite_drawdown_diario=True,
    )

    assert r.total_trades == MAX_POSITIONS  # so os perdedores -- F nunca abre dentro do dia 1


def test_limite_drawdown_diario_reseta_no_novo_dia_mesmo_sem_trade_lucrativo():
    previsoes, preparados = _cenario_limite_diario(dias=2)

    r = _simular_carteira_core(
        previsoes, preparados, LIMIAR, capital_inicial=CAPITAL_LIMITE_DIARIO,
        usar_limite_drawdown_diario=True,
    )

    # os perdedores (dia 1) + F, destravado no dia 2 sem nenhum trade lucrativo ter
    # fechado -- distingue do circuit breaker (spec 044), que ficaria preso para sempre aqui.
    assert r.total_trades == MAX_POSITIONS + 1


def test_limite_drawdown_diario_desligado_por_padrao_reproduz_resultado_ja_publicado():
    previsoes, preparados = _cenario_limite_diario(dias=1)

    r_sem_flag = _simular_carteira_core(
        previsoes, preparados, LIMIAR, capital_inicial=CAPITAL_LIMITE_DIARIO,
    )
    r_com_flag_false = _simular_carteira_core(
        previsoes, preparados, LIMIAR, capital_inicial=CAPITAL_LIMITE_DIARIO,
        usar_limite_drawdown_diario=False,
    )

    assert r_sem_flag.total_trades == r_com_flag_false.total_trades == MAX_POSITIONS + 1  # F abre, sem bloqueio
    assert r_sem_flag.total_return_pct == pytest.approx(r_com_flag_false.total_return_pct)


# ============================== spec 046 (combinacao correlacao + limite diario)

def test_gate_correlacao_e_limite_drawdown_diario_juntos_nao_quebram():
    """As duas flags ligadas ao mesmo tempo produzem um BacktestResult
    valido, sem excecao -- cenario com posicao correlacionada (bloqueada
    pelo gate) na mesma simulacao onde o limite diario tambem esta ativo
    (mas nao dispara, janela curta demais para perda > 5%)."""
    idx = _idx(30)
    base_a = _serie(30, semente=1)
    base_a[-2:] = [base_a[-3], base_a[-3]]
    preparados = {
        "A/USDT": _prep(idx, close=base_a),
        "B/USDT": _prep(idx, close=[c * 1.001 for c in base_a]),  # quase identico a A -> corr ~1.0
        "C/USDT": _prep(idx, close=_serie(30, semente=99)),
    }
    t1, t2 = idx[-2], idx[-1]
    previsoes = {
        "A/USDT": pd.Series([1.0, 0.0], index=[t1, t2]),
        "B/USDT": pd.Series([0.0, 1.0], index=[t1, t2]),
        "C/USDT": pd.Series([0.0, 1.0], index=[t1, t2]),
    }

    r = _simular_carteira_core(
        previsoes, preparados, LIMIAR, capital_inicial=1000.0,
        usar_gate_correlacao=True, usar_limite_drawdown_diario=True,
    )

    assert r is not None
    assert r.total_trades == 2  # A e C -- B bloqueado por correlacao


# ============================== spec 047 (combinacao total / teto)

def test_tres_mecanismos_juntos_nao_quebram():
    """Dimensionamento + gate de correlacao + limite de drawdown diario,
    os tres ligados ao mesmo tempo, produzem um BacktestResult valido,
    sem excecao."""
    idx = _idx(30)
    base_a = _serie(30, semente=1)
    base_a[-2:] = [base_a[-3], base_a[-3]]
    preparados = {
        "A/USDT": _prep(idx, close=base_a, atr_ratio=0.10),
        "B/USDT": _prep(idx, close=[c * 1.001 for c in base_a], atr_ratio=0.10),
        "C/USDT": _prep(idx, close=_serie(30, semente=99), atr_ratio=0.10),
    }
    t1, t2 = idx[-2], idx[-1]
    previsoes = {
        "A/USDT": pd.Series([1.0, 0.0], index=[t1, t2]),
        "B/USDT": pd.Series([0.0, 1.0], index=[t1, t2]),
        "C/USDT": pd.Series([0.0, 1.0], index=[t1, t2]),
    }

    r = _simular_carteira_core(
        previsoes, preparados, LIMIAR, capital_inicial=1000.0,
        usar_dimensionamento_vol=True, usar_gate_correlacao=True, usar_limite_drawdown_diario=True,
    )

    assert r is not None
    assert r.total_trades == 2  # A e C -- B bloqueado por correlacao com os tres ligados
