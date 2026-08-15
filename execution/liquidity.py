from dataclasses import dataclass
from typing import Optional

from config.settings import MAX_SPREAD_PCT_ENTRY, MIN_ORDERBOOK_DEPTH_USDT
from data.fetcher import fetch_order_book
from utils.logger import get_logger

log = get_logger("liquidity")


@dataclass
class LiquidityCheck:
    approved: bool
    reason: Optional[str]
    spread_pct: float
    depth_usdt: float
    best_ask: float = 0.0


def check_liquidity(symbol: str, order_size_usdt: float) -> LiquidityCheck:
    """Bloqueia entradas com spread alto ou profundidade insuficiente no lado
    ask do order book. Falha de rede vira bloqueio conservador ("liquidez
    indisponivel"), nunca aprovacao por omissao -- mesmo principio ja usado
    para saldo desconhecido em trading/position_lifecycle.py."""
    try:
        book = fetch_order_book(symbol)
    except Exception as exc:
        log.warning(f"Falha ao buscar order book de {symbol}: {exc}")
        return LiquidityCheck(approved=False, reason="liquidez indisponivel", spread_pct=0.0, depth_usdt=0.0)

    bids = book.get("bids") or []
    asks = book.get("asks") or []
    if not bids or not asks or bids[0][0] <= 0:
        return LiquidityCheck(approved=False, reason="liquidez indisponivel", spread_pct=0.0, depth_usdt=0.0)

    best_bid = bids[0][0]
    best_ask = asks[0][0]
    spread_pct = (best_ask - best_bid) / best_bid
    depth_usdt = sum(price * qty for price, qty in asks)

    if spread_pct > MAX_SPREAD_PCT_ENTRY:
        reason = f"spread {spread_pct * 100:.2f}% acima do limite {MAX_SPREAD_PCT_ENTRY * 100:.2f}%"
        return LiquidityCheck(approved=False, reason=reason, spread_pct=spread_pct, depth_usdt=depth_usdt, best_ask=best_ask)

    # Margem sobre o tamanho da propria ordem, alem do minimo configurado --
    # relevante quando o operador configura MIN_ORDERBOOK_DEPTH_USDT abaixo
    # de 3x MAX_ORDER_SIZE_USDT (o default ja usa esse mesmo fator).
    required_depth = max(MIN_ORDERBOOK_DEPTH_USDT, 3 * order_size_usdt)
    if depth_usdt < required_depth:
        reason = f"profundidade ${depth_usdt:.2f} abaixo do minimo ${required_depth:.2f}"
        return LiquidityCheck(approved=False, reason=reason, spread_pct=spread_pct, depth_usdt=depth_usdt, best_ask=best_ask)

    return LiquidityCheck(approved=True, reason=None, spread_pct=spread_pct, depth_usdt=depth_usdt, best_ask=best_ask)
