"""Contratos futuros com vencimento fixo (trimestrais) da Binance --
fonte de dados para H23 (prêmio de futuros vs funding perpétuo,
`specs/059-h23-futuros-trimestrais/`). Reusa a exchange futures já
instanciada por `data/funding.py` (mesmo `defaultType=future`) e a
exchange spot de `data/fetcher.py` -- nenhuma instância nova de ccxt.
"""
from typing import Dict, List, Sequence

from data.fetcher import get_exchange
from data.funding import _get_futures_exchange


def listar_contratos_trimestrais(bases: Sequence[str] = ("BTC", "ETH"),
                                  quote: str = "USDT") -> List[Dict]:
    """Contratos futuros com vencimento fixo (não perpétuos) para as
    bases pedidas, cotados em `quote`. Devolve lista ordenada por
    vencimento -- vazia se nenhum contrato existir para o par
    base/quote pedido (ex.: quote diferente de USDT)."""
    exchange = _get_futures_exchange()
    markets = exchange.load_markets()
    contratos = [
        {
            "symbol": m["symbol"],
            "base": m["base"],
            "expiry_ms": m["expiry"],
            "expiry_datetime": m["expiryDatetime"],
        }
        for m in markets.values()
        if m.get("type") == "future" and m.get("contract") and not m.get("swap")
        and m.get("quote") == quote and m.get("base") in bases and m.get("expiry")
    ]
    return sorted(contratos, key=lambda c: c["expiry_ms"])


def fetch_basis_snapshot(contrato: Dict) -> Dict:
    """Preço atual do contrato futuro + preço spot correspondente + dias
    até o vencimento. Instantâneo -- não há histórico contínuo de
    contratos já vencidos (diferente de funding rate; limitação
    declarada em `research.md` D2)."""
    futures_exchange = _get_futures_exchange()
    spot_exchange = get_exchange()

    par_spot = f"{contrato['base']}/USDT"
    preco_futuro = futures_exchange.fetch_ticker(contrato["symbol"])["last"]
    preco_spot = spot_exchange.fetch_ticker(par_spot)["last"]

    agora_ms = futures_exchange.milliseconds()
    dias_ate_vencimento = (contrato["expiry_ms"] - agora_ms) / (1000 * 60 * 60 * 24)

    return {
        "par": par_spot,
        "symbol": contrato["symbol"],
        "expiry_datetime": contrato["expiry_datetime"],
        "dias_ate_vencimento": dias_ate_vencimento,
        "preco_futuro": preco_futuro,
        "preco_spot": preco_spot,
    }
