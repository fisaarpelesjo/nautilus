import pandas as pd
from dataclasses import dataclass, field
from typing import List
from config.settings import STOP_LOSS_PCT, TAKE_PROFIT_PCT, MAX_ORDER_SIZE_USDT
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

    capital = initial_capital
    trades: List[Trade] = []
    peak_capital = initial_capital

    in_position = False
    entry_price = 0.0
    entry_time = None
    quantity = 0.0

    for i in range(100, len(df)):
        window = df.iloc[:i]
        current = df.iloc[i]
        price = current["close"]

        if in_position:
            exit_reason = None
            exit_price = price

            if price <= entry_price * (1 - STOP_LOSS_PCT):
                exit_reason = "Stop Loss"
                exit_price = entry_price * (1 - STOP_LOSS_PCT)
            elif price >= entry_price * (1 + TAKE_PROFIT_PCT):
                exit_reason = "Take Profit"
                exit_price = entry_price * (1 + TAKE_PROFIT_PCT)

            signal = strategy.generate_signal(window)
            if signal.signal == Signal.SELL and exit_reason is None:
                exit_reason = "Sinal de venda"

            if exit_reason:
                pnl = (exit_price - entry_price) * quantity
                pnl_pct = (exit_price - entry_price) / entry_price * 100
                capital += quantity * exit_price
                peak_capital = max(peak_capital, capital)

                trades.append(Trade(
                    entry_price=entry_price,
                    exit_price=exit_price,
                    quantity=quantity,
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    entry_time=entry_time,
                    exit_time=current.name,
                    exit_reason=exit_reason,
                ))
                in_position = False
        else:
            signal = strategy.generate_signal(window)
            if signal.signal == Signal.BUY and capital >= 10:
                order_size = min(MAX_ORDER_SIZE_USDT, capital * 0.95)
                quantity = order_size / price
                capital -= order_size
                entry_price = price
                entry_time = current.name
                in_position = True

    wins = [t for t in trades if t.pnl > 0]
    total_return = (capital - initial_capital) / initial_capital * 100
    win_rate = len(wins) / len(trades) * 100 if trades else 0
    max_dd = (peak_capital - capital) / peak_capital * 100 if peak_capital > 0 else 0

    result = BacktestResult(
        trades=trades,
        initial_capital=initial_capital,
        final_capital=capital,
        total_return_pct=total_return,
        win_rate=win_rate,
        total_trades=len(trades),
        max_drawdown_pct=max_dd,
    )

    _print_report(result)
    return result

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
                f"PnL=${t.pnl:+.2f} ({t.pnl_pct:+.1f}%) | {t.exit_reason}"
            )
