import pandas as pd
from dataclasses import dataclass
from math import sqrt
from typing import List, Optional
from config.settings import (
    STOP_LOSS_PCT,
    TAKE_PROFIT_PCT,
    ATR_SL_MULTIPLIER,
    ATR_TP_MULTIPLIER,
    MAX_STOP_LOSS_PCT,
    MAX_ORDER_SIZE_USDT,
    BACKTEST_FEE_RATE,
    BACKTEST_SLIPPAGE_PCT,
    REGIME_FILTER_ENABLED,
    HIGH_VOLATILITY_ATR_RATIO,
    HIGH_VOLATILITY_FILTER_ENABLED,
    ADAPTIVE_BOLLINGER_ENABLED,
)
from strategy.base import BaseStrategy, Signal
from strategy.ema_rsi import EmaRsiStrategy
from data.fetcher import fetch_ohlcv
from utils.display import C_CYAN, C_DIM, C_LABEL, C_NEG, C_POS, C_PRICE, console, _fmt_price
from utils.logger import get_logger

log = get_logger("backtest")

@dataclass
class Trade:
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    fees: float
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    exit_reason: str

@dataclass
class BacktestResult:
    trades: List[Trade]
    initial_capital: float
    final_capital: float
    total_return_pct: float
    win_rate: float
    total_trades: int
    max_drawdown_pct: float
    profit_factor: float
    expectancy: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    max_losing_streak: int
    exposure_pct: float
    sharpe: float
    expectancy_pct: float
    payoff_ratio: float
    buy_hold_return_pct: float
    edge_return_pct: float
    edge_score: float
    sortino: float
    calmar: float
    annualized_return_pct: float
    return_per_exposure_pct: Optional[float]

def run_backtest(
    symbol: str, timeframe: str, initial_capital: float = 1000.0, candle_limit: int = 2000,
    strategy: Optional[BaseStrategy] = None,
) -> BacktestResult:
    df = fetch_ohlcv(symbol, timeframe, limit=candle_limit)
    strategy = strategy or EmaRsiStrategy()
    df = strategy.calculate_indicators(df)

    result = simulate_backtest(df, strategy, initial_capital=initial_capital)
    print_report(result)
    return result


def precompute_signals(df: pd.DataFrame, strategy: EmaRsiStrategy) -> pd.Series:
    p = strategy.params

    prev_ef = df["ema_fast"].shift(1)
    prev_es = df["ema_slow"].shift(1)

    bullish_cross = (prev_ef < prev_es) & (df["ema_fast"] > df["ema_slow"])
    bearish_cross = (prev_ef > prev_es) & (df["ema_fast"] < df["ema_slow"])

    above_trend      = df["close"] > df["ema_trend"]
    volume_ok        = df["volume"] >= df["volume_ma"] * p.volume_min_ratio
    # Mesmos filtros aditivos ja aplicados em EmaRsiStrategy.generate_signal()
    # (strategy/ema_rsi.py) -- este caminho vetorizado precisa reproduzi-los
    # identicamente, senao optimize/backtest --validate/optimize --walk-forward
    # (que usam este caminho) divergem silenciosamente de backtest/edge/compare
    # (que usam generate_signal por candle) assim que qualquer flag e ligada
    # (achado de code-review).
    adaptive_breakout_ok = ADAPTIVE_BOLLINGER_ENABLED & above_trend & volume_ok
    not_overextended = (df["close"] <= df["bb_upper"]) | adaptive_breakout_ok
    rsi_buy_ok       = df["rsi"] < p.rsi_overbought
    rsi_sell_ok      = df["rsi"] > p.rsi_oversold

    regime_blocks_entry = pd.Series(False, index=df.index)
    if REGIME_FILTER_ENABLED and "regime" in df.columns:
        regime_blocks_entry = df["regime"].isin(["sideways", "indefinido"])

    high_volatility = pd.Series(False, index=df.index)
    if HIGH_VOLATILITY_FILTER_ENABLED and "atr_ratio" in df.columns:
        high_volatility = df["atr_ratio"] > HIGH_VOLATILITY_ATR_RATIO

    if p.pullback_entry_enabled:
        trend_aligned = (
            (df["ema_fast"] > df["ema_slow"]) &
            (df["ema_slow"] > df["ema_trend"]) &
            above_trend
        )
        pullback = (
            trend_aligned &
            (df["rsi"] >= p.pullback_rsi_min) & rsi_buy_ok &
            (df["low"] <= df["ema_slow"] * (1 + p.pullback_max_distance_pct)) &
            (df["close"] > df["ema_fast"]) &
            (df["close"] > df["open"])
        )
    else:
        pullback = pd.Series(False, index=df.index)

    buy  = (bullish_cross & above_trend & rsi_buy_ok & volume_ok & not_overextended) | (pullback & volume_ok & not_overextended)
    # Regime/volatilidade bloqueiam so novas entradas -- nunca a saida
    # (venda), mesmo escopo ja aplicado em generate_signal().
    buy  = buy & ~regime_blocks_entry & ~high_volatility
    sell = bearish_cross & rsi_sell_ok

    result = pd.Series(Signal.HOLD, index=df.index)
    result[sell] = Signal.SELL
    result[buy]  = Signal.BUY
    return result


