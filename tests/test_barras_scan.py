"""Comparação pareada entre amostragem por tempo e por informação (spec 026)."""
import datetime as dt

import pytest


def _res(trades=20, ret=10.0, dd=8.0, expo=50.0, bh=5.0, pf=1.5, nocional=100.0):
    from backtesting.engine import BacktestResult, Trade, _calculate_advanced_metrics

    m = _calculate_advanced_metrics([])
    m.update(profit_factor=pf, exposure_pct=expo)
    r = BacktestResult(
        trades=[], initial_capital=1000.0, final_capital=1000.0 + ret * 10,
        total_return_pct=ret, win_rate=50.0, total_trades=trades,
        max_drawdown_pct=dd, buy_hold_return_pct=bh, edge_return_pct=ret - bh, **m,
    )
    t0 = dt.datetime(2026, 1, 1)
    r.trades = [Trade(100.0, 100.0, nocional / 100.0, 0.0, 0.0, 0.0,
                      t0, t0 + dt.timedelta(days=10), "Take Profit")]
    return r


def _cmp(tempo, barras, **kw):
    """Comparação com valores que representam 'a reamostragem atuou e a janela
    é utilizável' — a premissa de qualquer teste sobre métrica."""
    from backtesting.barras import ComparacaoBarras

    kw.setdefault("n_base", 8000)
    kw.setdefault("n_tempo", 2000)
    kw.setdefault("n_barras", 1950)
    kw.setdefault("pct_barras_1_candle", 9.4)
    kw.setdefault("aquecimento_dias_tempo", 8.3)
    kw.setdefault("aquecimento_dias_barras", 8.5)
    kw.setdefault("dias_janela", 333.3)
    return ComparacaoBarras(
        estrategia="EMA/RSI", par="BTC/USDT", tipo="dollar",
        tempo=tempo, barras=barras, **kw)


def _com_validacao(c, ret_tempo, ret_barras):
    c.validacao_tempo = _res(ret=ret_tempo, nocional=100.0)
    c.validacao_barras = _res(ret=ret_barras, nocional=100.0)
    return c


# ==================================================== T016 grandezas derivadas

def test_deltas_sao_barras_menos_tempo():
    c = _cmp(_res(ret=10.0, dd=12.0, expo=60.0, trades=20),
             _res(ret=7.0, dd=8.0, expo=45.0, trades=14))

    assert c.delta_retorno == pytest.approx(-3.0)
    assert c.delta_drawdown == pytest.approx(-4.0)
    assert c.delta_exposicao == pytest.approx(-15.0)
    assert c.delta_operacoes == -6


def test_razao_observacoes_compara_com_a_versao_de_tempo():
    c = _cmp(_res(), _res(), n_tempo=2000, n_barras=1950)

    assert c.razao_observacoes == pytest.approx(0.975)


# ====================================== T017 buy-and-hold é a âncora

def test_buy_hold_divergente_produz_erro():
    """FR-007 — o buy-and-hold é o único ponto fixo entre as duas amostragens.
    Se ele se mover, nada é comparável."""
    from backtesting.barras import classificar_comparacao_barras

    c = _cmp(_res(bh=5.0), _res(bh=41.0))

    status, motivo = classificar_comparacao_barras(c)

    assert status == "erro"
    assert "buy" in motivo.lower() or "referencia" in motivo.lower()


def test_buy_hold_igual_dentro_da_tolerancia_prossegue():
    from backtesting.barras import classificar_comparacao_barras

    c = _cmp(_res(bh=5.0), _res(bh=5.0001))

    assert classificar_comparacao_barras(c)[0] != "erro"


# ====================================== T018 inércia — a lição de H12

def test_uma_barra_por_candle_de_base_e_inerte_nao_piora():
    """FR-012 — se cada candle de base virou uma barra, as duas versões não
    diferem em esquema de amostragem e não há comparação a julgar.

    Em H12, 37 de 48 combinações estavam nessa situação e apareciam como
    `piora`, afirmando deterioração onde nada mudara.
    """
    from backtesting.barras import classificar_comparacao_barras

    c = _cmp(_res(dd=8.0), _res(dd=11.0),
             n_base=8000, n_barras=8000, pct_barras_1_candle=100.0)

    status, motivo = classificar_comparacao_barras(c)

    assert status == "inerte"
    assert status != "piora"


