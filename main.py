#!/usr/bin/env python3
"""
Ponto de entrada principal.

Uso:
  python main.py backtest      -- run single-pair backtest
  python main.py backtest --validate  -- backtest with train/out-of-sample split + verdict
  python main.py backtest --montecarlo  -- backtest with Monte Carlo drawdown/ruin estimate
  python main.py edge          -- run profitability edge report
  python main.py multibacktest -- run backtest on fixed pair list
  python main.py scan          -- backtest top 30 pairs by volume
  python main.py compare       -- compare multiple strategies/presets side by side
  python main.py optimize      -- grid search best parameters
  python main.py optimize --validate      -- grid search with train/validation split
  python main.py optimize --walk-forward  -- validate winner across sliding windows
  python main.py analyze       -- analyze backtest results
  python main.py decisions     -- summarize data/decisions.csv (signals, blockers)
  python main.py select        -- select dynamic pairs
  python main.py chart [PAIR] [TF] [N]  -- terminal chart with EMAs and RSI
  python main.py bot           -- start the trading bot
  python main.py status        -- show balance and open positions
  python main.py kill          -- suspend new entries (kill switch)
  python main.py resume        -- resume new entries (kill switch)
"""
import sys
from config.settings import SYMBOL, TIMEFRAME, TRADING_MODE

def cmd_backtest():
    args = sys.argv[2:]
    if "--validate" in args:
        from backtesting.validation import run_backtest_with_validation
        run_backtest_with_validation(SYMBOL, TIMEFRAME)
        return
    from backtesting.engine import run_backtest
    result = run_backtest(SYMBOL, TIMEFRAME)
    if "--montecarlo" in args:
        from backtesting.robustness import run_monte_carlo_report
        run_monte_carlo_report(result.trades)

def cmd_edge():
    from backtesting.validation import run_edge_report
    run_edge_report(SYMBOL, TIMEFRAME)

def cmd_multibacktest():
    from backtesting.multi import run
    run()

def cmd_scan():
    from backtesting.scanner import run
    run()

def cmd_comparar():
    from backtesting.compare import run
    run()

def cmd_analisar():
    from backtesting.analysis import run
    run()

def cmd_decisions():
    from data.decisions_analysis import run
    run()

def cmd_otimizar():
    from backtesting.optimizer import run
    args = sys.argv[2:]
    walk_forward = "--walk-forward" in args
    validate = walk_forward or "--validate" in args
    run(validate=validate, walk_forward=walk_forward)

def cmd_selecionar():
    from market.commands import run
    run()

def cmd_chart():
    from utils.chart import run
    args = sys.argv[2:]
    symbol   = args[0].upper() if len(args) > 0 else None
    timeframe = args[1]        if len(args) > 1 else None
    limit    = int(args[2])    if len(args) > 2 else 100
    run(symbol=symbol, timeframe=timeframe, limit=limit)


def cmd_bot():
    from trading.runner import run
    run()

def _toggle_killswitch(active: bool):
    from datetime import datetime
    from data.killswitch_store import save_killswitch
    from utils.logger import log_event, safe_step, get_logger
    from utils.notifier import send_telegram

    log = get_logger("cli")
    save_killswitch(active)
    label = "ativado" if active else "desativado"
    safe_step(log, f"Kill switch {label}, mas falha ao publicar evento",
              lambda: log_event("killswitch_toggled", active=active))
    safe_step(log, f"Kill switch {label}, mas falha ao enviar alerta",
              lambda: send_telegram(f"Kill switch {label.upper()} via CLI — novas entradas {'suspensas' if active else 'liberadas'}."))
    print(f"Kill switch {label} em {datetime.now().isoformat()}")

def cmd_kill():
    _toggle_killswitch(True)

def cmd_resume():
    _toggle_killswitch(False)

def _fmt_or_na(value, fmt: str = ",.2f", prefix: str = "$") -> str:
    if value is None:
        return "indisponível"
    return f"{prefix}{value:{fmt}}"