def simulate_backtest(
    df: pd.DataFrame,
    strategy,
    initial_capital: float = 1000.0,
    start_index: int = 100,
    fee_rate: float = BACKTEST_FEE_RATE,
    slippage_pct: float = BACKTEST_SLIPPAGE_PCT,
    stop_loss_pct: float = STOP_LOSS_PCT,
    take_profit_pct: float = TAKE_PROFIT_PCT,
    atr_sl_multiplier: float = ATR_SL_MULTIPLIER,
    atr_tp_multiplier: float = ATR_TP_MULTIPLIER,
    precomputed_signals: Optional[pd.Series] = None,
) -> BacktestResult:
    capital = initial_capital
    trades: List[Trade] = []
    peak_equity = initial_capital
    max_drawdown_pct = 0.0

    in_position = False
    entry_price = 0.0
    entry_time = None
    quantity = 0.0
    entry_cost = 0.0
    entry_fee = 0.0
    entry_atr = 0.0

    for i in range(start_index, len(df)):
        current = df.iloc[i]
        price = current["close"]
        equity = capital + (quantity * price * (1 - slippage_pct) if in_position else 0.0)
        peak_equity = max(peak_equity, equity)
        if peak_equity > 0:
            max_drawdown_pct = max(max_drawdown_pct, (peak_equity - equity) / peak_equity * 100)

        if precomputed_signals is not None:
            sig = precomputed_signals.iloc[i]
        else:
            sig = strategy.generate_signal(df.iloc[:i]).signal

        if in_position:
            exit_reason = None
            exit_price = price * (1 - slippage_pct)

            stop_price = _stop_price(entry_price, entry_atr, stop_loss_pct, atr_sl_multiplier)
            take_price = _take_profit_price(entry_price, entry_atr, take_profit_pct, atr_tp_multiplier)

            if current["low"] <= stop_price:
                exit_reason = "Stop Loss"
                exit_price = stop_price * (1 - slippage_pct)
            elif current["high"] >= take_price:
                exit_reason = "Take Profit"
                exit_price = take_price * (1 - slippage_pct)

            if sig == Signal.SELL and exit_reason is None:
                exit_reason = "Sinal de venda"

            if exit_reason:
                capital, trade = _close_trade(
                    capital, entry_price, exit_price, quantity, entry_cost, entry_fee,
                    entry_time, current.name, exit_reason, fee_rate
                )
                trades.append(trade)

                in_position = False
                quantity = 0.0
        else:
            if sig == Signal.BUY and capital >= 10:
                order_size = min(MAX_ORDER_SIZE_USDT, capital * 0.95)
                if order_size * (1 + fee_rate) > capital:
                    order_size = capital / (1 + fee_rate)
                entry_price = price * (1 + slippage_pct)
                quantity = order_size / entry_price
                entry_fee = order_size * fee_rate
                entry_cost = order_size + entry_fee
                entry_atr = float(current.get("atr", 0) or 0)
                capital -= entry_cost
                entry_time = current.name
                in_position = True

    if in_position and len(df) > 0:
        current = df.iloc[-1]
        exit_price = current["close"] * (1 - slippage_pct)
        capital, trade = _close_trade(
            capital, entry_price, exit_price, quantity, entry_cost, entry_fee,
            entry_time, current.name, "Fim do periodo", fee_rate
        )
        trades.append(trade)

    wins = [t for t in trades if t.pnl > 0]
    total_return = (capital - initial_capital) / initial_capital * 100
    win_rate = len(wins) / len(trades) * 100 if trades else 0
    buy_hold_return = _buy_hold_return_pct(df, initial_capital, start_index, fee_rate, slippage_pct)
    edge_return = total_return - buy_hold_return
    metrics = _calculate_advanced_metrics(
        trades,
        total_return_pct=total_return,
        buy_hold_return_pct=buy_hold_return,
        max_drawdown_pct=max_drawdown_pct,
        period_start=df.index[start_index] if len(df) > start_index else None,
        period_end=df.index[-1] if len(df) > 0 else None,
    )

    result = BacktestResult(
        trades=trades,
        initial_capital=initial_capital,
        final_capital=capital,
        total_return_pct=total_return,
        win_rate=win_rate,
        total_trades=len(trades),
        max_drawdown_pct=max_drawdown_pct,
        buy_hold_return_pct=buy_hold_return,
        edge_return_pct=edge_return,
        **metrics,
    )

    return result


