"""Registro de fontes de dados OHLCV (spec 023).

Uma fonte atende um ou mais mercados. `data/fetcher.py::fetch_ohlcv` resolve o
mercado do simbolo e delega a fonte correspondente, de modo que os consumidores
nao saibam qual respondeu.

Contrato completo em specs/023-dados-multi-mercado/contracts/data-source.md.
"""
from typing import Protocol

import pandas as pd


class DataSource(Protocol):
    """Contrato uniforme de fonte.

    Implementacoes MUST devolver DataFrame com indice DatetimeIndex crescente
    sem duplicatas e colunas minusculas open/high/low/close/volume, e MUST
    levantar excecao quando nao puderem atender -- nunca DataFrame vazio ou
    parcial silencioso.
    """

    name: str

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        ...


def get_source(market_name: str) -> DataSource:
    """Fonte que atende `market_name`.

    Import tardio de proposito: `ccxt_source` importa ccxt e `yfinance_source`
    importa yfinance, ambos pesados. Importar os dois no topo faria o loop de
    producao (que so usa ccxt) carregar yfinance a cada arranque sem precisar.
    """
    from data.markets import MARKETS

    market = MARKETS.get(market_name)
    if market is None:
        raise ValueError(f"mercado '{market_name}' nao registrado -- nao ha fonte para resolver")

    if market.source == "ccxt":
        from data.sources.ccxt_source import CcxtSource
        return CcxtSource()
    if market.source == "yfinance":
        from data.sources.yfinance_source import YFinanceSource
        return YFinanceSource()

    raise ValueError(f"fonte '{market.source}' do mercado '{market_name}' nao tem implementacao")
