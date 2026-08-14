import random
from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd

from backtesting.engine import BacktestResult, Trade, precompute_signals, simulate_backtest
from backtesting.validation import MIN_WINDOW_CANDLES
from config.settings import EDGE_MIN_TRADES
from strategy.ema_rsi import EmaRsiStrategy
from utils.display import C_CYAN, C_DIM, C_NEG, C_POS, console
from utils.logger import get_logger

log = get_logger("backtest")

DEFAULT_MIN_WINDOWS = 3


def split_walk_forward_windows(
    df: pd.DataFrame,
    min_windows: int = DEFAULT_MIN_WINDOWS,
    min_window_candles: int = MIN_WINDOW_CANDLES,
) -> List[pd.DataFrame]:
    """Divide candles em `min_windows` fatias contiguas e nao sobrepostas (sem
    embaralhar -- dado e serie temporal), cobrindo o df inteiro.

    Retorna lista vazia se o historico nao cobrir `min_windows` janelas de
    `min_window_candles` cada -- MUST NOT rodar com menos janelas silenciosamente
    (FR-006).
    """
    if len(df) < min_windows * min_window_candles:
        return []

    window_size = len(df) // min_windows
    windows = []
    for i in range(min_windows):
        start = i * window_size
        end = (i + 1) * window_size if i < min_windows - 1 else len(df)
        windows.append(df.iloc[start:end])
    return windows


@dataclass
class WalkForwardWindow:
    window_index: int
    period_start: pd.Timestamp
    period_end: pd.Timestamp
    result: BacktestResult


@dataclass
class WalkForwardResult:
    status: str  # "ok" | "dados_insuficientes"
    windows: List[WalkForwardWindow] = field(default_factory=list)
    avg_return_pct: float = 0.0
    worst_window: Optional[WalkForwardWindow] = None


def walk_forward_validate(
    df: pd.DataFrame,
    strategy_params,
    min_windows: int = DEFAULT_MIN_WINDOWS,
    initial_capital: float = 1000.0,
) -> WalkForwardResult:
    """Avalia um conjunto de parametros JA ESCOLHIDO (nao reotimiza) em
    `min_windows` janelas deslizantes independentes -- confirma que o conjunto se
    sustenta em mais de um recorte de mercado, sem multiplicar o custo da busca em
    grade por janela (ver research.md)."""
    strategy = EmaRsiStrategy(strategy_params.strategy)
    prepared = strategy.calculate_indicators(df.copy())
    signals = precompute_signals(prepared, strategy)

    raw_windows = split_walk_forward_windows(prepared, min_windows=min_windows)
    if not raw_windows:
        return WalkForwardResult(status="dados_insuficientes")

    windows = []
    for i, window_df in enumerate(raw_windows):
        # so a primeira janela comeca no inicio do df completo e carrega NaN de
        # warmup de indicador; as demais ja herdam historico anterior valido do
        # mesmo df precomputado (mesmo raciocinio de split_train_validation).
        start_index = 100 if i == 0 else 0
        r = simulate_backtest(
            window_df,
            strategy,
            initial_capital=initial_capital,
            atr_sl_multiplier=strategy_params.atr_sl_multiplier,
            atr_tp_multiplier=strategy_params.atr_tp_multiplier,
            stop_loss_pct=strategy_params.stop_loss_pct,
            take_profit_pct=strategy_params.take_profit_pct,
            start_index=start_index,
            precomputed_signals=signals.loc[window_df.index],
        )
        windows.append(WalkForwardWindow(
            window_index=i,
            period_start=window_df.index[0],
            period_end=window_df.index[-1],
            result=r,
        ))

    avg_return = sum(w.result.total_return_pct for w in windows) / len(windows)
    worst = min(windows, key=lambda w: w.result.total_return_pct)
    return WalkForwardResult(status="ok", windows=windows, avg_return_pct=avg_return, worst_window=worst)


def run_walk_forward_report(dfs: dict, strategy_params, min_windows: int = DEFAULT_MIN_WINDOWS) -> None:
    console.print()
    console.print(f"[bold {C_CYAN}]VALIDACAO WALK-FORWARD[/]")
    log.info("\nVALIDACAO WALK-FORWARD")

    for sym, raw_df in dfs.items():
        result = walk_forward_validate(raw_df, strategy_params, min_windows=min_windows)
        console.print(f"  [{C_CYAN}]{sym}[/]")
        log.info(f"  {sym}")

        if result.status == "dados_insuficientes":
            msg = f"    dados insuficientes para {min_windows} janelas walk-forward"
            console.print(f"[{C_DIM}]{msg}[/]")
            log.info(msg)
            continue

        for w in result.windows:
            ret_color = C_POS if w.result.total_return_pct >= 0 else C_NEG
            plain = (
                f"    janela {w.window_index + 1}  "
                f"{w.period_start.strftime('%Y-%m-%d')} -> {w.period_end.strftime('%Y-%m-%d')}  "
                f"retorno {w.result.total_return_pct:+.2f}%  "
                f"drawdown {w.result.max_drawdown_pct:.2f}%  "
                f"trades {w.result.total_trades}"
            )
            markup = (
                f"    janela {w.window_index + 1}  "
                f"{w.period_start.strftime('%Y-%m-%d')} -> {w.period_end.strftime('%Y-%m-%d')}  "
                f"retorno [{ret_color}]{w.result.total_return_pct:+.2f}%[/{ret_color}]  "
                f"drawdown {w.result.max_drawdown_pct:.2f}%  "
                f"trades {w.result.total_trades}"
            )
            console.print(markup)
            log.info(plain)

        worst = result.worst_window
        console.print(
            f"    [{C_DIM}]media {result.avg_return_pct:+.2f}%  |  "
            f"pior janela: {worst.window_index + 1} ({worst.result.total_return_pct:+.2f}%)[/]"
        )
        log.info(f"    media {result.avg_return_pct:+.2f}%  |  pior janela: {worst.window_index + 1} ({worst.result.total_return_pct:+.2f}%)")


