"""Estimação, rótulo embaralhado e classificação (spec 027, H14, US1 e US3)."""
import datetime as dt

import numpy as np
import pandas as pd
import pytest


def _res(trades=20, ret=10.0, dd=8.0, expo=50.0, bh=5.0, pf=1.5):
    from backtesting.engine import BacktestResult, Trade, _calculate_advanced_metrics

    m = _calculate_advanced_metrics([])
    m.update(profit_factor=pf, exposure_pct=expo)
    r = BacktestResult(
        trades=[], initial_capital=1000.0, final_capital=1000.0 + ret * 10,
        total_return_pct=ret, win_rate=50.0, total_trades=trades,
        max_drawdown_pct=dd, buy_hold_return_pct=bh, edge_return_pct=ret - bh, **m,
    )
    t0 = dt.datetime(2026, 1, 1)
    r.trades = [Trade(100.0, 100.0, 1.0, 0.0, 0.0, 0.0,
                      t0, t0 + dt.timedelta(days=10), "Take Profit")]
    return r


def _modelo(razao_decidido=0.60, backtest=None, convergiu=True, n_treino=5000,
            n_teste=2000, razao_geral=0.372, n_decisoes=1000):
    """As contagens brutas sao derivadas da razao pedida.

    `supera_empate` usa o limite inferior do IC sobre as CONTAGENS, nao a razao
    pontual, entao um fixture que so setasse a razao testaria outra coisa.
    """
    from backtesting.modelo import ResultadoModelo

    stop = int(round(n_decisoes / (1.0 + razao_decidido)))
    alvo = n_decisoes - stop
    return ResultadoModelo(
        convergiu=convergiu, n_treino=n_treino, n_teste=n_teste,
        dist_classes={"alvo": 23.4, "stop": 62.8, "tempo": 12.8, "n": n_teste},
        razao_chances_geral=razao_geral,
        razao_chances_decidido=razao_decidido,
        n_decidido=n_decisoes, n_alvo_decidido=alvo, n_stop_decidido=stop,
        backtest=backtest if backtest is not None else _res(),
    )


def _aval(modelo=None, embaralhado=None, regras=None, **kw):
    from backtesting.modelo import AvaliacaoH14

    return AvaliacaoH14(
        par="BTC/USDT",
        modelo=modelo if modelo is not None else _modelo(),
        embaralhado=embaralhado if embaralhado is not None else _modelo(
            razao_decidido=0.30, backtest=_res(ret=1.0, dd=8.0)),
        regras=regras if regras is not None else _res(ret=5.0, dd=10.0),
        **kw,
    )


def _com_validacao(a, ret_modelo, ret_regras):
    a.validacao_modelo = _res(ret=ret_modelo)
    a.validacao_regras = _res(ret=ret_regras)
    return a


# ======================================================= T018 grandezas (US1)

def test_deltas_sao_modelo_menos_regras():
    a = _aval(modelo=_modelo(backtest=_res(ret=7.0, dd=8.0, expo=45.0, trades=14)),
              regras=_res(ret=10.0, dd=12.0, expo=60.0, trades=20))

    assert a.delta_retorno == pytest.approx(-3.0)
    assert a.delta_drawdown == pytest.approx(-4.0)
    assert a.delta_exposicao == pytest.approx(-15.0)
    assert a.delta_operacoes == -6


def test_delta_contra_embaralhado_usa_ganho_de_timing():
    a = _aval(modelo=_modelo(backtest=_res(ret=12.0, expo=50.0, bh=5.0)),
              embaralhado=_modelo(razao_decidido=0.30,
                                  backtest=_res(ret=4.0, expo=50.0, bh=5.0)))

    assert a.delta_vs_embaralhado > 0


# ============================================ T019 T020 convergência e classe

def test_falha_de_convergencia_produz_estado_proprio():
    """FR-012 — métricas calculadas sobre uma estimação que falhou seriam
    silenciosamente inválidas. A colinearidade de 0,959 medida entre candidatos
    descartados mostra que este caminho é real."""
    from backtesting.modelo import classificar_avaliacao

    a = _aval(modelo=_modelo(convergiu=False))

    status, motivo = classificar_avaliacao(a)

    assert status == "nao_convergiu"
    assert "converg" in motivo.lower()


