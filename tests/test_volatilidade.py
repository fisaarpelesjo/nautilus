import math

import pytest

from backtesting import volatilidade as V
from backtesting.volatilidade import ParametrosVolatilidade, fator_volatilidade


# ------------------------------------------------------------ T002 fumaca

def test_modulo_expoe_a_api_publica():
    for nome in ("ParametrosVolatilidade", "fator_volatilidade",
                 "ComparacaoPareada", "comparar_combinacao",
                 "run_volatilidade_scan"):
        assert hasattr(V, nome), f"{nome} ausente"


# --------------------------------------------- T003 teto, o invariante central

@pytest.mark.parametrize("atr_ratio", [1e-9, 1e-6, 0.001, 0.005, 0.0187, 0.05, 0.5])
def test_fator_nunca_excede_um(atr_ratio):
    """FR-003 + constituição (max_leverage=1).

    O `min(1.0, ...)` é a fórmula, não validação defensiva: não pode existir
    caminho pelo qual esta feature amplie exposição.
    """
    assert fator_volatilidade(atr_ratio) <= 1.0


@pytest.mark.parametrize("alvo", [0.02, 0.1, 0.5, 10.0])
def test_fator_nao_excede_um_nem_com_alvo_absurdo(alvo):
    """Cenário 4 do quickstart: alvo muito acima de qualquer atr_ratio real
    (p99 medido = 0,0474) deve saturar em 1,0, não ampliar."""
    p = ParametrosVolatilidade(alvo=alvo)

    for atr_ratio in (0.0001, 0.0064, 0.0187, 0.0474):
        assert fator_volatilidade(atr_ratio, p) <= 1.0


def test_alvo_muito_alto_produz_fator_exatamente_um():
    p = ParametrosVolatilidade(alvo=0.5)

    assert fator_volatilidade(0.0187, p) == 1.0


# --------------------------------------- T004 dado invalido recai no vigente

@pytest.mark.parametrize("invalido", [
    None, 0.0, -0.01, float("nan"), float("inf"), float("-inf"),
])
def test_atr_ratio_invalido_devolve_fator_um(invalido):
    """FR-012 — dado desconhecido não vira decisão silenciosa.

    Recair no tamanho vigente é a política de falha do projeto. Divisão por zero
    ou posição infinita seriam as alternativas.
    """
    assert fator_volatilidade(invalido) == 1.0


def test_atr_ratio_invalido_nao_levanta_excecao():
    for invalido in (None, 0.0, float("nan")):
        fator_volatilidade(invalido)


# ------------------------------------------------ T005 monotonicidade

def test_fator_decresce_quando_a_volatilidade_sobe():
    p = ParametrosVolatilidade(alvo=0.02, fator_minimo=0.0)
    valores = [fator_volatilidade(v, p) for v in (0.02, 0.04, 0.08, 0.16)]

    assert valores == sorted(valores, reverse=True)
    assert valores[0] > valores[-1]


def test_dobrar_a_volatilidade_reduz_o_fator_a_metade():
    p = ParametrosVolatilidade(alvo=0.02, fator_minimo=0.0)

    assert fator_volatilidade(0.04, p) == pytest.approx(0.5)
    assert fator_volatilidade(0.08, p) == pytest.approx(0.25)


def test_volatilidade_no_alvo_produz_fator_um():
    p = ParametrosVolatilidade(alvo=0.02)

    assert fator_volatilidade(0.02, p) == pytest.approx(1.0)


# ------------------------------------------------------- T006 piso do fator

def test_fator_respeita_o_piso():
    """Volatilidade extrema não pode produzir posição que a corretora recusa."""
    p = ParametrosVolatilidade(alvo=0.02, fator_minimo=0.25)

    assert fator_volatilidade(10.0, p) == pytest.approx(0.25)


def test_piso_nao_eleva_fator_de_volatilidade_moderada():
    p = ParametrosVolatilidade(alvo=0.02, fator_minimo=0.25)

    assert fator_volatilidade(0.04, p) == pytest.approx(0.5)


def test_fator_fica_entre_piso_e_um_para_qualquer_entrada():
    p = ParametrosVolatilidade(alvo=0.02, fator_minimo=0.2)

    for v in (1e-9, 0.001, 0.0187, 0.05, 0.5, 5.0, 1e6):
        f = fator_volatilidade(v, p)
        assert p.fator_minimo <= f <= 1.0
        assert math.isfinite(f)


