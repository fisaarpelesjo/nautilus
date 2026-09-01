import pandas as pd
import pytest

from backtesting import horizonte
from backtesting.horizonte import (
    DisponibilidadeHistorico,
    aquecimento_candles,
    aquecimento_dias,
    medir_disponibilidade,
)


def _disp(obtido, aquecimento=50, par="BTC/USDT", tf="1d", solicitado=2000, erro=None):
    return DisponibilidadeHistorico(
        par=par, horizonte=tf, solicitado=solicitado, obtido=obtido,
        aquecimento=aquecimento, erro=erro,
    )


# --------------------------------------------------------------- T002 fumaca

def test_modulo_importa_e_expoe_a_api_publica():
    for nome in ("DisponibilidadeHistorico", "medir_disponibilidade",
                 "aquecimento_candles", "aquecimento_dias", "marcar_historico_curto"):
        assert hasattr(horizonte, nome), f"{nome} ausente"


# ------------------------------------------------- T003 utilizaveis e lacuna

def test_utilizaveis_desconta_o_aquecimento():
    assert _disp(obtido=2000, aquecimento=50).utilizaveis == 1950


def test_utilizaveis_nunca_fica_negativo():
    # Par de listagem recente em escala semanal: o aquecimento pode exceder todo
    # o historico. O campo tem de saturar em zero, nao devolver negativo, porque
    # o consumidor usa este numero para dimensionar janelas.
    assert _disp(obtido=30, aquecimento=50).utilizaveis == 0


def test_lacuna_e_a_diferenca_entre_pedido_e_recebido():
    # FR-009: pedir 2000 e receber 400 e normal em escala semanal, mas passar
    # silencioso desbalancearia qualquer comparacao entre horizontes.
    assert _disp(obtido=400, solicitado=2000).lacuna == 1600


# ------------------------------------------------------------ T004 erro

def test_combinacao_com_erro_nao_conta_como_avaliada_com_zero():
    # Falha de busca tem de ser distinguivel de "avaliado e nao operou".
    # Confundir os dois faz um par inacessivel parecer uma estrategia inerte.
    d = _disp(obtido=0, erro="NetworkError: timeout")

    assert d.erro is not None
    assert d.obtido == 0
    assert d.utilizaveis == 0


def test_erro_ausente_em_medicao_bem_sucedida():
    assert _disp(obtido=2000).erro is None


# ------------------------------------------------------------ T007 aquecimento

def test_aquecimento_em_candles_deriva_da_ema_de_tendencia():
    from config.settings import EMA_TREND

    assert aquecimento_candles() >= EMA_TREND


@pytest.mark.parametrize("horizonte_tf,dias_esperados", [
    ("4h", 50 * 4 / 24),
    ("1d", 50.0),
    ("1w", 350.0),
])
def test_aquecimento_em_dias_converte_por_horizonte(horizonte_tf, dias_esperados):
    # FR-010 exige as duas unidades: 50 candles em escala semanal sao quase um
    # ano, fato invisivel se declarado apenas em candles.
    assert aquecimento_dias(horizonte_tf) == pytest.approx(dias_esperados, rel=0.01)


def test_aquecimento_semanal_consome_quase_um_ano():
    assert aquecimento_dias("1w") / 365 > 0.9


# ------------------------------------------------------- T006 medicao

def test_medir_disponibilidade_devolve_um_registro_por_par(monkeypatch):
    def falso_fetch(par, tf, limite):
        return pd.DataFrame({"close": range(1200)})

    monkeypatch.setattr(horizonte, "fetch_ohlcv", falso_fetch, raising=False)
    resultado = medir_disponibilidade(["BTC/USDT", "ETH/USDT"], "1d", solicitado=2000)

    assert len(resultado) == 2
    assert {d.par for d in resultado} == {"BTC/USDT", "ETH/USDT"}
    assert all(d.obtido == 1200 for d in resultado)
    assert all(d.lacuna == 800 for d in resultado)


def test_medir_disponibilidade_nao_aborta_quando_um_par_falha(monkeypatch):
    # R7: uma varredura de 144 combinacoes que morre na terceira e inutil.
    def falso_fetch(par, tf, limite):
        if par == "QUEBRA/USDT":
            raise RuntimeError("simbolo inexistente")
        return pd.DataFrame({"close": range(500)})

    monkeypatch.setattr(horizonte, "fetch_ohlcv", falso_fetch, raising=False)
    resultado = medir_disponibilidade(
        ["BTC/USDT", "QUEBRA/USDT", "ETH/USDT"], "1d", solicitado=2000,
    )

    assert len(resultado) == 3
    quebrado = next(d for d in resultado if d.par == "QUEBRA/USDT")
    assert quebrado.erro is not None
    assert quebrado.obtido == 0
    assert all(d.erro is None for d in resultado if d.par != "QUEBRA/USDT")


def test_medir_disponibilidade_trata_dataframe_vazio_como_zero(monkeypatch):
    monkeypatch.setattr(horizonte, "fetch_ohlcv",
                        lambda p, t, limite: pd.DataFrame(), raising=False)
    resultado = medir_disponibilidade(["BTC/USDT"], "1w", solicitado=2000)

    assert resultado[0].obtido == 0
    assert resultado[0].utilizaveis == 0


