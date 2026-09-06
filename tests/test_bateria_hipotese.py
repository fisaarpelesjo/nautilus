import pandas as pd

from backtesting.bateria_hipotese import rodar_bateria, walk_forward_generico
from backtesting.engine import BacktestResult


def _resultado(trades=20, pf=2.0, ret=10.0, buy_hold=1.0, dd=2.0, exposure=10.0):
    """BacktestResult minimo com os campos que evaluate_approval()/exposicao_de_capital() consultam."""
    return BacktestResult(
        trades=[], initial_capital=1000.0, final_capital=1000.0 * (1 + ret / 100),
        total_return_pct=ret, win_rate=50.0, total_trades=trades, max_drawdown_pct=dd,
        profit_factor=pf, expectancy=1.0, average_win=1.0, average_loss=-1.0,
        largest_win=1.0, largest_loss=-1.0, max_losing_streak=1, exposure_pct=exposure,
        sharpe=1.0, expectancy_pct=1.0, payoff_ratio=1.0, buy_hold_return_pct=buy_hold,
        edge_return_pct=ret - buy_hold, edge_score=10.0, sortino=1.0, calmar=1.0,
        annualized_return_pct=ret, return_per_exposure_pct=1.0,
    )


def _candles(n=1000):
    return pd.DataFrame({"close": range(n)})


def test_e1_sanidade_falha_interrompe_a_bateria_sem_rodar_o_resto():
    chamadas = []

    def gerar(df, custo_zero):
        chamadas.append((len(df), custo_zero))
        return _resultado()

    relatorio = rodar_bateria(_candles(), gerar, teste_sanidade=lambda: False)

    assert relatorio.e1_sanidade_ok is False
    assert relatorio.e2_janela_unica is None
    assert chamadas == []


def test_sem_teste_de_sanidade_roda_a_bateria_inteira():
    relatorio = rodar_bateria(_candles(), lambda df, custo_zero: _resultado(pf=2.0))

    assert relatorio.e1_sanidade_ok is None
    assert relatorio.e2_janela_unica is not None
    assert relatorio.e6_sem_custo is not None


def test_e2_janela_unica_usa_evaluate_approval_sobre_o_dataframe_completo():
    vistos = []

    def gerar(df, custo_zero):
        vistos.append(len(df))
        return _resultado(pf=2.0)

    relatorio = rodar_bateria(_candles(1000), gerar, teste_sanidade=lambda: True)

    assert relatorio.e2_janela_unica.status == "aprovado"
    assert vistos[0] == 1000  # primeira chamada e sobre o dataframe inteiro (E2)


def test_e3_confirmado_quando_aprova_nas_duas_janelas():
    relatorio = rodar_bateria(_candles(1000), lambda df, custo_zero: _resultado(pf=2.0))

    assert relatorio.e3_status == "confirmado"
    assert relatorio.e3_busca.status == "aprovado"
    assert relatorio.e3_confirmacao.status == "aprovado"


def test_e3_inconclusivo_quando_historico_curto_demais_para_dividir():
    # Menos que 2x MIN_WINDOW_CANDLES (150): split_train_validation devolve
    # confirmacao=None -- mesma regra de "nunca aprovado por omissao de dado".
    chamadas = []

    def gerar(df, custo_zero):
        chamadas.append(custo_zero)
        return _resultado(pf=2.0)

    relatorio = rodar_bateria(_candles(100), gerar)

    assert relatorio.e3_status == "inconclusivo"
    assert relatorio.e3_confirmacao is None
    assert chamadas == [False, True]  # so E2 (janela unica) e E6 (sem custo) -- E3 reusou o resultado de E2 em vez de recalcular, E4 nao rodou (janela < MIN_WINDOW_CANDLES)


def test_e4_produz_o_numero_de_janelas_pedido():
    relatorio = rodar_bateria(
        _candles(1000), lambda df, custo_zero: _resultado(pf=2.0), n_janelas_walk_forward=5,
    )

    assert len(relatorio.e4_folds) == 5
    assert relatorio.e4_resumo["janelas"] == 5


def test_walk_forward_generico_chama_gerar_resultado_por_fatia_nao_sobreposta():
    fatias = []

    def gerar(df, custo_zero):
        fatias.append(list(df["close"]))
        return _resultado()

    walk_forward_generico(_candles(1500), gerar, n_janelas=5)

    assert len(fatias) == 5
    assert [f[0] for f in fatias] == [0, 300, 600, 900, 1200]
    assert [f[-1] for f in fatias] == [299, 599, 899, 1199, 1499]


def test_walk_forward_generico_bloqueia_janela_menor_que_min_window_candles():
    # Cada fatia precisa do warmup de indicadores (EMA50 etc, MIN_WINDOW_CANDLES=150)
    # -- sem essa guarda, um fold curto demais vira "resultado" degenerado lido
    # como veredito real em vez de defeito de motor (mesmo raciocinio do E1).
    chamadas = []

    def gerar(df, custo_zero):
        chamadas.append(len(df))
        return _resultado()

    folds = walk_forward_generico(_candles(500), gerar, n_janelas=5)  # tam=100 < 150

    assert folds == []
    assert chamadas == []


def test_e6_compara_com_e_sem_custo_via_flag_explicita():
    def gerar(df, custo_zero):
        return _resultado(pf=0.8 if not custo_zero else 2.0)

    relatorio = rodar_bateria(_candles(1000), gerar)

    assert relatorio.e6_com_custo.status == "reprovado"
    assert relatorio.e6_sem_custo.status == "aprovado"
    assert relatorio.e6_com_custo is relatorio.e2_janela_unica  # mesmo resultado, nao recalculado


def test_e5_ganho_de_timing_e_number_mesmo_sem_trades():
    relatorio = rodar_bateria(_candles(1000), lambda df, custo_zero: _resultado(pf=2.0))

    assert isinstance(relatorio.e5_ganho_de_timing_pp, float)
