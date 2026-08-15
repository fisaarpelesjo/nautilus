import time
from datetime import datetime
from typing import Dict

from config.settings import (
    DAILY_DRAWDOWN_LIMIT,
    DAILY_REPORT_HOUR,
    DYNAMIC_PAIRS_ENABLED,
    ENTRY_COOLDOWN_CYCLES,
    MAX_CONSECUTIVE_LOSSES,
    MAX_ORDER_SIZE_USDT,
    MAX_POSITIONS,
    MIN_PRICE_USDT,
    MONTHLY_DRAWDOWN_LIMIT,
    PAIRS,
    TIMEFRAME,
    TRADING_MODE,
    WEEKLY_DRAWDOWN_LIMIT,
)
from data.fetcher import fetch_ohlcv
from data.killswitch_store import load_killswitch
from data.ohlcv_store import save_ohlcv
from data.signal_store import log_signal
from execution.order_manager import OrderManager
from execution.reconciliation import reconcile
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
    live_confirmation_banner,
    pairs_table,
    phase,
    shutdown,
    spinner,
    trade_result,
    waiting,
)
from utils.logger import get_logger, log_event, safe_step
from utils.notifier import send_telegram

log = get_logger("bot")
POLL_INTERVAL = 60
MAX_ENTRIES_PER_CYCLE = 1
RECONCILIATION_INTERVAL_CYCLES = 30


def _run_reconciliation(manager: OrderManager, tracked_symbols):
    # Chamado tanto na inicializacao (fora do loop principal) quanto
    # periodicamente -- uma falha aqui nunca pode derrubar o bot.
    try:
        result = reconcile(manager, tracked_symbols=tracked_symbols)
    except Exception as exc:
        error_message = str(exc)  # captura antes de qualquer lambda/closure
        log.error(f"Reconciliacao falhou: {error_message}")
        safe_step(log, "Falha ao publicar evento de erro de reconciliacao",
                  lambda: log_event("reconciliation_error", mode=TRADING_MODE, error=error_message))
        safe_step(log, "Falha ao persistir status de erro de reconciliacao", lambda: manager.record_reconciliation(
            "error", datetime.now().isoformat(), [error_message]
        ))
        return

    if result is None:
        return

    # O alerta de uma divergencia real vem ANTES de persistir o resultado, e
    # cada passo e isolado (safe_step): uma falha ao persistir (I/O) nao pode
    # engolir o alerta de uma divergencia genuina -- isso derrotaria o
    # proposito da reconciliacao.
    if result.status == "mismatch":
        log.warning(f"Divergencia de reconciliacao: {result.diffs}")
        safe_step(log, "Falha ao registrar evento de divergencia", lambda: log_event(
            "reconciliation_mismatch",
            mode=TRADING_MODE,
            diffs=result.diffs,
            checked_at=result.checked_at.isoformat(),
        ))
        safe_step(log, "Falha ao enviar alerta de divergencia",
                  lambda: send_telegram("Divergencia de reconciliacao detectada:\n" + "\n".join(result.diffs)))
    else:
        log.info("Reconciliacao ok")

    # record_reconciliation ja usa _persist_state_with_retry internamente (nao
    # deveria propagar falha), mas ainda isolado aqui por seguranca -- este
    # runner nao pode assumir esse invariante de qualquer `manager` que receba.
    safe_step(log, "Falha ao persistir resultado de reconciliacao", lambda: manager.record_reconciliation(
        result.status, result.checked_at.isoformat(), result.diffs
    ))


