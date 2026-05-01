# Roadmap

This roadmap tracks improvements identified by comparing this bot with mature open-source crypto trading bots such as Freqtrade, Jesse, Hummingbot, VibeTrading, and Wisp. Prioritize changes that improve validation, observability, and decision quality before adding advanced automation.

## Prioridade Alta

- Advanced backtest metrics: add profit factor, expectancy, average win/loss, largest win/loss, max losing streak, simplified Sharpe, exposure, and return by pair/timeframe.
- `analyze` command: read `data/trades.csv` and generate a local performance summary after paper or live sessions.
- Parameter optimization: add `python main.py optimize` to test ranges for EMA, RSI, ATR, volume, and Bollinger Band parameters.
- Dynamic whitelist: select tradable pairs automatically using volume, spread, volatility, trend, and recent backtest results.
- Pair blacklist: support `BLACKLIST_PAIRS` and skip stablecoins, low-liquidity pairs, or assets known to be problematic.

## Prioridade Média

- Local dashboard: add `python main.py dashboard` to show balance, open positions, PnL, latest trades, latest signals, and pair status.
- Strategy debug mode: explain why each pair is `BUY`, `SELL`, or `HOLD`, including EMA, RSI, volume, MTF, and Bollinger filter results.
- Strategy benchmark: compare multiple strategies, presets, pairs, and timeframes in one command.
- Report exports: save backtest and analysis output under `reports/` as JSON, CSV, and Markdown.
- Charts: generate equity curve, drawdown, PnL by pair, and candle charts with trade markers.

## Prioridade Baixa / Avançado

- Monte Carlo analysis: stress-test trade sequences and candle variations to estimate robustness and overfitting risk.
- ML signal filter: collect labeled features from backtests and optionally gate entries by model confidence.
- Multiple exchanges: generalize exchange configuration beyond Binance using the existing `ccxt` foundation.
- Smart order handling: add limit/stop orders, order reconciliation, partial-fill tracking, and safer live execution controls.

## Implementation Notes

Keep each item small enough for its own commit and validation step. Prefer deterministic tests before behavior changes. Any feature that can affect live trading must preserve `TRADING_MODE=paper` as the default and keep explicit live-mode safeguards.
