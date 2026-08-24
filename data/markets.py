"""Mercados, perfis de custo e resolucao de simbolo (spec 023).

Um mercado determina tres coisas sobre um simbolo: qual fonte busca seus
candles, qual custo a simulacao aplica, e se o caminho de execucao ao vivo
pode opera-lo. Hoje apenas cripto e operavel -- os demais existem para
pesquisa (avaliar estrategias), nao para operacao.
"""
from dataclasses import dataclass
from typing import Optional

from config.settings import (
    BACKTEST_FEE_RATE,
    BACKTEST_SLIPPAGE_PCT,
    MARKET_COST_PROFILES,
)


@dataclass(frozen=True)
class CostProfile:
    """Custo de execucao de um mercado, usado pela simulacao.

    `source_note` nao e decorativo: mercados com corretagem fixa (acoes,
    futuros) sao representados aqui por um percentual equivalente ao tamanho de
    ordem configurado, e essa aproximacao precisa ficar registrada junto do
    numero -- e precisa para triagem, imprecisa para dimensionamento fino.
    """
    fee_rate: float
    slippage_pct: float
    source_note: str


@dataclass(frozen=True)
class Market:
    name: str
    source: str
    continuous: bool
    cost: Optional[CostProfile]
    tradable: bool


def _cost(market_name: str) -> Optional[CostProfile]:
    perfil = MARKET_COST_PROFILES.get(market_name)
    if perfil is None:
        return None
    return CostProfile(
        fee_rate=perfil["fee_rate"],
        slippage_pct=perfil["slippage_pct"],
        source_note=perfil["source_note"],
    )


# Cripto reusa BACKTEST_FEE_RATE/BACKTEST_SLIPPAGE_PCT diretamente em vez de
# duplicar os numeros: se divergissem, o backtest cripto mudaria de resultado
# ao passar por esta camada -- exatamente o que tests/test_crypto_no_regression.py
# existe para impedir.
_CRYPTO_COST = CostProfile(
    fee_rate=BACKTEST_FEE_RATE,
    slippage_pct=BACKTEST_SLIPPAGE_PCT,
    source_note="taxa e slippage de exchange cripto (BACKTEST_FEE_RATE/BACKTEST_SLIPPAGE_PCT)",
)

MARKETS = {
    "crypto":    Market("crypto",    "ccxt",     continuous=True,  cost=_CRYPTO_COST,        tradable=True),
    "stocks_us": Market("stocks_us", "yfinance", continuous=False, cost=_cost("stocks_us"),  tradable=False),
    "stocks_br": Market("stocks_br", "yfinance", continuous=False, cost=_cost("stocks_br"),  tradable=False),
    "forex":     Market("forex",     "yfinance", continuous=True,  cost=_cost("forex"),      tradable=False),
    "futures":   Market("futures",   "yfinance", continuous=False, cost=_cost("futures"),    tradable=False),
    "index":     Market("index",     "yfinance", continuous=False, cost=_cost("index"),      tradable=False),
}


def resolve_market(symbol: str) -> Market:
    """Deduz o mercado a partir do formato do simbolo.

    Ordem do mais especifico para o mais geral. Um simbolo nao resolvivel
    levanta ValueError em vez de cair num mercado padrao -- cair num padrao
    reproduziria o defeito do MIN_PRICE_USDT (spec 021), onde o simbolo parecia
    aceito e nunca operava de verdade.
    """
    if not symbol or not symbol.strip():
        raise ValueError("simbolo vazio nao pode ser resolvido para um mercado")

    s = symbol.strip()

    if "/" in s:
        if s.endswith("/USDT"):
            return MARKETS["crypto"]
        raise ValueError(
            f"simbolo com par '{s}' nao reconhecido -- apenas pares /USDT sao suportados em cripto"
        )
    if s.endswith(".SA"):
        return MARKETS["stocks_br"]
    if s.endswith("=X"):
        return MARKETS["forex"]
    if s.endswith("=F"):
        return MARKETS["futures"]
    if s.startswith("^"):
        return MARKETS["index"]
    if s.replace(".", "").replace("-", "").isalnum():
        return MARKETS["stocks_us"]

    raise ValueError(f"simbolo '{s}' nao corresponde a nenhum mercado conhecido")


def require_cost(market: Market) -> CostProfile:
    """Perfil de custo do mercado, ou ValueError se nao houver.

    FR-004: um mercado sem custo declarado MUST NOT herdar o de outro. Foi o
    mecanismo inverso disso -- slippage de par ultra-liquido aplicado a book
    fino -- que fez ACE/BIO/ALLO parecerem operaveis no backtest e entregarem
    prejuizo real em paper mode.
    """
    if market.cost is None:
        raise ValueError(
            f"mercado '{market.name}' nao tem perfil de custo declarado -- "
            "avaliar com o custo de outro mercado produziria numero que parece "
            "confiavel e nao e"
        )
    return market.cost