def _print_live_confirmation_banner(pairs, manager: OrderManager):
    # Chamado uma vez, antes do loop principal, quando TRADING_MODE=live --
    # nao bloqueia esperando confirmacao interativa alem do
    # LIVE_TRADING_CONFIRMATION ja validado em config/settings.py (FR-003).
    balance = manager._reference_balance()
    live_confirmation_banner(
        pairs, balance, MAX_ORDER_SIZE_USDT, MAX_POSITIONS,
        DAILY_DRAWDOWN_LIMIT, WEEKLY_DRAWDOWN_LIMIT, MONTHLY_DRAWDOWN_LIMIT, MAX_CONSECUTIVE_LOSSES,
    )
    safe_step(log, "Falha ao publicar evento de inicio de sessao live", lambda: log_event(
        "live_session_started",
        mode=TRADING_MODE,
        pairs=pairs,
        balance_usdt=balance,
        max_order_size_usdt=MAX_ORDER_SIZE_USDT,
        max_positions=MAX_POSITIONS,
        daily_limit_pct=DAILY_DRAWDOWN_LIMIT,
        weekly_limit_pct=WEEKLY_DRAWDOWN_LIMIT,
        monthly_limit_pct=MONTHLY_DRAWDOWN_LIMIT,
        max_consecutive_losses=MAX_CONSECUTIVE_LOSSES,
    ))


def _maybe_print_live_banner(pairs, manager: OrderManager):
    if TRADING_MODE == "live":
        _print_live_confirmation_banner(pairs, manager)


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
    entry_cooldown = 0

    _maybe_print_live_banner(active_pairs, manager)
    bot_boot(active_pairs, MAX_POSITIONS, POLL_INTERVAL, DYNAMIC_PAIRS_ENABLED)
    send_telegram(f"Bot iniciado | {len(active_pairs)} pares | Modo={TRADING_MODE}")
    _run_reconciliation(manager, active_pairs)

    while True:
        try:
            cycle_id += 1
            if cycle_id % RECONCILIATION_INTERVAL_CYCLES == 0:
                _run_reconciliation(manager, active_pairs)
            if entry_cooldown > 0:
                entry_cooldown -= 1
            pair_rows = []
            trade_events = []
            new_entries = 0
            blocked_entries = 0
            max_entries_this_cycle = 0 if entry_cooldown > 0 else MAX_ENTRIES_PER_CYCLE
            # Le do disco a cada ciclo (nao guarda em memoria): o kill switch
            # e ativado por um comando de CLI separado enquanto o bot roda, e
            # precisa refletir no proximo ciclo, nao so num restart.
            killswitch_active = load_killswitch()

            cycle_start(cycle_id, active_pairs, len(manager.positions), manager.paper_balance_usdt, manager.daily_pnl)
            phase("coleta e avaliacao", "candles -> indicadores -> sinais -> risco")

            with spinner("atualizando pares..."):
                for symbol in active_pairs:
                    try:
                        df = fetch_ohlcv(symbol, TIMEFRAME)
                        signal = strategy.generate_signal(df)
                        if signal.price < MIN_PRICE_USDT:
                            pair_rows.append(_skipped_row(symbol, signal.price, "preco abaixo do minimo"))
                            continue
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
                                row, trade_events, new_entries, max_entries_this_cycle,
                                killswitch_active=killswitch_active,
                            )
                            if opened:
                                new_entries += 1
                                entry_cooldown = ENTRY_COOLDOWN_CYCLES
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
        "ema_aligned": float(indicators["ema_fast"]) > float(indicators["ema_slow"]),
        "buy_score": sum([
            bool(checks["bullish_cross"] or checks["pullback_entry"]),
            checks["trend_ok"],
            checks["rsi_ok"],
            checks["volume_ok"],
            checks["bb_ok"],
        ]),
        "in_pos": pos is not None,
        "pnl_pct": pnl_pct,
        "entry_opened": False,
        "blockers": "",
        "mtf_checked": False,
        "mtf_ok": "",
        "decision": "posicao aberta: monitorando saidas" if pos else hold_diagnosis(signal, indicators, previous, current_price, strategy),
    }


def _skipped_row(symbol: str, price: float, reason: str):
    return {
        "symbol": symbol, "price": price, "signal": "HOLD",
        "rsi": 0, "ema_fast": 0, "ema_slow": 0, "ema_trend": 0,
        "volume_ratio": 0, "trend_gap_pct": 0, "atr_pct": 0,
        "ema_aligned": False, "buy_score": 0,
        "in_pos": False, "pnl_pct": None,
        "entry_opened": False, "blockers": reason,
        "mtf_checked": False, "mtf_ok": "",
        "decision": f"ignorado: {reason}",
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
