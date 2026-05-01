# Repository Guidelines

## Project Structure & Module Organization

This is a Python crypto trading bot. `main.py` is the CLI entry point and `bot.py` contains the live/paper trading loop. Configuration lives in `config/settings.py` and is loaded from `.env`. Market data and persistence are in `data/`, strategy logic in `strategy/`, risk sizing in `risk/`, orders in `execution/`, backtests in `backtesting/`, and shared helpers in `utils/`.

Runtime artifacts such as `data/signals.csv`, `data/trades.csv`, `data/state.json`, `data/ohlcv/`, and `logs/` are generated locally and ignored by Git. There is no test directory yet; add tests under `tests/`.

For deeper architecture, strategy, and runtime behavior details, consult `CLAUDE.md`.

## Build, Test, and Development Commands

Create an isolated environment before installing dependencies:

```bash
python -m venv .venv
pip install -r requirements.txt
```

Common commands:

```bash
python main.py status         # show configured pairs, balance, and open positions
python main.py backtest       # run a single-pair backtest using PAIRS[0]
python main.py multibacktest  # run configured multi-pair backtests
python main.py scan           # scan top Binance pairs by volume
python main.py bot            # start the trading loop
```

Default to `TRADING_MODE=paper` while developing.

## Coding Style & Naming Conventions

Use idiomatic Python with 4-space indentation. Keep module names lowercase with underscores, classes in `PascalCase`, and functions/variables in `snake_case`. Follow the existing small-module style with explicit local imports. Prefer typed signatures for new strategy, risk, and execution logic. Keep comments brief; do not commit generated CSV, cache, log, or state files.

## Testing Guidelines

No test framework is currently declared in `requirements.txt`. For new tests, use `pytest` unless the project adopts another standard. Name files `tests/test_<module>.py` and functions `test_<behavior>()`. Prioritize deterministic tests for strategy signals, risk calculations, state recovery, and order-manager behavior. Mock Binance, Telegram, and network calls.

## Commit & Pull Request Guidelines

Commit history follows simple Conventional Commits in Portuguese: `feat:` for new bot capabilities and `fix:` for corrections or operational improvements. Keep messages concise, for example `feat: adicionar filtro de volatilidade` or `fix: corrigir restauração de posição`. Pull requests should describe behavior changes, list validation commands, note config changes, and include screenshots or log excerpts when CLI/display output changes.

## Security & Configuration Tips

Never commit `.env`, API keys, Telegram tokens, or production state. Use `.env.example` for documented configuration only. Binance API keys should have read and spot-trading permissions only; never enable withdrawals. Treat `TRADING_MODE=live` changes as high risk.
