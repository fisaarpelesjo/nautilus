from dataclasses import dataclass
from itertools import product
from typing import Iterable, List

import pandas as pd
from rich import box
from rich.table import Table

from backtesting.engine import BacktestResult, simulate_backtest
from config.settings import (
    ATR_SL_MULTIPLIER,
    ATR_TP_MULTIPLIER,
    SYMBOL,
    TIMEFRAME,
    STOP_LOSS_PCT,
    TAKE_PROFIT_PCT,
)
from data.fetcher import fetch_ohlcv
from strategy.ema_rsi import EmaRsiParams, EmaRsiStrategy
from utils.display import C_DIM, C_NEG, C_POS, console, header


@dataclass(frozen=True)
class OptimizationParams:
    strategy: EmaRsiParams
    stop_loss_pct: float = STOP_LOSS_PCT
    take_profit_pct: float = TAKE_PROFIT_PCT
    atr_sl_multiplier: float = ATR_SL_MULTIPLIER
    atr_tp_multiplier: float = ATR_TP_MULTIPLIER


@dataclass
class OptimizationResult:
    params: OptimizationParams
    result: BacktestResult
    score: float


DEFAULT_GRID = {
    "ema_fast": [7, 9, 12],
    "ema_slow": [21, 26],
    "rsi_overbought": [60, 65, 70],
    "volume_min_ratio": [1.0, 1.2],
    "bb_std": [2.0, 2.5],
    "atr_sl_multiplier": [1.2, 1.5, 2.0],
    "atr_tp_multiplier": [2.4, 3.0, 4.0],
}


def optimize_parameter_grid(
    df: pd.DataFrame,
    grid: dict | None = None,
    top_n: int = 10,
    min_trades: int = 2,
) -> List[OptimizationResult]:
    results = []
    for params in _iter_param_sets(grid or DEFAULT_GRID):
        strategy = EmaRsiStrategy(params.strategy)
        try:
            prepared = strategy.calculate_indicators(df)
            result = simulate_backtest(
                prepared,
                strategy,
                atr_sl_multiplier=params.atr_sl_multiplier,
                atr_tp_multiplier=params.atr_tp_multiplier,
                stop_loss_pct=params.stop_loss_pct,
                take_profit_pct=params.take_profit_pct,
            )
        except Exception:
            continue

        score = _score_result(result, min_trades=min_trades)
        results.append(OptimizationResult(params=params, result=result, score=score))

    return sorted(results, key=lambda r: r.score, reverse=True)[:top_n]


def run(symbol: str = SYMBOL, timeframe: str = TIMEFRAME, candle_limit: int = 2000):
    header()
    console.print(f"  [{C_DIM}]otimizando parametros para {symbol} {timeframe}[/{C_DIM}]")
    console.print()

    df = fetch_ohlcv(symbol, timeframe, limit=candle_limit)
    results = optimize_parameter_grid(df)
    _print_results(results)


def _iter_param_sets(grid: dict) -> Iterable[OptimizationParams]:
    keys = list(grid.keys())
    for values in product(*(grid[key] for key in keys)):
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


def _score_result(result: BacktestResult, min_trades: int = 2) -> float:
    if result.total_trades < min_trades:
        return -9999.0
    profit_factor = result.profit_factor if result.profit_factor != float("inf") else 10.0
    return (
        result.total_return_pct
        - result.max_drawdown_pct
        + profit_factor
        + result.win_rate / 20
        - result.max_losing_streak
    )


def _print_results(results: List[OptimizationResult]):
    if not results:
        console.print(f"  [{C_DIM}]nenhum resultado valido encontrado[/{C_DIM}]")
        console.print()
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim", border_style="dim", pad_edge=False)
    table.add_column("  rank", justify="right", min_width=5)
    table.add_column("retorno", justify="right", min_width=9)
    table.add_column("dd", justify="right", min_width=8)
    table.add_column("trades", justify="right", min_width=7)
    table.add_column("win", justify="right", min_width=7)
    table.add_column("score", justify="right", min_width=8)
    table.add_column("parametros", style="white", min_width=44)

    for idx, item in enumerate(results, 1):
        result = item.result
        params = item.params
        ret_color = C_POS if result.total_return_pct >= 0 else C_NEG
        param_text = (
            f"EMA {params.strategy.ema_fast}/{params.strategy.ema_slow}, "
            f"RSI<{params.strategy.rsi_overbought}, "
            f"Vol {params.strategy.volume_min_ratio:.1f}x, "
            f"BB {params.strategy.bb_std:.1f}, "
            f"ATR {params.atr_sl_multiplier:.1f}/{params.atr_tp_multiplier:.1f}"
        )
        table.add_row(
            f"  {idx}",
            f"[{ret_color}]{result.total_return_pct:+.2f}%[/{ret_color}]",
            f"{result.max_drawdown_pct:.2f}%",
            str(result.total_trades),
            f"{result.win_rate:.0f}%",
            f"{item.score:.2f}",
            param_text,
        )

    console.print(table)
    console.print()