def _calculate_advanced_metrics(
    trades: List[Trade],
    total_return_pct: float = 0.0,
    buy_hold_return_pct: float = 0.0,
    max_drawdown_pct: float = 0.0,
    period_start=None,
    period_end=None,
) -> dict:
    wins = [t.pnl for t in trades if t.pnl > 0]
    losses = [t.pnl for t in trades if t.pnl < 0]
    win_returns = [t.pnl_pct for t in trades if t.pnl > 0]
    loss_returns = [t.pnl_pct for t in trades if t.pnl < 0]
    total_profit = sum(wins)
    total_loss = abs(sum(losses))
    trade_returns = [t.pnl_pct for t in trades]

    profit_factor = total_profit / total_loss if total_loss else (float("inf") if total_profit > 0 else 0.0)
    average_win = total_profit / len(wins) if wins else 0.0
    average_loss = sum(losses) / len(losses) if losses else 0.0
    expectancy = sum(t.pnl for t in trades) / len(trades) if trades else 0.0
    largest_win = max(wins) if wins else 0.0
    largest_loss = min(losses) if losses else 0.0
    max_losing_streak = _max_losing_streak(trades)
    exposure_pct = _exposure_pct(trades, period_start, period_end)
    sharpe = _simplified_sharpe(trade_returns)
    sortino = _simplified_sortino(trade_returns)
    annualized_return = _annualized_return_pct(total_return_pct, period_start, period_end)
    calmar = (
        annualized_return / max_drawdown_pct if max_drawdown_pct > 0
        else (float("inf") if annualized_return > 0 else 0.0)
    )
    expectancy_pct = sum(trade_returns) / len(trade_returns) if trade_returns else 0.0
    avg_win_pct = sum(win_returns) / len(win_returns) if win_returns else 0.0
    avg_loss_pct = sum(loss_returns) / len(loss_returns) if loss_returns else 0.0
    payoff_ratio = avg_win_pct / abs(avg_loss_pct) if avg_loss_pct else (float("inf") if avg_win_pct > 0 else 0.0)
    return_per_exposure_pct = total_return_pct / (exposure_pct / 100) if exposure_pct > 0 else None
    score = edge_score(
        total_return_pct=total_return_pct,
        buy_hold_return_pct=buy_hold_return_pct,
        profit_factor=profit_factor,
        expectancy_pct=expectancy_pct,
        max_losing_streak=max_losing_streak,
        trade_count=len(trades),
    )

    return {
        "profit_factor": profit_factor,
        "expectancy": expectancy,
        "average_win": average_win,
        "average_loss": average_loss,
        "largest_win": largest_win,
        "largest_loss": largest_loss,
        "max_losing_streak": max_losing_streak,
        "exposure_pct": exposure_pct,
        "sharpe": sharpe,
        "sortino": sortino,
        "calmar": calmar,
        "annualized_return_pct": annualized_return,
        "return_per_exposure_pct": return_per_exposure_pct,
        "expectancy_pct": expectancy_pct,
        "payoff_ratio": payoff_ratio,
        "edge_score": score,
    }


def _buy_hold_return_pct(
    df: pd.DataFrame,
    initial_capital: float,
    start_index: int,
    fee_rate: float,
    slippage_pct: float,
) -> float:
    if initial_capital <= 0 or len(df) <= start_index:
        return 0.0

    entry_price = float(df.iloc[start_index]["close"]) * (1 + slippage_pct)
    exit_price = float(df.iloc[-1]["close"]) * (1 - slippage_pct)
    if entry_price <= 0 or exit_price <= 0:
        return 0.0

    order_size = initial_capital / (1 + fee_rate)
    entry_fee = order_size * fee_rate
    quantity = order_size / entry_price
    gross_exit = quantity * exit_price
    exit_fee = gross_exit * fee_rate
    final_capital = gross_exit - exit_fee
    invested = order_size + entry_fee
    return (final_capital - invested) / invested * 100


