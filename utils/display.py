import sys
import io
from rich.console import Console
from rich.table import Table
from rich import box
from contextlib import contextmanager
from datetime import datetime

_out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
console = Console(file=_out, highlight=False, force_terminal=True)

# ── palette ────────────────────────────────────────────────────
C_DIAMOND  = "bold cyan"
C_PIPE     = "dim"
C_OK       = "bold bright_green"
C_FAIL     = "bold bright_red"
C_WARN     = "bold yellow"
C_PRICE    = "bold white"
C_LABEL    = "dim"
C_DIM      = "dim"
C_BUY      = "bold bright_green"
C_SELL     = "bold bright_red"
C_HOLD     = "dim"
C_CYAN     = "cyan"
C_RSI_OK   = "white"
C_RSI_HOT  = "bright_red"
C_RSI_COLD = "bright_green"
C_POS      = "bright_green"
C_NEG      = "bright_red"

def _d(txt):   return f"[{C_DIAMOND}]◆[/{C_DIAMOND}]  {txt}"
def _p(txt):   return f"[{C_PIPE}]│[/{C_PIPE}]  {txt}"
def _ok(txt):  return f"[{C_OK}]✓[/{C_OK}]  {txt}"
def _err(txt): return f"[{C_FAIL}]✗[/{C_FAIL}]  {txt}"

def _fmt_price(price: float) -> str:
    if price == 0:
        return "$0"
    if price >= 1000:
        return f"${price:,.2f}"
    if price >= 1:
        return f"${price:,.4f}"
    if price >= 0.01:
        return f"${price:.6f}"
    return f"${price:.8f}"

def _fmt_num(value: float) -> str:
    if value == 0:
        return "0"
    if value >= 1000:
        return f"{value:,.2f}"
    if value >= 1:
        return f"{value:,.4f}"
    if value >= 0.01:
        return f"{value:.6f}"
    return f"{value:.8f}"

def _rsi_color(rsi):
    if rsi > 65: return C_RSI_HOT
    if rsi < 35: return C_RSI_COLD
    return C_RSI_OK

def _pnl_color(v):
    return C_POS if v >= 0 else C_NEG

# ── header ─────────────────────────────────────────────────────
def header():
    from config.settings import SYMBOL, TIMEFRAME, TRADING_MODE
    console.print()
    console.print(_d(f"[bold white]crypto trader[/bold white]"))
    console.print(_p(f"[{C_DIM}]{SYMBOL}  ·  {TIMEFRAME}  ·  {TRADING_MODE}[/{C_DIM}]"))
    console.print()

# ── spinner ─────────────────────────────────────────────────────
@contextmanager
def spinner(text: str):
    with console.status(
        f"[{C_DIM}]{text}[/{C_DIM}]",
        spinner="dots",
        spinner_style=C_CYAN,
    ):
        yield

# ── signal line ─────────────────────────────────────────────────
def signal_line(price: float, signal: str, rsi: float, ema_fast: float, ema_slow: float):
    now = datetime.now().strftime("%H:%M:%S")

    if signal == "BUY":
        sig = f"[{C_BUY}]▲  BUY[/{C_BUY}]"
    elif signal == "SELL":
        sig = f"[{C_SELL}]▼  SELL[/{C_SELL}]"
    else:
        sig = f"[{C_HOLD}]hold[/{C_HOLD}]"

    rc    = _rsi_color(rsi)
    rsi_s = f"[{rc}]{rsi:.0f}[/{rc}]"

    console.print(_d(f"[{C_DIM}]{now}[/{C_DIM}]"))
    console.print(_p(
        f"[{C_LABEL}]preço[/{C_LABEL}]   [{C_PRICE}]{_fmt_price(price)}[/{C_PRICE}]"
        f"      {sig}"
    ))
    console.print(_p(
        f"[{C_LABEL}]RSI[/{C_LABEL}]     {rsi_s}"
        f"   [{C_LABEL}]EMA[/{C_LABEL}] [{C_CYAN}]{_fmt_num(ema_fast)}[/{C_CYAN}]"
        f"  [{C_LABEL}]/[/{C_LABEL}]  [{C_DIM}]{_fmt_num(ema_slow)}[/{C_DIM}]"
    ))