def test_inercia_e_medida_contra_a_base_nao_contra_a_versao_de_tempo():
    """A calibração faz `n_barras ≈ n_tempo` de propósito (D2). Medir inércia
    por essa razão marcaria como inerte exatamente o caso bem calibrado."""
    from backtesting.barras import classificar_comparacao_barras

    c = _cmp(_res(dd=8.0, ret=10.0), _res(dd=6.0, ret=9.5),
             n_base=8000, n_tempo=2000, n_barras=2000, pct_barras_1_candle=9.4)

    assert classificar_comparacao_barras(c)[0] != "inerte"


# ====================================== T019 aquecimento em dias — lição de H11

def test_aquecimento_que_nao_cabe_no_historico_e_inconclusivo():
    """FR-010 — 50 barras podem cobrir um mês ou um dia. H11 tropeçou nisto:
    50 candles semanais eram 350 dias, quase um ano antes da primeira decisão."""
    from backtesting.barras import classificar_comparacao_barras

    c = _cmp(_res(), _res(), aquecimento_dias_barras=200.0, dias_janela=333.3)

    status, motivo = classificar_comparacao_barras(c)

    assert status == "inconclusivo"
    assert "aquecimento" in motivo.lower()


def test_aquecimento_curto_nao_bloqueia():
    from backtesting.barras import classificar_comparacao_barras

    c = _cmp(_res(dd=8.0, ret=10.0), _res(dd=6.0, ret=9.5),
             aquecimento_dias_barras=9.0, dias_janela=333.3)

    assert classificar_comparacao_barras(c)[0] != "inconclusivo"


# ====================================== T020 amostra — regra de H10/H11/M9

def test_amostra_insuficiente_em_qualquer_versao_e_inconclusiva():
    from backtesting.barras import classificar_comparacao_barras
    from config.settings import EDGE_MIN_TRADES

    poucas = EDGE_MIN_TRADES - 1

    s1, m1 = classificar_comparacao_barras(_cmp(_res(trades=30), _res(trades=poucas)))
    s2, m2 = classificar_comparacao_barras(_cmp(_res(trades=poucas), _res(trades=30)))

    assert s1 == "inconclusivo" and "opera" in m1.lower()
    assert s2 == "inconclusivo" and "opera" in m2.lower()


def test_amostra_precede_avaliacao_de_metrica():
    from backtesting.barras import classificar_comparacao_barras

    c = _cmp(_res(trades=30, dd=12.0, ret=10.0), _res(trades=3, dd=2.0, ret=20.0))

    assert classificar_comparacao_barras(c)[0] == "inconclusivo"


def test_versao_ausente_produz_erro():
    from backtesting.barras import classificar_comparacao_barras

    assert classificar_comparacao_barras(_cmp(_res(), None))[0] == "erro"


# ============================ T027 T028 T029 T030 — guardas M7/M11/H10 (US2)

def test_ganho_que_nao_sobrevive_ao_desconto_de_exposicao_e_sem_vantagem():
    """FR-009 — barras mais grossas produzem menos sinais e menos exposição.
    Num mercado em queda isso sozinho melhora o retorno relativo."""
    from backtesting.barras import classificar_comparacao_barras

    # Retorno melhora exatamente na proporção da menor exposição: sem ganho real.
    tempo = _res(ret=-20.0, dd=12.0, expo=60.0, bh=-40.0)
    barras = _res(ret=-14.0, dd=8.0, expo=45.0, bh=-40.0)

    status, motivo = classificar_comparacao_barras(_cmp(tempo, barras))

    assert status in ("sem_vantagem", "confundido")
    assert status != "melhora"