def edge_score(
    total_return_pct: float,
    buy_hold_return_pct: float,
    profit_factor: float,
    expectancy_pct: float,
    max_losing_streak: int,
    trade_count: int,
) -> float:
    pf = profit_factor if profit_factor != float("inf") else 3.0
    sample_penalty = max(0, 10 - trade_count) * 2
    return (
        (total_return_pct - buy_hold_return_pct)
        + (pf - 1.0) * 10
        + expectancy_pct * 5
        - max_losing_streak
        - sample_penalty
    )


def edge_score_band(score: float) -> str:
    """Faixa legivel do edge_score, para comparar pares/timeframes sem decorar a
    escala numerica. Limiares derivados da propria composicao do edge_score: um
    profit factor de 1.5 sozinho ja contribui +5 pontos, entao uma faixa de 20
    pontos representa uma combinacao real de varios fatores positivos, nao um
    unico indicador isolado.

        score >= 20            -> "Forte"
        0 <= score < 20         -> "Medio"
        -20 <= score < 0        -> "Fraco"
        score < -20             -> "Reprovado"
    """
    if score >= 20:
        return "Forte"
    if score >= 0:
        return "Médio"
    if score >= -20:
        return "Fraco"
    return "Reprovado"


def _stop_price(entry_price: float, atr: float, stop_loss_pct: float, atr_sl_multiplier: float) -> float:
    if atr > 0:
        # Mesmo teto de risk/manager.py calculate_risk() -- sem isso o backtest
        # simula um SL mais largo do que o bot realmente usaria em paper/live
        # num par de alta volatilidade, distorcendo o veredito de aprovacao.
        return max(entry_price - atr_sl_multiplier * atr, entry_price * (1 - MAX_STOP_LOSS_PCT))
    return entry_price * (1 - stop_loss_pct)


def _take_profit_price(entry_price: float, atr: float, take_profit_pct: float, atr_tp_multiplier: float) -> float:
    if atr > 0:
        return entry_price + atr_tp_multiplier * atr
    return entry_price * (1 + take_profit_pct)


def _max_losing_streak(trades: List[Trade]) -> int:
    current = 0
    longest = 0
    for trade in trades:
        if trade.pnl < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _exposure_pct(trades: List[Trade], period_start, period_end) -> float:
    if not trades or period_start is None or period_end is None or period_end <= period_start:
        return 0.0
    total_seconds = (period_end - period_start).total_seconds()
    exposed_seconds = sum(
        max((trade.exit_time - trade.entry_time).total_seconds(), 0)
        for trade in trades
    )
    return min(exposed_seconds / total_seconds * 100, 100.0) if total_seconds else 0.0


def _annualized_return_pct(total_return_pct: float, period_start, period_end) -> float:
    """Retorno anualizado via juros compostos, base 365 dias (cripto opera 24/7,
    diferente do calendario de pregao de mercados tradicionais). Compartilhado
    entre Calmar Ratio e o retorno anualizado exibido no relatorio -- calculado
    uma unica vez, nao duas formulas divergentes."""
    if period_start is None or period_end is None:
        return 0.0
    period_days = (period_end - period_start).total_seconds() / 86400
    if period_days <= 0:
        return 0.0
    growth_factor = 1 + total_return_pct / 100
    if growth_factor <= 0:
        # perda total (>=100%) ou pior: potencia fracionaria de base negativa vira
        # numero complexo silenciosamente em Python -- retorno anualizado nesse
        # caso e perda total, nao um numero indefinido.
        return -100.0
    try:
        return (growth_factor ** (365 / period_days) - 1) * 100
    except OverflowError:
        # periodo curto + retorno grande (ex: TIMEFRAME=1m, poucas horas de
        # historico com retorno acumulado alto) faz o expoente estourar o range
        # de float -- extrapolar isso para "1 ano" ja e instavel por natureza;
        # inf explicito e mais honesto que deixar o comando inteiro crashar.
        return float("inf")


