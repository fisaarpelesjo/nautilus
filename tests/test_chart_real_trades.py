from utils import chart


def _synthetic_ohlcv_df():
    import pandas as pd
    from datetime import datetime, timedelta

    n = 150
    now = datetime.utcnow()
    index = [now - timedelta(hours=4 * (n - i)) for i in range(n)]
    closes = [100.0 + i * 0.1 for i in range(n)]
    return pd.DataFrame({
        "open": closes, "high": [c + 1.0 for c in closes], "low": [c - 1.0 for c in closes],
        "close": closes, "volume": [1000.0] * n,
        "ema_fast": closes, "ema_slow": closes, "ema_trend": closes,
        "rsi": [50.0] * n, "bb_upper": [c + 5 for c in closes], "bb_middle": closes, "bb_lower": [c - 5 for c in closes],
    }, index=pd.DatetimeIndex(index))


def test_build_figure_adds_real_trade_marker_layer(monkeypatch):
    df = _synthetic_ohlcv_df()
    monkeypatch.setattr(chart, "fetch_ohlcv", lambda symbol, timeframe, limit=200: df)
    monkeypatch.setattr(chart, "precompute_signals", lambda df, strategy: __import__("pandas").Series(
        ["HOLD"] * len(df), index=df.index,
    ))

    # index proximo do fim -- indices iniciais sao descartados por
    # calculate_indicators() (dropna do warmup de BB/EMA50), entao um
    # indice cedo demais nao sobreviveria ao df final usado para o filtro
    # de periodo em _add_real_trade_markers.
    closed_at = df.index[-5].isoformat()
    monkeypatch.setattr(chart, "load_recent_trades", lambda n=100000: [
        {"symbol": "BTC/USDT", "closed_at": closed_at, "exit_price": "105.0", "pnl_usdt": "5.0"},
    ])

    fig = chart._build_figure("BTC/USDT", "4h")

    trace_names = [t.name for t in fig.data]
    assert "trade real" in trace_names


def test_build_figure_without_real_trades_has_no_extra_trace(monkeypatch):
    df = _synthetic_ohlcv_df()
    monkeypatch.setattr(chart, "fetch_ohlcv", lambda symbol, timeframe, limit=200: df)
    monkeypatch.setattr(chart, "precompute_signals", lambda df, strategy: __import__("pandas").Series(
        ["HOLD"] * len(df), index=df.index,
    ))
    monkeypatch.setattr(chart, "load_recent_trades", lambda n=100000: [])

    fig = chart._build_figure("BTC/USDT", "4h")

    trace_names = [t.name for t in fig.data]
    assert "trade real" not in trace_names
