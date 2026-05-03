from dataclasses import dataclass, field
from itertools import product
from typing import Dict, List

import pandas as pd
from rich import box
from rich.console import Console
from rich.table import Table
import io, sys

from backtesting.engine import BacktestResult, precompute_signals, simulate_backtest
from config.settings import (
    ATR_SL_MULTIPLIER,
    ATR_TP_MULTIPLIER,
    STOP_LOSS_PCT,
    TAKE_PROFIT_PCT,
    TIMEFRAME,
)
from data.fetcher import fetch_ohlcv
from strategy.ema_rsi import EmaRsiParams, EmaRsiStrategy
from utils.display import C_DIM, C_NEG, C_POS, console, header

OPTIMIZE_PAIRS = [
    "BTC/USDT",
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT",
    "XRP/USDT",
]

DEFAULT_GRID = {
    "ema_fast":         [7, 9, 12],
    "ema_slow":         [21, 26],
    "rsi_overbought":   [60, 65, 70],
    "volume_min_ratio": [1.0, 1.2],
    "bb_std":           [2.0, 2.5],
    "atr_sl_multiplier": [1.2, 1.5, 2.0],
    "atr_tp_multiplier": [2.4, 3.0, 4.0],
}


@dataclass(frozen=True)
class OptimizationParams:
    strategy: EmaRsiParams
    stop_loss_pct: float = STOP_LOSS_PCT
    take_profit_pct: float = TAKE_PROFIT_PCT
    atr_sl_multiplier: float = ATR_SL_MULTIPLIER
    atr_tp_multiplier: float = ATR_TP_MULTIPLIER


@dataclass
class MultiOptResult:
    params: OptimizationParams
    avg_score: float
    avg_return: float
    avg_winrate: float
    avg_drawdown: float
    total_trades: int
    per_pair: Dict[str, float] = field(default_factory=dict)


def run(symbols: list = None, timeframe: str = TIMEFRAME, candle_limit: int = 2000):
    symbols = symbols or OPTIMIZE_PAIRS
    header()
    console.print(f"  [{C_DIM}]otimizando parametros em {len(symbols)} pares · {timeframe} · {candle_limit} candles[/{C_DIM}]")
    console.print(f"  [{C_DIM}]pares: {', '.join(symbols)}[/{C_DIM}]")
    console.print()

    dfs: Dict[str, pd.DataFrame] = {}
    for sym in symbols:
        with console.status(f"  [{C_DIM}]carregando {sym}...[/{C_DIM}]", spinner="dots", spinner_style="cyan"):
            dfs[sym] = fetch_ohlcv(sym, timeframe, limit=candle_limit)

    console.print()
    total_combos = sum(1 for _ in _iter_param_sets(DEFAULT_GRID))
    console.print(f"  [{C_DIM}]testando {total_combos} combinacoes × {len(symbols)} pares...[/{C_DIM}]")
    console.print()

    results = _optimize_multi(dfs)
    _print_results(results, symbols)


def _indicator_key(params: EmaRsiParams) -> tuple:
    return (params.ema_fast, params.ema_slow, params.ema_trend,
            params.rsi_period, params.bb_period, params.bb_std,
            params.volume_ma_period)


def _optimize_multi(
    dfs: Dict[str, pd.DataFrame],
    grid: dict = None,
    top_n: int = 15,
    min_trades_per_pair: int = 2,
) -> List[MultiOptResult]:
    results = []
    indicator_cache: Dict[tuple, Dict[str, pd.DataFrame]] = {}

    for params in _iter_param_sets(grid or DEFAULT_GRID):
        strategy = EmaRsiStrategy(params.strategy)
        ikey = _indicator_key(params.strategy)

        if ikey not in indicator_cache:
            indicator_cache[ikey] = {
                sym: strategy.calculate_indicators(raw_df)
                for sym, raw_df in dfs.items()
            }

        pair_scores, pair_returns, pair_winrates, pair_drawdowns = [], [], [], []
        per_pair: Dict[str, float] = {}
        total_trades = 0

        for sym, prepared in indicator_cache[ikey].items():
            try:
                signals = precompute_signals(prepared, strategy)
                r = simulate_backtest(
                    prepared,
                    strategy,
                    atr_sl_multiplier=params.atr_sl_multiplier,
                    atr_tp_multiplier=params.atr_tp_multiplier,
                    stop_loss_pct=params.stop_loss_pct,
                    take_profit_pct=params.take_profit_pct,
                    precomputed_signals=signals,
                )
                score = _score(r, min_trades=min_trades_per_pair)
                pair_scores.append(score)
                pair_returns.append(r.total_return_pct)
                pair_winrates.append(r.win_rate)
                pair_drawdowns.append(r.max_drawdown_pct)
                per_pair[sym] = r.total_return_pct
                total_trades += r.total_trades
            except Exception:
                pair_scores.append(-9999.0)
                per_pair[sym] = 0.0

        if not pair_scores:
            continue

        results.append(MultiOptResult(
            params=params,
            avg_score=sum(pair_scores) / len(pair_scores),
            avg_return=sum(pair_returns) / len(pair_returns) if pair_returns else 0.0,
            avg_winrate=sum(pair_winrates) / len(pair_winrates) if pair_winrates else 0.0,
            avg_drawdown=sum(pair_drawdowns) / len(pair_drawdowns) if pair_drawdowns else 0.0,
            total_trades=total_trades,
            per_pair=per_pair,
        ))

    return sorted(results, key=lambda r: r.avg_score, reverse=True)[:top_n]


