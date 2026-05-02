# AGENTS.md — Crypto Day Trader Bot

## Overview

Algorithmic trading bot for crypto written in Python. Connects to Binance via `ccxt`. Supports **paper** (simulated) and **live** (real money) modes. Main strategy: EMA crossover (9/21) with EMA50 trend filter and RSI confirmation.

---

## Project Structure

```
├── main.py                    # CLI entry point: python main.py [backtest|multibacktest|scan|bot|status]
├── bot.py                     # Compatibility wrapper for trading/runner.py
├── config/
│   └── settings.py            # All configs loaded from .env
├── data/
│   ├── fetcher.py             # Fetches OHLCV from Binance with in-memory cache
│   ├── paths.py               # Local file paths
│   ├── trade_store.py         # Closed trades
│   ├── signal_store.py        # Signal changes
│   ├── decision_store.py      # Decisions per cycle/pair
│   ├── state_store.py         # Current bot state
│   ├── ohlcv_store.py         # Accumulated candles
│   ├── trade_logger.py        # Backwards-compat for old imports
│   └── ohlcv/                 # Accumulated historical candles (CSV per pair/TF)
├── strategy/
│   ├── base.py                # BaseStrategy interface + Signal/TradeSignal dataclasses
│   ├── diagnostics.py         # Signal checks and diagnostics
│   └── ema_rsi.py             # EMA9/21/50 + RSI14 strategy
├── trading/
│   ├── runner.py              # Main bot loop (polls every 60s)
│   ├── decision_logger.py     # Analytical decision history
│   └── position_lifecycle.py  # Entry, exit, trailing stop, and MTF
├── risk/
│   └── manager.py             # Calculates SL, TP, position size
├── execution/
│   └── order_manager.py       # Opens/closes orders; persists state; restores on restart
├── backtesting/
│   ├── engine.py              # Simulates strategy on historical data
│   ├── multi.py               # Backtest on fixed pair list
│   └── scanner.py             # Scans top 30 pairs by volume and backtests
└── utils/
    ├── display.py             # Rich display: multi-pair table, price formatting
    ├── logger.py              # Colored terminal logger + file output in logs/
    └── notifier.py            # Telegram alerts (optional)
```

Runtime artifacts (`data/signals.csv`, `data/trades.csv`, `data/state.json`, `data/ohlcv/`, `logs/`) are local and git-ignored. Tests go under `tests/`.

---

## Commands

```bash
python main.py backtest         # backtest on main pair (PAIRS[0])
python main.py multibacktest    # backtest on fixed pair list
python main.py scan             # backtest on top 30 Binance pairs by volume
python main.py bot              # start multi-pair trading loop
python main.py status           # current price and balance
python main.py analisar         # summarize data/trades.csv
python main.py otimizar         # test EMA/RSI/ATR/volume/BB parameter combinations
python main.py selecionar       # rank dynamic pair candidates
```

Default to `TRADING_MODE=paper` while developing.

---

## Incremental Workflow

For any non-trivial change in this project, split the work into small topical steps. After each completed topic, run the relevant tests, commit with a concise Conventional Commit message in Portuguese, push to `origin/main`, and only then continue to the next topic. Do not commit runtime artifacts.

---

## Configuration (.env)

All environment variables live in `.env` (never commit). `.env.example` has the template without real values.

| Variable | Default | Description |
|---|---|---|
| `BINANCE_API_KEY` | — | Binance API key |
| `BINANCE_API_SECRET` | — | Binance API secret |
| `TRADING_MODE` | `paper` | `paper` or `live` |
| `PAIRS` | `ENSO/USDT,...` | Comma-separated pair list; `SYMBOL` = `PAIRS[0]` |
| `TIMEFRAME` | `4h` | Candle timeframe |
| `MAX_ORDER_SIZE_USDT` | `100.0` | Per-order cap in USDT |
| `MAX_POSITIONS` | `5` | Max simultaneous open positions |
| `STOP_LOSS_PCT` | `0.015` | Fixed stop loss (fallback without ATR) |
| `TAKE_PROFIT_PCT` | `0.06` | Fixed take profit (fallback without ATR) |
| `ATR_SL_MULTIPLIER` | `1.5` | ATR multiplier for stop loss |
| `ATR_TP_MULTIPLIER` | `3.0` | ATR multiplier for take profit |
| `VOLUME_MA_PERIOD` | `20` | Volume moving average window for filter |
| `VOLUME_MIN_RATIO` | `1.2` | Minimum volume = average × ratio for BUY |
| `MTF_TIMEFRAME` | `1d` | Trend confirmation timeframe (multi-timeframe) |
| `COOLDOWN_HOURS` | `4` | Re-entry block hours after stop loss |
| `DAILY_DRAWDOWN_LIMIT` | `0.05` | Daily loss limit (5% of initial balance = $50) |
| `DAILY_REPORT_HOUR` | `0` | Hour (0–23) to send daily Telegram report |
| `BB_PERIOD` | `20` | Bollinger Bands period |
| `BB_STD` | `2.0` | Bollinger Bands standard deviations |
| `TELEGRAM_BOT_TOKEN` | — | Telegram bot token (optional) |
| `TELEGRAM_CHAT_ID` | — | Telegram chat ID (optional) |

---