def test_classe_unica_produz_estado_proprio():
    from backtesting.modelo import classificar_avaliacao

    m = _modelo()
    m.dist_classes = {"alvo": 0.0, "stop": 100.0, "tempo": 0.0, "n": 2000}

    status, motivo = classificar_avaliacao(_aval(modelo=m))

    assert status == "classe_unica"


def test_convergencia_precede_qualquer_metrica():
    """Ordem: sem modelo estimado não há o que julgar."""
    from backtesting.modelo import classificar_avaliacao

    a = _aval(modelo=_modelo(convergiu=False, backtest=_res(ret=100.0, dd=0.1)))

    assert classificar_avaliacao(a)[0] == "nao_convergiu"


# --------------------------------------------------------- T021 amostra (M9)

def test_amostra_insuficiente_em_qualquer_versao_e_inconclusiva():
    from backtesting.modelo import classificar_avaliacao
    from config.settings import EDGE_MIN_TRADES

    poucas = EDGE_MIN_TRADES - 1

    s1, m1 = classificar_avaliacao(_aval(
        modelo=_modelo(backtest=_res(trades=poucas)), regras=_res(trades=30)))
    s2, m2 = classificar_avaliacao(_aval(
        modelo=_modelo(backtest=_res(trades=30)), regras=_res(trades=poucas)))

    assert s1 == "inconclusivo" and "opera" in m1.lower()
    assert s2 == "inconclusivo" and "opera" in m2.lower()


def test_treino_pos_purga_insuficiente_e_inconclusivo():
    from backtesting.modelo import classificar_avaliacao

    a = _aval(modelo=_modelo(n_treino=5))

    status, motivo = classificar_avaliacao(a)

    assert status == "inconclusivo"
    assert "treino" in motivo.lower()


# ====================================== T028 embaralhamento preserva classes

def test_embaralhamento_preserva_a_distribuicao():
    """FR-007 — embaralhar destrói a associação atributo–rótulo, não a proporção
    entre classes. Alterar as proporções compararia duas coisas diferentes."""
    from backtesting.modelo import embaralhar_rotulos

    y = pd.Series([1] * 30 + [0] * 70)

    z = embaralhar_rotulos(y, semente=7)

    assert z.sum() == y.sum()
    assert len(z) == len(y)
    assert sorted(z.tolist()) == sorted(y.tolist())


def test_embaralhamento_destroi_a_associacao():
    from backtesting.modelo import embaralhar_rotulos

    y = pd.Series(list(range(2)) * 200)

    z = embaralhar_rotulos(y, semente=3)

    assert not z.equals(y), "uma permutacao identica nao seria linha de base"


def test_embaralhamento_e_reprodutivel():
    from backtesting.modelo import embaralhar_rotulos

    y = pd.Series([1] * 40 + [0] * 60)

    assert embaralhar_rotulos(y, semente=1).equals(embaralhar_rotulos(y, semente=1))


# ============================ T029 T030 sem_sinal e insuficiente (US3, P1)

def test_indistinguivel_do_embaralhado_e_sem_sinal():
    """FR-008 — o cenário mais importante da spec.

    Um classificador sempre encontra alguma estrutura. Se o mesmo modelo com
    rótulos permutados alcança o mesmo desempenho, o que se mediu foi capacidade
    de ajustar ruído, não sinal nos dados.
    """
    from backtesting.modelo import classificar_avaliacao

    bt = _res(ret=8.0, dd=6.0, expo=50.0, bh=5.0)
    a = _aval(modelo=_modelo(razao_decidido=0.60, backtest=bt),
              embaralhado=_modelo(razao_decidido=0.60, backtest=bt),
              regras=_res(ret=5.0, dd=10.0))

    status, motivo = classificar_avaliacao(a)

    assert status == "sem_sinal"
    assert status != "melhora"


def test_sinal_que_nao_paga_as_barreiras_e_insuficiente():
    """Estado novo neste registro. Distingue "não há sinal" de "há sinal e ele
    não paga as barreiras" — a segunda é o único achado positivo possível se
    H14 não for aprovada, e colapsá-la perderia isso."""
    from backtesting.modelo import classificar_avaliacao

    a = _aval(
        modelo=_modelo(razao_decidido=0.45, backtest=_res(ret=8.0, dd=6.0, bh=5.0)),
        embaralhado=_modelo(razao_decidido=0.30, backtest=_res(ret=1.0, dd=9.0, bh=5.0)),
        regras=_res(ret=5.0, dd=10.0))

    status, motivo = classificar_avaliacao(a)

    assert status == "insuficiente"
    assert "0,5" in motivo or "0.5" in motivo