# ======================================== T009 T010 — guardas de integracao

def _serie(n=400, semente=2):
    import numpy as np
    import pandas as pd
    rng = np.random.default_rng(semente)
    preco = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.02, n)))
    idx = pd.date_range("2024-01-01", periods=n, freq="1D")
    return pd.DataFrame({
        "open": preco, "close": preco, "high": preco * 1.02,
        "low": preco * 0.98, "volume": np.full(n, 1000.0),
    }, index=idx)


def test_default_do_motor_nao_altera_nada():
    """T009 — o parâmetro é opcional e seu default reproduz o comportamento
    vigente. Sem esta garantia, adicionar a feature mudaria silenciosamente todo
    resultado histórico já registrado."""
    from backtesting.engine import simulate_backtest
    from backtesting.horizonte import preparar
    from strategy.ema_rsi import EmaRsiStrategy

    e = EmaRsiStrategy()
    df = preparar(_serie(), e)

    sem_param = simulate_backtest(df, e, start_index=50)
    com_none = simulate_backtest(df, e, start_index=50, position_sizer=None)

    assert sem_param.total_trades == com_none.total_trades
    assert sem_param.total_return_pct == pytest.approx(com_none.total_return_pct)
    assert sem_param.max_drawdown_pct == pytest.approx(com_none.max_drawdown_pct)
    assert sem_param.final_capital == pytest.approx(com_none.final_capital)


def test_sizer_que_devolve_um_equivale_a_nao_passar_sizer():
    """Fator 1,0 em toda vela: o resultado tem de ser idêntico à linha de base.
    É o cenário 4 do quickstart em forma de teste unitário."""
    from backtesting.engine import simulate_backtest
    from backtesting.horizonte import preparar
    from strategy.ema_rsi import EmaRsiStrategy

    e = EmaRsiStrategy()
    df = preparar(_serie(), e)

    base = simulate_backtest(df, e, start_index=50)
    neutro = simulate_backtest(df, e, start_index=50, position_sizer=lambda linha: 1.0)

    assert base.total_trades == neutro.total_trades
    assert base.final_capital == pytest.approx(neutro.final_capital)


def test_sizer_reduz_a_exposicao_e_o_capital_movimentado():
    """Fator constante < 1 tem de reduzir o tamanho, não o número de sinais:
    o dimensionamento decide QUANTO, nunca SE (FR-002)."""
    from backtesting.engine import simulate_backtest
    from backtesting.horizonte import preparar
    from strategy.ema_rsi import EmaRsiStrategy

    e = EmaRsiStrategy()
    df = preparar(_serie(), e)

    base = simulate_backtest(df, e, start_index=50)
    meio = simulate_backtest(df, e, start_index=50, position_sizer=lambda linha: 0.5)

    assert base.total_trades == meio.total_trades, "o sizer nao pode alterar o sinal"
    if base.total_trades > 0:
        assert abs(meio.total_return_pct) <= abs(base.total_return_pct) + 1e-9


