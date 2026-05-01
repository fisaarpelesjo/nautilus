import pandas as pd
from dataclasses import dataclass
from typing import List
from config.settings import (
    STOP_LOSS_PCT,
    TAKE_PROFIT_PCT,
    MAX_ORDER_SIZE_USDT,
    BACKTEST_FEE_RATE,
    BACKTEST_SLIPPAGE_PCT,
)
from strategy.base import Signal
from strategy.ema_rsi import EmaRsiStrategy
from data.fetcher import fetch_ohlcv
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

def run_backtest(symbol: str, timeframe: str, initial_capital: float = 1000.0, candle_limit: int = 2000) -> BacktestResult:
    df = fetch_ohlcv(symbol, timeframe, limit=candle_limit)
    strategy = EmaRsiStrategy()
    df = strategy.calculate_indicators(df)

    result = simulate_backtest(df, strategy, initial_capital=initial_capital)
    _print_report(result)
    return result


def simulate_backtest(
    df: pd.DataFrame,
    strategy,
    initial_capital: float = 1000.0,
    start_index: int = 100,
    fee_rate: float = BACKTEST_FEE_RATE,
    slippage_pct: float = BACKTEST_SLIPPAGE_PCT,
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

    for i in range(start_index, len(df)):
        window = df.iloc[:i]
        current = df.iloc[i]
        price = current["close"]
        equity = capital + (quantity * price * (1 - slippage_pct) if in_position else 0.0)
        peak_equity = max(peak_equity, equity)
        if peak_equity > 0:
            max_drawdown_pct = max(max_drawdown_pct, (peak_equity - equity) / peak_equity * 100)

        if in_position:
            exit_reason = None
            exit_price = price * (1 - slippage_pct)

            if current["low"] <= entry_price * (1 - STOP_LOSS_PCT):
                exit_reason = "Stop Loss"
                exit_price = entry_price * (1 - STOP_LOSS_PCT) * (1 - slippage_pct)
            elif current["high"] >= entry_price * (1 + TAKE_PROFIT_PCT):
                exit_reason = "Take Profit"
                exit_price = entry_price * (1 + TAKE_PROFIT_PCT) * (1 - slippage_pct)

            signal = strategy.generate_signal(window)
            if signal.signal == Signal.SELL and exit_reason is None:
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
            signal = strategy.generate_signal(window)
            if signal.signal == Signal.BUY and capital >= 10:
                order_size = min(MAX_ORDER_SIZE_USDT, capital * 0.95)
                if order_size * (1 + fee_rate) > capital:
                    order_size = capital / (1 + fee_rate)
                entry_price = price * (1 + slippage_pct)
                quantity = order_size / entry_price
                entry_fee = order_size * fee_rate
                entry_cost = order_size + entry_fee
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

    result = BacktestResult(
        trades=trades,
        initial_capital=initial_capital,
        final_capital=capital,
        total_return_pct=total_return,
        win_rate=win_rate,
        total_trades=len(trades),
        max_drawdown_pct=max_drawdown_pct,
    )

    return result


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

def _print_report(r: BacktestResult):
    log.info("=" * 50)
    log.info("RESULTADO DO BACKTEST")
    log.info("=" * 50)
    log.info(f"Capital inicial:   ${r.initial_capital:.2f}")
    log.info(f"Capital final:     ${r.final_capital:.2f}")
    log.info(f"Retorno total:     {r.total_return_pct:+.2f}%")
    log.info(f"Total de trades:   {r.total_trades}")
    log.info(f"Win rate:          {r.win_rate:.1f}%")
    log.info(f"Max drawdown:      {r.max_drawdown_pct:.2f}%")
    log.info("=" * 50)

    if r.trades:
        log.info("\nUltimos 5 trades:")
        for t in r.trades[-5:]:
            log.info(
                f"  {t.entry_time.strftime('%Y-%m-%d %H:%M')} -> {t.exit_time.strftime('%Y-%m-%d %H:%M')} | "
                f"Entrada=${t.entry_price:.2f} Saida=${t.exit_price:.2f} | "
                f"PnL=${t.pnl:+.2f} ({t.pnl_pct:+.1f}%) | Taxas=${t.fees:.2f} | {t.exit_reason}"
            )