def test_razao_de_empate_vem_das_barreiras_nao_de_escolha():
    """0,500 = sl_mult/tp_mult = 1,5/3,0. Não é limiar arbitrário."""
    from strategy.barreira_tripla import ParametrosBarreira

    assert ParametrosBarreira().razao_de_empate == pytest.approx(0.5)
    assert ParametrosBarreira(sl_mult=1.0, tp_mult=4.0).razao_de_empate == pytest.approx(0.25)


# --------------------------------------------------- T031 melhora exige tudo

def test_melhora_exige_superar_regras_embaralhado_e_a_razao_de_empate():
    from backtesting.modelo import classificar_avaliacao

    a = _com_validacao(_aval(
        modelo=_modelo(razao_decidido=0.65, backtest=_res(ret=14.0, dd=6.0, bh=5.0)),
        embaralhado=_modelo(razao_decidido=0.30, backtest=_res(ret=2.0, dd=9.0, bh=5.0)),
        regras=_res(ret=8.0, dd=10.0, bh=5.0)), 9.0, 4.0)

    assert classificar_avaliacao(a)[0] == "melhora"


def test_sem_confirmacao_fora_da_amostra_e_so_na_busca():
    from backtesting.modelo import classificar_avaliacao

    a = _com_validacao(_aval(
        modelo=_modelo(razao_decidido=0.65, backtest=_res(ret=14.0, dd=6.0, bh=5.0)),
        embaralhado=_modelo(razao_decidido=0.30, backtest=_res(ret=2.0, dd=9.0, bh=5.0)),
        regras=_res(ret=8.0, dd=10.0, bh=5.0)), 2.0, 9.0)

    assert classificar_avaliacao(a)[0] == "so_na_busca"


def test_regras_perdedoras_produzem_confundido():
    """Guarda M11 reusada."""
    from backtesting.modelo import classificar_avaliacao

    a = _com_validacao(_aval(
        modelo=_modelo(razao_decidido=0.65, backtest=_res(ret=-1.0, dd=6.0, bh=-10.0)),
        embaralhado=_modelo(razao_decidido=0.30, backtest=_res(ret=-8.0, dd=9.0, bh=-10.0)),
        regras=_res(ret=-5.0, dd=10.0, bh=-10.0)), -1.0, -4.0)

    assert classificar_avaliacao(a)[0] == "confundido"


def test_drawdown_maior_e_piora():
    from backtesting.modelo import classificar_avaliacao

    a = _aval(modelo=_modelo(razao_decidido=0.65, backtest=_res(ret=9.0, dd=14.0, bh=5.0)),
              embaralhado=_modelo(razao_decidido=0.30, backtest=_res(ret=1.0, dd=9.0, bh=5.0)),
              regras=_res(ret=8.0, dd=10.0, bh=5.0))

    assert classificar_avaliacao(a)[0] == "piora"


# ------------------------------------------------------------ T022 estimação

def _dados(n=800, semente=5, com_sinal=True):
    rng = np.random.default_rng(semente)
    X = pd.DataFrame({
        "volume_ratio": rng.normal(1.0, 0.3, n),
        "atr_ratio": rng.normal(0.02, 0.005, n),
        "adx": rng.normal(25.0, 8.0, n),
        "dist_ema_slow": rng.normal(0.0, 0.02, n),
        "macd": rng.normal(0.0, 0.005, n),
    })
    if com_sinal:
        z = 2.0 * X["dist_ema_slow"] / 0.02 - 1.0
        p = 1 / (1 + np.exp(-z))
        y = pd.Series(rng.binomial(1, p))
    else:
        y = pd.Series(rng.binomial(1, 0.3, n))
    return X, y


def test_estimacao_converge_em_dados_bem_condicionados():
    from backtesting.modelo import estimar

    X, y = _dados()

    m = estimar(X, y)

    assert m is not None
    assert len(m.params) == len(X.columns) + 1, "cinco atributos mais intercepto"