def _simplified_sharpe(trade_returns: List[float]) -> float:
    if len(trade_returns) < 2:
        return 0.0
    series = pd.Series(trade_returns)
    std = series.std(ddof=1)
    if std == 0:
        return 0.0
    return float(series.mean() / std * sqrt(len(trade_returns)))


def _simplified_sortino(trade_returns: List[float]) -> float:
    """Mesma formula/convencao de _simplified_sharpe, trocando o desvio padrao
    geral pelo desvio padrao so dos retornos negativos (downside). Precisa de
    >=2 trades com prejuizo para o desvio ser calculavel -- com menos que isso
    (ou nenhum prejuizo), cai no mesmo padrao ja usado por profit_factor/
    payoff_ratio: inf se a media for positiva, 0.0 caso contrario."""
    if not trade_returns:
        return 0.0
    mean = pd.Series(trade_returns).mean()
    downside = [r for r in trade_returns if r < 0]
    if len(downside) < 2:
        return float("inf") if mean > 0 else 0.0
    downside_std = pd.Series(downside).std(ddof=1)
    if downside_std == 0:
        return float("inf") if mean > 0 else 0.0
    return float(mean / downside_std * sqrt(len(trade_returns)))


def _close_trade(
    capital: float,
    entry_price: float,
    exit_price: float,
    quantity: float,
    entry_cost: float,
    entry_fee: float,
    entry_time: pd.Timestamp,
    exit_time: pd.Timestamp,
    exit_reason: str,
    fee_rate: float,
):
    gross_exit = quantity * exit_price
    exit_fee = gross_exit * fee_rate
    net_exit = gross_exit - exit_fee
    pnl = net_exit - entry_cost
    pnl_pct = pnl / entry_cost * 100 if entry_cost else 0.0
    capital += net_exit

    return capital, Trade(
        entry_price=entry_price,
        exit_price=exit_price,
        quantity=quantity,
        pnl=pnl,
        pnl_pct=pnl_pct,
        fees=entry_fee + exit_fee,
        entry_time=entry_time,
        exit_time=exit_time,
        exit_reason=exit_reason,
    )

