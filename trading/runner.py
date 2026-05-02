import time
from datetime import datetime
from typing import Dict

from config.settings import (
    DAILY_REPORT_HOUR,
    DYNAMIC_PAIRS_ENABLED,
    MAX_POSITIONS,
    PAIRS,
    TIMEFRAME,
    TRADING_MODE,
)
from data.fetcher import fetch_ohlcv
from data.trade_logger import log_signal, save_ohlcv
from execution.order_manager import OrderManager
from market.selector import select_dynamic_pairs, selected_symbols
from strategy.base import Signal
from strategy.diagnostics import hold_diagnosis, signal_checks
from strategy.ema_rsi import EmaRsiStrategy
from trading.decision_logger import log_decision_snapshot, log_error_decision
from trading.position_lifecycle import handle_entry_candidate, handle_open_position
from utils.display import (
    bot_boot,
    buy_opened,
    cycle_start,
    cycle_summary,
    error,
    header,
    pairs_table,
    phase,
    shutdown,
    spinner,
    trade_result,
    waiting,
)
from utils.logger import get_logger, log_event
from utils.notifier import send_telegram

log = get_logger("bot")
POLL_INTERVAL = 60
MAX_ENTRIES_PER_CYCLE = 1


def _round_price(price: float) -> float:
    if price >= 1:
        return round(price, 4)
    if price >= 0.01:
        return round(price, 6)
    return round(price, 10)


def run():
    header()

    strategy = EmaRsiStrategy()
    manager = OrderManager()
    last_report_date = ""
    last_signals: Dict[str, str] = {}
    active_pairs = _load_active_pairs()
    cycle_id = 0

    bot_boot(active_pairs, MAX_POSITIONS, POLL_INTERVAL, DYNAMIC_PAIRS_ENABLED)
    send_telegram(f"Bot iniciado | {len(active_pairs)} pares | Modo={TRADING_MODE}")

    while True:
        try:
            cycle_id += 1
            pair_rows = []
            trade_events = []
            new_entries = 0
            blocked_entries = 0

            cycle_start(cycle_id, active_pairs, len(manager.positions), manager.paper_balance_usdt, manager.daily_pnl)
            phase("coleta e avaliacao", "candles -> indicadores -> sinais -> risco")

            with spinner("atualizando pares..."):
                for symbol in active_pairs:
                    try:
                        df = fetch_ohlcv(symbol, TIMEFRAME)
                        signal = strategy.generate_signal(df)
                        prepared = strategy.calculate_indicators(df)
                        indicators = prepared.iloc[-1]
                        previous = prepared.iloc[-2] if len(prepared) >= 2 else None
                        current_price = signal.price

                        save_ohlcv(symbol, TIMEFRAME, df)
                        _log_signal_change(symbol, signal, indicators, current_price, last_signals)

                        pos = manager.get_position(symbol)
                        row = _build_pair_row(symbol, signal, indicators, previous, current_price, pos, strategy)
                        pair_rows.append(row)

                        if pos:
                            handle_open_position(manager, symbol, pos, signal, current_price, row, trade_events)
                        else:
                            opened = handle_entry_candidate(
                                manager, symbol, signal, indicators, current_price, strategy,
                                row, trade_events, new_entries, MAX_ENTRIES_PER_CYCLE
                            )
                            if opened:
                                new_entries += 1
                            elif signal.signal == Signal.BUY:
                                blocked_entries += 1

                        log_decision_snapshot(cycle_id, symbol, signal, indicators, previous, current_price, row, strategy)

                    except Exception as exc:
                        log.error(f"{symbol}: {exc}")
                        log_event("pair_cycle_error", mode=TRADING_MODE, symbol=symbol, error=str(exc))
                        pair_rows.append(_error_row(symbol, exc))
                        log_error_decision(cycle_id, symbol, exc)

            for row in pair_rows:
                row["in_pos"] = manager.has_position(row["symbol"])

            phase("eventos de execucao", "ordens, fechamentos e alertas")
            for event in trade_events:
                if event[0] == "result":
                    trade_result(event[1], event[2], event[3], event[4])
                elif event[0] == "buy":
                    buy_opened(event[1], event[2], event[3], event[4], event[5])

            phase("resumo operacional", "estado atual, bloqueios e proximo ciclo")
            pairs_table(pair_rows, manager.paper_balance_usdt, manager.pnl(), manager.total_trades, manager.win_rate())
            cycle_summary(pair_rows, trade_events, new_entries, blocked_entries)

            now = datetime.now()
            today = now.strftime("%Y-%m-%d")
            if now.hour == DAILY_REPORT_HOUR and today != last_report_date:
                _send_daily_report(manager)
                last_report_date = today

        except KeyboardInterrupt:
            _shutdown()
            break
        except Exception as exc:
            error(str(exc))
            log.error(exc)
            log_event("bot_cycle_error", mode=TRADING_MODE, error=str(exc))

        try:
            waiting(POLL_INTERVAL)
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            _shutdown()
            break


