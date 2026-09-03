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


# ==================================================== spec 034 (H17) — T001
# Regressao: avaliar_par() SEM os parametros novos (atributos/
# extrair_atributos_fn) MUST continuar produzindo exatamente o resultado
# de hoje -- e a garantia que torna aceitavel tocar codigo que ja produziu
# o resultado publicado de H14. Valores capturados rodando o codigo ANTES
# da parametrizacao (D4, specs/034-sinais-onchain/research.md).

def _serie_onchain_regressao(n=1200, semente=7):
    rng = np.random.default_rng(semente)
    preco = 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.03, n)))
    idx = pd.date_range("2024-01-01", periods=n, freq="4h")
    return pd.DataFrame({
        "open": preco, "close": preco, "high": preco * 1.03,
        "low": preco * 0.97, "volume": np.full(n, 1000.0),
    }, index=idx)


def test_avaliar_par_sem_parametros_novos_reproduz_resultado_atual():
    from backtesting.modelo import avaliar_par

    df = _serie_onchain_regressao()
    a = avaliar_par("BTC/USDT", df=df)

    assert a.status == "inconclusivo"
    assert a.motivo == "versao modelo com 0 operacoes, abaixo do minimo de 10"
    assert a.n_purgadas == 10
    assert a.n_embargadas == 13
    assert a.modelo.n_treino == 782
    assert a.modelo.n_teste == 346
    assert a.modelo.convergiu is True
    assert a.modelo.razao_chances_geral == pytest.approx(0.6411764705882353)
    assert sorted(a.modelo.coeficientes.keys()) == sorted(
        ["const", "volume_ratio", "atr_ratio", "adx", "dist_ema_slow", "macd"]
    )
    assert a.modelo.coeficientes["atr_ratio"] == pytest.approx(-226.6898, abs=0.01)


# ============================================== spec 037 (motor de carteira)
# T001/T002: `retornar_previsao` expoe a previsao de teste ja calculada
# internamente, sem retreinar -- e o default preserva o resultado publicado
# byte a byte (D2, specs/037-motor-carteira-h14/research.md).

def test_avaliar_par_retornar_previsao_expoe_a_mesma_probabilidade_ja_calculada():
    """Reconstroi a probabilidade manualmente (sigmoide sobre os coeficientes
    ja publicados em `a.modelo.coeficientes`) e confirma que bate com
    `previsao_teste` -- prova que nao ha retreino nem formula duplicada."""
    import numpy as np

    from backtesting.horizonte import preparar
    from backtesting.modelo import ATRIBUTOS, avaliar_par, extrair_atributos
    from strategy.ema_rsi import EmaRsiStrategy

    df = _serie_onchain_regressao()
    a = avaliar_par("BTC/USDT", df=df, retornar_previsao=True)

    assert isinstance(a.previsao_teste, pd.Series)
    assert len(a.previsao_teste) == a.modelo.n_teste
    assert a.previsao_teste.index.is_monotonic_increasing

    prep = preparar(df, EmaRsiStrategy())
    x_teste = extrair_atributos(prep).loc[a.previsao_teste.index, ATRIBUTOS]
    coef = a.modelo.coeficientes
    z = coef["const"] + sum(x_teste[c] * coef[c] for c in ATRIBUTOS)
    prob_manual = 1.0 / (1.0 + np.exp(-z))

    assert a.previsao_teste.values == pytest.approx(prob_manual.values, abs=1e-9)


def test_avaliar_par_sem_retornar_previsao_reproduz_resultado_atual():
    """Regressao: `retornar_previsao=False` (default) MUST continuar
    produzindo exatamente o resultado ja publicado, e `previsao_teste`
    MUST ficar `None` -- mesmos valores de referencia de
    `test_avaliar_par_sem_parametros_novos_reproduz_resultado_atual`."""
    from backtesting.modelo import avaliar_par

    df = _serie_onchain_regressao()
    a = avaliar_par("BTC/USDT", df=df)

    assert a.previsao_teste is None
    assert a.status == "inconclusivo"
    assert a.motivo == "versao modelo com 0 operacoes, abaixo do minimo de 10"
    assert a.n_purgadas == 10
    assert a.n_embargadas == 13
    assert a.modelo.n_treino == 782
    assert a.modelo.n_teste == 346
    assert a.modelo.convergiu is True
    assert a.modelo.razao_chances_geral == pytest.approx(0.6411764705882353)


def test_avaliar_par_aceita_atributos_customizados_sem_quebrar_default():
    """Confirma que os parametros novos existem e mudam o comportamento
    apenas quando passados explicitamente -- nunca por efeito colateral."""
    from backtesting.modelo import ATRIBUTOS, avaliar_par, extrair_atributos

    df = _serie_onchain_regressao()

    a_default = avaliar_par("BTC/USDT", df=df)
    a_explicito = avaliar_par("BTC/USDT", df=df, atributos=ATRIBUTOS,
                              extrair_atributos_fn=extrair_atributos)

    assert a_default.status == a_explicito.status
    assert a_default.modelo.coeficientes == a_explicito.modelo.coeficientes


# ==================================== spec 049 (H20 backtest real) — T001

