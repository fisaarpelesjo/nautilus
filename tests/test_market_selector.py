import pandas as pd

from market.selector import _filter_tickers, _spread_pct, _trend_pct, _volatility_pct, selected_symbols


def _df(closes):
    rows = []
    for close in closes:
        rows.append({
            "open": close,
            "high": close * 1.03,
            "low": close * 0.98,
            "close": close,
            "volume": 1000,
        })
    return pd.DataFrame(rows)


def test_spread_pct_uses_bid_ask_midpoint():
    assert round(_spread_pct(99, 101), 4) == 0.02


def test_filter_tickers_keeps_liquid_usdt_pairs_with_small_spread():
    tickers = {
        "BTC/USDT": {"quoteVolume": 50_000_000, "bid": 100, "ask": 100.1},
        "ETH/BTC": {"quoteVolume": 50_000_000, "bid": 1, "ask": 1.01},
        "USDC/USDT": {"quoteVolume": 50_000_000, "bid": 1, "ask": 1.001},
        "LOW/USDT": {"quoteVolume": 1_000, "bid": 1, "ask": 1.001},
        "WIDE/USDT": {"quoteVolume": 50_000_000, "bid": 1, "ask": 1.2},
    }

    result = _filter_tickers(tickers, min_volume_usdt=10_000_000, max_spread_pct=0.003)

    assert selected_symbols(result) == ["BTC/USDT"]


def test_volatility_and_trend_metrics():
    df = _df([100, 101, 102, 103, 104])

    assert _volatility_pct(df, window=5) > 0
    assert round(_trend_pct(df, window=5), 2) == 4.0
