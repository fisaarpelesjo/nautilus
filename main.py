#!/usr/bin/env python3
"""
Ponto de entrada principal.

Uso:
  python main.py backtest      -- run single-pair backtest
  python main.py edge          -- run profitability edge report
  python main.py multibacktest -- run backtest on fixed pair list
  python main.py scan          -- backtest top 30 pairs by volume
  python main.py optimize      -- grid search best parameters
  python main.py analyze       -- analyze backtest results
  python main.py select        -- select dynamic pairs
  python main.py chart [PAIR] [TF] [N]  -- terminal chart with EMAs and RSI
  python main.py bot           -- start the trading bot
  python main.py status        -- show balance and open positions
"""
import sys
from config.settings import SYMBOL, TIMEFRAME

def cmd_backtest():
    from backtesting.engine import run_backtest
    run_backtest(SYMBOL, TIMEFRAME)

def cmd_edge():
    from backtesting.engine import run_backtest
    run_backtest(SYMBOL, TIMEFRAME)

def cmd_multibacktest():
    from backtesting.multi import run
    run()

def cmd_scan():
    from backtesting.scanner import run
    run()

def cmd_analisar():
    from backtesting.analysis import run
    run()

def cmd_otimizar():
    from backtesting.optimizer import run
    run()

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

def cmd_status():
    from data.fetcher import fetch_ticker
    from data.state_store import load_state
    from utils.display import console, header, C_LABEL, C_PRICE, C_POS, C_NEG, C_DIM, C_CYAN, _fmt_price

    header()
    state = load_state()

    balance     = state.get("paper_balance_usdt", 1000.0) if state else 1000.0
    pnl         = balance - 1000.0
    total       = state.get("total_trades", 0) if state else 0
    wins        = state.get("winning_trades", 0) if state else 0
    positions   = state.get("positions", {}) if state else {}
    win_rate    = (wins / total * 100) if total else 0
    pc          = C_POS if pnl >= 0 else C_NEG
    wc          = C_POS if win_rate >= 50 else C_NEG

    console.print(f"  [{C_LABEL}]saldo[/{C_LABEL}]     [{C_PRICE}]${balance:,.2f}[/{C_PRICE}]"
                  f"   [{C_LABEL}]pnl[/{C_LABEL}] [{pc}]{pnl:+.2f}[/{pc}]"
                  f"   [{C_LABEL}]trades[/{C_LABEL}] [white]{total}[/white]"
                  f"   [{C_LABEL}]win rate[/{C_LABEL}] [{wc}]{win_rate:.0f}%[/{wc}]")
    console.print()

    if positions:
        console.print(f"  [{C_LABEL}]posições abertas ({len(positions)}):[/{C_LABEL}]")
        for symbol, pos in positions.items():
            try:
                ticker  = fetch_ticker(symbol)
                current = ticker["last"]
                pnl_pct = (current - pos["entry_price"]) / pos["entry_price"] * 100
                pc2     = C_POS if pnl_pct >= 0 else C_NEG
                console.print(
                    f"  [{C_CYAN}]{symbol}[/{C_CYAN}]"
                    f"  [{C_LABEL}]entrada[/{C_LABEL}] [{C_PRICE}]{_fmt_price(pos['entry_price'])}[/{C_PRICE}]"
                    f"  [{C_LABEL}]atual[/{C_LABEL}] [{C_PRICE}]{_fmt_price(current)}[/{C_PRICE}]"
                    f"  [{pc2}]{pnl_pct:+.2f}%[/{pc2}]"
                )
            except Exception:
                console.print(f"  [{C_DIM}]{symbol}  erro ao buscar preço[/{C_DIM}]")
    else:
        console.print(f"  [{C_DIM}]nenhuma posição aberta[/{C_DIM}]")
    console.print()

COMMANDS = {
    "backtest":      cmd_backtest,
    "edge":          cmd_edge,
    "multibacktest": cmd_multibacktest,
    "scan":          cmd_scan,
    "analyze":       cmd_analisar,
    "optimize":      cmd_otimizar,
    "select":        cmd_selecionar,
    "chart":         cmd_chart,
    "bot":           cmd_bot,
    "status":        cmd_status,
    # aliases pt-br
    "analisar":      cmd_analisar,
    "otimizar":      cmd_otimizar,
    "selecionar":    cmd_selecionar,
}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "bot"
    if cmd not in COMMANDS:
        print(f"Comando invalido. Use: {', '.join(COMMANDS)}")
        sys.exit(1)
    COMMANDS[cmd]()
