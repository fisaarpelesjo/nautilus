from backtesting import performance_charts


def _trade_row(symbol, pnl_usdt, closed_at, balance_after):
    return {
        "symbol": symbol, "pnl_usdt": str(pnl_usdt), "closed_at": closed_at,
        "balance_after": str(balance_after), "exit_reason": "take profit",
    }


def test_build_performance_figures_returns_three_figures():
    trades = [
        _trade_row("BTC/USDT", 10.0, "2026-01-01T00:00:00", 1010.0),
        _trade_row("ETH/USDT", -5.0, "2026-01-02T00:00:00", 1005.0),
        _trade_row("BTC/USDT", 8.0, "2026-01-03T00:00:00", 1013.0),
    ]

    figures = performance_charts.build_performance_figures(trades)

    assert figures.status == "ok"
    assert figures.capital_curve is not None
    assert figures.drawdown_curve is not None
    assert figures.pnl_by_pair is not None


def test_build_performance_figures_handles_empty_trade_list():
    figures = performance_charts.build_performance_figures([])

    assert figures.status == "sem_dados"
    assert figures.capital_curve is None
    assert figures.drawdown_curve is None
    assert figures.pnl_by_pair is None