DEFAULT_MONTE_CARLO_SIMULATIONS = 1000


@dataclass
class MonteCarloResult:
    n_simulations: int
    max_drawdown_median_pct: float
    max_drawdown_p95_pct: float
    worst_losing_streak_median: int
    low_confidence: bool
    sample_size: int


def monte_carlo_resample(
    trades: List[Trade],
    n_simulations: int = DEFAULT_MONTE_CARLO_SIMULATIONS,
    seed: Optional[int] = None,
    initial_capital: float = 1000.0,
) -> MonteCarloResult:
    """Reamostra (bootstrap COM reposicao, metodo padrao para amostra pequena --
    ver research.md) a ordem da sequencia de PnLs de trades ja fechados, estimando
    a distribuicao de drawdown maximo e maior sequencia de perdas alem do valor
    unico ja observado no backtest original."""
    sample_size = len(trades)
    if sample_size == 0:
        return MonteCarloResult(
            n_simulations=0, max_drawdown_median_pct=0.0, max_drawdown_p95_pct=0.0,
            worst_losing_streak_median=0, low_confidence=True, sample_size=0,
        )

    pnls = [t.pnl for t in trades]
    rng = random.Random(seed)

    drawdowns: List[float] = []
    streaks: List[int] = []
    for _ in range(n_simulations):
        resampled = [rng.choice(pnls) for _ in range(sample_size)]
        drawdowns.append(_max_drawdown_pct_from_pnls(resampled, initial_capital))
        streaks.append(_max_losing_streak_from_pnls(resampled))

    drawdowns.sort()
    streaks.sort()

    return MonteCarloResult(
        n_simulations=n_simulations,
        max_drawdown_median_pct=_percentile(drawdowns, 50),
        max_drawdown_p95_pct=_percentile(drawdowns, 95),
        worst_losing_streak_median=round(_percentile(streaks, 50)),
        low_confidence=sample_size < EDGE_MIN_TRADES,
        sample_size=sample_size,
    )


def _max_drawdown_pct_from_pnls(pnls: List[float], initial_capital: float) -> float:
    equity = initial_capital
    peak = initial_capital
    max_dd = 0.0
    for pnl in pnls:
        equity += pnl
        peak = max(peak, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak * 100)
    return max_dd


def _max_losing_streak_from_pnls(pnls: List[float]) -> int:
    current = longest = 0
    for pnl in pnls:
        if pnl < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _percentile(sorted_values: List[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * (pct / 100)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


def run_monte_carlo_report(trades: List[Trade], n_simulations: int = DEFAULT_MONTE_CARLO_SIMULATIONS) -> None:
    result = monte_carlo_resample(trades, n_simulations=n_simulations)

    console.print()
    console.print(f"[bold {C_CYAN}]ANALISE MONTE CARLO[/]")
    log.info("\nANALISE MONTE CARLO")

    if result.sample_size == 0:
        msg = "  sem trades para reamostrar"
        console.print(f"[{C_DIM}]{msg}[/]")
        log.info(msg)
        return

    console.print(f"  [{C_DIM}]{result.n_simulations} simulacoes sobre {result.sample_size} trades[/]")
    log.info(f"  {result.n_simulations} simulacoes sobre {result.sample_size} trades")
    console.print(
        f"  drawdown maximo: mediana [{C_NEG}]{result.max_drawdown_median_pct:.2f}%[/{C_NEG}]  "
        f"p95 [{C_NEG}]{result.max_drawdown_p95_pct:.2f}%[/{C_NEG}]"
    )
    log.info(f"  drawdown maximo: mediana {result.max_drawdown_median_pct:.2f}%  p95 {result.max_drawdown_p95_pct:.2f}%")
    console.print(f"  maior sequencia de perdas esperada (mediana): {result.worst_losing_streak_median}")
    log.info(f"  maior sequencia de perdas esperada (mediana): {result.worst_losing_streak_median}")

    if result.low_confidence:
        msg = f"  confianca baixa: amostra de {result.sample_size} trades abaixo do minimo recomendado ({EDGE_MIN_TRADES})"
        console.print(f"[{C_DIM}]{msg}[/]")
        log.info(msg)
