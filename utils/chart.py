import sys
import io
import plotext as plt

# força UTF-8 no stdout para caracteres de gráfico no Windows
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

from config.settings import TIMEFRAME, EMA_FAST, EMA_SLOW, EMA_TREND, RSI_OVERBOUGHT, RSI_OVERSOLD
from data.fetcher import fetch_ohlcv
from strategy.ema_rsi import EmaRsiStrategy


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
    symbol = symbol or _select_pair()
    timeframe = timeframe or TIMEFRAME

    df = fetch_ohlcv(symbol, timeframe, limit=limit)
    strategy = EmaRsiStrategy()
    df = strategy.calculate_indicators(df)
    df = df.tail(limit)

    n = len(df)
    xs = list(range(n))
    closes    = df["close"].tolist()
    ema_fast  = df["ema_fast"].tolist()
    ema_slow  = df["ema_slow"].tolist()
    ema_trend = df["ema_trend"].tolist()
    volumes   = df["volume"].tolist()
    vol_ma    = df["volume_ma"].tolist()
    rsi       = df["rsi"].tolist()

    # tick labels: show ~8 dates evenly spaced
    tick_step = max(1, n // 8)
    tick_xs   = list(range(0, n, tick_step))
    tick_lbs  = [str(df.index[i])[:13] for i in tick_xs]

    plt.clf()
    plt.theme("dark")
    plt.subplots(3, 1)

    # --- subplot 1: preço + EMAs ---
    plt.subplot(1, 1)
    plt.title(f"{symbol}  {timeframe}  EMA {EMA_FAST}/{EMA_SLOW}/{EMA_TREND}")
    plt.plot(xs, closes,    color="white",  label="preco")
    plt.plot(xs, ema_fast,  color="green",  label=f"EMA{EMA_FAST}")
    plt.plot(xs, ema_slow,  color="yellow", label=f"EMA{EMA_SLOW}")
    plt.plot(xs, ema_trend, color="red",    label=f"EMA{EMA_TREND}")
    plt.xticks(tick_xs, tick_lbs)
    plt.yfrequency(5)

    # --- subplot 2: volume ---
    plt.subplot(2, 1)
    plt.title("volume")
    plt.bar(xs, volumes, color="cyan",   label="vol", width=0.8)
    plt.plot(xs, vol_ma, color="orange", label="MA")
    plt.xticks(tick_xs, tick_lbs)
    plt.yfrequency(3)

    # --- subplot 3: RSI ---
    plt.subplot(3, 1)
    plt.title(f"RSI14  OB={RSI_OVERBOUGHT}  OS={RSI_OVERSOLD}")
    plt.plot(xs, rsi, color="magenta", label="RSI")
    plt.hline(RSI_OVERBOUGHT, color="red")
    plt.hline(RSI_OVERSOLD,   color="green")
    plt.hline(50,             color="white+")
    plt.ylim(0, 100)
    plt.xticks(tick_xs, tick_lbs)
    plt.yfrequency(3)

    plt.show()
