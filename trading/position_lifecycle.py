from typing import Optional

from config.settings import ATR_SL_MULTIPLIER, MAX_ORDER_SIZE_USDT, MAX_POSITIONS, MTF_TIMEFRAME, TRADING_MODE
from data.fetcher import fetch_balance, fetch_ohlcv
from execution.liquidity import LiquidityCheck, check_liquidity
from execution.order_manager import OrderManager
from risk.manager import calculate_risk, should_stop_loss, should_take_profit
from strategy.base import Signal


def handle_open_position(manager: OrderManager, symbol: str, pos, signal, current_price: float, row: dict, trade_events: list):
    if current_price > pos.highest_price and pos.atr > 0:
        new_trail = current_price - ATR_SL_MULTIPLIER * pos.atr
        if new_trail > pos.stop_loss:
            pos.highest_price = current_price
            pos.stop_loss = new_trail
            manager._persist_state_with_retry(f"ao ajustar trailing stop de {symbol}")
            row["decision"] = "trailing stop ajustado"

    if should_stop_loss(current_price, pos.stop_loss):
        _attempt_close(manager, symbol, pos, current_price, "Stop Loss", "stop loss", row, trade_events, cooldown="always")
    elif should_take_profit(current_price, pos.take_profit):
        _attempt_close(manager, symbol, pos, current_price, "Take Profit", "take profit", row, trade_events, cooldown="never")
    elif signal.signal == Signal.SELL:
        _attempt_close(manager, symbol, pos, current_price, "Sinal de venda", "sinal de venda", row, trade_events, cooldown="on_loss")


def _attempt_close(manager, symbol, pos, current_price, reason, label, row, trade_events, cooldown):
    # pnl/pnl_pct vem do retorno de close_position(), nao de um pre-calculo a
    # partir do preco de mercado bruto -- em paper mode o preco/custo real de
    # preenchimento (slippage + fee, ver execution/order_manager.py) diverge do
    # preco de mercado, entao um pre-calculo aqui ficaria dessincronizado do
    # pnl real gravado em data/trades.csv (achado de code-review da spec 010).
    result = manager.close_position(symbol, reason, current_price)
    if manager.has_position(symbol):
        # close_position pode falhar silenciosamente (ex: erro de rede em
        # live) e manter a posicao local de proposito -- ver
        # execution/order_manager.py _live_sell. Nao reportar como fechada.
        row["decision"] = f"fechamento falhou: {label} (posicao mantida para nova tentativa)"
        return
    pnl, pnl_pct_val = result
    if cooldown == "always" or (cooldown == "on_loss" and pnl < 0):
        manager.set_cooldown(symbol)
    row["in_pos"] = False
    row["decision"] = f"fechou: {label}"
    trade_events.append(("result", f"{label}  {symbol}", pnl, pnl_pct_val, _current_balance(manager)))


def handle_entry_candidate(
    manager: OrderManager,
    symbol: str,
    signal,
    indicators,
    current_price: float,
    strategy,
    row: dict,
    trade_events: list,
    new_entries: int,
    max_entries_per_cycle: int,
    killswitch_active: bool = False,
) -> bool:
    open_count = len(manager.positions)
    slots_left = MAX_POSITIONS - open_count
    blockers = []

    if signal.signal != Signal.BUY:
        return False
    if slots_left <= 0:
        blockers.append("sem slot")
    if new_entries >= max_entries_per_cycle:
        blockers.append("limite ciclo")
    if manager.is_daily_limit_hit():
        blockers.append("drawdown diario")
    if manager.is_weekly_limit_hit():
        blockers.append("limite semanal")
    if manager.is_monthly_limit_hit():
        blockers.append("limite mensal")
    if manager.circuit_breaker_active:
        blockers.append("circuit breaker")
    if killswitch_active:
        blockers.append("kill switch")
    if manager.is_in_cooldown(symbol):
        blockers.append("cooldown")

    if not blockers:
        row["mtf_checked"] = True
        row["mtf_ok"] = mtf_confirmed(symbol, current_price, strategy)
        if not row["mtf_ok"]:
            blockers.append("MTF negado")

    liquidity: Optional[LiquidityCheck] = None
    if not blockers:
        # Estimativa conservadora do tamanho da ordem (teto configurado, nao
        # o valor final) -- evita buscar o saldo (proxima checagem) so para
        # calcular o tamanho exato antes de saber se a liquidez ja bloqueia.
        # best_ask e reaproveitado como preco limite (US4) se USE_LIMIT_ORDERS
        # estiver ligado -- nao gasta uma segunda chamada de rede so pra isso.
        liquidity = check_liquidity(symbol, MAX_ORDER_SIZE_USDT)
        if not liquidity.approved:
            blockers.append(f"liquidez: {liquidity.reason}")

    current_balance = None
    if not blockers:
        # So busca o saldo se nenhum bloqueio mais barato (incluindo MTF) ja
        # descartou a entrada -- preserva a ordem original (MTF antes do
        # saldo) para nao gastar uma chamada de rede extra quando o MTF ja
        # bloqueia. Saldo desconhecido (falha ao buscar) MUST bloquear a
        # compra -- tratar como 0.0 mandaria uma ordem de quantidade zero de
        # verdade para a exchange (ver risk/manager.py calculate_risk).
        current_balance = _current_balance(manager)
        if current_balance is None:
            blockers.append("saldo indisponivel")

    if blockers:
        row["blockers"] = ", ".join(blockers)
        row["decision"] = "compra bloqueada: " + ", ".join(blockers)
        return False

    available = current_balance / slots_left
    atr = float(indicators.get("atr", 0) or 0)
    risk = calculate_risk(current_price, available, atr)
    limit_price = liquidity.best_ask if liquidity and liquidity.best_ask > 0 else None
    manager.open_long(symbol, risk, limit_price=limit_price)
    opened = manager.has_position(symbol)
    row["entry_opened"] = opened
    row["in_pos"] = opened
    if opened:
        row["decision"] = "compra aberta"
    elif symbol in manager.pending_limit_orders:
        row["decision"] = "ordem limit enviada: aguardando preenchimento"
    else:
        row["decision"] = "compra falhou: ordem nao abriu"
    if opened:
        trade_events.append(("buy", symbol, risk.entry_price, risk.quantity, risk.stop_loss, risk.take_profit))
    return opened


def mtf_confirmed(symbol: str, price: float, strategy) -> bool:
    """Confirma tendencia no timeframe maior. Falha FECHADA (bloqueia a entrada)
    em qualquer erro -- mesmo principio ja usado para saldo/liquidez desconhecidos
    neste arquivo; um candle MTF que nao pode ser buscado nao pode ser tratado
    como "tendencia confirmada" por omissao (achado de auditoria de codigo)."""
    try:
        df = fetch_ohlcv(symbol, MTF_TIMEFRAME)
        ind = strategy.calculate_indicators(df).iloc[-1]
        return price > ind["ema_trend"]
    except Exception:
        return False


def _current_balance(manager: OrderManager):
    """Saldo atual em USDT, paper ou live. Retorna None (nao 0.0) quando o
    saldo real nao pode ser obtido -- um saldo desconhecido nao pode ser
    exibido como "$0.00", que pareceria uma conta zerada de verdade."""
    if TRADING_MODE == "paper":
        return manager.paper_balance_usdt
    try:
        balance = fetch_balance()
        return float(balance.get("USDT", 0))
    except Exception:
        return None
