from dataclasses import dataclass, field
from itertools import product
from typing import Dict, List, Optional, Tuple

import pandas as pd
from rich import box
from rich.table import Table

from backtesting.engine import BacktestResult, precompute_signals, simulate_backtest
from backtesting.validation import split_train_validation
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
    validation_avg_return: Optional[float] = None
    validation_avg_drawdown: Optional[float] = None
    validation_total_trades: int = 0
    validation_symbols_skipped: List[str] = field(default_factory=list)


def run(symbols: list = None, timeframe: str = TIMEFRAME, candle_limit: int = 2000,
        validate: bool = False, walk_forward: bool = False):
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

    results = _optimize_multi(dfs, validate=validate or walk_forward)
    _print_results(results, symbols, validate=validate or walk_forward)

    if walk_forward and results:
        from backtesting.robustness import run_walk_forward_report
        run_walk_forward_report(dfs, results[0].params)

    return results


def _indicator_key(params: EmaRsiParams) -> tuple:
    return (params.ema_fast, params.ema_slow, params.ema_trend,
            params.rsi_period, params.bb_period, params.bb_std,
            params.volume_ma_period)


def _optimize_multi(
    dfs: Dict[str, pd.DataFrame],
    grid: dict = None,
    top_n: int = 15,
    min_trades_per_pair: int = 2,
    validate: bool = False,
) -> List[MultiOptResult]:
    results = []
    indicator_cache: Dict[tuple, Dict[str, pd.DataFrame]] = {}
    split_cache: Dict[tuple, Dict[str, Tuple[pd.DataFrame, Optional[pd.DataFrame]]]] = {}

    for params in _iter_param_sets(grid or DEFAULT_GRID):
        strategy = EmaRsiStrategy(params.strategy)
        ikey = _indicator_key(params.strategy)

        if ikey not in indicator_cache:
            indicator_cache[ikey] = {
                sym: strategy.calculate_indicators(raw_df)
                for sym, raw_df in dfs.items()
            }
        if validate and ikey not in split_cache:
            split_cache[ikey] = {
                sym: split_train_validation(prepared)
                for sym, prepared in indicator_cache[ikey].items()
            }

        pair_scores, pair_returns, pair_winrates, pair_drawdowns = [], [], [], []
        per_pair: Dict[str, float] = {}
        total_trades = 0

        for sym, prepared in indicator_cache[ikey].items():
            try:
                signals = precompute_signals(prepared, strategy)
                if validate:
                    eval_df, _validation_df = split_cache[ikey][sym]
                    eval_signals = signals.loc[eval_df.index]
                else:
                    eval_df = prepared
                    eval_signals = signals
                r = simulate_backtest(
                    eval_df,
                    strategy,
                    atr_sl_multiplier=params.atr_sl_multiplier,
                    atr_tp_multiplier=params.atr_tp_multiplier,
                    stop_loss_pct=params.stop_loss_pct,
                    take_profit_pct=params.take_profit_pct,
                    precomputed_signals=eval_signals,
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

    top = sorted(results, key=lambda r: r.avg_score, reverse=True)[:top_n]

    if validate:
        for item in top:
            _apply_validation(item, indicator_cache, split_cache)

    return top


def _apply_validation(
    item: MultiOptResult,
    indicator_cache: Dict[tuple, Dict[str, pd.DataFrame]],
    split_cache: Dict[tuple, Dict[str, Tuple[pd.DataFrame, Optional[pd.DataFrame]]]],
) -> None:
    """Reavalia um candidato ja escolhido (via fatia de treino) contra a fatia de
    validacao de cada simbolo. Muta `item` in-place -- so os top_n candidatos
    finais passam por aqui, nao a busca em grade inteira (custo desprezivel)."""
    strategy = EmaRsiStrategy(item.params.strategy)
    ikey = _indicator_key(item.params.strategy)

    returns, drawdowns = [], []
    total_trades = 0
    skipped: List[str] = []

    for sym, prepared in indicator_cache[ikey].items():
        _train_df, validation_df = split_cache[ikey][sym]
        if validation_df is None:
            skipped.append(sym)
            continue
        try:
            signals = precompute_signals(prepared, strategy)
            r = simulate_backtest(
                validation_df,
                strategy,
                atr_sl_multiplier=item.params.atr_sl_multiplier,
                atr_tp_multiplier=item.params.atr_tp_multiplier,
                stop_loss_pct=item.params.stop_loss_pct,
                take_profit_pct=item.params.take_profit_pct,
                start_index=0,
                precomputed_signals=signals.loc[validation_df.index],
            )
            returns.append(r.total_return_pct)
            drawdowns.append(r.max_drawdown_pct)
            total_trades += r.total_trades
        except Exception:
            skipped.append(sym)

    item.validation_avg_return = sum(returns) / len(returns) if returns else None
    item.validation_avg_drawdown = sum(drawdowns) / len(drawdowns) if drawdowns else None
    item.validation_total_trades = total_trades
    item.validation_symbols_skipped = skipped


def _iter_param_sets(grid: dict):
    keys = list(grid.keys())
    for values in product(*(grid[k] for k in keys)):
        raw = dict(zip(keys, values, strict=True))
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


def _print_results(results: List[MultiOptResult], symbols: list, validate: bool = False):
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
    if validate:
        table.add_column("retorno valid", justify="right", min_width=13)
        table.add_column("dd valid",      justify="right", min_width=9)
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
        row = [
            f"  {idx}",
            f"[{ret_color}]{item.avg_return:+.2f}%[/{ret_color}]",
            f"[{wr_color}]{item.avg_winrate:.0f}%[/{wr_color}]",
            f"{item.avg_drawdown:.2f}%",
            str(item.total_trades),
            f"{item.avg_score:.2f}",
        ]
        if validate:
            if item.validation_avg_return is None:
                row.append(f"[{C_DIM}]sem dados[/{C_DIM}]")
                row.append(f"[{C_DIM}]-[/{C_DIM}]")
            else:
                vret_color = C_POS if item.validation_avg_return >= 0 else C_NEG
                row.append(f"[{vret_color}]{item.validation_avg_return:+.2f}%[/{vret_color}]")
                row.append(f"{item.validation_avg_drawdown:.2f}%")
        row.append(param_text)
        table.add_row(*row)

        empty_cols = 8 if validate else 6
        extra = [""] * empty_cols + [per_pair_str]
        table.add_row(*extra)
        if validate and item.validation_symbols_skipped:
            skipped_str = f"  [{C_DIM}]sem validacao: {', '.join(item.validation_symbols_skipped)}[/{C_DIM}]"
            table.add_row(*([""] * empty_cols + [skipped_str]))

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
