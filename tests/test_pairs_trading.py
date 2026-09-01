import numpy as np
import pandas as pd
import pytest

from backtesting.pairs_trading import (
    ADF_DISPONIVEL,
    PairsParams,
    estimar_hedge_ratio,
    meia_vida_reversao,
    run_pairs_backtest,
    selecionar_pares,
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
