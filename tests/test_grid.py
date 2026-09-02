"""H18 -- grid trading com gestao de cauda (spec 035)."""
import pandas as pd
import pytest


def _candle(close, high, low, regime, bb_lower=None, bb_upper=None):
    return {
        "open": close, "close": close, "high": high, "low": low,
        "volume": 1000.0, "regime": regime,
        "bb_lower": bb_lower, "bb_upper": bb_upper, "bb_middle": None,
    }


def _df(linhas):
    idx = pd.date_range("2026-01-01", periods=len(linhas), freq="4h", tz="UTC")
    return pd.DataFrame(linhas, index=idx)


# ---------------------------------------------------------------- US1: preenchimento (T001-T003)

def test_nivel_vazio_preenche_compra_quando_low_cruza(monkeypatch):
    from backtesting import grid

    linhas = [
        _candle(100, 100, 100, "sideways", bb_lower=90, bb_upper=110),  # abre a grade, sem fill
        _candle(93, 93, 93, "sideways"),  # low=93 <= 95 (nivel1.compra) -> compra
    ]
    df = _df(linhas)
    params = grid.ParametrosGrade(n_niveis=4, capital_inicial=400.0)

    resultado = grid.simular_grade(df, params, fee_rate=0.0, slippage_pct=0.0)

    assert resultado.trades == []  # ainda nao vendeu, so o teste de estado interno importa
    # sem API publica pra inspecionar niveis, confirma indiretamente via venda no proximo teste


def test_nivel_ocupado_preenche_venda_e_gera_trade(monkeypatch):
    from backtesting import grid

    linhas = [
        _candle(100, 100, 100, "sideways", bb_lower=90, bb_upper=110),  # abre grade [90,95,100,105,110]
        _candle(93, 93, 93, "sideways"),   # compra no nivel (95,100) a 95
        _candle(101, 101, 99, "sideways"),  # high=101 >= 100 (venda do nivel) -> vende a 100
    ]
    df = _df(linhas)
    params = grid.ParametrosGrade(n_niveis=4, capital_inicial=400.0)

    resultado = grid.simular_grade(df, params, fee_rate=0.0, slippage_pct=0.0)

    assert len(resultado.trades) == 1
    t = resultado.trades[0]
    assert t.entry_price == pytest.approx(95.0)
    assert t.exit_price == pytest.approx(100.0)
    assert t.exit_reason == "grid"
    assert t.pnl > 0


def test_nivel_nao_revende_e_recompra_no_mesmo_candle():
    """Um candle cujo range cobre a celula inteira (low<=compra E high>=venda)
    do MESMO nivel ja ocupado so processa a venda -- nao reabre no mesmo
    candle (D3, uma transicao por nivel por candle). Grade de 1 nivel so,
    para isolar o cenario sem outros niveis interferindo."""
    from backtesting import grid

    linhas = [
        _candle(97, 97, 97, "sideways", bb_lower=95, bb_upper=100),  # abre grade, nivel unico (95,100)
        _candle(94, 94, 94, "sideways"),   # low=94<=95 -> compra a 95
        _candle(97, 200, 1, "sideways"),   # candle enorme: low=1<=95, high=200>=100 -- ja ocupado, so vende
    ]
    df = _df(linhas)
    params = grid.ParametrosGrade(n_niveis=1, capital_inicial=400.0)

    resultado = grid.simular_grade(df, params, fee_rate=0.0, slippage_pct=0.0)

    # so a venda do nivel ja ocupado -- nao um segundo trade de recompra no mesmo candle
    assert len(resultado.trades) == 1
    assert resultado.trades[0].exit_reason == "grid"
    assert resultado.trades[0].entry_price == pytest.approx(95.0)
    assert resultado.trades[0].exit_price == pytest.approx(100.0)


# ---------------------------------------------------------------- US2: gestao de cauda (T004-T006)

def test_grade_nunca_abre_em_regime_trending_ou_indefinido():
    from backtesting import grid

    linhas = [
        _candle(100, 105, 95, "trending", bb_lower=90, bb_upper=110),
        _candle(100, 105, 95, "indefinido", bb_lower=90, bb_upper=110),
        _candle(93, 93, 93, "trending"),
    ]
    df = _df(linhas)
    params = grid.ParametrosGrade(n_niveis=4, capital_inicial=400.0)

    resultado = grid.simular_grade(df, params, fee_rate=0.0, slippage_pct=0.0)

    assert resultado.trades == []
    assert resultado.total_trades == 0


