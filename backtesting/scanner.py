import ccxt
import io, sys
from typing import List
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich import box

from backtesting.engine import run_backtest
from utils.logger import get_logger

log = get_logger("scanner")

_stdout_utf8 = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
console = Console(file=_stdout_utf8, highlight=False, force_terminal=True)

MIN_VOLUME_USDT = 10_000_000   # mínimo $10M volume 24h
TOP_N           = 30            # top N pares por volume

STABLECOINS = {"USDC", "BUSD", "TUSD", "USDP", "DAI", "FDUSD", "USDT", "USDS"}
TIMEFRAME       = "4h"
CANDLE_LIMIT    = 2000

@dataclass
class ScanResult:
    pair: str
    volume_24h: float
    trades: int
    win_rate: float
    retorno_pct: float
    drawdown_pct: float
    capital_final: float

    @property
    def score(self) -> float:
        if self.trades < 3:
            return -999
        return self.retorno_pct * (self.win_rate / 100)

def get_top_pairs() -> List[str]:
    console.print("  [dim cyan]buscando mercados da Binance...[/dim cyan]")
    exchange = ccxt.binance({"enableRateLimit": True, "options": {"fetchCurrencies": False}})
    tickers  = exchange.fetch_tickers()

    pairs = []
    for symbol, ticker in tickers.items():
        if not symbol.endswith("/USDT"):
            continue
        base = symbol.split("/")[0]
        if base in STABLECOINS:
            continue
        vol = ticker.get("quoteVolume") or 0
        if vol >= MIN_VOLUME_USDT:
            pairs.append((symbol, vol))

    pairs.sort(key=lambda x: x[1], reverse=True)
    top = [p[0] for p in pairs[:TOP_N]]

    console.print(
        f"  [dim]encontrados [white]{len(pairs)}[/white] pares com volume > "
        f"$[white]{MIN_VOLUME_USDT/1_000_000:.0f}M[/white]  "
        f"testando top [white]{TOP_N}[/white] por liquidez[/dim]"
    )
    console.print()
    return top

def run_scan() -> List[ScanResult]:
    pairs   = get_top_pairs()
    results = []

    for i, pair in enumerate(pairs, 1):
        with console.status(
            f"  [dim cyan]{pair}  ({i}/{len(pairs)})[/dim cyan]",
            spinner="dots", spinner_style="cyan"
        ):
            try:
                r = run_backtest(pair, TIMEFRAME, candle_limit=CANDLE_LIMIT)
                vol = _get_volume(pair)
                results.append(ScanResult(
                    pair          = pair,
                    volume_24h    = vol,
                    trades        = r.total_trades,
                    win_rate      = r.win_rate,
                    retorno_pct   = r.total_return_pct,
                    drawdown_pct  = r.max_drawdown_pct,
                    capital_final = r.final_capital,
                ))
            except Exception as e:
                log.error(f"{pair}: {e}")

    results.sort(key=lambda r: r.score, reverse=True)
    return results

def _get_volume(pair: str) -> float:
    try:
        exchange = ccxt.binance({"enableRateLimit": True, "options": {"fetchCurrencies": False}})
        t = exchange.fetch_ticker(pair)
        return t.get("quoteVolume") or 0
    except Exception:
        return 0

def print_scan(results: List[ScanResult]):
    console.print()
    console.print(
        f"  [bold cyan]◆[/bold cyan] [bold white]market scanner[/bold white]  "
        f"[dim cyan]{TIMEFRAME} · EMA 9/21/50 · SL 1.5% · TP 6% · top {TOP_N} pares[/dim cyan]"
    )
    console.print("  [dim]" + "─" * 74 + "[/dim]")
    console.print()

    positivos = [r for r in results if r.retorno_pct > 0]
    negativos = [r for r in results if r.retorno_pct <= 0]

    _print_table("melhores oportunidades", positivos[:10], highlight=True)
    _print_table("evitar", negativos[-5:], highlight=False)

    console.print("  [dim]" + "─" * 74 + "[/dim]")
    console.print()
    console.print(f"  [dim]positivos[/dim]  [bright_green]{len(positivos)}/{len(results)}[/bright_green]")
    if positivos:
        m = positivos[0]
        console.print(
            f"  [dim]melhor   [/dim]  [bright_green]{m.pair}  "
            f"{m.retorno_pct:+.2f}%  win {m.win_rate:.0f}%  "
            f"{m.trades} trades[/bright_green]"
        )
    console.print()

def _print_table(title: str, results: List[ScanResult], highlight: bool):
    if not results:
        return

    color = "bright_green" if highlight else "dim red"

    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold dim",
        border_style="dim",
        pad_edge=False,
    )
    table.add_column(f"  {title}", style="white", min_width=14)
    table.add_column("vol 24h",   justify="right", min_width=10)
    table.add_column("trades",    justify="right", min_width=7)
    table.add_column("win rate",  justify="right", min_width=9)
    table.add_column("retorno",   justify="right", min_width=9)
    table.add_column("drawdown",  justify="right", min_width=10)
    table.add_column("capital",   justify="right", min_width=10)

    for r in results:
        ret_color = "bright_green" if r.retorno_pct > 0 else "bright_red"
        wr_color  = "bright_green" if r.win_rate >= 50 else "yellow" if r.win_rate >= 40 else "red"
        dd_color  = "bright_red"   if r.drawdown_pct > 10 else "yellow" if r.drawdown_pct > 5 else "green"
        vol_str   = f"${r.volume_24h/1_000_000:.0f}M"

        table.add_row(
            f"  {r.pair}",
            f"[dim]{vol_str}[/dim]",
            str(r.trades),
            f"[{wr_color}]{r.win_rate:.0f}%[/{wr_color}]",
            f"[{ret_color}]{r.retorno_pct:+.2f}%[/{ret_color}]",
            f"[{dd_color}]{r.drawdown_pct:.2f}%[/{dd_color}]",
            f"${r.capital_final:.2f}",
        )

    console.print(table)

def run():
    results = run_scan()
    print_scan(results)