def _log_signal_change(symbol: str, signal, indicators, current_price: float, last_signals: Dict[str, str]):
    if signal.signal.value == last_signals.get(symbol):
        return
    log_signal({
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol,
        "timeframe": TIMEFRAME,
        "price": _round_price(current_price),
        "signal": signal.signal.value,
        "ema_fast": _round_price(float(indicators["ema_fast"])),
        "ema_slow": _round_price(float(indicators["ema_slow"])),
        "ema_trend": _round_price(float(indicators["ema_trend"])),
        "rsi": round(float(indicators["rsi"]), 4),
        "macd": round(float(indicators["macd"]), 6),
        "reason": signal.reason,
    })
    last_signals[symbol] = signal.signal.value


def _build_pair_row(symbol: str, signal, indicators, previous, current_price: float, pos, strategy: EmaRsiStrategy):
    checks = signal_checks(indicators, previous, current_price, strategy)
    pnl_pct = (current_price - pos.entry_price) / pos.entry_price * 100 if pos else None
    return {
        "symbol": symbol,
        "price": current_price,
        "signal": signal.signal.value,
        "rsi": indicators["rsi"],
        "ema_fast": indicators["ema_fast"],
        "ema_slow": indicators["ema_slow"],
        "ema_trend": indicators["ema_trend"],
        "volume_ratio": checks["volume_ratio"],
        "trend_gap_pct": checks["trend_gap_pct"],
        "atr_pct": checks["atr_pct"],
        "in_pos": pos is not None,
        "pnl_pct": pnl_pct,
        "entry_opened": False,
        "blockers": "",
        "mtf_checked": False,
        "mtf_ok": "",
        "decision": "posicao aberta: monitorando saidas" if pos else hold_diagnosis(signal, indicators, previous, current_price, strategy),
    }


def _error_row(symbol: str, exc: Exception):
    return {
        "symbol": symbol,
        "price": 0,
        "signal": "ERR",
        "rsi": 0,
        "ema_fast": 0,
        "ema_slow": 0,
        "trend_gap_pct": 0,
        "volume_ratio": 0,
        "atr_pct": 0,
        "in_pos": False,
        "pnl_pct": None,
        "decision": f"erro: {str(exc)[:42]}",
    }


def _send_daily_report(manager: OrderManager):
    today = datetime.now().strftime("%d/%m/%Y")
    positions_info = f"{len(manager.positions)} aberta(s)" if manager.positions else "nenhuma"
    msg = (
        f"Relatorio diario - {today}\n"
        f"PnL do dia: {manager.daily_pnl:+.2f} USDT\n"
        f"Trades totais: {manager.total_trades}\n"
        f"Win rate: {manager.win_rate():.0f}%\n"
        f"Saldo: ${manager.paper_balance_usdt:.2f}\n"
        f"Posicoes: {positions_info}"
    )
    send_telegram(msg)
    log.info("Relatorio diario enviado")


def _shutdown():
    shutdown()
    send_telegram("Bot encerrado.")


def _load_active_pairs():
    if not DYNAMIC_PAIRS_ENABLED:
        return PAIRS
    try:
        pairs = selected_symbols(select_dynamic_pairs())
        return pairs or PAIRS
    except Exception as exc:
        log.error(f"Selecao dinamica falhou: {exc}")
        return PAIRS
