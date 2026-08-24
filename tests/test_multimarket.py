"""Varredura multi-mercado com confirmacao fora da amostra (spec 023, T026-T028).

FR-012/013/014. Testar N estrategias x M simbolos faz algumas combinacoes
passarem POR ACASO -- com o profit factor mediano observado neste projeto, e
matematicamente esperado. O guarda-corpo escolhido pelo operador foi exigir que
a aprovacao se confirme numa janela que nao participou da descoberta.

O caso concreto que motivou: PETR4.SA apareceu com profit factor 6,13 em 4
trades na primeira medicao multi-mercado. Sem confirmacao fora da amostra, esse
numero entraria num relatorio parecendo uma descoberta.
"""

from backtesting import multimarket
from backtesting.engine import BacktestResult


def _resultado(trades=20, pf=2.0, ret=10.0, buy_hold=1.0, dd=2.0):
    """BacktestResult minimo com os campos que evaluate_approval() consulta."""
    return BacktestResult(
        trades=[], initial_capital=1000.0, final_capital=1000.0 * (1 + ret / 100),
        total_return_pct=ret, win_rate=50.0, total_trades=trades, max_drawdown_pct=dd,
        profit_factor=pf, expectancy=1.0, average_win=1.0, average_loss=-1.0,
        largest_win=1.0, largest_loss=-1.0, max_losing_streak=1, exposure_pct=10.0,
        sharpe=1.0, expectancy_pct=1.0, payoff_ratio=1.0, buy_hold_return_pct=buy_hold,
        edge_return_pct=ret - buy_hold, edge_score=10.0, sortino=1.0, calmar=1.0,
        annualized_return_pct=ret, return_per_exposure_pct=1.0,
    )


def test_aprovado_nas_duas_janelas_vira_confirmado():
    entrada = multimarket.classify(
        search=_resultado(pf=2.0), confirmation=_resultado(pf=2.0),
    )
    assert entrada == "confirmado"


def test_aprovado_so_na_busca_nao_e_apresentado_como_aprovado():
    # FR-014: o coracao do guarda-corpo. Passar onde foi descoberto nao e
    # evidencia -- e o resultado esperado de procurar bastante.
    entrada = multimarket.classify(
        search=_resultado(pf=2.0),                    # aprova
        confirmation=_resultado(pf=0.5, ret=-5.0),    # reprova
    )
    assert entrada == "so_na_busca"
    assert entrada != "confirmado"


def test_reprovado_nas_duas_janelas():
    entrada = multimarket.classify(
        search=_resultado(pf=0.5, ret=-5.0), confirmation=_resultado(pf=0.5, ret=-5.0),
    )
    assert entrada == "reprovado"


def test_sem_janela_de_confirmacao_e_inconclusivo():
    # FR-012: historico insuficiente para dividir MUST NOT aprovar por omissao.
    entrada = multimarket.classify(search=_resultado(pf=2.0), confirmation=None)
    assert entrada == "inconclusivo"


def test_contagem_de_combinacoes_e_registrada():
    # FR-013: uma aprovacao isolada entre 200 tentativas tem peso estatistico
    # diferente de uma entre 3. O relatorio precisa expor isso.
    resultado = multimarket.MultiMarketScanResult(combinations_tested=0, entries=[])
    for i in range(7):
        resultado.add(multimarket.ScanEntry(
            strategy_name="EMA/RSI", symbol=f"SYM{i}", market="stocks_us",
            search_result=_resultado(), confirmation_result=_resultado(), status="confirmado",
        ))

    assert resultado.combinations_tested == 7
    assert len(resultado.entries) == 7


def test_entrada_com_erro_nao_interrompe_a_varredura():
    # US3 cenario 2: um simbolo que falha ao buscar dados nao pode derrubar os
    # demais -- uma varredura de 40 simbolos que morre no terceiro e inutil.
    resultado = multimarket.MultiMarketScanResult(combinations_tested=0, entries=[])
    resultado.add(multimarket.ScanEntry(
        strategy_name="EMA/RSI", symbol="QUEBRADO", market=None,
        search_result=None, confirmation_result=None, status="erro",
        error="simbolo inexistente",
    ))
    resultado.add(multimarket.ScanEntry(
        strategy_name="EMA/RSI", symbol="AAPL", market="stocks_us",
        search_result=_resultado(), confirmation_result=_resultado(), status="confirmado",
    ))

    assert resultado.combinations_tested == 2
    assert [e.status for e in resultado.entries] == ["erro", "confirmado"]


def test_ranking_poe_confirmado_acima_de_so_na_busca():
    # Um resultado confirmado com numero modesto vale mais que um espetacular
    # que so passou onde foi descoberto.
    resultado = multimarket.MultiMarketScanResult(combinations_tested=0, entries=[])
    resultado.add(multimarket.ScanEntry(
        strategy_name="E", symbol="ESPETACULAR", market="stocks_us",
        search_result=_resultado(pf=9.0, ret=80.0), confirmation_result=_resultado(pf=0.3, ret=-9.0),
        status="so_na_busca",
    ))
    resultado.add(multimarket.ScanEntry(
        strategy_name="E", symbol="MODESTO", market="stocks_us",
        search_result=_resultado(pf=1.4, ret=3.0), confirmation_result=_resultado(pf=1.3, ret=2.0),
        status="confirmado",
    ))

    ordenado = resultado.ranked()

    assert ordenado[0].symbol == "MODESTO"
    assert ordenado[1].symbol == "ESPETACULAR"
