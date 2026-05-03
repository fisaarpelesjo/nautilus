import sys
import io
import plotext as plt

# força UTF-8 no stdout para caracteres de gráfico no Windows
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

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

    n = len(df)
    xs = list(range(n))

    # x-tick labels: ~8 evenly spaced date strings
    DATE_FMT = "%Y-%m-%d %H:%M"
    dates    = [ts.strftime(DATE_FMT) for ts in df.index]
    step     = max(1, n // 8)
    tick_pos = xs[::step]
    tick_lbl = [dates[i] for i in tick_pos]

    ohlc = {
        "Open":  df["open"].tolist(),
        "High":  df["high"].tolist(),
        "Low":   df["low"].tolist(),
        "Close": df["close"].tolist(),
    }
    volumes   = df["volume"].tolist()
    vol_ma    = df["volume_ma"].tolist()
    rsi       = df["rsi"].tolist()

    # sinais BUY/SELL para marcadores
    signals    = precompute_signals(df, strategy)
    buy_xs     = [i for i, s in enumerate(signals) if s == Signal.BUY]
    buy_prices = [df["low"].iloc[i] * 0.998 for i in buy_xs]
    sell_xs    = [i for i, s in enumerate(signals) if s == Signal.SELL]
    sell_prices = [df["high"].iloc[i] * 1.002 for i in sell_xs]

    cur_rsi   = rsi[-1]
    cur_price = ohlc["Close"][-1]

    plt.clf()
    plt.theme("dark")
    plt.subplots(3, 1)
    plt.plotsize(plt.terminal_width(), plt.terminal_height())

    # --- subplot 1: candlestick + EMAs + sinais ---
    plt.subplot(1, 1)
    plt.title(
        f"{symbol}  {timeframe}  |  "
        f"preco {cur_price}  RSI {cur_rsi:.0f}  "
        f"EMA{EMA_FAST}/{EMA_SLOW}/{EMA_TREND}"
    )
    plt.candlestick(xs, ohlc, colors=["red", "green"])
    if buy_xs:
        plt.scatter(buy_xs,  buy_prices,  color="bright green", marker="^", label="BUY")
    if sell_xs:
        plt.scatter(sell_xs, sell_prices, color="bright red",   marker="v", label="SELL")
    plt.xticks(tick_pos, tick_lbl)

    # --- subplot 2: volume ---
    plt.subplot(2, 1)
    plt.title("volume")
    plt.bar(xs, volumes, color="cyan",   label="vol", width=0.8)
    plt.plot(xs, vol_ma, color="orange", label="MA20")
    plt.xticks(tick_pos, tick_lbl)
    plt.yfrequency(3)

    # --- subplot 3: RSI ---
    plt.subplot(3, 1)
    plt.title(f"RSI14  OB={RSI_OVERBOUGHT}  OS={RSI_OVERSOLD}  atual={cur_rsi:.0f}")
    plt.plot(xs, rsi, color="magenta", label="RSI")
    plt.hline(RSI_OVERBOUGHT, color="red")
    plt.hline(RSI_OVERSOLD,   color="green")
    plt.hline(50,             color="white+")
    plt.ylim(0, 100)
    plt.xticks(tick_pos, tick_lbl)
    plt.yfrequency(3)

    plt.show()
