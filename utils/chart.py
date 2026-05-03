import numpy as np
import pandas as pd
import mplfinance as mpf

from config.settings import TIMEFRAME, EMA_FAST, EMA_SLOW, EMA_TREND, RSI_OVERBOUGHT, RSI_OVERSOLD
from data.fetcher import fetch_ohlcv
from strategy.ema_rsi import EmaRsiStrategy
from backtesting.engine import precompute_signals
from strategy.base import Signal


def _select_pair() -> str:
    from config.settings import PAIRS
    print("\n  pares disponíveis:")
    for i, p in enumerate(PAIRS, 1):
        print(f"  {i:2}. {p}")
    print()
    try:
        choice = input("  selecione [1-{}]: ".format(len(PAIRS))).strip()
        idx = int(choice) - 1
        if 0 <= idx < len(PAIRS):
            return PAIRS[idx]
    except (ValueError, KeyboardInterrupt):
        pass
    return PAIRS[0]


def run(symbol: str = None, timeframe: str = None, limit: int = 100):
    symbol    = symbol    or _select_pair()
    timeframe = timeframe or TIMEFRAME

    from datetime import datetime, timedelta
    df = fetch_ohlcv(symbol, timeframe, limit=limit)
    strategy = EmaRsiStrategy()
    df = strategy.calculate_indicators(df)
    cutoff = datetime.utcnow() - timedelta(days=7)
    df = df[df.index >= cutoff]

    # mplfinance requer index DatetimeIndex sem timezone e colunas capitalizadas
    df_plot = df[["open", "high", "low", "close", "volume"]].copy()
    df_plot.columns = ["Open", "High", "Low", "Close", "Volume"]
    if df_plot.index.tz is not None:
        df_plot.index = df_plot.index.tz_localize(None)

    cur_price = df["close"].iloc[-1]
    cur_rsi   = df["rsi"].iloc[-1]

    # sinais BUY/SELL como scatter
    signals = precompute_signals(df, strategy)
    buy_s  = pd.Series(np.nan, index=df.index)
    sell_s = pd.Series(np.nan, index=df.index)
    for i, s in enumerate(signals):
        if s == Signal.BUY:
            buy_s.iloc[i]  = df["low"].iloc[i]  * 0.997
        elif s == Signal.SELL:
            sell_s.iloc[i] = df["high"].iloc[i] * 1.003
    buy_s.index  = df_plot.index
    sell_s.index = df_plot.index

    # EMAs e RSI como addplots
    ema_fast_s  = df["ema_fast"].copy();  ema_fast_s.index  = df_plot.index
    ema_slow_s  = df["ema_slow"].copy();  ema_slow_s.index  = df_plot.index
    ema_trend_s = df["ema_trend"].copy(); ema_trend_s.index = df_plot.index
    rsi_s       = df["rsi"].copy();       rsi_s.index       = df_plot.index
    rsi_ob_s    = pd.Series(RSI_OVERBOUGHT, index=df_plot.index, dtype=float)
    rsi_os_s    = pd.Series(RSI_OVERSOLD,   index=df_plot.index, dtype=float)
    rsi_mid_s   = pd.Series(50,             index=df_plot.index, dtype=float)

    ap = [
        mpf.make_addplot(ema_fast_s,  color="#00e676", width=1.2, label=f"EMA{EMA_FAST}"),
        mpf.make_addplot(ema_slow_s,  color="#ffeb3b", width=1.2, label=f"EMA{EMA_SLOW}"),
        mpf.make_addplot(ema_trend_s, color="#ff5252", width=1.2, label=f"EMA{EMA_TREND}"),
        mpf.make_addplot(rsi_s,      panel=1, color="#ce93d8", width=1.4, ylabel="RSI", ylim=(0, 100)),
        mpf.make_addplot(rsi_ob_s,   panel=1, color="#ff5252", width=0.8, linestyle="--"),
        mpf.make_addplot(rsi_os_s,   panel=1, color="#69f0ae", width=0.8, linestyle="--"),
        mpf.make_addplot(rsi_mid_s,  panel=1, color="#ffffff", width=0.6, linestyle=":"),
    ]
    if not buy_s.isna().all():
        ap.append(mpf.make_addplot(buy_s,  type="scatter", markersize=120, marker="^", color="#69f0ae", label="BUY"))
    if not sell_s.isna().all():
        ap.append(mpf.make_addplot(sell_s, type="scatter", markersize=120, marker="v", color="#ff5252", label="SELL"))

    mpf.plot(
        df_plot,
        type="candle",
        style="nightclouds",
        title=f"\n{symbol}  {timeframe}  |  preço {cur_price}  RSI {cur_rsi:.0f}  EMA{EMA_FAST}/{EMA_SLOW}/{EMA_TREND}",
        addplot=ap,
        volume=False,
        panel_ratios=(4, 1),
        figsize=(16, 9),
        tight_layout=True,
    )
