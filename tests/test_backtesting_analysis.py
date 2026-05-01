from backtesting.analysis import analyze_trades
from data.trade_logger import TRADE_HEADERS


def test_analyze_trades_calculates_summary_metrics(tmp_path):
    path = tmp_path / "trades.csv"
    path.write_text(
        ",".join(TRADE_HEADERS)
        + "\n"
        + "2026-01-01,2026-01-01,BTC/USDT,long,100,110,1,10,10,Take Profit,1010\n"
        + "2026-01-02,2026-01-02,ETH/USDT,long,100,95,1,-5,-5,Stop Loss,1005\n"
        + "2026-01-03,2026-01-03,BTC/USDT,long,100,98,1,-2,-2,Sinal de venda,1003\n",
        encoding="utf-8",
    )

    result = analyze_trades(str(path))

    assert result.total_trades == 3
    assert result.total_pnl == 3.0
    assert round(result.win_rate, 2) == 33.33
    assert result.profit_factor == 10 / 7
    assert result.expectancy == 1.0
    assert result.average_win == 10.0
    assert result.average_loss == -3.5
    assert result.largest_win == 10.0
    assert result.largest_loss == -5.0
    assert result.max_losing_streak == 2
    assert result.by_symbol == {"BTC/USDT": 8.0, "ETH/USDT": -5.0}
    assert result.by_exit_reason == {"Take Profit": 1, "Stop Loss": 1, "Sinal de venda": 1}
    assert result.final_balance == 1003.0


def test_analyze_trades_returns_empty_result_for_missing_file(tmp_path):
    result = analyze_trades(str(tmp_path / "missing.csv"))

    assert result.total_trades == 0
    assert result.total_pnl == 0.0
    assert result.by_symbol == {}
