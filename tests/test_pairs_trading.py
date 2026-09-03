import numpy as np
import pandas as pd
import pytest

from backtesting.pairs_trading import (
    ADF_DISPONIVEL,
    PairsParams,
    estimar_hedge_ratio,
    meia_vida_reversao,
    run_pairs_backtest,
    run_pairs_scan,
    selecionar_pares,
    split_treino_validacao,
)


def _passeio(n, semente, sigma=0.01, inicio=100.0):
    rng = np.random.default_rng(semente)
    return inicio * np.exp(np.cumsum(rng.normal(0, sigma, n)))


def _par_cointegrado(n=1500, meia_vida=20, semente=11):
    """B e passeio aleatorio; A segue B com spread AR(1) de meia-vida conhecida."""
    rng = np.random.default_rng(semente)
    b = _passeio(n, semente)
    lam = -np.log(2) / meia_vida
    sp = np.zeros(n)
    for t in range(1, n):
        sp[t] = sp[t - 1] + lam * sp[t - 1] + rng.normal(0, 0.02)
    return b * np.exp(sp), b


# A selecao de pares exige o portao ADF (statsmodels). Sem ele `teste_adf`
# devolve p=1,0 por falha fechada e nada e selecionado -- comportamento correto,
# mas que torna estes testes inaplicaveis. statsmodels e dependencia de pesquisa
# (requirements-dev.txt), ausente no ambiente de producao de proposito.
precisa_adf = pytest.mark.skipif(
    not ADF_DISPONIVEL,
    reason="requer statsmodels (requirements-dev.txt); ausente em producao",
)


def _df(serie, n=None):
    n = n or len(serie)
    idx = pd.date_range("2026-01-01", periods=n, freq="4h")
    return pd.DataFrame({"open": serie, "high": serie * 1.01,
                         "low": serie * 0.99, "close": serie}, index=idx)


def test_hedge_ratio_recupera_coeficiente_construido():
    rng = np.random.default_rng(3)
    b = rng.normal(0, 1, 500)
    a = 2.5 * b + rng.normal(0, 0.01, 500)

    assert estimar_hedge_ratio(a, b) == pytest.approx(2.5, abs=0.05)


def test_meia_vida_recupera_valor_construido():
    rng = np.random.default_rng(5)
    alvo = 20
    lam = -np.log(2) / alvo
    sp = np.zeros(4000)
    for t in range(1, len(sp)):
        sp[t] = sp[t - 1] + lam * sp[t - 1] + rng.normal(0, 0.05)

    assert meia_vida_reversao(sp) == pytest.approx(alvo, rel=0.35)


def test_meia_vida_sozinha_nao_separa_passeio_aleatorio():
    """Regressao do achado M8 (2026-09-01).

    O estimador OLS do coeficiente AR e enviesado para baixo (vies de
    Dickey-Fuller), entao passeio aleatorio recebe meia-vida FINITA, nao
    infinita. Este teste FIXA o defeito para que ninguem volte a usar a
    meia-vida como criterio unico de cointegracao.
    """
    finitas = sum(1 for s in range(30)
                  if np.isfinite(meia_vida_reversao(
                      np.cumsum(np.random.default_rng(s).normal(0, 1, 250)))))

    # A maioria esmagadora recebe meia-vida finita apesar de nao reverter.
    assert finitas >= 25


@precisa_adf
def test_a_selecao_rejeita_universo_de_passeios_aleatorios():
    """O portao ADF e o que separa; a meia-vida so mede negociabilidade.

    Taxa medida de falso positivo: 4,8% com ADF a alpha=0,05, contra 28% quando
    a selecao usava apenas a faixa de meia-vida.
    """
    p = PairsParams(formacao=250)
    selecionados = 0
    universos = 60
    for s in range(universos):
        rng = np.random.default_rng(s)
        d = pd.DataFrame({f"{c}/USDT": 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 300)))
                          for c in "ABC"})
        selecionados += len(selecionar_pares(d, p))

    # 3 combinacoes por universo; a 5% de alpha o esperado fica proximo de 5%.
    assert selecionados <= universos * 3 * 0.15


@precisa_adf
def test_selecao_encontra_o_par_cointegrado_e_o_ranqueia_primeiro():
    # Meia-vida 5 de proposito: e a faixa em que o ADF tem poder proximo de 100%
    # com formacao 250 (ver test_poder_do_seletor_e_baixo_para_reversao_lenta).
    a, b = _par_cointegrado(meia_vida=5)
    c = _passeio(1500, 99)
    precos = pd.DataFrame({"A/USDT": a, "B/USDT": b, "C/USDT": c})

    pares = selecionar_pares(precos, PairsParams(formacao=250))

    assert pares, "nenhum par selecionado"
    assert {pares[0].a, pares[0].b} == {"A/USDT", "B/USDT"}