def cmd_status():
    from data.fetcher import fetch_ticker
    from data.killswitch_store import load_killswitch
    from execution.order_manager import OrderManager
    from trading.portfolio import compute_portfolio_snapshot
    from utils.display import console, header, C_LABEL, C_PRICE, C_POS, C_NEG, C_DIM, C_CYAN, _fmt_price

    header()
    manager = OrderManager()
    snap = compute_portfolio_snapshot(manager)

    total       = manager.total_trades
    wins        = manager.winning_trades
    positions   = manager.positions
    win_rate    = (wins / total * 100) if total else 0
    consecutive_losses     = manager.consecutive_losses
    circuit_breaker_active = manager.circuit_breaker_active
    killswitch_active = load_killswitch()
    pnl_c   = C_POS if (snap.total_pnl is None or snap.total_pnl >= 0) else C_NEG
    wc      = C_POS if win_rate >= 50 else C_NEG

    console.print(f"  [{C_LABEL}]caixa livre[/{C_LABEL}]   [{C_PRICE}]{_fmt_or_na(snap.free_cash)}[/{C_PRICE}]"
                  f"   [{C_LABEL}]posições[/{C_LABEL}] [{C_PRICE}]{_fmt_or_na(snap.positions_value)}[/{C_PRICE}]"
                  f"   [{C_LABEL}]patrimônio[/{C_LABEL}] [{C_PRICE}]{_fmt_or_na(snap.total_equity)}[/{C_PRICE}]")
    console.print(f"  [{C_LABEL}]pnl realizado[/{C_LABEL}] [{C_POS if snap.realized_pnl >= 0 else C_NEG}]{snap.realized_pnl:+.2f}[/]"
                  f"   [{C_LABEL}]pnl não realizado[/{C_LABEL}] [white]{_fmt_or_na(snap.unrealized_pnl, fmt='+.2f')}[/white]"
                  f"   [{C_LABEL}]pnl total[/{C_LABEL}] [{pnl_c}]{_fmt_or_na(snap.total_pnl, fmt='+.2f')}[/{pnl_c}]")
    console.print(f"  [{C_LABEL}]trades[/{C_LABEL}] [white]{total}[/white]"
                  f"   [{C_LABEL}]win rate[/{C_LABEL}] [{wc}]{win_rate:.0f}%[/{wc}]")
    console.print()

    if killswitch_active or circuit_breaker_active:
        if killswitch_active:
            console.print(f"  [{C_NEG}]kill switch ATIVADO[/{C_NEG}] — novas entradas suspensas manualmente")
        if circuit_breaker_active:
            console.print(
                f"  [{C_NEG}]circuit breaker ATIVADO[/{C_NEG}] — {consecutive_losses} perdas seguidas, novas entradas suspensas"
            )
        console.print()

    if positions:
        console.print(f"  [{C_LABEL}]posições abertas ({len(positions)}):[/{C_LABEL}]")
        for symbol, pos in positions.items():
            try:
                ticker  = fetch_ticker(symbol)
                current = ticker["last"]
                pnl_pct = (current - pos.entry_price) / pos.entry_price * 100
                pc2     = C_POS if pnl_pct >= 0 else C_NEG
                console.print(
                    f"  [{C_CYAN}]{symbol}[/{C_CYAN}]"
                    f"  [{C_LABEL}]entrada[/{C_LABEL}] [{C_PRICE}]{_fmt_price(pos.entry_price)}[/{C_PRICE}]"
                    f"  [{C_LABEL}]atual[/{C_LABEL}] [{C_PRICE}]{_fmt_price(current)}[/{C_PRICE}]"
                    f"  [{pc2}]{pnl_pct:+.2f}%[/{pc2}]"
                )
            except Exception:
                console.print(f"  [{C_DIM}]{symbol}  erro ao buscar preço[/{C_DIM}]")
    else:
        console.print(f"  [{C_DIM}]nenhuma posição aberta[/{C_DIM}]")
    console.print()

    if TRADING_MODE == "live":
        last_reconciliation = manager.last_reconciliation
        if last_reconciliation:
            status = last_reconciliation.get("status", "?")
            checked_at = last_reconciliation.get("checked_at", "?")
            rc = C_POS if status == "ok" else C_NEG
            console.print(
                f"  [{C_LABEL}]reconciliação[/{C_LABEL}] [{rc}]{status}[/{rc}]"
                f"   [{C_LABEL}]em[/{C_LABEL}] [{C_DIM}]{checked_at}[/{C_DIM}]"
            )
            for diff in last_reconciliation.get("diffs", []):
                console.print(f"  [{C_NEG}]  {diff}[/{C_NEG}]")
        else:
            console.print(f"  [{C_DIM}]reconciliação ainda não rodou nesta sessão[/{C_DIM}]")
        console.print()

COMMANDS = {
    "backtest":      cmd_backtest,
    "edge":          cmd_edge,
    "multibacktest": cmd_multibacktest,
    "scan":          cmd_scan,
    "compare":       cmd_comparar,
    "analyze":       cmd_analisar,
    "decisions":     cmd_decisions,
    "optimize":      cmd_otimizar,
    "select":        cmd_selecionar,
    "chart":         cmd_chart,
    "bot":           cmd_bot,
    "status":        cmd_status,
    "kill":          cmd_kill,
    "resume":        cmd_resume,
    # aliases pt-br
    "analisar":      cmd_analisar,
    "decisoes":      cmd_decisions,
    "otimizar":      cmd_otimizar,
    "selecionar":    cmd_selecionar,
    "comparar":      cmd_comparar,
}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "bot"
    if cmd not in COMMANDS:
        print(f"Comando invalido. Use: {', '.join(COMMANDS)}")
        sys.exit(1)
    COMMANDS[cmd]()