def test_base_de_tempo_perdedora_produz_confundido():
    """Guarda M11 — sobre estratégia de expectativa negativa, operar menos
    aproxima o resultado de zero e a métrica registra ganho. O limite da lógica
    é não operar, que maximizaria o critério sem ganhar nada."""
    from backtesting.barras import classificar_comparacao_barras

    tempo = _res(ret=-3.91, dd=3.94, expo=50.0, bh=-10.0)
    barras = _res(ret=-1.20, dd=3.20, expo=50.0, bh=-10.0)

    status, motivo = classificar_comparacao_barras(_com_validacao(
        _cmp(tempo, barras), -3.0, -1.0))

    assert status == "confundido"
    assert status != "melhora"


def test_melhora_exige_confirmacao_fora_da_amostra():
    """Lição de H10 — sem confirmação, `melhora` significa apenas 'melhorou
    onde foi medido'."""
    from backtesting.barras import classificar_comparacao_barras

    tempo = _res(ret=8.0, dd=12.0, expo=50.0, bh=5.0)
    barras = _res(ret=14.0, dd=8.0, expo=50.0, bh=5.0)

    c = _com_validacao(_cmp(tempo, barras), 4.0, 1.0)
    status, motivo = classificar_comparacao_barras(c)

    assert status == "so_na_busca"
    assert status != "melhora"


def test_melhora_confirmada_e_melhora():
    from backtesting.barras import classificar_comparacao_barras

    tempo = _res(ret=8.0, dd=12.0, expo=50.0, bh=5.0)
    barras = _res(ret=14.0, dd=8.0, expo=50.0, bh=5.0)

    c = _com_validacao(_cmp(tempo, barras), 4.0, 9.0)

    assert classificar_comparacao_barras(c)[0] == "melhora"


def test_sem_janela_de_validacao_e_inconclusivo_nao_melhora():
    from backtesting.barras import classificar_comparacao_barras

    tempo = _res(ret=8.0, dd=12.0, expo=50.0, bh=5.0)
    barras = _res(ret=14.0, dd=8.0, expo=50.0, bh=5.0)

    assert classificar_comparacao_barras(_cmp(tempo, barras))[0] == "inconclusivo"


def test_delta_exposicao_usa_tempo_e_e_sempre_calculado():
    """FR-008, D4 — diferente de H12, aqui o mecanismo muda QUANDO as decisões
    acontecem, então a exposição de tempo responde e é a medida correta."""
    from backtesting.barras import classificar_comparacao_barras

    for tempo, barras in (
        (_res(ret=10.0, dd=12.0, expo=60.0), _res(ret=9.0, dd=8.0, expo=45.0)),
        (_res(ret=10.0, dd=8.0, expo=60.0), _res(ret=6.0, dd=11.0, expo=55.0)),
    ):
        c = _cmp(tempo, barras)
        c.status, c.motivo = classificar_comparacao_barras(c)
        assert c.delta_exposicao == pytest.approx(
            barras.exposure_pct - tempo.exposure_pct)


def test_drawdown_maior_e_piora():
    from backtesting.barras import classificar_comparacao_barras

    c = _cmp(_res(ret=10.0, dd=8.0), _res(ret=9.0, dd=11.0))

    assert classificar_comparacao_barras(c)[0] == "piora"


def test_ordem_das_checagens_erro_precede_inercia():
    """A ordem é a regra: uma versão ausente não pode ser lida como inércia."""
    from backtesting.barras import classificar_comparacao_barras

    c = _cmp(_res(), None, n_barras=8000, pct_barras_1_candle=100.0)

    assert classificar_comparacao_barras(c)[0] == "erro"


# ============================================ T039 T040 — custo de giro (US4)

def test_delta_custo_entre_versoes():
    c = _cmp(_res(ret=10.0, trades=20), _res(ret=14.0, trades=32))
    c.retorno_sem_custo_tempo = 12.0
    c.retorno_sem_custo_barras = 17.0

    assert c.delta_operacoes == 12
    assert c.delta_custo == pytest.approx((14.0 - 17.0) - (10.0 - 12.0))


def test_custo_nao_medido_nao_vira_zero_silencioso():
    c = _cmp(_res(), _res())

    assert c.retorno_sem_custo_tempo is None
    assert c.delta_custo == 0.0