@precisa_adf
def test_poder_do_seletor_e_baixo_para_reversao_lenta():
    """Limitacao medida, nao defeito: o ADF tem poder baixo em amostra curta.

    Taxa de deteccao de par cointegrado CONSTRUIDO, 30 sementes:

        meia-vida  5, formacao 250 -> 100%
        meia-vida 10, formacao 250 ->  70%
        meia-vida 20, formacao 250 ->  20%
        meia-vida 20, formacao 500 ->  60%

    Consequencia para a avaliacao de H10: com formacao 250 o seletor perde a
    maioria dos pares de reversao lenta. Um resultado negativo nessa
    configuracao nao distingue "nao ha vantagem" de "nao detectamos os pares".
    Este teste fixa a medicao para que a ressalva nao se perca.
    """
    def taxa(meia_vida, formacao, sementes=12):
        ok = 0
        for s in range(sementes):
            a, b = _par_cointegrado(n=max(1500, formacao * 3), meia_vida=meia_vida, semente=s)
            precos = pd.DataFrame({"A/USDT": a, "B/USDT": b})
            pares = selecionar_pares(precos, PairsParams(formacao=formacao))
            if pares:
                ok += 1
        return ok / sementes

    rapida = taxa(5, 250)
    lenta = taxa(20, 250)

    assert rapida >= 0.8, f"reversao rapida deveria ser detectada quase sempre: {rapida:.0%}"
    assert lenta < rapida, "o poder tem de cair com a meia-vida maior"


def test_selecao_respeita_a_faixa_de_meia_vida():
    a, b = _par_cointegrado(meia_vida=20)
    precos = pd.DataFrame({"A/USDT": a, "B/USDT": b})

    # Faixa que exclui a meia-vida construida: nada deve ser selecionado.
    fora = selecionar_pares(precos, PairsParams(formacao=250, meia_vida_min=200, meia_vida_max=400))
    assert fora == []


def test_selecao_nao_usa_informacao_futura():
    # `ate` limita a janela ao passado disponivel. Selecionar com a serie
    # inteira e o vies que faz pairs trading parecer excelente em backtest.
    a, b = _par_cointegrado()
    precos = pd.DataFrame({"A/USDT": a, "B/USDT": b})
    p = PairsParams(formacao=250)

    cedo = selecionar_pares(precos, p, ate=300)
    tarde = selecionar_pares(precos, p, ate=1400)

    # As duas chamadas veem janelas diferentes; a estimativa nao pode ser igual
    # por acaso de implementacao (o que indicaria que `ate` esta sendo ignorado).
    if cedo and tarde:
        assert cedo[0].hedge_ratio != tarde[0].hedge_ratio


@precisa_adf
def test_backtest_opera_o_par_cointegrado():
    a, b = _par_cointegrado()
    dados = {"A/USDT": _df(a), "B/USDT": _df(b)}

    r = run_pairs_backtest(dados, PairsParams(formacao=250))

    assert r.total_trades > 0
    assert r.final_capital != r.initial_capital


@precisa_adf
def test_custo_zerado_rende_mais_que_custo_real():
    a, b = _par_cointegrado()
    dados = {"A/USDT": _df(a), "B/USDT": _df(b)}
    p = PairsParams(formacao=250)

    com = run_pairs_backtest(dados, p)
    sem = run_pairs_backtest(dados, p, fee_rate=0.0, slippage_pct=0.0)

    assert sem.total_return_pct >= com.total_return_pct


def test_menos_de_dois_simbolos_devolve_resultado_vazio():
    r = run_pairs_backtest({"A/USDT": _df(_passeio(500, 1))}, PairsParams())

    assert r.total_trades == 0
    assert r.final_capital == r.initial_capital


def test_historico_menor_que_a_formacao_nao_estoura():
    a, b = _par_cointegrado(n=100)
    dados = {"A/USDT": _df(a, 100), "B/USDT": _df(b, 100)}

    r = run_pairs_backtest(dados, PairsParams(formacao=250))

    assert r.total_trades == 0


# ==================================================== spec 039 (reavaliar H10)
# T001-T004: split treino/validacao com corte de tempo compartilhado e
# aquecimento causal, e run_pairs_scan com o instrumento corrigido.