# ── position line ───────────────────────────────────────────────
def position_line(entry: float, current: float, sl: float, tp: float):
    pnl     = (current - entry) / entry * 100
    pc      = _pnl_color(pnl)
    pnl_s   = f"[{pc}]{pnl:+.2f}%[/{pc}]"
    console.print(_p(
        f"[{C_LABEL}]posição[/{C_LABEL}] [{C_LABEL}]entrada[/{C_LABEL}] [{C_PRICE}]{_fmt_price(entry)}[/{C_PRICE}]"
        f"   pnl {pnl_s}"
        f"   [{C_LABEL}]sl[/{C_LABEL}] [{C_NEG}]{_fmt_price(sl)}[/{C_NEG}]"
        f"   [{C_LABEL}]tp[/{C_LABEL}] [{C_POS}]{_fmt_price(tp)}[/{C_POS}]"
    ))

# ── stats line ──────────────────────────────────────────────────
def stats_line(balance: float, pnl: float, trades: int, win_rate: float):
    pc  = _pnl_color(pnl)
    wc  = C_POS if win_rate >= 50 else C_NEG
    console.print(_p(
        f"[{C_LABEL}]saldo[/{C_LABEL}]   [{C_PRICE}]${balance:,.2f}[/{C_PRICE}]"
        f"   [{C_LABEL}]pnl[/{C_LABEL}] [{pc}]{pnl:+.2f}[/{pc}]"
        f"   [{C_LABEL}]trades[/{C_LABEL}] [white]{trades}[/white]"
        f"   [{C_LABEL}]win[/{C_LABEL}] [{wc}]{win_rate:.0f}%[/{wc}]"
    ))

# ── buy opened ──────────────────────────────────────────────────
def buy_opened(symbol: str, price: float, qty: float, sl: float, tp: float):
    console.print()
    console.print(_ok(f"[{C_BUY}]compra aberta  {symbol}[/{C_BUY}]"))
    console.print(_p(
        f"[{C_LABEL}]entrada[/{C_LABEL}] [{C_PRICE}]{_fmt_price(price)}[/{C_PRICE}]"
        f"   [{C_LABEL}]qty[/{C_LABEL}] [{C_CYAN}]{qty:.4f}[/{C_CYAN}]"
    ))
    console.print(_p(
        f"[{C_LABEL}]sl[/{C_LABEL}]      [{C_NEG}]{_fmt_price(sl)}[/{C_NEG}]"
        f"   [{C_LABEL}]tp[/{C_LABEL}] [{C_POS}]{_fmt_price(tp)}[/{C_POS}]"
    ))
    console.print()

# ── trade result ────────────────────────────────────────────────
def trade_result(action: str, pnl: float, pnl_pct: float, balance: float):
    console.print()
    if pnl >= 0:
        console.print(_ok(f"[{C_BUY}]{action}[/{C_BUY}]"))
        console.print(_p(f"[{C_POS}]+${pnl:.4f}  ({pnl_pct:+.2f}%)[/{C_POS}]   [{C_LABEL}]saldo[/{C_LABEL}] [{C_PRICE}]${balance:,.2f}[/{C_PRICE}]"))
    else:
        console.print(_err(f"[{C_SELL}]{action}[/{C_SELL}]"))
        console.print(_p(f"[{C_NEG}]-${abs(pnl):.4f}  ({pnl_pct:+.2f}%)[/{C_NEG}]   [{C_LABEL}]saldo[/{C_LABEL}] [{C_PRICE}]${balance:,.2f}[/{C_PRICE}]"))
    console.print()

