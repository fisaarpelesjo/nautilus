import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config.settings import TIMEFRAME, EMA_FAST, EMA_SLOW, EMA_TREND, RSI_OVERBOUGHT, RSI_OVERSOLD
from data.fetcher import fetch_ohlcv
from strategy.ema_rsi import EmaRsiStrategy
from backtesting.engine import precompute_signals
from strategy.base import Signal

_BG     = "#131722"
_GRID   = "#1c2030"
_TEXT   = "#d1d4dc"
_UP     = "#26a69a"
_DOWN   = "#ef5350"
_EMA1   = "#00e676"
_EMA2   = "#ffeb3b"
_EMA3   = "#ff5252"
_BB     = "#4fc3f7"
_RSI    = "#ce93d8"


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

    dates     = df.index
    cur_price = df["close"].iloc[-1]
    cur_rsi   = df["rsi"].iloc[-1]

    # sinais BUY/SELL
    signals = precompute_signals(df, strategy)
    buy_idx  = [i for i, s in enumerate(signals) if s == Signal.BUY]
    sell_idx = [i for i, s in enumerate(signals) if s == Signal.SELL]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.75, 0.25],
    )

    # --- candlestick ---
    fig.add_trace(go.Candlestick(
        x=dates,
        open=df["open"], high=df["high"],
        low=df["low"],   close=df["close"],
        increasing_line_color=_UP,  increasing_fillcolor=_UP,
        decreasing_line_color=_DOWN, decreasing_fillcolor=_DOWN,
        name="candle", showlegend=False,
    ), row=1, col=1)

    # --- Bollinger Bands ---
    fig.add_trace(go.Scatter(
        x=dates, y=df["bb_upper"],
        line=dict(color=_BB, width=0.8, dash="dot"),
        name="BB superior", showlegend=False, opacity=0.6,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=dates, y=df["bb_lower"],
        line=dict(color=_BB, width=0.8, dash="dot"),
        fill="tonexty", fillcolor="rgba(79,195,247,0.05)",
        name="BB inferior", showlegend=False, opacity=0.6,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=dates, y=df["bb_middle"],
        line=dict(color=_BB, width=0.6, dash="dot"),
        name="BB mid", showlegend=False, opacity=0.3,
    ), row=1, col=1)

    # --- EMAs ---
    for col, name, label in [
        ("ema_fast",  _EMA1, f"EMA{EMA_FAST}"),
        ("ema_slow",  _EMA2, f"EMA{EMA_SLOW}"),
        ("ema_trend", _EMA3, f"EMA{EMA_TREND}"),
    ]:
        fig.add_trace(go.Scatter(
            x=dates, y=df[col],
            line=dict(color=name, width=1.3),
            name=label,
        ), row=1, col=1)

    # --- BUY markers ---
    if buy_idx:
        fig.add_trace(go.Scatter(
            x=dates[buy_idx],
            y=df["low"].iloc[buy_idx] * 0.996,
            mode="markers",
            marker=dict(symbol="triangle-up", size=12, color=_UP),
            name="BUY",
        ), row=1, col=1)

    # --- SELL markers ---
    if sell_idx:
        fig.add_trace(go.Scatter(
            x=dates[sell_idx],
            y=df["high"].iloc[sell_idx] * 1.004,
            mode="markers",
            marker=dict(symbol="triangle-down", size=12, color=_DOWN),
            name="SELL",
        ), row=1, col=1)

    # --- linha de preço atual ---
    fig.add_hline(
        y=cur_price, line_dash="dash",
        line_color="rgba(209,212,220,0.5)", line_width=0.8,
        row=1, col=1,
    )

    # --- RSI ---
    fig.add_trace(go.Scatter(
        x=dates, y=df["rsi"],
        line=dict(color=_RSI, width=1.4),
        name="RSI",
    ), row=2, col=1)
    for level, color in [(RSI_OVERBOUGHT, _DOWN), (RSI_OVERSOLD, _UP), (50, "#555555")]:
        fig.add_hline(y=level, line_dash="dash", line_color=color,
                      line_width=0.8, row=2, col=1)

    # --- layout ---
    fig.update_layout(
        title=dict(
            text=f"{symbol}  {timeframe}  |  {cur_price}  RSI {cur_rsi:.0f}  "
                 f"EMA{EMA_FAST}/{EMA_SLOW}/{EMA_TREND}",
            font=dict(color=_TEXT, size=13),
        ),
        paper_bgcolor=_BG,
        plot_bgcolor=_BG,
        font=dict(color=_TEXT),
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=False,
        legend=dict(
            bgcolor="rgba(0,0,0,0)", font=dict(size=10),
            orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0,
        ),
        margin=dict(l=10, r=60, t=60, b=10),
        height=750,
    )
    for row in [1, 2]:
        fig.update_xaxes(
            gridcolor=_GRID, showgrid=True,
            zeroline=False, row=row, col=1,
        )
        fig.update_yaxes(
            gridcolor=_GRID, showgrid=True,
            zeroline=False, side="right", row=row, col=1,
        )
    fig.update_yaxes(range=[0, 100], row=2, col=1)

    fig.show()