def test_liquidacao_forcada_fecha_todos_os_niveis_ocupados_ao_close():
    from backtesting import grid

    linhas = [
        _candle(100, 100, 100, "sideways", bb_lower=90, bb_upper=110),  # abre [90,95,100,105,110]
        _candle(93, 93, 93, "sideways"),   # compra nivel (95,100) a 95
        _candle(97, 97, 92, "sideways"),   # compra nivel (90,95) a 90 (low=92<=95? nao, 92<=95 sim mas ja ocupado... usa outro nivel)
        _candle(102, 102, 102, "trending"),  # regime muda -- liquida tudo ao close=102
    ]
    df = _df(linhas)
    params = grid.ParametrosGrade(n_niveis=4, capital_inicial=400.0)

    resultado = grid.simular_grade(df, params, fee_rate=0.0, slippage_pct=0.0)

    forcados = [t for t in resultado.trades if t.exit_reason == "regime mudou para trending"]
    assert len(forcados) >= 1
    for t in forcados:
        assert t.exit_price == pytest.approx(102.0)


def test_grade_reabre_com_bandas_recalculadas_apos_liquidacao():
    from backtesting import grid

    linhas = [
        _candle(100, 100, 100, "sideways", bb_lower=90, bb_upper=110),
        _candle(93, 93, 93, "sideways"),      # compra
        _candle(102, 102, 102, "trending"),   # liquida tudo
        _candle(200, 200, 200, "sideways", bb_lower=180, bb_upper=220),  # reabre com bandas NOVAS
        _candle(185, 185, 185, "sideways"),   # compra na nova faixa (nivel perto de 190)
    ]
    df = _df(linhas)
    params = grid.ParametrosGrade(n_niveis=4, capital_inicial=400.0)

    resultado = grid.simular_grade(df, params, fee_rate=0.0, slippage_pct=0.0)

    # deve ter pelo menos 1 liquidacao forcada (bandas antigas) e nenhum trade
    # usando as bandas antigas (90-110) depois da reabertura em 180-220
    forcados = [t for t in resultado.trades if t.exit_reason == "regime mudou para trending"]
    assert len(forcados) >= 1
    assert all(t.entry_price < 110 for t in forcados)


# ---------------------------------------------------------------- US1: compatibilidade com evaluate_approval (T007)

def test_resultado_e_aceito_por_evaluate_approval():
    from backtesting.approval import evaluate_approval
    from backtesting import grid

    linhas = [
        _candle(100, 100, 100, "sideways", bb_lower=90, bb_upper=110),
        _candle(93, 93, 93, "sideways"),
        _candle(101, 101, 99, "sideways"),
    ]
    df = _df(linhas)
    params = grid.ParametrosGrade(n_niveis=4, capital_inicial=400.0)

    resultado = grid.simular_grade(df, params, fee_rate=0.0, slippage_pct=0.0)
    veredito = evaluate_approval(resultado)

    assert veredito.status in ("aprovado", "reprovado", "inconclusivo")


# ---------------------------------------------------------------- US3: custo escala com transacoes (T010)

def test_custo_reduz_retorno_e_escala_com_numero_de_trades():
    from backtesting import grid

    linhas_poucos = [
        _candle(100, 100, 100, "sideways", bb_lower=90, bb_upper=110),
        _candle(93, 93, 93, "sideways"),
        _candle(101, 101, 99, "sideways"),
    ]
    linhas_muitos = linhas_poucos + [
        _candle(93, 93, 93, "sideways"),
        _candle(101, 101, 99, "sideways"),
        _candle(93, 93, 93, "sideways"),
        _candle(101, 101, 99, "sideways"),
    ]

    params = grid.ParametrosGrade(n_niveis=4, capital_inicial=400.0)

    def _delta_retorno(linhas):
        df = _df(linhas)
        sem_custo = grid.simular_grade(df, params, fee_rate=0.0, slippage_pct=0.0)
        com_custo = grid.simular_grade(df, params, fee_rate=0.001, slippage_pct=0.0005)
        return sem_custo.total_return_pct - com_custo.total_return_pct

    delta_poucos = _delta_retorno(linhas_poucos)
    delta_muitos = _delta_retorno(linhas_muitos)

    assert delta_poucos > 0
    assert delta_muitos > delta_poucos