def test_estimacao_com_classe_unica_devolve_none():
    from backtesting.modelo import estimar

    X, _ = _dados()

    assert estimar(X, pd.Series([1] * len(X))) is None


def test_estimacao_com_atributo_constante_nao_explode():
    """Atributo constante não contribui e pode impedir a estimação. O caminho
    precisa ser explícito, não uma exceção vazando."""
    from backtesting.modelo import estimar

    X, y = _dados()
    X["adx"] = 25.0

    m = estimar(X, y)

    assert m is None or hasattr(m, "params")


# ================== limiar de decisão — lacuna achada por teste de mutação

def test_limiar_de_decisao_zera_a_expectativa():
    """A propriedade que define o limiar, não o número que ele calhou de dar.

    Entrar com probabilidade `p` de alvo tem expectativa `p·tp − (1−p)·sl`.
    O limiar é o `p` que zera isso. Testar apenas `== 1/3` deixaria passar uma
    fórmula invertida que também desse um número plausível — foi o que a
    mutação `tp/(sl+tp)` explorou.
    """
    from backtesting.modelo import limiar_de_decisao
    from strategy.barreira_tripla import ParametrosBarreira

    for sl, tp in ((1.5, 3.0), (1.0, 1.0), (2.0, 1.0), (0.5, 4.0)):
        p = ParametrosBarreira(sl_mult=sl, tp_mult=tp)
        limiar = limiar_de_decisao(p)

        expectativa = limiar * tp - (1 - limiar) * sl
        assert expectativa == pytest.approx(0.0, abs=1e-12), (sl, tp)


def test_limiar_de_decisao_dos_parametros_do_bot():
    from backtesting.modelo import limiar_de_decisao

    assert limiar_de_decisao() == pytest.approx(1 / 3)


def test_limiar_de_decisao_e_maior_que_a_taxa_base_observada():
    """23,4% dos eventos atingem o alvo ao acaso, contra um limiar de 33,3%.
    O modelo só opera onde consegue elevar a probabilidade acima do ponto de
    equilíbrio — se o limiar fosse menor que a taxa base, entrar sempre já
    passaria no critério."""
    from backtesting.modelo import limiar_de_decisao

    TAXA_BASE_MEDIDA = 0.234

    assert limiar_de_decisao() > TAXA_BASE_MEDIDA


def test_alvo_maior_reduz_o_limiar_de_decisao():
    """Monotonicidade: alvo mais distante exige menos probabilidade para
    compensar o mesmo stop."""
    from backtesting.modelo import limiar_de_decisao
    from strategy.barreira_tripla import ParametrosBarreira

    estreito = limiar_de_decisao(ParametrosBarreira(sl_mult=1.5, tp_mult=2.0))
    largo = limiar_de_decisao(ParametrosBarreira(sl_mult=1.5, tp_mult=6.0))

    assert largo < estreito


# ========= banda de incerteza no limiar — lacuna achada na execução real

def test_razao_acima_do_empate_por_ruido_nao_supera():
    """A estimativa pontual acima do limiar não basta.

    Medido na execução real: razão pooled de 0,5134 contra empate de 0,500,
    com 536 alvos e 1044 stops. Sob a hipótese de empate exato esperar-se-iam
    526,7 alvos, erro padrão 18,7 — a diferença é de meio erro padrão,
    p = 0,318. Comparar `0,5134 > 0,500` converteria ruído em aprovação.
    """
    from backtesting.modelo import supera_empate_com_confianca

    assert supera_empate_com_confianca(alvo=536, stop=1044) is False


def test_razao_folgadamente_acima_do_empate_supera():
    from backtesting.modelo import supera_empate_com_confianca

    # Mesma amostra, mas com vantagem grande: razao ~0,80.
    assert supera_empate_com_confianca(alvo=700, stop=880) is True


def test_amostra_minuscula_nunca_supera_por_falta_de_evidencia():
    """Três alvos e um stop dão razão 3,0, muito acima do empate — e não
    significam nada. A banda de incerteza precisa cobrir isso."""
    from backtesting.modelo import supera_empate_com_confianca

    assert supera_empate_com_confianca(alvo=3, stop=1) is False


def test_sem_decisoes_nao_supera():
    from backtesting.modelo import supera_empate_com_confianca

    assert supera_empate_com_confianca(alvo=0, stop=0) is False
