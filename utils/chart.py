import numpy as np
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt

from config.settings import TIMEFRAME, EMA_FAST, EMA_SLOW, EMA_TREND, RSI_OVERBOUGHT, RSI_OVERSOLD
from data.fetcher import fetch_ohlcv
from strategy.ema_rsi import EmaRsiStrategy
from backtesting.engine import precompute_signals
from strategy.base import Signal

# cores TradingView-inspired
_UP    = "#26a69a"
_DOWN  = "#ef5350"
_BG    = "#131722"
_GRID  = "#1c2030"
_TEXT  = "#d1d4dc"
_EMA1  = "#00e676"
_EMA2  = "#ffeb3b"
_EMA3  = "#ff5252"
_BB    = "#4fc3f7"
_RSI   = "#ce93d8"
_WHITE = "#d1d4dc"

_STYLE = mpf.make_mpf_style(
    base_mpf_style="nightclouds",
    marketcolors=mpf.make_marketcolors(
        up=_UP, down=_DOWN,
        edge="inherit", wick="inherit",
        volume={"up": _UP, "down": _DOWN},
    ),
    gridcolor=_GRID,
    gridstyle="-",
    facecolor=_BG,
    edgecolor="#2a2d3e",
    figcolor="#0d1117",
    y_on_right=True,
    rc={"font.size": 9, "axes.labelcolor": _TEXT, "text.color": _TEXT,
        "xtick.color": _TEXT, "ytick.color": _TEXT},
)


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

    df_plot = df[["open", "high", "low", "close", "volume"]].copy()
    df_plot.columns = ["Open", "High", "Low", "Close", "Volume"]
    if df_plot.index.tz is not None:
        df_plot.index = df_plot.index.tz_localize(None)

    n         = len(df_plot)
    idx       = df_plot.index
    cur_price = df["close"].iloc[-1]
    cur_rsi   = df["rsi"].iloc[-1]

    def s(col): return df[col].values  # array helper

    # BUY/SELL markers
    signals = precompute_signals(df, strategy)
    buy_s  = pd.Series(np.nan, index=idx)
    sell_s = pd.Series(np.nan, index=idx)
    for i, sig in enumerate(signals):
        if sig == Signal.BUY:
            buy_s.iloc[i]  = df["low"].iloc[i]  * 0.996
        elif sig == Signal.SELL:
            sell_s.iloc[i] = df["high"].iloc[i] * 1.004

    # addplots
    def S(arr): return pd.Series(arr if hasattr(arr, "__len__") else [arr]*n, index=idx)

    ap = [
        # Bollinger Bands
        mpf.make_addplot(S(s("bb_upper")),  color=_BB,   width=0.8, linestyle="--", alpha=0.7),
        mpf.make_addplot(S(s("bb_lower")),  color=_BB,   width=0.8, linestyle="--", alpha=0.7),
        mpf.make_addplot(S(s("bb_middle")), color=_BB,   width=0.6, linestyle=":",  alpha=0.4),
        # EMAs
        mpf.make_addplot(S(s("ema_fast")),  color=_EMA1, width=1.3, label=f"EMA{EMA_FAST}"),
        mpf.make_addplot(S(s("ema_slow")),  color=_EMA2, width=1.3, label=f"EMA{EMA_SLOW}"),
        mpf.make_addplot(S(s("ema_trend")), color=_EMA3, width=1.3, label=f"EMA{EMA_TREND}"),
        # RSI panel (panel=2 porque volume ocupa panel=1)
        mpf.make_addplot(S(s("rsi")),                panel=2, color=_RSI,   width=1.4, ylabel="RSI", ylim=(0, 100)),
        mpf.make_addplot(S(RSI_OVERBOUGHT),          panel=2, color=_DOWN,  width=0.8, linestyle="--"),
        mpf.make_addplot(S(RSI_OVERSOLD),            panel=2, color=_UP,    width=0.8, linestyle="--"),
        mpf.make_addplot(S(50),                      panel=2, color="#555",  width=0.6, linestyle=":"),
    ]
    if not buy_s.isna().all():
        ap.append(mpf.make_addplot(buy_s,  type="scatter", markersize=150, marker="^", color=_UP,   label="BUY"))
    if not sell_s.isna().all():
        ap.append(mpf.make_addplot(sell_s, type="scatter", markersize=150, marker="v", color=_DOWN, label="SELL"))

    fig, axes = mpf.plot(
        df_plot,
        type="candle",
        style=_STYLE,
        title=f"\n{symbol}  {timeframe}  |  {cur_price}  RSI {cur_rsi:.0f}  "
              f"EMA{EMA_FAST}/{EMA_SLOW}/{EMA_TREND}",
        addplot=ap,
        volume=True,
        panel_ratios=(5, 1, 2),
        figsize=(18, 10),
        tight_layout=True,
        returnfig=True,
    )

    ax_main = axes[0]

    # Bollinger Band fill
    bb_lo = s("bb_lower")
    bb_hi = s("bb_upper")
    xs    = np.arange(n)
    ax_main.fill_between(xs, bb_lo, bb_hi, alpha=0.05, color=_BB, zorder=0)

    # linha de preço atual
    ax_main.axhline(cur_price, color=_WHITE, linewidth=0.8, linestyle="--", alpha=0.6)
    ax_main.annotate(
        f"  {cur_price}",
        xy=(1, cur_price), xycoords=("axes fraction", "data"),
        color=_WHITE, fontsize=8, va="center",
    )

    plt.show()