def print_report(r: BacktestResult):
    metric_rows = [
        ("Capital inicial", f"${r.initial_capital:.2f}", C_PRICE, f"Capital inicial:   ${r.initial_capital:.2f}"),
        ("Capital final", f"${r.final_capital:.2f}", _money_color(r.final_capital - r.initial_capital), f"Capital final:     ${r.final_capital:.2f}"),
        ("Retorno total", f"{r.total_return_pct:+.2f}%", _value_color(r.total_return_pct), f"Retorno total:     {r.total_return_pct:+.2f}%"),
        ("Total de trades", str(r.total_trades), C_CYAN, f"Total de trades:   {r.total_trades}"),
        ("Win rate", f"{r.win_rate:.1f}%", C_POS if r.win_rate >= 50 else C_NEG, f"Win rate:          {r.win_rate:.1f}%"),
        ("Max drawdown", f"{r.max_drawdown_pct:.2f}%", C_NEG if r.max_drawdown_pct > 10 else C_CYAN, f"Max drawdown:      {r.max_drawdown_pct:.2f}%"),
        ("Profit factor", _fmt_metric(r.profit_factor), C_POS if r.profit_factor > 1 else C_NEG, f"Profit factor:     {_fmt_metric(r.profit_factor)}"),
        ("Expectativa", f"${r.expectancy:+.2f}/trade", _value_color(r.expectancy), f"Expectativa:       ${r.expectancy:+.2f}/trade"),
        ("Media win/loss", f"${r.average_win:+.2f} / ${r.average_loss:+.2f}", C_CYAN, f"Media win/loss:    ${r.average_win:+.2f} / ${r.average_loss:+.2f}"),
        ("Maior win/loss", f"${r.largest_win:+.2f} / ${r.largest_loss:+.2f}", C_CYAN, f"Maior win/loss:    ${r.largest_win:+.2f} / ${r.largest_loss:+.2f}"),
        ("Max perdas seg.", str(r.max_losing_streak), C_NEG if r.max_losing_streak >= 3 else C_CYAN, f"Max perdas seg.:   {r.max_losing_streak}"),
        ("Exposicao", f"{r.exposure_pct:.1f}%", C_CYAN, f"Exposicao:         {r.exposure_pct:.1f}%"),
        ("Retorno anualiz.", f"{r.annualized_return_pct:+.2f}%", _value_color(r.annualized_return_pct), f"Retorno anualiz.:  {r.annualized_return_pct:+.2f}%"),
        ("Retorno/exposicao", _fmt_exposure_return(r.return_per_exposure_pct), _value_color(r.return_per_exposure_pct or 0.0), f"Retorno/exposicao: {_fmt_exposure_return(r.return_per_exposure_pct)}"),
        ("Sharpe simplif.", f"{r.sharpe:.2f}", _value_color(r.sharpe), f"Sharpe simplif.:   {r.sharpe:.2f}"),
        ("Sortino", _fmt_metric(r.sortino), C_POS if r.sortino > 0 else C_NEG, f"Sortino:           {_fmt_metric(r.sortino)}"),
        ("Calmar", _fmt_metric(r.calmar), C_POS if r.calmar > 1 else C_NEG, f"Calmar:            {_fmt_metric(r.calmar)}"),
        ("Expectativa %", f"{r.expectancy_pct:+.2f}%/trade", _value_color(r.expectancy_pct), f"Expectativa %:     {r.expectancy_pct:+.2f}%/trade"),
        ("Payoff ratio", _fmt_metric(r.payoff_ratio), C_POS if r.payoff_ratio > 1 else C_NEG, f"Payoff ratio:      {_fmt_metric(r.payoff_ratio)}"),
        ("Buy & hold", f"{r.buy_hold_return_pct:+.2f}%", _value_color(r.buy_hold_return_pct), f"Buy & hold:        {r.buy_hold_return_pct:+.2f}%"),
        ("Edge vs B&H", f"{r.edge_return_pct:+.2f}%", _value_color(r.edge_return_pct), f"Edge vs B&H:       {r.edge_return_pct:+.2f}%"),
        ("Edge score", f"{r.edge_score:+.2f}", _value_color(r.edge_score), f"Edge score:        {r.edge_score:+.2f}"),
    ]

    _emit_report("=" * 50)
    _emit_report(f"[bold {C_CYAN}]RESULTADO DO BACKTEST[/]", "RESULTADO DO BACKTEST")
    _emit_report("=" * 50)
    for label, value, color, plain in metric_rows:
        _emit_report(f"[{C_LABEL}]{label:<16}[/] [{color}]{value}[/]", plain)
    _emit_report("=" * 50)

    if r.trades:
        console.print()
        console.print(f"[bold {C_CYAN}]Ultimos 5 trades:[/]")
        log.info("\nUltimos 5 trades:")
        for t in r.trades[-5:]:
            pnl_color = C_POS if t.pnl >= 0 else C_NEG
            markup = (
                f"[{C_DIM}]  {t.entry_time.strftime('%Y-%m-%d %H:%M')} -> {t.exit_time.strftime('%Y-%m-%d %H:%M')}[/] | "
                f"[{C_LABEL}]Entrada[/]=[{C_PRICE}]{_fmt_price(t.entry_price)}[/] "
                f"[{C_LABEL}]Saida[/]=[{C_PRICE}]{_fmt_price(t.exit_price)}[/] | "
                f"[{C_LABEL}]PnL[/]=[{pnl_color}]${t.pnl:+.2f} ({t.pnl_pct:+.1f}%)[/] | "
                f"[{C_LABEL}]Taxas[/]=[white]${t.fees:.2f}[/] | [{C_CYAN}]{t.exit_reason}[/]"
            )
            plain = (
                f"  {t.entry_time.strftime('%Y-%m-%d %H:%M')} -> {t.exit_time.strftime('%Y-%m-%d %H:%M')} | "
                f"Entrada={_fmt_price(t.entry_price)} Saida={_fmt_price(t.exit_price)} | "
                f"PnL=${t.pnl:+.2f} ({t.pnl_pct:+.1f}%) | Taxas=${t.fees:.2f} | {t.exit_reason}"
            )
            console.print(markup)
            log.info(plain)


def _emit_report(markup: str, plain: str = None):
    console.print(markup)
    log.info(plain if plain is not None else markup)


def _value_color(value: float) -> str:
    if value > 0:
        return C_POS
    if value < 0:
        return C_NEG
    return C_DIM


def _money_color(value: float) -> str:
    return _value_color(value)


def _fmt_metric(value: float) -> str:
    if value == float("inf"):
        return "inf"
    return f"{value:.2f}"


def _fmt_exposure_return(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"{value:+.2f}%"
