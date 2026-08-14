import ccxt
import io
import sys
from typing import List, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich import box

from backtesting.approval import ApprovalVerdict, evaluate_approval, ranking_key, verdict_markup
from backtesting.engine import edge_score_band, run_backtest
from config.settings import (
    BLACKLIST_PAIRS, EMA_FAST, EMA_SLOW, EMA_TREND,
    ATR_SL_MULTIPLIER, ATR_TP_MULTIPLIER,
)
from market.selector import is_blacklisted
from utils.logger import get_logger

log = get_logger("scanner")

_stdout_utf8 = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
# width fixo: sem terminal real (pipe, log redirecionado, CI), Rich cai para ~79
# colunas e derruba silenciosamente as ultimas colunas da tabela quando elas nao
# cabem -- achado de /code-review high depois que as colunas de edge score/veredito
# empurraram a tabela para alem desse fallback.
console = Console(file=_stdout_utf8, highlight=False, force_terminal=True, width=150)

MIN_VOLUME_USDT = 10_000_000   # mínimo $10M volume 24h
TOP_N           = 30            # top N pares por volume

STABLECOINS = {"USDC", "BUSD", "TUSD", "USDP", "DAI", "FDUSD", "USDT", "USDS"}
TIMEFRAME       = "4h"
CANDLE_LIMIT    = 2000

@dataclass
class ScanResult:
    pair: str
    volume_24h: float = 0.0
    trades: int = 0
    win_rate: float = 0.0
    retorno_pct: float = 0.0
    drawdown_pct: float = 0.0
    capital_final: float = 0.0
    profit_factor: float = 0.0
    buy_hold_return_pct: float = 0.0
    edge_score: float = float("-inf")
    verdict: Optional[ApprovalVerdict] = None
    error: Optional[str] = None

def get_top_pairs() -> List[str]:
    console.print("  [dim cyan]buscando mercados da Binance...[/dim cyan]")
    exchange = ccxt.binance({"enableRateLimit": True, "options": {"fetchCurrencies": False}})
    tickers  = exchange.fetch_tickers()

    pairs = []
    for symbol, ticker in tickers.items():
        if not symbol.endswith("/USDT"):
            continue
        base = symbol.split("/")[0]
        if base in STABLECOINS or is_blacklisted(symbol, BLACKLIST_PAIRS):
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
                    pair                = pair,
                    volume_24h          = vol,
                    trades              = r.total_trades,
                    win_rate            = r.win_rate,
                    retorno_pct         = r.total_return_pct,
                    drawdown_pct        = r.max_drawdown_pct,
                    capital_final       = r.final_capital,
                    profit_factor       = r.profit_factor,
                    buy_hold_return_pct = r.buy_hold_return_pct,
                    edge_score          = r.edge_score,
                    verdict             = evaluate_approval(r),
                ))
            except Exception as e:
                log.error(f"{pair}: {e}")
                results.append(ScanResult(pair=pair, error=str(e)))

    # ranking_key compartilhado com backtesting/multi.py (mesmo criterio de
    # desempate e protecao contra amostra minuscula).
    results.sort(key=ranking_key, reverse=True)
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
        f"[dim cyan]{TIMEFRAME} · EMA {EMA_FAST}/{EMA_SLOW}/{EMA_TREND} · "
        f"SL {ATR_SL_MULTIPLIER}×ATR · TP {ATR_TP_MULTIPLIER}×ATR · top {TOP_N} pares[/dim cyan]"
    )
    console.print("  [dim]" + "─" * 74 + "[/dim]")
    console.print()

    valid   = [r for r in results if r.error is None]
    errors  = [r for r in results if r.error is not None]
    positivos = [r for r in valid if r.retorno_pct > 0]
    negativos = [r for r in valid if r.retorno_pct <= 0]

    _print_table("melhores oportunidades", positivos[:10], highlight=True)
    _print_table("evitar", negativos[-5:], highlight=False)
    if errors:
        console.print(f"  [bright_red]{len(errors)} par(es) com erro:[/bright_red]")
        for r in errors:
            console.print(f"    [dim]{r.pair}[/dim]  [bright_red]{r.error}[/bright_red]")
        console.print()

    console.print("  [dim]" + "─" * 74 + "[/dim]")
    console.print()
    console.print(f"  [dim]positivos[/dim]  [bright_green]{len(positivos)}/{len(valid)}[/bright_green]")
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
    table.add_column(f"  {title}", style=color, min_width=14)
    table.add_column("vol 24h",   justify="right", min_width=10)
    table.add_column("trades",    justify="right", min_width=7)
    table.add_column("win rate",  justify="right", min_width=9)
    table.add_column("retorno",   justify="right", min_width=9)
    table.add_column("drawdown",  justify="right", min_width=10)
    table.add_column("capital",   justify="right", min_width=10)
    table.add_column("edge score", justify="right", min_width=14)
    table.add_column("veredito",  justify="right", min_width=12)

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
            f"{r.edge_score:+.1f} {edge_score_band(r.edge_score)}",
            verdict_markup(r.verdict),
        )

    console.print(table)

def run():
    results = run_scan()
    print_scan(results)