def test_split_treino_validacao_usa_corte_de_tempo_compartilhado():
    a, b = _par_cointegrado(n=1000)
    dados = {"A/USDT": _df(a, 1000), "B/USDT": _df(b, 1000)}

    treino, validacao = split_treino_validacao(dados, formacao=100, validation_ratio=0.3)

    # corte = int(1000*0.7) = 700; aquecimento comeca em 700-100=600.
    assert len(treino["A/USDT"]) == 700
    assert len(validacao["A/USDT"]) == 400  # 100 de aquecimento + 300 reais
    assert len(treino["B/USDT"]) == len(treino["A/USDT"])
    assert len(validacao["B/USDT"]) == len(validacao["A/USDT"])
    # Nenhuma sobreposicao ALEM do aquecimento declarado.
    assert treino["A/USDT"].index[-1] < validacao["A/USDT"].index[100]


@precisa_adf
def test_aquecimento_nao_conta_no_periodo_reportado_da_validacao():
    a, b = _par_cointegrado(n=1000, meia_vida=15)
    dados = {"A/USDT": _df(a, 1000), "B/USDT": _df(b, 1000)}
    formacao = 100

    _, validacao = split_treino_validacao(dados, formacao=formacao, validation_ratio=0.3)
    r = run_pairs_backtest(validacao, PairsParams(formacao=formacao), reselecionar_a_cada=formacao)

    # Nenhum trade pode abrir antes do candle 100 da fatia de validacao (o
    # inicio real, apos os 100 de aquecimento) -- run_pairs_backtest pula
    # exatamente os primeiros `formacao` candles do `dados` recebido.
    inicio_real = validacao["A/USDT"].index[formacao]
    assert all(t.entry_time >= inicio_real for t in r.trades)


def test_run_pairs_scan_usa_formacao_500_por_padrao(monkeypatch):
    from unittest.mock import MagicMock

    chamadas = []

    def fake_run_pairs_backtest(dados_, params_, **kwargs):
        chamadas.append((params_.formacao, kwargs.get("reselecionar_a_cada")))
        return MagicMock()

    import backtesting.pairs_trading as pt
    monkeypatch.setattr(pt, "run_pairs_backtest", fake_run_pairs_backtest)
    monkeypatch.setattr("backtesting.approval.evaluate_approval", lambda r: MagicMock())

    a, b = _par_cointegrado(n=1000)
    dados = {"A/USDT": _df(a, 1000), "B/USDT": _df(b, 1000)}

    pt.run_pairs_scan(pares=["A/USDT", "B/USDT"], dados=dados)

    assert len(chamadas) == 2  # treino + validacao
    for formacao, reselecionar in chamadas:
        assert formacao == 500
        assert reselecionar == 500


@precisa_adf
def test_run_pairs_scan_produz_resultado_aceito_por_evaluate_approval():
    from backtesting.approval import evaluate_approval

    a, b = _par_cointegrado(n=2000, meia_vida=15)
    dados = {"A/USDT": _df(a, 2000), "B/USDT": _df(b, 2000)}

    _, resultado_validacao, veredito = run_pairs_scan(
        pares=["A/USDT", "B/USDT"], params=PairsParams(formacao=300), dados=dados,
    )

    assert veredito is not None
    assert veredito.status in {"aprovado", "reprovado", "inconclusivo"}
    assert evaluate_approval(resultado_validacao).status == veredito.status


# ==================================== spec 052 (H10 universo amplo)

@precisa_adf
def test_selecao_e_monotonica_em_relacao_ao_universo():
    """Mais candidatos nunca pode reduzir o conjunto elegivel -- cada
    combinacao e avaliada de forma independente (`combinations(colunas, 2)`),
    entao um par que passa no universo pequeno continua passando quando mais
    colunas de ruido sao adicionadas; nada nas colunas novas pode fazer A-B
    parar de passar."""
    a, b = _par_cointegrado(meia_vida=5)
    ruido_base = _passeio(1500, 99)
    precos_base = pd.DataFrame({"A/USDT": a, "B/USDT": b, "C/USDT": ruido_base})

    ruido_extra = {f"{c}/USDT": _passeio(1500, 100 + i) for i, c in enumerate("DEFGHIJ")}
    precos_amplo = precos_base.assign(**ruido_extra)

    # max_pares alto o suficiente para nao truncar -- o invariante testado e
    # elegibilidade (cada combinacao e avaliada de forma independente), nao
    # ranking sob mais concorrencia (isso spec 052 nao depende).
    p = PairsParams(formacao=250, max_pares=100)
    pares_base = selecionar_pares(precos_base, p)
    pares_amplo = selecionar_pares(precos_amplo, p)

    achados_base = {frozenset((par.a, par.b)) for par in pares_base}
    achados_amplo = {frozenset((par.a, par.b)) for par in pares_amplo}

    assert frozenset(("A/USDT", "B/USDT")) in achados_base
    assert frozenset(("A/USDT", "B/USDT")) in achados_amplo
    assert achados_base <= achados_amplo  # universo amplo nunca perde o que o pequeno ja achava