## Strategy — EmaRsiStrategy

**File:** `strategy/ema_rsi.py`

**Calculated indicators:**
- `ema_fast` — EMA(9)
- `ema_slow` — EMA(21)
- `ema_trend` — EMA(50), trend filter
- `rsi` — RSI(14)
- `macd` — MACD diff (logged, not yet used in signal)
- `atr` — ATR(14), used by risk manager for dynamic SL/TP
- `volume_ma` — simple moving average of volume (period `VOLUME_MA_PERIOD`)
- `bb_upper`, `bb_middle`, `bb_lower` — Bollinger Bands(20, 2)

**Entry/exit rules:**

| Signal | Condition |
|---|---|
| BUY | EMA9 crosses above EMA21 **and** price > EMA50 **and** RSI < 65 **and** volume > 1.2× avg(20) **and** price > EMA50 on daily timeframe (MTF) **and** price ≤ BB upper (not overextended) |
| SELL | EMA9 crosses below EMA21 **and** RSI > 35 |
| HOLD | none of the above |

**Stop Loss / Trailing Stop / Take Profit** are managed in `trading/position_lifecycle.py`, not in the strategy. Each poll, if price makes a new high, stop loss rises to `high - 1.5×ATR`, locking in profit. Fixed TP remains as max target.

**Cycle management rules (`trading/runner.py`):**
- `MAX_ENTRIES_PER_CYCLE = 1` — max 1 new position per 60s cycle, avoids correlated simultaneous entries
- Cooldown activated after Stop Loss **and** after Sell signal with loss
- `log_signal` only records when signal changes (HOLD→BUY, BUY→SELL, etc.), not every poll

---

## Risk Management — risk/manager.py

- Order size: `min(MAX_ORDER_SIZE_USDT, balance * 0.95)`
- **Dynamic SL/TP via ATR:** `SL = entry - ATR_SL_MULTIPLIER × ATR14` / `TP = entry + ATR_TP_MULTIPLIER × ATR14`
- Fallback (if ATR = 0): fixed SL at `STOP_LOSS_PCT` (1.5%), fixed TP at `TAKE_PROFIT_PCT` (6%)
- Minimum SL: never below 50% of entry price
- Default risk/reward ratio with ATR: 1:2 (1.5× ATR risk, 3× ATR target)

---

## Data Persistence

| File | Format | Content |
|---|---|---|
| `data/decisions.csv` | CSV | Each cycle per pair: signal, final decision, blocks, filters and indicators |
| `data/signals.csv` | CSV | Signal changes: timestamp, price, indicators, signal |
| `data/trades.csv` | CSV | Each closed trade: entry, exit, PnL, reason |
| `data/ohlcv/BTCUSDT_4h.csv` | CSV | Accumulated historical candles |
| `data/state.json` | JSON | Current state: balance, open position, counters |
| `logs/YYYY-MM-DD.log` | text | Full daily text log |
| `logs/events-YYYY-MM-DD.jsonl` | JSONL | Structured events: orders, errors, operational cycle |

Bot restores state from `state.json` on restart — open position and paper balance are preserved.

---

## Candle Cache

`data/fetcher.py` maintains an in-memory cache (`_cache` dict). First call fetches `CANDLE_LIMIT=100` candles. Subsequent calls fetch only the last 5 and merge, avoiding repeated latency (~5s per full call from Brazil).

---

## How to Add a New Strategy

1. Create `strategy/my_strategy.py` inheriting `BaseStrategy`
2. Implement `calculate_indicators(df)` and `generate_signal(df) -> TradeSignal`
3. Swap the instance in `trading/runner.py` and `backtesting/engine.py`

---

## Coding Style & Naming Conventions

Use idiomatic Python with 4-space indentation. Module names lowercase with underscores, classes in `PascalCase`, functions/variables in `snake_case`. Follow the existing small-module style with explicit local imports. Prefer typed signatures for new strategy, risk, and execution logic. Keep comments brief; do not commit generated CSV, cache, log, or state files.

---

## Testing Guidelines

Use `pytest`. Name files `tests/test_<module>.py` and functions `test_<behavior>()`. Prioritize deterministic tests for strategy signals, risk calculations, state recovery, and order-manager behavior. Mock Binance, Telegram, and network calls.

---

## Commit & Pull Request Guidelines

Conventional Commits in Portuguese: `feat:` for new capabilities, `fix:` for corrections. Keep messages concise: `feat: adicionar filtro de volatilidade`, `fix: corrigir restauração de posição`. Pull requests should describe behavior changes, list validation commands, note config changes, and include screenshots or log excerpts when CLI/display output changes.

---

## Main Dependencies

```
ccxt          # exchange connection (Binance, etc.)
pandas        # time series manipulation
ta            # technical indicators (EMA, RSI, MACD)
python-dotenv # .env loading
colorlog      # colored terminal logs
requests      # Telegram notifications
```

---

## Security & Important Warnings

- **Never commit `.env`** — it is in `.gitignore`
- **Never enable withdrawals on Binance API keys** — required permissions: Read + Spot Trading only
- Always validate in **paper mode for weeks** before going live
- Bot operates **long positions only** (buy). Short is not implemented.
- Treat `TRADING_MODE=live` changes as high risk — explicit confirmation required.
