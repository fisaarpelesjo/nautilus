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


def estimate_slippage_pct(symbol: str, order_size_usdt: float, side: str = "buy") -> Optional[float]:
    """Slippage esperado de uma ordem a mercado de `order_size_usdt`, obtido
    caminhando o order book real -- consome os niveis a partir do melhor preco
    ate preencher a ordem e compara o preco medio de preenchimento com o topo
    do book.

    Existe porque `BACKTEST_SLIPPAGE_PCT` e uma constante unica (0,05%) aplicada
    a TODOS os pares: realista so para os mais liquidos. Em par de book fino o
    slippage real e ordens de grandeza maior, e medimos que a estrategia perde
    a vantagem inteira nessa faixa -- ou seja, a constante fixa nao era um
    detalhe, era o que fazia o resultado parecer melhor do que e.

    Retorna None quando o book nao pode ser lido ou nao tem profundidade para
    preencher a ordem inteira -- o chamador MUST tratar como desconhecido, nunca
    como zero.
    """
    try:
        book = fetch_order_book(symbol)
    except Exception as exc:
        log.warning(f"Falha ao buscar order book de {symbol} para estimar slippage: {exc}")
        return None

    levels = (book.get("asks") if side == "buy" else book.get("bids")) or []
    if not levels or levels[0][0] <= 0:
        return None

    best_price = levels[0][0]
    restante = order_size_usdt
    custo_total = 0.0
    qtd_total = 0.0
    for price, qty in levels:
        if price <= 0 or qty <= 0:
            continue
        valor_nivel = price * qty
        consumido = min(restante, valor_nivel)
        custo_total += consumido
        qtd_total += consumido / price
        restante -= consumido
        if restante <= 0:
            break

    if restante > 0 or qtd_total <= 0:
        # Book raso demais para a ordem inteira -- slippage real seria pior do
        # que qualquer numero que extrapolassemos daqui.
        return None

    preco_medio = custo_total / qtd_total
    return abs(preco_medio - best_price) / best_price


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
    # asks[0][0] <= 0 e checado tao explicitamente quanto bids[0][0] -- um best_ask
    # corrompido (0 ou negativo) faria spread_pct sair negativo, passando trivialmente
    # pelo limite MAX_SPREAD_PCT_ENTRY, e viraria limit_price de uma ordem real
    # (position_lifecycle.py) se USE_LIMIT_ORDERS estiver ligado (achado de auditoria).
    if not bids or not asks or bids[0][0] <= 0 or asks[0][0] <= 0:
        return LiquidityCheck(approved=False, reason="liquidez indisponivel", spread_pct=0.0, depth_usdt=0.0)

    best_bid = bids[0][0]
    best_ask = asks[0][0]
    spread_pct = (best_ask - best_bid) / best_bid
    # Profundidade util e so a alcancavel dentro do desvio de preco ja aceito
    # para esta entrada (MAX_SPREAD_PCT_ENTRY) -- niveis mais distantes do
    # melhor preco nunca seriam preenchidos a um preco que a propria checagem
    # de spread, logo abaixo, aceitaria. Antes desta checagem, a soma bruta
    # de todos os niveis do book podia aprovar profundidade "fantasma"
    # distante do preco. Ver specs/030-liquidez-proxima-preco/research.md D1.
    preco_limite = best_ask * (1 + MAX_SPREAD_PCT_ENTRY)
    depth_usdt = sum(price * qty for price, qty in asks if price <= preco_limite)

    if spread_pct > MAX_SPREAD_PCT_ENTRY:
        reason = f"spread {spread_pct * 100:.2f}% acima do limite {MAX_SPREAD_PCT_ENTRY * 100:.2f}%"
        return LiquidityCheck(approved=False, reason=reason, spread_pct=spread_pct, depth_usdt=depth_usdt, best_ask=best_ask)

    # Margem sobre o tamanho da propria ordem, alem do minimo configurado --
    # relevante quando o operador configura MIN_ORDERBOOK_DEPTH_USDT abaixo
    # de 3x MAX_ORDER_SIZE_USDT (o default ja usa esse mesmo fator).
    required_depth = max(MIN_ORDERBOOK_DEPTH_USDT, 3 * order_size_usdt)
    if depth_usdt < required_depth:
        reason = f"profundidade ${depth_usdt:.2f} perto do preco abaixo do minimo ${required_depth:.2f}"
        return LiquidityCheck(approved=False, reason=reason, spread_pct=spread_pct, depth_usdt=depth_usdt, best_ask=best_ask)

    return LiquidityCheck(approved=True, reason=None, spread_pct=spread_pct, depth_usdt=depth_usdt, best_ask=best_ask)
