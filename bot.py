import time
from datetime import datetime
from typing import Dict
from config.settings import PAIRS, TIMEFRAME, TRADING_MODE, MAX_POSITIONS, MTF_TIMEFRAME, ATR_SL_MULTIPLIER, DAILY_REPORT_HOUR
from data.fetcher import fetch_ohlcv, fetch_balance
from data.trade_logger import log_signal, save_ohlcv
from strategy.ema_rsi import EmaRsiStrategy
from strategy.base import Signal
from risk.manager import calculate_risk, should_stop_loss, should_take_profit
from execution.order_manager import OrderManager
from utils.display import (
    console, header, spinner, pairs_table,
    trade_result, waiting, error, buy_opened, shutdown
)
from utils.notifier import send_telegram
from utils.logger import get_logger, log_event

log = get_logger("bot")
POLL_INTERVAL = 60
MAX_ENTRIES_PER_CYCLE = 1

def _round_price(p: float) -> float:
    if p >= 1:    return round(p, 4)
    if p >= 0.01: return round(p, 6)
    return round(p, 10)

def run():
    header()

    strategy          = EmaRsiStrategy()
    manager           = OrderManager()
    last_report_date  = ""
    last_signals: Dict[str, str] = {}

    send_telegram(f"Bot iniciado | {len(PAIRS)} pares | Modo={TRADING_MODE}")

    while True:
        try:
            pair_rows    = []
            trade_events = []
            new_entries  = 0

            with spinner("atualizando pares..."):
                for symbol in PAIRS:
                    try:
                        df            = fetch_ohlcv(symbol, TIMEFRAME)
                        signal        = strategy.generate_signal(df)
                        indicators    = strategy.calculate_indicators(df).iloc[-1]
                        current_price = signal.price

                        save_ohlcv(symbol, TIMEFRAME, df)

                        # Fix 1: só loga quando o sinal muda
                        if signal.signal.value != last_signals.get(symbol):
                            log_signal({
                                "timestamp": datetime.now().isoformat(),
                                "symbol":    symbol,
                                "timeframe": TIMEFRAME,
                                "price":     _round_price(current_price),
                                "signal":    signal.signal.value,
                                "ema_fast":  _round_price(float(indicators["ema_fast"])),
                                "ema_slow":  _round_price(float(indicators["ema_slow"])),
                                "ema_trend": _round_price(float(indicators["ema_trend"])),
                                "rsi":       round(float(indicators["rsi"]), 4),
                                "macd":      round(float(indicators["macd"]), 6),
                                "reason":    signal.reason,
                            })
                            last_signals[symbol] = signal.signal.value

                        pos = manager.get_position(symbol)
                        pnl_pct = None
                        if pos:
                            pnl_pct = (current_price - pos.entry_price) / pos.entry_price * 100

                        pair_rows.append({
                            "symbol":    symbol,
                            "price":     current_price,
                            "signal":    signal.signal.value,
                            "rsi":       indicators["rsi"],
                            "ema_fast":  indicators["ema_fast"],
                            "ema_slow":  indicators["ema_slow"],
                            "in_pos":    pos is not None,
                            "pnl_pct":   pnl_pct,
                        })

                        if pos:
                            if current_price > pos.highest_price and pos.atr > 0:
                                new_trail = current_price - ATR_SL_MULTIPLIER * pos.atr
                                if new_trail > pos.stop_loss:
                                    pos.highest_price = current_price
                                    pos.stop_loss     = new_trail
                                    manager._persist_state()

                            if should_stop_loss(current_price, pos.stop_loss):
                                pnl         = (current_price - pos.entry_price) * pos.quantity
                                pnl_pct_val = (current_price - pos.entry_price) / pos.entry_price * 100
                                manager.close_position(symbol, "Stop Loss", current_price)
                                manager.set_cooldown(symbol)
                                trade_events.append(("result", f"stop loss  {symbol}", pnl, pnl_pct_val, manager.paper_balance_usdt))

                            elif should_take_profit(current_price, pos.take_profit):
                                pnl         = (current_price - pos.entry_price) * pos.quantity
                                pnl_pct_val = (current_price - pos.entry_price) / pos.entry_price * 100
                                manager.close_position(symbol, "Take Profit", current_price)
                                trade_events.append(("result", f"take profit  {symbol}", pnl, pnl_pct_val, manager.paper_balance_usdt))

                            elif signal.signal == Signal.SELL:
                                pnl         = (current_price - pos.entry_price) * pos.quantity
                                pnl_pct_val = (current_price - pos.entry_price) / pos.entry_price * 100
                                manager.close_position(symbol, "Sinal de venda", current_price)
                                # Fix 2: cooldown também após saída por sinal com prejuízo
                                if pnl < 0:
                                    manager.set_cooldown(symbol)
                                trade_events.append(("result", f"sinal de venda  {symbol}", pnl, pnl_pct_val, manager.paper_balance_usdt))

                        else:
                            open_count = len(manager.positions)
                            slots_left = MAX_POSITIONS - open_count
                            # Fix 3: máximo de MAX_ENTRIES_PER_CYCLE novas entradas por ciclo
                            if (signal.signal == Signal.BUY
                                    and slots_left > 0
                                    and new_entries < MAX_ENTRIES_PER_CYCLE
                                    and not manager.is_daily_limit_hit()
                                    and not manager.is_in_cooldown(symbol)
                                    and _mtf_confirmed(symbol, current_price, strategy)):
                                if TRADING_MODE == "paper":
                                    available = manager.paper_balance_usdt / slots_left
                                else:
                                    available = _get_usdt_balance() / slots_left
                                atr  = float(indicators.get("atr", 0) or 0)
                                risk = calculate_risk(current_price, available, atr)
                                manager.open_long(symbol, risk)
                                new_entries += 1
                                trade_events.append(("buy", symbol, risk.entry_price, risk.quantity, risk.stop_loss, risk.take_profit))

                    except Exception as e:
                        log.error(f"{symbol}: {e}")
                        log_event("pair_cycle_error", mode=TRADING_MODE, symbol=symbol, error=str(e))
                        pair_rows.append({
                            "symbol":   symbol,
                            "price":    0,
                            "signal":   "ERR",
                            "rsi":      0,
                            "ema_fast": 0,
                            "ema_slow": 0,
                            "in_pos":   False,
                            "pnl_pct":  None,
                        })

            for row in pair_rows:
                row["in_pos"] = manager.has_position(row["symbol"])

            for ev in trade_events:
                if ev[0] == "result":
                    trade_result(ev[1], ev[2], ev[3], ev[4])
                elif ev[0] == "buy":
                    buy_opened(ev[1], ev[2], ev[3], ev[4], ev[5])

            pairs_table(pair_rows, manager.paper_balance_usdt, manager.pnl(), manager.total_trades, manager.win_rate())

            now   = datetime.now()
            today = now.strftime("%Y-%m-%d")
            if now.hour == DAILY_REPORT_HOUR and today != last_report_date:
                _send_daily_report(manager)
                last_report_date = today

        except KeyboardInterrupt:
            _shutdown()
            break
        except Exception as e:
            error(str(e))
            log.error(e)
            log_event("bot_cycle_error", mode=TRADING_MODE, error=str(e))

        try:
            waiting(POLL_INTERVAL)
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            _shutdown()
            break

def _send_daily_report(manager: OrderManager):
    today = datetime.now().strftime("%d/%m/%Y")
    positions_info = f"{len(manager.positions)} aberta(s)" if manager.positions else "nenhuma"
    msg = (
        f"Relatorio diario — {today}\n"
        f"PnL do dia: {manager.daily_pnl:+.2f} USDT\n"
        f"Trades totais: {manager.total_trades}\n"
        f"Win rate: {manager.win_rate():.0f}%\n"
        f"Saldo: ${manager.paper_balance_usdt:.2f}\n"
        f"Posicoes: {positions_info}"
    )
    send_telegram(msg)
    log.info("Relatorio diario enviado")

def _mtf_confirmed(symbol: str, price: float, strategy: EmaRsiStrategy) -> bool:
    try:
        df  = fetch_ohlcv(symbol, MTF_TIMEFRAME)
        ind = strategy.calculate_indicators(df).iloc[-1]
        return price > ind["ema_trend"]
    except Exception:
        return True

def _shutdown():
    shutdown()
    send_telegram("Bot encerrado.")

def _get_usdt_balance() -> float:
    try:
        balance = fetch_balance()
        return float(balance.get("USDT", 0))
    except Exception:
        return 0.0

if __name__ == "__main__":
    run()
