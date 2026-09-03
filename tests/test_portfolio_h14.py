import pandas as pd
import pytest

from backtesting.portfolio_h14 import UNIVERSO_AMPLO, _simular_carteira_core, comparar_drawdown

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