def test_modulo_nao_depende_de_risk_manager():
    """T010 / FR-013 — guarda contra regressão de escopo.

    `risk/manager.py` é caminho de produção, sujeito ao princípio Safety First da
    constituição. Esta feature não pode alcançá-lo nem por importação indireta.
    """
    import ast
    from pathlib import Path

    # Checagem sobre as IMPORTACOES, nao sobre o texto do arquivo: o docstring do
    # modulo menciona `risk/manager.py` justamente para declarar que nao o toca,
    # e uma busca por string acusaria essa mencao como violacao.
    arvore = ast.parse(Path("backtesting/volatilidade.py").read_text(encoding="utf-8"))
    importados = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            importados.update(a.name for a in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module:
            importados.add(no.module)

    assert not any(m.startswith("risk") for m in importados), importados


def test_sizer_recebe_a_linha_do_candle_e_consegue_ler_atr_ratio():
    """Contrato do sizer: recebe a linha corrente, com os indicadores já
    calculados. É o que permite usar `atr_ratio` sem recomputar nada."""
    from backtesting.engine import simulate_backtest
    from backtesting.horizonte import preparar
    from strategy.ema_rsi import EmaRsiStrategy

    e = EmaRsiStrategy()
    df = preparar(_serie(), e)
    vistos = []

    def sizer(linha):
        vistos.append(linha.get("atr_ratio"))
        return 1.0

    simulate_backtest(df, e, start_index=50, position_sizer=sizer)

    if vistos:
        assert all(v is not None for v in vistos)


# ============================================ F3/US1 + F4/US2 — comparacao

def _res(trades=20, ret=10.0, dd=8.0, expo=50.0, bh=0.0, pf=1.5):
    """BacktestResult minimo, so com os campos que a comparacao consulta."""
    from backtesting.engine import BacktestResult, _calculate_advanced_metrics

    m = _calculate_advanced_metrics([])
    m.update(profit_factor=pf, exposure_pct=expo)
    return BacktestResult(
        trades=[], initial_capital=1000.0, final_capital=1000.0 + ret * 10,
        total_return_pct=ret, win_rate=50.0, total_trades=trades,
        max_drawdown_pct=dd, buy_hold_return_pct=bh, edge_return_pct=ret - bh, **m,
    )


def _com_trades(ret, dd, nocional, bh=-40.0, expo=50.0, trades=20):
    """BacktestResult com uma operacao de nocional declarado, para
    `exposicao_de_capital` ter o que medir."""
    import datetime as dt

    from backtesting.engine import Trade

    r = _res(trades=trades, ret=ret, dd=dd, expo=expo, bh=bh)
    t0 = dt.datetime(2026, 1, 1)
    r.trades = [Trade(100.0, 100.0, nocional / 100.0, 0.0, 0.0, 0.0,
                      t0, t0 + dt.timedelta(days=10), "Take Profit")]
    return r


def _cmp(base, dim, **kw):
    """`fator_medio` abaixo de 1,0 por padrao: representa o mecanismo TENDO
    atuado, que e a premissa de qualquer teste sobre amostra ou metrica. Com
    1,0 a comparacao e inerte e a classificacao para antes."""
    from backtesting.volatilidade import ComparacaoPareada
    kw.setdefault("fator_medio", 0.8)
    return ComparacaoPareada(estrategia="X", par="BTC/USDT",
                             sem_dimensionamento=base, com_dimensionamento=dim, **kw)


# ------------------------------------------------------------ T011 deltas

def test_deltas_sao_dimensionado_menos_base():
    c = _cmp(_res(ret=10.0, dd=12.0, expo=60.0), _res(ret=7.0, dd=8.0, expo=45.0))

    assert c.delta_retorno == pytest.approx(-3.0)
    assert c.delta_drawdown == pytest.approx(-4.0)
    # Exposicao de TEMPO: a que o motor mede e que este mecanismo nao move.
    assert c.delta_exposicao_tempo == pytest.approx(-15.0)


def test_delta_operacoes_e_custo_entre_versoes():
    c = _cmp(_res(trades=20), _res(trades=26))
    c.retorno_sem_custo_base = 12.0
    c.retorno_sem_custo_dim = 11.0

    assert c.delta_operacoes == 6
    assert c.delta_custo == pytest.approx(
        (c.com_dimensionamento.total_return_pct - 11.0)
        - (c.sem_dimensionamento.total_return_pct - 12.0)
    )


# ---------------------------------- T019 T020 — o teste central da spec

def test_drawdown_cai_sem_ganho_de_timing_e_sem_vantagem():
    """FR-008 — o teste mais importante desta spec, reescrito apos D3.

    A versao original supunha que reduzir tamanho reduz a exposicao MEDIDA. Nao
    reduz: o motor mede exposicao em tempo, e o dimensionamento nao muda quando
    se entra ou sai. Ver `exposicao_de_capital`.

    O caso real e este: o dimensionamento escala tudo por um fator uniforme.
    Retorno, drawdown e capital exposto caem todos na mesma proporcao. Nao houve
    selecao alguma -- apostou-se menos, e so. O ganho por unidade de capital
    exposto fica identico, e isso NAO e melhoria.
    """
    from backtesting.volatilidade import classificar_comparacao

    base = _com_trades(ret=-24.0, dd=12.0, nocional=100.0, bh=-40.0)
    dim = _com_trades(ret=-12.0, dd=6.0, nocional=50.0, bh=-40.0)

    status, motivo = classificar_comparacao(_cmp(base, dim, fator_medio=0.5))

    assert status == "sem_vantagem", motivo


def test_drawdown_cai_com_ganho_de_timing_e_melhora():
    """Reducao SELETIVA sobre base LUCRATIVA: o dimensionamento cortou tamanho
    onde doia e manteve onde rendia, e o ganho por capital exposto sobe.

    A base precisa lucrar. Sobre base perdedora o mesmo numero sairia
    `confundido` -- ver `test_melhora_sobre_base_perdedora_e_confundida`.
    """
    from backtesting.volatilidade import classificar_comparacao

    base = _com_trades(ret=10.0, dd=12.0, nocional=100.0, bh=-40.0)
    dim = _com_trades(ret=9.0, dd=6.0, nocional=50.0, bh=-40.0)
    c = _cmp(base, dim, fator_medio=0.5)
    c.validacao_base = _com_trades(ret=5.0, dd=8.0, nocional=100.0)
    c.validacao_dim = _com_trades(ret=4.5, dd=4.0, nocional=50.0)

    status, motivo = classificar_comparacao(c)

    assert status == "melhora", motivo


def test_drawdown_nao_cai_e_piora():
    from backtesting.volatilidade import classificar_comparacao

    base = _res(trades=20, ret=10.0, dd=8.0, expo=60.0)
    dim = _res(trades=20, ret=6.0, dd=11.0, expo=55.0)

    status, _ = classificar_comparacao(_cmp(base, dim))

    assert status == "piora"


# ------------------------------------------ T012 T013 — amostra e erro

def test_amostra_insuficiente_em_qualquer_versao_e_inconclusiva():
    """FR-011 — comparar 30 operações contra 4 mede diferença de amostra,
    não dimensionamento."""
    from backtesting.volatilidade import classificar_comparacao
    from config.settings import EDGE_MIN_TRADES

    poucas = EDGE_MIN_TRADES - 1

    s1, m1 = classificar_comparacao(_cmp(_res(trades=30), _res(trades=poucas)))
    s2, m2 = classificar_comparacao(_cmp(_res(trades=poucas), _res(trades=30)))

    assert s1 == "inconclusivo" and "opera" in m1.lower()
    assert s2 == "inconclusivo" and "opera" in m2.lower()


def test_amostra_insuficiente_precede_avaliacao_de_metrica():
    """Mesmo com métricas boas, amostra insuficiente decide primeiro."""
    from backtesting.volatilidade import classificar_comparacao

    base = _res(trades=30, ret=-24.0, dd=12.0, expo=60.0, bh=-40.0)
    dim = _res(trades=3, ret=20.0, dd=2.0, expo=45.0, bh=-40.0)

    status, _ = classificar_comparacao(_cmp(base, dim))

    assert status == "inconclusivo"


def test_versao_ausente_produz_erro_nao_piora():
    from backtesting.volatilidade import classificar_comparacao

    status, _ = classificar_comparacao(_cmp(_res(trades=20), None))

    assert status == "erro"


def test_ganho_de_timing_reusa_a_metrica_de_cross_sectional():
    """A definição de ganho de timing vive em cross_sectional.WalkForwardFold.
    Redefini-la aqui criaria duas fórmulas do mesmo conceito no mesmo sistema."""
    from backtesting.cross_sectional import WalkForwardFold
    from backtesting.volatilidade import ganho_de_timing

    r = _res(ret=-18.0, expo=45.0, bh=-40.0)
    esperado = WalkForwardFold(1, -40.0, -18.0, 45.0, 0.0, 20).ganho_de_timing_pp

    assert ganho_de_timing(r) == pytest.approx(esperado)


# ------------------------------ T021 — exposicao reportada em toda comparacao

def test_exposicao_reportada_em_toda_comparacao_avaliada():
    """FR-007 — sem exposição na saída, a leitura de M7 fica indisponível ao
    leitor do relatório mesmo com o status correto."""
    from backtesting.volatilidade import classificar_comparacao

    for base, dim in (
        (_res(trades=20, ret=-24.0, dd=12.0, expo=60.0, bh=-40.0),
         _res(trades=20, ret=-18.0, dd=9.0, expo=45.0, bh=-40.0)),
        (_res(trades=20, ret=10.0, dd=8.0, expo=60.0),
         _res(trades=20, ret=6.0, dd=11.0, expo=55.0)),
    ):
        c = _cmp(base, dim)
        c.status, c.motivo = classificar_comparacao(c)
        assert c.delta_exposicao_tempo == pytest.approx(
            dim.exposure_pct - base.exposure_pct)
        assert c.delta_exposicao is not None


# ------------------------------------ T015 T016 — varredura sobre serie real

def _serie_longa(n=900, semente=2):
    """Serie que efetivamente PRODUZ operacoes.

    `_serie` usa volume constante, e com volume constante nenhum candle fica
    acima da propria media movel -- o filtro `volume >= volume_ma x ratio`
    reprova todos os cruzamentos e a serie rende zero trades. Medido: 8
    cruzamentos de EMA, 6 sobrevivem a tendencia e ao RSI, 0 sobrevivem ao
    volume. Uma comparacao entre dois backtests vazios passa em quase qualquer
    assercao sem medir nada.

    Nome distinto de proposito: um segundo `_serie` sobrescreveria o primeiro e
    mudaria calada a entrada dos testes de T009.
    """
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(semente)
    preco = 100 * np.exp(np.cumsum(0.0015 + rng.normal(0, 0.008, n)))
    return pd.DataFrame({
        "open": preco, "close": preco, "high": preco * 1.01,
        "low": preco * 0.99, "volume": rng.uniform(1e5, 1e6, n),
    }, index=pd.date_range("2026-01-01", periods=n, freq="4h"))


def test_comparar_combinacao_roda_as_duas_versoes_sobre_a_mesma_serie():
    from backtesting.volatilidade import comparar_combinacao
    from strategy.ema_rsi import EmaRsiStrategy

    c = comparar_combinacao(EmaRsiStrategy(), "EMA/RSI", "BTC/USDT", df=_serie_longa())

    assert c.sem_dimensionamento is not None
    assert c.com_dimensionamento is not None
    assert c.status in {"melhora", "sem_vantagem", "piora", "inconclusivo"}
    assert 0.0 < c.fator_medio <= 1.0


def test_dimensionamento_nunca_amplia_o_capital_final_acima_da_base():
    """FR-003 na ponta: o fator vive em (0, 1], então a versão dimensionada
    nunca aloca mais que a base — e nunca vira alavancagem por acidente."""
    from backtesting.volatilidade import comparar_combinacao
    from strategy.ema_rsi import EmaRsiStrategy

    c = comparar_combinacao(EmaRsiStrategy(), "EMA/RSI", "BTC/USDT", df=_serie_longa())

    assert c.fator_medio <= 1.0
    assert c.delta_exposicao <= 0.001


def test_scan_nao_aborta_quando_uma_combinacao_falha():
    from backtesting.volatilidade import run_volatilidade_scan
    from strategy.ema_rsi import EmaRsiStrategy

    class Explode(EmaRsiStrategy):
        def calculate_indicators(self, df):
            raise RuntimeError("falha proposital")

    saida = run_volatilidade_scan(
        estrategias={"boa": EmaRsiStrategy(), "ruim": Explode()},
        pares=["BTC/USDT"],
    )

    assert len(saida) == 2
    assert {c.estrategia for c in saida} == {"boa", "ruim"}
    assert next(c for c in saida if c.estrategia == "ruim").status == "erro"


# ================================================ F5/US3 — custo de giro

def test_execucao_sem_custo_rende_mais_ou_igual_nas_duas_versoes():
    """T027 — zerar taxa e slippage não pode piorar o retorno. Se piorar, o
    custo não está sendo aplicado onde se pensa que está."""
    from backtesting.volatilidade import comparar_combinacao
    from strategy.ema_rsi import EmaRsiStrategy

    c = comparar_combinacao(EmaRsiStrategy(), "EMA/RSI", "BTC/USDT", df=_serie_longa())

    assert c.retorno_sem_custo_base is not None
    assert c.retorno_sem_custo_dim is not None
    assert c.retorno_sem_custo_base >= c.sem_dimensionamento.total_return_pct - 1e-9
    assert c.retorno_sem_custo_dim >= c.com_dimensionamento.total_return_pct - 1e-9


def test_custo_de_giro_e_separavel_da_vantagem():
    """FR-014 — dimensionar implica giro, e giro paga taxa. Sem separar, um
    delta negativo não distingue mecanismo ruim de custo adicional."""
    from backtesting.volatilidade import comparar_combinacao
    from strategy.ema_rsi import EmaRsiStrategy

    c = comparar_combinacao(EmaRsiStrategy(), "EMA/RSI", "BTC/USDT", df=_serie_longa())

    delta_sem_custo = c.retorno_sem_custo_dim - c.retorno_sem_custo_base

    # O delta observado é o delta sem custo mais o que o custo adicional levou.
    assert c.delta_retorno == pytest.approx(delta_sem_custo + c.delta_custo, abs=1e-6)


def test_custo_ausente_nao_vira_zero_silencioso():
    """Reexecução sem custo pode falhar. Nesse caso `delta_custo` devolve 0,0 —
    mas os campos ficam None, para o relatório poder distinguir 'custo nulo' de
    'custo não medido'."""
    c = _cmp(_res(trades=20), _res(trades=20))

    assert c.retorno_sem_custo_base is None
    assert c.retorno_sem_custo_dim is None
    assert c.delta_custo == 0.0


# ==================== D1 D2 D3 — defeitos achados na primeira varredura real

def test_estrategia_sem_atr_ratio_e_inerte_nao_piora():
    """D1 — só EmaRsiStrategy calcula `atr_ratio`. Nas demais o fator caía no
    fallback de entrada inválida e devolvia 1,0 em todo candle: as duas versões
    rodavam idênticas e a combinação era rotulada `piora`.

    36 das 48 combinações da primeira varredura foram isso. Fallback por candle
    é política correta; fallback em 100% dos candles é ausência de medição e
    precisa aparecer como tal.
    """
    from backtesting.volatilidade import comparar_combinacao
    from strategy.breakout import BreakoutStrategy

    c = comparar_combinacao(BreakoutStrategy(window=150), "Breakout 150",
                            "BTC/USDT", df=_serie_longa())

    assert c.status == "inerte"
    assert "atr_ratio" in c.motivo


def test_drawdown_identico_nao_e_piora():
    """D2 — `delta_drawdown >= 0` classificava "não mudou" como deterioração."""
    from backtesting.volatilidade import classificar_comparacao

    c = _cmp(_res(trades=20, dd=8.0, ret=5.0), _res(trades=20, dd=8.0, ret=5.0))
    c.fator_medio = 1.0

    status, motivo = classificar_comparacao(c)

    assert status == "inerte"
    assert status != "piora"


def test_drawdown_maior_continua_piora():
    from backtesting.volatilidade import classificar_comparacao

    c = _cmp(_res(trades=20, dd=8.0, ret=5.0), _res(trades=20, dd=11.0, ret=4.0))
    c.fator_medio = 0.8

    assert classificar_comparacao(c)[0] == "piora"


# --------------------------------------------------------------- D3, o grave

def test_exposicao_de_tempo_e_cega_a_dimensionamento():
    """D3 — a premissa do defeito, medida e não suposta.

    `_exposure_pct` do motor mede TEMPO em mercado. Dimensionar por volatilidade
    muda quanto capital entra, nunca quando entra ou sai. Logo a exposição de
    tempo é idêntica entre as duas versões, `delta_timing` vira igual a
    `delta_retorno` por identidade, e `sem_vantagem` fica inatingível.
    """
    from backtesting.volatilidade import comparar_combinacao
    from strategy.ema_rsi import EmaRsiStrategy

    c = comparar_combinacao(EmaRsiStrategy(), "EMA/RSI", "BTC/USDT", df=_serie_longa())

    b, d = c.sem_dimensionamento, c.com_dimensionamento
    assert c.fator_medio < 1.0, "o mecanismo precisa ter atuado para o teste valer"
    assert d.exposure_pct == pytest.approx(b.exposure_pct), (
        "se a exposicao de tempo mudar, a premissa de D3 mudou")


def test_exposicao_de_capital_responde_ao_dimensionamento():
    """A medida que a guarda passa a usar: capital alocado x tempo."""
    from backtesting.volatilidade import comparar_combinacao, exposicao_de_capital
    from strategy.ema_rsi import EmaRsiStrategy

    c = comparar_combinacao(EmaRsiStrategy(), "EMA/RSI", "BTC/USDT", df=_serie_longa())

    ec_base = exposicao_de_capital(c.sem_dimensionamento)
    ec_dim = exposicao_de_capital(c.com_dimensionamento)

    assert ec_dim < ec_base, "reduzir tamanho tem de reduzir a exposicao de capital"
    assert c.delta_exposicao < 0.0


def test_exposicao_de_capital_e_menor_que_a_de_tempo_quando_o_teto_limita():
    """MAX_ORDER_SIZE_USDT faz o bot alocar uma fracao do caixa. Exposicao de
    tempo de 40% com 10% do capital em risco nao e 40% de exposicao."""
    from backtesting.volatilidade import comparar_combinacao, exposicao_de_capital
    from strategy.ema_rsi import EmaRsiStrategy

    c = comparar_combinacao(EmaRsiStrategy(), "EMA/RSI", "BTC/USDT", df=_serie_longa())
    r = c.sem_dimensionamento

    assert 0.0 < exposicao_de_capital(r) < r.exposure_pct


def test_ganho_de_timing_aceita_exposicao_explicita():
    """Uma formula, duas medidas de exposicao — explicito no ponto de chamada."""
    from backtesting.cross_sectional import WalkForwardFold
    from backtesting.volatilidade import ganho_de_timing

    r = _res(ret=-18.0, expo=45.0, bh=-40.0)
    esperado = WalkForwardFold(1, -40.0, -18.0, 4.5, 0.0, 20).ganho_de_timing_pp

    assert ganho_de_timing(r, exposicao=4.5) == pytest.approx(esperado)


def test_escalonamento_puro_nao_move_o_ganho_por_capital():
    """A invariancia que sustenta a decisao: se so o tamanho mudou, a grandeza
    nao se move -- para qualquer fator."""
    from backtesting.volatilidade import ComparacaoPareada

    for f in (0.2, 0.5, 0.9):
        c = ComparacaoPareada(
            estrategia="X", par="BTC/USDT", fator_medio=f,
            sem_dimensionamento=_com_trades(ret=-24.0, dd=12.0, nocional=100.0),
            com_dimensionamento=_com_trades(ret=-24.0 * f, dd=12.0 * f,
                                            nocional=100.0 * f),
        )
        assert c.delta_timing == pytest.approx(0.0, abs=1e-9), f


# ============ D4 D5 — confundimento por base perdedora e confirmacao fora

def _validado(c, ret_base_val, ret_dim_val, nocional_base=100.0, nocional_dim=50.0):
    c.validacao_base = _com_trades(ret=ret_base_val, dd=10.0, nocional=nocional_base)
    c.validacao_dim = _com_trades(ret=ret_dim_val, dd=5.0, nocional=nocional_dim)
    return c


def test_melhora_sobre_base_perdedora_e_confundida():
    """D4 — encolher uma estratégia de expectativa negativa aproxima o resultado
    de zero. A métrica registra melhora, mas o limite dessa lógica é não operar,
    que maximizaria o critério sem ganhar nada.

    Medido: correlação −0,92 entre retorno base e `delta_timing`, concordância
    de sinal em 8 de 8 combinações da primeira varredura válida.
    """
    from backtesting.volatilidade import classificar_comparacao

    base = _com_trades(ret=-3.91, dd=3.94, nocional=100.0)
    dim = _com_trades(ret=-3.23, dd=3.26, nocional=97.0)
    c = _validado(_cmp(base, dim, fator_medio=0.93), -3.0, -2.0)

    status, motivo = classificar_comparacao(c)

    assert status == "confundido"
    assert status != "melhora"


def test_melhora_exige_base_lucrativa_e_confirmacao_fora_da_amostra():
    from backtesting.volatilidade import classificar_comparacao

    base = _com_trades(ret=8.0, dd=10.0, nocional=100.0)
    dim = _com_trades(ret=7.6, dd=6.0, nocional=50.0)
    c = _validado(_cmp(base, dim, fator_medio=0.6), 4.0, 3.8)

    assert classificar_comparacao(c)[0] == "melhora"


def test_melhora_so_na_busca_nao_e_aprovacao():
    """D5 — sem confirmação, `melhora` significa só "melhorou onde foi medido"."""
    from backtesting.volatilidade import classificar_comparacao

    base = _com_trades(ret=8.0, dd=10.0, nocional=100.0)
    dim = _com_trades(ret=7.6, dd=6.0, nocional=50.0)
    c = _validado(_cmp(base, dim, fator_medio=0.6), 4.0, 1.0)

    status, motivo = classificar_comparacao(c)

    assert status == "so_na_busca"
    assert status != "melhora"


def test_sem_janela_de_validacao_e_inconclusivo_nao_melhora():
    from backtesting.volatilidade import classificar_comparacao

    base = _com_trades(ret=8.0, dd=10.0, nocional=100.0)
    dim = _com_trades(ret=7.6, dd=6.0, nocional=50.0)

    status, _ = classificar_comparacao(_cmp(base, dim, fator_medio=0.6))

    assert status == "inconclusivo"