def test_avaliar_par_propaga_geometria_ao_backtest_real(monkeypatch):
    """A geometria usada para rotular/treinar (ParametrosBarreira) MUST chegar
    ao backtest real das linhas de base que decidem pelo MODELO (modelo,
    embaralhado, custo de giro) -- antes desta correcao, essas chamadas sempre
    saiam aos multiplicadores fixos de producao, independente do tp_mult/
    sl_mult declarado (achado de auditoria, specs/049-h20-backtest-real/
    spec.md). A linha de base de REGRAS continua nos multiplicadores de
    producao de proposito -- ela nao usa geometria de barreira alguma, sempre
    espelha o que o bot realmente operaria."""
    import backtesting.engine as engine_mod
    from backtesting.modelo import avaliar_par
    from strategy.barreira_tripla import ParametrosBarreira

    capturados = []
    original = engine_mod.simulate_backtest

    def _spy(*args, **kwargs):
        capturados.append((kwargs.get("atr_tp_multiplier"), kwargs.get("atr_sl_multiplier")))
        return original(*args, **kwargs)

    monkeypatch.setattr(engine_mod, "simulate_backtest", _spy)

    # n=2000/semente=7: fixture onde a estimacao converge tambem sob tp=2.0 --
    # a serie padrao de 1200 candles produz matriz singular com esta geometria.
    df = _serie_onchain_regressao(n=2000, semente=7)
    a = avaliar_par("BTC/USDT", params=ParametrosBarreira(tp_mult=2.0, sl_mult=1.5), df=df)

    assert a.modelo is not None and a.modelo.convergiu
    assert (2.0, 1.5) in capturados, capturados


def test_avaliar_par_default_propaga_multiplicadores_de_producao(monkeypatch):
    """params=None MUST propagar exatamente os multiplicadores de producao --
    o comportamento antigo (sem propagacao alguma) e este (propagando o default,
    que ja coincide) sao indistinguiveis, o que torna a correcao retrocompativel
    por construcao (FR-002)."""
    import backtesting.engine as engine_mod
    from backtesting.modelo import avaliar_par
    from config.settings import ATR_SL_MULTIPLIER, ATR_TP_MULTIPLIER

    capturados = []
    original = engine_mod.simulate_backtest

    def _spy(*args, **kwargs):
        capturados.append((kwargs.get("atr_tp_multiplier"), kwargs.get("atr_sl_multiplier")))
        return original(*args, **kwargs)

    monkeypatch.setattr(engine_mod, "simulate_backtest", _spy)

    df = _serie_onchain_regressao()
    avaliar_par("BTC/USDT", df=df)

    assert capturados
    assert all(tp == ATR_TP_MULTIPLIER and sl == ATR_SL_MULTIPLIER for tp, sl in capturados), capturados


# ==================================== spec 051 (H20 decomposicao de custo)

def test_avaliar_par_decompoe_custo_em_taxa_e_slippage(monkeypatch):
    """Bloco E6 (custo de giro) MUST produzir tres variantes sem custo, cada
    uma zerando so um parametro por vez -- retorno_sem_custo_modelo (os dois
    zerados, ja existente), retorno_sem_slippage_modelo (so slippage zerado,
    taxa real) e retorno_sem_taxa_modelo (so taxa zerada, slippage real)."""
    import backtesting.engine as engine_mod
    from backtesting.modelo import avaliar_par
    from config.settings import BACKTEST_FEE_RATE, BACKTEST_SLIPPAGE_PCT
    from strategy.barreira_tripla import ParametrosBarreira

    capturados = []
    original = engine_mod.simulate_backtest

    def _spy(*args, **kwargs):
        capturados.append((kwargs.get("fee_rate"), kwargs.get("slippage_pct")))
        return original(*args, **kwargs)

    monkeypatch.setattr(engine_mod, "simulate_backtest", _spy)

    # n=2000/semente=7: mesmo fixture de spec 049 onde a estimacao converge
    # tambem sob tp=2.0.
    df = _serie_onchain_regressao(n=2000, semente=7)
    a = avaliar_par("BTC/USDT", params=ParametrosBarreira(tp_mult=2.0, sl_mult=1.5), df=df)

    assert a.modelo is not None and a.modelo.convergiu
    assert a.retorno_sem_custo_modelo is not None
    assert a.retorno_sem_slippage_modelo is not None
    assert a.retorno_sem_taxa_modelo is not None

    # kwargs.get(...) so enxerga o que foi passado EXPLICITAMENTE -- None
    # significa que a chamada usou o default real da funcao (fee/slippage de
    # producao), nao que o valor seja zero.
    assert (0.0, 0.0) in capturados  # sem_custo: os dois explicitos
    assert (None, 0.0) in capturados  # sem_slippage: so slippage explicito, taxa no default real
    assert (0.0, None) in capturados  # sem_taxa: so taxa explicita, slippage no default real
    assert BACKTEST_FEE_RATE > 0 and BACKTEST_SLIPPAGE_PCT > 0  # confirma que os defaults nao sao zero


def test_avaliar_par_default_retorno_sem_custo_modelo_inalterado():
    """FR-002 -- a decomposicao e aditiva, retorno_sem_custo_modelo continua
    exatamente como antes (regressao)."""
    from backtesting.modelo import avaliar_par

    df = _serie_onchain_regressao(n=2000, semente=11)
    a = avaliar_par("BTC/USDT", df=df)

    if a.modelo is not None and a.modelo.convergiu:
        assert a.retorno_sem_custo_modelo is not None
