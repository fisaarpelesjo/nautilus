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


# ================================================ T013 T015 T016 T029

def test_marcar_historico_curto_usa_a_mediana_nao_o_solicitado():
    """D3 — comparar com o solicitado marcava 12 de 12 pares em escala semanal.

    Numeros reais medidos em 1w (2026-09-01): mediana 414, BTC/ETH no teto com
    473, AVAX no piso com 311.
    """
    from backtesting.horizonte import marcar_historico_curto

    disp = [_disp(obtido=o, tf="1w", par=p) for p, o in
            [("BTC/USDT", 473), ("ETH/USDT", 473), ("LTC/USDT", 456),
             ("ADA/USDT", 438), ("XRP/USDT", 436), ("TRX/USDT", 430),
             ("LINK/USDT", 399), ("ATOM/USDT", 384), ("BCH/USDT", 354),
             ("SOL/USDT", 317), ("DOT/USDT", 316), ("AVAX/USDT", 311)]]

    marcados = {d.par for d in marcar_historico_curto(disp) if d.historico_curto}

    assert "AVAX/USDT" in marcados
    assert "BTC/USDT" not in marcados
    assert len(marcados) < len(disp), "marcar todos equivale a nao marcar nenhum"


def test_universo_homogeneo_nao_produz_marcacao():
    """A marca nao pode disparar por construcao."""
    from backtesting.horizonte import marcar_historico_curto

    disp = [_disp(obtido=400, tf="1w", par=f"P{i}/USDT") for i in range(6)]

    assert not any(d.historico_curto for d in marcar_historico_curto(disp))


def test_folds_vazios_sao_excluidos_das_agregacoes():
    """R3 / FR-006 — janela sem operacao dilui media se contada como neutra."""
    from backtesting.cross_sectional import WalkForwardFold
    from backtesting.horizonte import folds_nao_vazios

    folds = [
        WalkForwardFold(1, -20.0, -5.0, 50.0, 3.0, 0),   # vazio
        WalkForwardFold(2, -20.0, -5.0, 50.0, 3.0, 7),
        WalkForwardFold(3, 10.0, 4.0, 60.0, 2.0, 0),     # vazio
    ]

    assert [f.janela for f in folds_nao_vazios(folds)] == [2]


def test_relatorio_agrega_contagens_por_status():
    from backtesting.horizonte import CombinacaoAvaliada, RelatorioHorizonte

    def _c(status):
        return CombinacaoAvaliada(
            estrategia="X", horizonte="1d", par="BTC/USDT",
            disponibilidade=_disp(obtido=2000), status=status,
        )

    rel = RelatorioHorizonte(horizonte="1d", combinacoes=[
        _c("confirmado"), _c("so_na_busca"), _c("reprovado"),
        _c("inconclusivo"), _c("inconclusivo"), _c("erro"),
    ])

    assert rel.n_avaliadas == 6
    assert rel.n_confirmadas == 1
    assert rel.n_inconclusivas == 2
    assert rel.n_erros == 1
    assert [c.status for c in rel.ordenadas()][0] == "confirmado"


def test_combinacao_com_aquecimento_maior_que_historico_e_inconclusiva():
    """T030 / FR-010 — guard antes de simular."""
    from backtesting.horizonte import _avaliar_combinacao
    from strategy.ema_rsi import EmaRsiStrategy

    comb = _avaliar_combinacao(
        EmaRsiStrategy(), "EMA/RSI", "1w", "NOVO/USDT",
        _disp(obtido=30, aquecimento=50, tf="1w", par="NOVO/USDT"),
    )

    assert comb.status == "inconclusivo"
    assert "aquecimento" in comb.motivo.lower()


def test_combinacao_com_erro_de_dado_vira_status_erro():
    from backtesting.horizonte import _avaliar_combinacao
    from strategy.ema_rsi import EmaRsiStrategy

    comb = _avaliar_combinacao(
        EmaRsiStrategy(), "EMA/RSI", "1d", "QUEBRA/USDT",
        _disp(obtido=0, tf="1d", par="QUEBRA/USDT", erro="NetworkError"),
    )

    assert comb.status == "erro"


def test_run_horizonte_scan_varre_todas_as_combinacoes(monkeypatch):
    """Varredura completa sobre serie sintetica, sem tocar a rede.

    340 candles de proposito: cobre aquecimento (50) + split 70/30 + 2 janelas
    de walk-forward, que e o minimo para exercitar o caminho completo. Com 900
    o mesmo teste levava 150 s -- suite lenta e suite que ninguem roda.
    """
    import numpy as np
    from backtesting import horizonte as H
    from backtesting.horizonte import run_horizonte_scan
    from strategy.breakout import BreakoutStrategy
    from strategy.ema_rsi import EmaRsiStrategy

    def serie(n=340, semente=0):
        rng = np.random.default_rng(semente)
        preco = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.02, n)))
        idx = pd.date_range("2024-01-01", periods=n, freq="1D")
        return pd.DataFrame({
            "open": preco, "close": preco,
            "high": preco * 1.02, "low": preco * 0.98,
            "volume": np.abs(rng.normal(1000, 200, n)),
        }, index=idx)

    monkeypatch.setattr(H, "fetch_ohlcv",
                        lambda par, tf, lim: serie(semente=hash(par) % 100),
                        raising=False)

    rels = run_horizonte_scan(
        {"EMA/RSI": EmaRsiStrategy(), "Breakout": BreakoutStrategy(window=50)},
        ["BTC/USDT", "ETH/USDT"], ["1d"],
    )

    assert len(rels) == 1
    assert rels[0].n_avaliadas == 4          # 2 estrategias x 2 pares
    assert rels[0].n_erros == 0
    assert all(c.status in {"confirmado", "so_na_busca", "reprovado",
                            "inconclusivo", "erro"}
               for c in rels[0].combinacoes)


def test_run_horizonte_scan_nao_aborta_com_par_quebrado(monkeypatch):
    """R7 — varredura de 144 combinacoes que morre na terceira e inutil."""
    import numpy as np
    from backtesting import horizonte as H
    from backtesting.horizonte import run_horizonte_scan
    from strategy.ema_rsi import EmaRsiStrategy

    def fetch(par, tf, lim):
        if par == "QUEBRA/USDT":
            raise RuntimeError("simbolo inexistente")
        rng = np.random.default_rng(1)
        preco = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, 340)))
        idx = pd.date_range("2024-01-01", periods=340, freq="1D")
        return pd.DataFrame({"open": preco, "close": preco,
                             "high": preco * 1.02, "low": preco * 0.98,
                             "volume": np.full(340, 1000.0)}, index=idx)

    monkeypatch.setattr(H, "fetch_ohlcv", fetch, raising=False)

    rels = run_horizonte_scan(
        {"EMA/RSI": EmaRsiStrategy()},
        ["BTC/USDT", "QUEBRA/USDT", "ETH/USDT"], ["1d"],
    )

    assert rels[0].n_avaliadas == 3
    assert rels[0].n_erros == 1
    quebrado = next(c for c in rels[0].combinacoes if c.par == "QUEBRA/USDT")
    assert quebrado.status == "erro"