# ── multi-pair table ────────────────────────────────────────────
def pairs_table(rows: list, balance: float, pnl: float, trades: int, win_rate: float):
    now = datetime.now().strftime("%H:%M:%S")
    console.print()
    console.print(_d(f"[{C_DIM}]{now}[/{C_DIM}]"))

    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold dim",
        border_style="dim",
        pad_edge=False,
    )
    table.add_column("  par",      style="white",   min_width=14)
    table.add_column("preço",      justify="right", min_width=12)
    table.add_column("sinal",      justify="center", min_width=6)
    table.add_column("RSI",        justify="right", min_width=5)
    table.add_column("EMA rápida", justify="right", min_width=12)
    table.add_column("EMA lenta",  justify="right", min_width=12)
    table.add_column("posição",    justify="center", min_width=8)
    table.add_column("pnl",        justify="right", min_width=8)

    for r in rows:
        sig = r["signal"]
        if sig == "BUY":
            sig_s = f"[{C_BUY}]▲ BUY[/{C_BUY}]"
        elif sig == "SELL":
            sig_s = f"[{C_SELL}]▼ SELL[/{C_SELL}]"
        elif sig == "ERR":
            sig_s = f"[{C_FAIL}]ERR[/{C_FAIL}]"
        else:
            sig_s = f"[{C_HOLD}]hold[/{C_HOLD}]"

        rsi   = r["rsi"]
        rc    = _rsi_color(rsi)
        rsi_s = f"[{rc}]{rsi:.0f}[/{rc}]" if rsi else "[dim]—[/dim]"

        price_s = f"[{C_PRICE}]{_fmt_price(r['price'])}[/{C_PRICE}]" if r["price"] else "[dim]—[/dim]"
        ef_s    = f"[{C_CYAN}]{_fmt_num(r['ema_fast'])}[/{C_CYAN}]" if r["ema_fast"] else "[dim]—[/dim]"
        es_s    = f"[{C_DIM}]{_fmt_num(r['ema_slow'])}[/{C_DIM}]"   if r["ema_slow"] else "[dim]—[/dim]"

        if r["in_pos"]:
            pos_s = f"[{C_BUY}]● long[/{C_BUY}]"
        else:
            pos_s = f"[{C_DIM}]—[/{C_DIM}]"

        pnl_pct = r.get("pnl_pct")
        if pnl_pct is not None:
            pc    = _pnl_color(pnl_pct)
            pnl_s = f"[{pc}]{pnl_pct:+.2f}%[/{pc}]"
        else:
            pnl_s = f"[{C_DIM}]—[/{C_DIM}]"

        table.add_row(
            f"  {r['symbol']}",
            price_s,
            sig_s,
            rsi_s,
            ef_s,
            es_s,
            pos_s,
            pnl_s,
        )

    console.print(table)

    pc  = _pnl_color(pnl)
    wc  = C_POS if win_rate >= 50 else C_NEG
    console.print(_p(
        f"[{C_LABEL}]saldo[/{C_LABEL}]   [{C_PRICE}]${balance:,.2f}[/{C_PRICE}]"
        f"   [{C_LABEL}]pnl[/{C_LABEL}] [{pc}]{pnl:+.2f}[/{pc}]"
        f"   [{C_LABEL}]trades[/{C_LABEL}] [white]{trades}[/white]"
        f"   [{C_LABEL}]win[/{C_LABEL}] [{wc}]{win_rate:.0f}%[/{wc}]"
    ))
    console.print()

# ── waiting ─────────────────────────────────────────────────────
def waiting(seconds: int):
    console.print()
    console.print(f"  [{C_DIM}]⏳ próxima checagem em {seconds}s[/{C_DIM}]")
    console.print()

# ── error ───────────────────────────────────────────────────────
def error(msg: str):
    console.print(_err(f"[{C_DIM}]{msg}[/{C_DIM}]"))

# ── shutdown ────────────────────────────────────────────────────
def shutdown():
    console.print()
    console.print(_d(f"[{C_DIM}]bot encerrado.[/{C_DIM}]"))
    console.print()
