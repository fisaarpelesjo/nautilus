import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output
import webbrowser
import threading

from config.settings import TIMEFRAME, EMA_FAST, EMA_SLOW, EMA_TREND, RSI_OVERBOUGHT, RSI_OVERSOLD, PAIRS
from data.fetcher import fetch_ohlcv
from strategy.ema_rsi import EmaRsiStrategy
from backtesting.engine import precompute_signals
from strategy.base import Signal

_BG   = "#131722"
_GRID = "#1c2030"
_TEXT = "#d1d4dc"
_UP   = "#26a69a"
_DOWN = "#ef5350"
_EMA1 = "#00e676"
_EMA2 = "#ffeb3b"
_EMA3 = "#ff5252"
_BB   = "#4fc3f7"
_RSI  = "#ce93d8"


def _build_figure(symbol: str, timeframe: str) -> go.Figure:
    from datetime import datetime, timedelta
    df = fetch_ohlcv(symbol, timeframe, limit=200)
    strategy = EmaRsiStrategy()
    df = strategy.calculate_indicators(df)
    cutoff = datetime.utcnow() - timedelta(days=7)
    df = df[df.index >= cutoff]

    dates     = df.index
    cur_price = df["close"].iloc[-1]
    cur_rsi   = df["rsi"].iloc[-1]

    signals  = precompute_signals(df, strategy)
    buy_idx  = [i for i, s in enumerate(signals) if s == Signal.BUY]
    sell_idx = [i for i, s in enumerate(signals) if s == Signal.SELL]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.75, 0.25],
    )

    fig.add_trace(go.Candlestick(
        x=dates,
        open=df["open"], high=df["high"],
        low=df["low"],   close=df["close"],
        increasing_line_color=_UP,  increasing_fillcolor=_UP,
        decreasing_line_color=_DOWN, decreasing_fillcolor=_DOWN,
        name="candle", showlegend=False,
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=dates, y=df["bb_upper"],
        line=dict(color=_BB, width=0.8, dash="dot"),
        name="BB sup", showlegend=False, opacity=0.6,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=dates, y=df["bb_lower"],
        line=dict(color=_BB, width=0.8, dash="dot"),
        fill="tonexty", fillcolor="rgba(79,195,247,0.05)",
        name="BB inf", showlegend=False, opacity=0.6,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=dates, y=df["bb_middle"],
        line=dict(color=_BB, width=0.6, dash="dot"),
        name="BB mid", showlegend=False, opacity=0.3,
    ), row=1, col=1)

    for col_name, color, label in [
        ("ema_fast",  _EMA1, f"EMA{EMA_FAST}"),
        ("ema_slow",  _EMA2, f"EMA{EMA_SLOW}"),
        ("ema_trend", _EMA3, f"EMA{EMA_TREND}"),
    ]:
        fig.add_trace(go.Scatter(
            x=dates, y=df[col_name],
            line=dict(color=color, width=1.3),
            name=label,
        ), row=1, col=1)

    if buy_idx:
        fig.add_trace(go.Scatter(
            x=dates[buy_idx],
            y=df["low"].iloc[buy_idx] * 0.996,
            mode="markers",
            marker=dict(symbol="triangle-up", size=12, color=_UP),
            name="BUY",
        ), row=1, col=1)
    if sell_idx:
        fig.add_trace(go.Scatter(
            x=dates[sell_idx],
            y=df["high"].iloc[sell_idx] * 1.004,
            mode="markers",
            marker=dict(symbol="triangle-down", size=12, color=_DOWN),
            name="SELL",
        ), row=1, col=1)

    fig.add_hline(
        y=cur_price, line_dash="dash",
        line_color="rgba(209,212,220,0.5)", line_width=0.8,
        row=1, col=1,
    )

    # posição aberta
    title_suffix = ""
    try:
        from data.state_store import load_state
        state = load_state() or {}
        pos = state.get("positions", {}).get(symbol)
        if pos:
            entry = pos["entry_price"]
            sl    = pos["stop_loss"]
            tp    = pos["take_profit"]
            hi    = pos.get("highest_price", entry)
            pnl_pct = (cur_price - entry) / entry * 100
            for y, color, dash, label in [
                (entry, "#ffeb3b", "solid",   f"Entrada {entry}"),
                (sl,    _DOWN,    "dot",      f"SL {sl:.4f}"),
                (tp,    _UP,      "dot",      f"TP {tp:.4f}"),
                (hi,    "#aaa",   "dashdot",  f"Máx {hi:.4f}"),
            ]:
                fig.add_hline(
                    y=y, line_dash=dash, line_color=color, line_width=1.0,
                    annotation_text=label,
                    annotation_position="right",
                    annotation_font=dict(color=color, size=9),
                    row=1, col=1,
                )
            c = _UP if pnl_pct >= 0 else _DOWN
            title_suffix = f"  <span style='color:{c}'>PnL {pnl_pct:+.2f}%</span>"
    except Exception:
        pass

    fig.add_trace(go.Scatter(
        x=dates, y=df["rsi"],
        line=dict(color=_RSI, width=1.4),
        name="RSI",
    ), row=2, col=1)
    for level, color in [(RSI_OVERBOUGHT, _DOWN), (RSI_OVERSOLD, _UP), (50, "#555")]:
        fig.add_hline(y=level, line_dash="dash", line_color=color,
                      line_width=0.8, row=2, col=1)

    fig.update_layout(
        title=dict(
            text=f"{symbol}  {timeframe}  |  {cur_price}  RSI {cur_rsi:.0f}  "
                 f"EMA{EMA_FAST}/{EMA_SLOW}/{EMA_TREND}{title_suffix}",
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
        uirevision=symbol,
    )
    for row in [1, 2]:
        fig.update_xaxes(gridcolor=_GRID, showgrid=True, zeroline=False, row=row, col=1)
        fig.update_yaxes(gridcolor=_GRID, showgrid=True, zeroline=False,
                         side="right", row=row, col=1)
    fig.update_yaxes(range=[0, 100], row=2, col=1)

    return fig


def run(symbol: str = None, timeframe: str = None, limit: int = 100):
    timeframe = timeframe or TIMEFRAME
    default   = symbol or PAIRS[0]

    btn_ids   = [f"pbtn-{i}" for i in range(len(PAIRS))]
    _btn_style = {"color": _TEXT, "padding": "6px 12px", "cursor": "pointer",
                  "borderRadius": "4px", "fontSize": "12px",
                  "backgroundColor": "#1e2235", "border": "1px solid #2a2d3e"}

    app = Dash(__name__, title=default)
    app.layout = html.Div(
        style={"backgroundColor": _BG, "padding": "12px", "fontFamily": "monospace"},
        children=[
            html.Div(
                style={"display": "flex", "gap": "8px", "flexWrap": "wrap", "marginBottom": "10px"},
                children=[
                    html.Button(p, id=btn_ids[i], n_clicks=0, style=_btn_style)
                    for i, p in enumerate(PAIRS)
                ],
            ),
            dcc.Store(id="selected-pair", data=default),
            dcc.Store(id="_title-sink"),
            dcc.Interval(id="refresh", interval=30_000, n_intervals=0),
            dcc.Graph(id="chart", figure=_build_figure(default, timeframe),
                      config={"scrollZoom": True, "displaylogo": False}),
        ],
    )

    @app.callback(
        Output("selected-pair", "data"),
        [Input(bid, "n_clicks") for bid in btn_ids],
        prevent_initial_call=True,
    )
    def _select(*args):
        from dash import ctx
        return PAIRS[btn_ids.index(ctx.triggered_id)]

    # atualiza título da aba via JS
    app.clientside_callback(
        "function(sym) { document.title = sym + ' | itgr'; return null; }",
        Output("_title-sink", "data"),
        Input("selected-pair", "data"),
    )

    @app.callback(
        Output("chart", "figure"),
        Input("selected-pair", "data"),
        Input("refresh", "n_intervals"),
    )
    def _update(sym, _):
        return _build_figure(sym, timeframe)

    port = 8051
    threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
    app.run(port=port, debug=False)