def _iter_param_sets(grid: dict):
    keys = list(grid.keys())
    for values in product(*(grid[k] for k in keys)):
        raw = dict(zip(keys, values))
        if raw["ema_fast"] >= raw["ema_slow"]:
            continue
        yield OptimizationParams(
            strategy=EmaRsiParams(
                ema_fast=raw["ema_fast"],
                ema_slow=raw["ema_slow"],
                rsi_overbought=raw["rsi_overbought"],
                volume_min_ratio=raw["volume_min_ratio"],
                bb_std=raw["bb_std"],
            ),
            atr_sl_multiplier=raw["atr_sl_multiplier"],
            atr_tp_multiplier=raw["atr_tp_multiplier"],
        )


def _score(r: BacktestResult, min_trades: int = 2) -> float:
    if r.total_trades < min_trades:
        return -9999.0
    pf = r.profit_factor if r.profit_factor != float("inf") else 10.0
    return (
        r.total_return_pct
        - r.max_drawdown_pct
        + pf
        + r.win_rate / 20
        - r.max_losing_streak
    )


def _print_results(results: List[MultiOptResult], symbols: list):
    if not results:
        console.print(f"  [{C_DIM}]nenhum resultado valido encontrado[/{C_DIM}]")
        console.print()
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim", border_style="dim", pad_edge=False)
    table.add_column("  #",         justify="right",  min_width=4)
    table.add_column("retorno med", justify="right",  min_width=11)
    table.add_column("win med",     justify="right",  min_width=8)
    table.add_column("dd med",      justify="right",  min_width=8)
    table.add_column("trades",      justify="right",  min_width=7)
    table.add_column("score",       justify="right",  min_width=8)
    table.add_column("parametros",  style="white",    min_width=52)

    for idx, item in enumerate(results, 1):
        p = item.params
        ret_color = C_POS if item.avg_return >= 0 else C_NEG
        wr_color  = C_POS if item.avg_winrate >= 50 else "yellow" if item.avg_winrate >= 40 else C_NEG
        per_pair_str = "  " + "  ".join(
            f"[{C_POS if v >= 0 else C_NEG}]{s.split('/')[0]}:{v:+.1f}%[/]"
            for s, v in item.per_pair.items()
        )
        param_text = (
            f"EMA {p.strategy.ema_fast}/{p.strategy.ema_slow}  "
            f"RSI<{p.strategy.rsi_overbought}  "
            f"vol {p.strategy.volume_min_ratio:.1f}x  "
            f"BB {p.strategy.bb_std:.1f}  "
            f"ATR {p.atr_sl_multiplier:.1f}/{p.atr_tp_multiplier:.1f}"
        )
        table.add_row(
            f"  {idx}",
            f"[{ret_color}]{item.avg_return:+.2f}%[/{ret_color}]",
            f"[{wr_color}]{item.avg_winrate:.0f}%[/{wr_color}]",
            f"{item.avg_drawdown:.2f}%",
            str(item.total_trades),
            f"{item.avg_score:.2f}",
            param_text,
        )
        table.add_row("", "", "", "", "", "", per_pair_str)

    console.print(table)

    best = results[0]
    console.print(f"  [{C_DIM}]melhores parametros:[/{C_DIM}]")
    console.print(f"  [white]EMA_FAST={best.params.strategy.ema_fast}[/white]")
    console.print(f"  [white]EMA_SLOW={best.params.strategy.ema_slow}[/white]")
    console.print(f"  [white]RSI_OVERBOUGHT={best.params.strategy.rsi_overbought}[/white]")
    console.print(f"  [white]VOLUME_MIN_RATIO={best.params.strategy.volume_min_ratio}[/white]")
    console.print(f"  [white]BB_STD={best.params.strategy.bb_std}[/white]")
    console.print(f"  [white]ATR_SL_MULTIPLIER={best.params.atr_sl_multiplier}[/white]")
    console.print(f"  [white]ATR_TP_MULTIPLIER={best.params.atr_tp_multiplier}[/white]")
    console.print()