def test_medir_disponibilidade_calcula_cobertura_em_dias(monkeypatch):
    monkeypatch.setattr(horizonte, "fetch_ohlcv",
                        lambda p, t, limite: pd.DataFrame({"close": range(400)}),
                        raising=False)
    resultado = medir_disponibilidade(["BTC/USDT"], "1w", solicitado=2000)

    assert resultado[0].dias_cobertos == pytest.approx(2800.0)


# =========================================================== F3 / US1

def _fake_result(trades=20, pf=1.5, dd=5.0, ret=10.0, bh=0.0):
    """BacktestResult minimo, so com os campos que o veredito consulta."""
    from backtesting.engine import BacktestResult, _calculate_advanced_metrics

    metrics = _calculate_advanced_metrics([])
    metrics.update(profit_factor=pf, exposure_pct=50.0)
    return BacktestResult(
        trades=[], initial_capital=1000.0, final_capital=1000.0 + ret * 10,
        total_return_pct=ret, win_rate=50.0, total_trades=trades,
        max_drawdown_pct=dd, buy_hold_return_pct=bh, edge_return_pct=ret - bh,
        **metrics,
    )


# --------------------------------------------------- T008 precedencia FR-003

def test_amostra_abaixo_do_minimo_e_inconclusiva_nunca_reprovada():
    """FR-003 / R1 — a regra que separou H10 de uma reprovacao indevida.

    Metricas ruins com amostra insuficiente NAO sao evidencia de ausencia de
    vantagem. O status tem de ser decidido pela amostra antes de qualquer
    avaliacao de metrica.
    """
    from backtesting.horizonte import classificar_status
    from config.settings import EDGE_MIN_TRADES

    ruim = _fake_result(trades=EDGE_MIN_TRADES - 1, pf=0.2, dd=40.0, ret=-30.0)
    status, motivo = classificar_status(
        resultado=ruim, confirmacao=None, n_janelas=5, utilizaveis=2000,
    )

    assert status == "inconclusivo"
    assert "operac" in motivo.lower()


def test_amostra_suficiente_com_metrica_ruim_e_reprovada():
    from backtesting.horizonte import classificar_status

    ruim = _fake_result(trades=50, pf=0.3, dd=40.0, ret=-30.0)
    status, _ = classificar_status(
        resultado=ruim, confirmacao=None, n_janelas=5, utilizaveis=2000,
    )

    assert status == "reprovado"


# ----------------------------------------------- T009 janela de confirmacao

def test_sem_janela_de_validacao_valida_o_status_e_inconclusivo():
    from backtesting.horizonte import classificar_status
    from backtesting.validation import MIN_WINDOW_CANDLES

    bom = _fake_result(trades=30, pf=1.8, dd=5.0, ret=20.0)
    status, motivo = classificar_status(
        resultado=bom, confirmacao=None, n_janelas=5,
        utilizaveis=MIN_WINDOW_CANDLES,  # cabe a busca, nao a confirmacao
    )

    assert status == "inconclusivo"
    assert "amostra" in motivo.lower() or "janela" in motivo.lower()


# ------------------------------------------------------ T010 n_janelas D2

def test_n_janelas_derivado_do_historico_utilizavel():
    from backtesting.horizonte import derivar_n_janelas
    from backtesting.validation import MIN_WINDOW_CANDLES

    assert derivar_n_janelas(1950) == 5                      # 4h e 1d
    assert derivar_n_janelas(MIN_WINDOW_CANDLES * 3) == 3
    assert derivar_n_janelas(MIN_WINDOW_CANDLES * 2) == 2    # 1w: abaixo do minimo
    assert derivar_n_janelas(100) == 0


def test_menos_de_tres_janelas_torna_o_resultado_inconclusivo():
    """D2 — em escala semanal sobram 1 ou 2 janelas, insuficiente para E4."""
    from backtesting.horizonte import classificar_status

    bom = _fake_result(trades=30, pf=1.8, dd=5.0, ret=20.0)
    status, motivo = classificar_status(
        resultado=bom, confirmacao=_fake_result(trades=15, pf=1.5),
        n_janelas=2, utilizaveis=400,
    )

    assert status == "inconclusivo"
    assert "janela" in motivo.lower()


# --------------------------------------------------------- T011 so_na_busca

def test_aprovado_na_busca_e_reprovado_na_confirmacao_vira_so_na_busca():
    from backtesting.horizonte import classificar_status

    status, _ = classificar_status(
        resultado=_fake_result(trades=30, pf=1.8, dd=5.0, ret=20.0),
        confirmacao=_fake_result(trades=20, pf=0.4, dd=5.0, ret=-8.0),
        n_janelas=5, utilizaveis=2000,
    )

    assert status == "so_na_busca"


def test_aprovado_nas_duas_janelas_vira_confirmado():
    from backtesting.horizonte import classificar_status

    status, _ = classificar_status(
        resultado=_fake_result(trades=30, pf=1.8, dd=5.0, ret=20.0),
        confirmacao=_fake_result(trades=20, pf=1.6, dd=6.0, ret=15.0),
        n_janelas=5, utilizaveis=2000,
    )

    assert status == "confirmado"
