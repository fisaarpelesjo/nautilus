"""Resolucao simbolo -> mercado e perfis de custo (spec 023, T004/T022/T023)."""
import pytest

from data import markets


@pytest.mark.parametrize("simbolo,esperado", [
    ("BTC/USDT", "crypto"),
    ("ETH/USDT", "crypto"),
    ("PETR4.SA", "stocks_br"),
    ("VALE3.SA", "stocks_br"),
    ("EURUSD=X", "forex"),
    ("USDBRL=X", "forex"),
    ("ES=F", "futures"),
    ("CL=F", "futures"),
    ("^GSPC", "index"),
    ("^BVSP", "index"),
    ("AAPL", "stocks_us"),
    ("MSFT", "stocks_us"),
])
def test_resolve_mercado_pelo_formato_do_simbolo(simbolo, esperado):
    assert markets.resolve_market(simbolo).name == esperado


def test_simbolo_nao_resolvivel_falha_explicitamente():
    # Cair num mercado padrao seria o mesmo erro do MIN_PRICE_USDT (spec 021):
    # o simbolo parece aceito e nunca funciona de verdade.
    for invalido in ["", "   ", "BTC/EUR", "!!!"]:
        with pytest.raises(ValueError):
            markets.resolve_market(invalido)


def test_apenas_cripto_e_operavel():
    # tradable=True habilita o caminho de execucao. Hoje so cripto tem
    # execucao implementada -- FR-007.
    assert markets.resolve_market("BTC/USDT").tradable is True
    for nao_operavel in ["AAPL", "PETR4.SA", "EURUSD=X", "ES=F", "^GSPC"]:
        assert markets.resolve_market(nao_operavel).tradable is False


def test_continuidade_por_mercado():
    # Mercado descontinuo tem gap de abertura, onde o teto de perda por trade
    # nao age -- FR-009.
    assert markets.resolve_market("BTC/USDT").continuous is True
    assert markets.resolve_market("EURUSD=X").continuous is True
    for com_gap in ["AAPL", "PETR4.SA", "ES=F", "^GSPC"]:
        assert markets.resolve_market(com_gap).continuous is False


def test_cada_mercado_tem_fonte_declarada():
    assert markets.resolve_market("BTC/USDT").source == "ccxt"
    for nao_cripto in ["AAPL", "PETR4.SA", "EURUSD=X", "ES=F", "^GSPC"]:
        assert markets.resolve_market(nao_cripto).source == "yfinance"


# --------------------------------------------------------------- perfis de custo

def test_todo_mercado_tem_perfil_de_custo():
    for simbolo in ["BTC/USDT", "AAPL", "PETR4.SA", "EURUSD=X", "ES=F", "^GSPC"]:
        custo = markets.resolve_market(simbolo).cost
        assert custo is not None
        assert custo.fee_rate >= 0
        assert custo.slippage_pct >= 0
        # source_note documenta o que o numero aproxima -- auditabilidade (FR-011)
        assert custo.source_note


def test_mercado_sem_perfil_de_custo_e_recusado():
    # FR-004: MUST NOT cair no custo de cripto por omissao. Foi exatamente esse
    # mecanismo (custo de par liquido aplicado a book fino) que fez ACE/BIO/ALLO
    # parecerem operaveis e entregarem prejuizo real.
    sem_custo = markets.Market(
        name="mercado_ficticio", source="yfinance",
        continuous=False, cost=None, tradable=False,
    )

    with pytest.raises(ValueError, match="custo"):
        markets.require_cost(sem_custo)


def test_require_cost_devolve_o_perfil_quando_definido():
    mercado = markets.resolve_market("AAPL")
    assert markets.require_cost(mercado) is mercado.cost


def test_custo_de_cripto_bate_com_a_config_existente():
    # O perfil de cripto MUST refletir BACKTEST_FEE_RATE/BACKTEST_SLIPPAGE_PCT
    # ja usados, senao o backtest cripto mudaria de resultado -- que e
    # exatamente o que test_crypto_no_regression.py proibe.
    from config.settings import BACKTEST_FEE_RATE, BACKTEST_SLIPPAGE_PCT

    custo = markets.resolve_market("BTC/USDT").cost
    assert custo.fee_rate == BACKTEST_FEE_RATE
    assert custo.slippage_pct == BACKTEST_SLIPPAGE_PCT
