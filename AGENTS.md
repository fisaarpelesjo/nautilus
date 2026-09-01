# AGENTS.md — Crypto Day Trader Bot

## Overview

Algorithmic trading bot for crypto written in Python. Connects to Binance via `ccxt`. Supports **paper** (simulated) and **live** (real money) modes. Main strategy: EMA crossover (default 9/21, configurable) with EMA50 trend filter, RSI confirmation, and trend-pullback entry.

---

## Project Structure

```
├── main.py                    # CLI entry point: python main.py [backtest|edge|multibacktest|scan|bot|status]
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
│   └── ema_rsi.py             # EMA12/21/50 + RSI14 strategy
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
    ├── chart.py               # Interactive Dash/Plotly chart (candlestick, EMAs, RSI, open position)
    ├── display.py             # Rich display: multi-pair table, price formatting
    ├── logger.py              # Colored terminal logger + file output in logs/
    └── notifier.py            # Telegram alerts (optional)
```

Runtime artifacts (`data/signals.csv`, `data/trades.csv`, `data/state.json`, `data/ohlcv/`, `logs/`) are local and git-ignored. Tests go under `tests/`.

---

## Commands

```bash
python main.py backtest             # backtest on main pair (PAIRS[0])
python main.py backtest --validate  # backtest with train/out-of-sample split + verdict
python main.py edge                 # profitability edge report vs buy-and-hold
python main.py edge --validate      # edge report on the out-of-sample validation slice (train + validation side by side)
python main.py multibacktest        # backtest on fixed pair list
python main.py scan                 # backtest on top 30 Binance pairs by volume
python main.py compare              # compare multiple strategies/presets side by side
python main.py multimarket [SYM..]  # sweep strategy x symbol across markets, with out-of-sample confirmation
python main.py horizonte [TF..]     # evaluate strategies on 4h/1d/1w with the full battery (spec 024)
python main.py volatilidade [TGT]   # compare each strategy with and without volatility-based sizing (spec 025)
python main.py optimize             # grid search best EMA/RSI/ATR/volume/BB parameters
python main.py analyze              # summarize data/trades.csv
python main.py decisions            # summarize data/decisions.csv: signals, blockers, average RSI by signal
python main.py select               # rank dynamic pair candidates
python main.py chart [PAIR] [TF]    # interactive browser chart (Dash/Plotly)
python main.py bot                  # start multi-pair trading loop
python main.py status               # portfolio (cash/positions/total), PnL, circuit breaker and kill switch
python main.py kill                 # suspend new entries (manual kill switch)
python main.py resume               # resume new entries (manual kill switch)
python main.py painel               # portfolio, positions, recent trades/signals and recent blockers
python main.py debug [PAIR]         # explains each entry condition (EMA, RSI, MTF, regime, cooldown...)
python main.py performance          # capital curve, drawdown and PnL per pair (HTML in browser)
python main.py replay [PAIR]        # runs the real decision path over history, isolated (never touches real files)
```

Default to `TRADING_MODE=paper` while developing.

---

## Incremental Workflow

For any non-trivial change in this project, split the work into small topical steps. After each completed topic, run the relevant tests, commit with a concise Conventional Commit message in Portuguese, push to `origin/main`, and only then continue to the next topic. Do not commit runtime artifacts.

## CLAUDE.md ↔ AGENTS.md Sync

`CLAUDE.md` (PT) and `AGENTS.md` (EN) must always have the same content. When modifying any section in one file, update the equivalent in the other in the same commit.

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
| `MAX_SPREAD_PCT_ENTRY` | `0.005` | Max order book spread allowed to enter a position (distinct from `MAX_SPREAD_PCT`, used in dynamic pair selection) |
| `MIN_ORDERBOOK_DEPTH_USDT` | `3 × MAX_ORDER_SIZE_USDT` | Minimum ask-side depth required to enter a position |
| `USE_LIMIT_ORDERS` | `false` | When `true`, entries use a limit order instead of market |
| `LIMIT_ORDER_TIMEOUT_CYCLES` | `3` | Cycles (60s each) before cancelling an unfilled limit order (or accepting the partial fill already obtained) |
| `STOP_LOSS_PCT` | `0.015` | Fixed stop loss (fallback without ATR) |
| `TAKE_PROFIT_PCT` | `0.06` | Fixed take profit (fallback without ATR) |
| `ATR_SL_MULTIPLIER` | `1.5` | ATR multiplier for stop loss |
| `ATR_TP_MULTIPLIER` | `3.0` | ATR multiplier for take profit |
| `MAX_STOP_LOSS_PCT` | `0.08` | Per-trade loss cap when SL comes from ATR (protects high-volatility pairs where a raw `ATR_SL_MULTIPLIER` has no practical limit) |
| `EMA_FAST` | `9` | Fast EMA period |
| `EMA_SLOW` | `21` | Slow EMA period |
| `EMA_TREND` | `50` | Trend EMA period |
| `RSI_PERIOD` | `14` | RSI period |
| `RSI_OVERSOLD` | `35` | Minimum RSI to allow a sell signal |
| `RSI_OVERBOUGHT` | `70` | Maximum RSI to allow an entry |
| `PULLBACK_ENTRY_ENABLED` | `true` | Enables trend-pullback entry (in addition to crossover) |
| `PULLBACK_RSI_MIN` | `45` | Minimum RSI for a pullback entry |
| `PULLBACK_MAX_DISTANCE_PCT` | `0.01` | Max distance between the candle's low and the slow EMA on a pullback |
| `VOLUME_MA_PERIOD` | `20` | Volume moving average window for filter |
| `VOLUME_MIN_RATIO` | `1.0` | Minimum volume = average × ratio for BUY |
| `MTF_TIMEFRAME` | `1d` | Trend confirmation timeframe (multi-timeframe) |
| `COOLDOWN_HOURS` | `4` | Re-entry block hours after stop loss |
| `DAILY_DRAWDOWN_LIMIT` | `0.05` | Daily loss limit (5% of the daily reference balance) |
| `WEEKLY_DRAWDOWN_LIMIT` | `0.10` | Weekly loss limit (10% of the weekly reference balance); must be ≥ `DAILY_DRAWDOWN_LIMIT` |
| `MONTHLY_DRAWDOWN_LIMIT` | `0.20` | Monthly loss limit (20% of the monthly reference balance); must be ≥ `WEEKLY_DRAWDOWN_LIMIT` |
| `MAX_CONSECUTIVE_LOSSES` | `3` | Consecutive losses (`pnl < 0`) before the circuit breaker trips; resets on a trade with `pnl > 0` |
| `CIRCUIT_BREAKER_COOLDOWN_HOURS` | `4` | Hours after the circuit breaker trips before it auto-deactivates even with no profitable trade |
| `MAX_POSITION_CORRELATION` | `0.7` | Return correlation (over `CORRELATION_LOOKBACK`) above which a new entry is blocked for already having a correlated open position |
| `CORRELATION_LOOKBACK` | `50` | Number of candles used to compute correlation between pairs |
| `ADAPTIVE_RSI_ENABLED` | `false` | Allows the crossover entry above `RSI_OVERBOUGHT` when volume confirms a real spike |
| `ADAPTIVE_RSI_VOLUME_RATIO` | `2.0` | Minimum volume (× average) for adaptive RSI to allow the entry |
| `BACKTEST_FEE_RATE` | `0.001` | Exchange fee on entry/exit notional value — used by the backtest **and** in `TRADING_MODE=paper` (not in `live`, which already pays a real fee) |
| `BACKTEST_SLIPPAGE_PCT` | `0.0005` | Slippage applied to entry/exit price — used by the backtest **and** as floor/fallback in `TRADING_MODE=paper` (not in `live`, which already experiences real slippage) |
| `REAL_SLIPPAGE_ENABLED` | `true` | In paper mode, measures slippage by walking the real order book instead of using a flat `BACKTEST_SLIPPAGE_PCT` |
| `DAILY_REPORT_HOUR` | `0` | Hour (0–23) to send daily Telegram report |
| `BB_PERIOD` | `20` | Bollinger Bands period |
| `BB_STD` | `2.0` | Bollinger Bands standard deviations |
| `REGIME_ADX_THRESHOLD` | `20` | Minimum ADX to classify market regime as `trending` |
| `REGIME_FILTER_ENABLED` | `false` | When `true`, suspends new entries in `sideways`/`indefinido` regime |
| `HIGH_VOLATILITY_ATR_RATIO` | `0.05` | `ATR_ratio` (ATR14/close) above which a candle is considered high volatility |
| `HIGH_VOLATILITY_FILTER_ENABLED` | `false` | When `true`, blocks new entries on high-volatility candles |
| `ADAPTIVE_BOLLINGER_ENABLED` | `false` | When `true`, allows entry above the upper band with strong trend/volume |
| `BREAKOUT_WINDOW` | `150` | Default window (periods) for `strategy/breakout.py` |
| `TELEGRAM_BOT_TOKEN` | — | Telegram bot token (optional) |
| `TELEGRAM_CHAT_ID` | — | Telegram chat ID (optional) |

---

## Strategy — EmaRsiStrategy

**File:** `strategy/ema_rsi.py`

**Calculated indicators** (configurable periods via `.env`, see Configuration section):
- `ema_fast` — EMA(`EMA_FAST`, default 9)
- `ema_slow` — EMA(`EMA_SLOW`, default 21)
- `ema_trend` — EMA(`EMA_TREND`, default 50), trend filter
- `rsi` — RSI(`RSI_PERIOD`, default 14)
- `macd` — MACD diff (logged, not yet used in signal)
- `atr` — ATR(14), used by risk manager for dynamic SL/TP
- `atr_ratio` — ATR14 / close, relative volatility indicator
- `adx` — ADX(14), basis for the market regime
- `regime` — `trending`/`sideways`/`indefinido`, derived from `adx` vs `REGIME_ADX_THRESHOLD`
- `volume_ma` — simple moving average of volume (period `VOLUME_MA_PERIOD`)
- `bb_upper`, `bb_middle`, `bb_lower` — Bollinger Bands(20, 2)

**Entry/exit rules:**

| Signal | Condition |
|---|---|
| BUY (crossover) | Fast EMA crosses above slow EMA **and** price > trend EMA **and** RSI < `RSI_OVERBOUGHT` (default 70) **and** volume ≥ avg×`VOLUME_MIN_RATIO` (default 1.0) **and** price > trend EMA on the MTF timeframe **and** price ≤ BB upper (not overextended, or `ADAPTIVE_BOLLINGER_ENABLED` with strong trend/volume) |
| BUY (pullback) | Alternative to crossover, on by default (`PULLBACK_ENTRY_ENABLED=true`): trend already established (fast EMA > slow EMA > trend EMA), RSI between `PULLBACK_RSI_MIN` (default 45) and `RSI_OVERBOUGHT`, candle low near the slow EMA (`PULLBACK_MAX_DISTANCE_PCT`), price already recovered above the fast EMA, bullish candle — same volume/Bollinger filters as crossover |
| SELL | Fast EMA crosses below slow EMA **and** RSI > `RSI_OVERSOLD` (default 35) |
| HOLD | none of the above, **or** blocked by `REGIME_FILTER_ENABLED`/`HIGH_VOLATILITY_FILTER_ENABLED` (new entries only — a sell signal for an already-open position is never blocked by these filters) |

**Optional filters** (all off by default, additive — see `specs/006-evolucao-estrategia-novas/`): market regime via ADX (`REGIME_FILTER_ENABLED`), high volatility via `ATR_ratio` (`HIGH_VOLATILITY_FILTER_ENABLED`), the adaptive Bollinger filter (`ADAPTIVE_BOLLINGER_ENABLED`), and adaptive RSI (`ADAPTIVE_RSI_ENABLED`): allows the **crossover** entry above `RSI_OVERBOUGHT` when volume confirms a real spike (`volume >= ADAPTIVE_RSI_VOLUME_RATIO × average`, default `2.0`) — doesn't affect the pullback's own RSI ceiling, a different scenario (controlled dip in an already-established trend, not a vertical spike). Applied both in the per-candle path (`generate_signal`) and the vectorized one (`precompute_signals`, used by `optimize`/`backtest --validate`/`optimize --walk-forward`) — the two paths must stay in sync whenever a new filter is added.

**Stop Loss / Trailing Stop / Take Profit** are managed in `trading/position_lifecycle.py`, not in the strategy. Each poll, if price makes a new high, stop loss rises to `high - 1.5×ATR`, locking in profit. Fixed TP remains as max target.

**Breakout strategy** (`strategy/breakout.py`, `BreakoutStrategy`): Donchian channel — buys when price breaks above the highest high of the last `BREAKOUT_WINDOW` candles (default `150`, testable at 50/150/200), sells when it breaks below the lowest low. Runs through the same backtest infrastructure via `run_backtest(..., strategy=BreakoutStrategy(window=N))`.

**Strategy/preset comparison**: `python main.py compare` (alias `comparar`) runs multiple strategies/presets over the same pairs/timeframe in a single run, reusing the already-established `evaluate_approval`/`edge_score` — no new comparison criterion.

---

## Multi-market (research only — spec 023)

The bot **trades** crypto on Binance exclusively. Since spec 023 it can **evaluate** strategies on other markets, to answer "does any strategy × market combination have real edge?" before investing in a broker and execution for any new market.

**Markets and sources** (`data/markets.py`, `data/sources/`): the market is derived from the symbol's format, and each market declares its source, cost, continuity and whether it's tradable.

| Market | Example symbol | Source | Continuous | Tradable |
|---|---|---|---|---|
| `crypto` | `BTC/USDT` | ccxt | yes | **yes** |
| `stocks_us` | `AAPL` | yfinance | no | no |
| `stocks_br` | `PETR4.SA` | yfinance | no | no |
| `forex` | `EURUSD=X` | yfinance | yes | no |
| `futures` | `ES=F` | yfinance | no | no |
| `index` | `^GSPC` | yfinance | no | no |

- **`fetch_ohlcv()`'s signature did not change** — it resolves the market and delegates to the source. The ~10 consumers stay identical. `fetch_ticker`/`fetch_tickers`/`fetch_balance`/`fetch_order_book` remain **crypto-only** (they belong to the execution path).
- **`PAIRS` vs `RESEARCH_SYMBOLS`**: two separate lists. `PAIRS` feeds the live loop and keeps the strict `/USDT` format validation; `RESEARCH_SYMBOLS` feeds research only and accepts any resolvable symbol. Relaxing `PAIRS` would reopen the path for a non-tradable symbol to reach execution.
- **`trading/runner.py::assert_pares_operaveis()`** refuses startup if `PAIRS` contains a symbol from a market without execution, naming every offender at once.
- **Cost per market** (`MARKET_COST_PROFILES` in `config/settings.py`): each market has its own fee and slippage, overridable via `.env`. A market with no declared profile is **rejected**, never evaluated with another market's cost — the inverse of that mechanism is what made ACE/BIO/ALLO look tradable and deliver real losses. Crypto reuses `BACKTEST_FEE_RATE`/`BACKTEST_SLIPPAGE_PCT` directly, so passing through the new layer can't change crypto backtest results.
- **History limit**: the non-crypto source caps intraday history at **730 days** (~993 candles at 4h vs 2,000 for crypto). `YFinanceSource.last_shortfall` and `BacktestResult.requested_candles` make the gap detectable — asking for 2,000 and getting 993 is normal, but going unnoticed would silently unbalance a comparison.
- **Session gaps**: discontinuous markets set `BacktestResult.has_session_gaps`. The per-trade loss cap (`MAX_STOP_LOSS_PCT`) **does not act inside an opening gap** — price jumps over the stop.

**`python main.py multimarket [SYMBOLS...]`** (`backtesting/multimarket.py`): sweeps strategy × symbol and requires approval to be **confirmed on a window that did not take part in the discovery**. Testing N strategies × M symbols produces approvals by chance; without that split, luck reads as a finding. Statuses: `confirmado`, `defensivo` (confirmation's PF/drawdown/trades would pass `evaluate_approval()` if not solely for not beating an extreme buy-and-hold rally — **not an approval**, but real edge proven out-of-sample, distinct from `reprovado`; the bot never allocates 100% into a single pair, so "beating buy-and-hold" is stricter than the risk it actually takes), `so na busca` (passed where it was discovered and didn't hold up — **not an approval**, weaker evidence than `defensivo` since it proves nothing in the confirmation window itself), `reprovado`, `inconclusivo` (not enough history to split). Reuses the existing `split_train_validation()` and `evaluate_approval()` — `defensivo` uses `evaluate_approval()`'s `require_beat_buy_hold=False` parameter, no new criterion invented.

**Cycle management rules (`trading/runner.py`):**
- `MAX_ENTRIES_PER_CYCLE = 1` — max 1 new position per 60s cycle, avoids correlated simultaneous entries
- Cooldown activated after Stop Loss **and** after Sell signal with loss
- `log_signal` only records when signal changes (HOLD→BUY, BUY→SELL, etc.), not every poll

---

## Risk Management — risk/manager.py

- Order size: `min(MAX_ORDER_SIZE_USDT, (balance / remaining_slots) * 0.95)` — `trading/position_lifecycle.py` reserves balance proportionally to the slots still free (`MAX_POSITIONS - open positions`) before calling `risk/manager.py`, not plain `balance * 0.95`
- **Dynamic SL/TP via ATR:** `SL = entry - ATR_SL_MULTIPLIER × ATR14` / `TP = entry + ATR_TP_MULTIPLIER × ATR14`
- Fallback (if ATR = 0): fixed SL at `STOP_LOSS_PCT` (1.5%), fixed TP at `TAKE_PROFIT_PCT` (6%)
- Minimum SL: never below `MAX_STOP_LOSS_PCT` (8%) of entry price, even with a wide ATR on high-volatility pairs
- Default risk/reward ratio with ATR: 1:2 (1.5× ATR risk, 3× ATR target)
- **Execution cost in paper mode** (`execution/order_manager.py` `_paper_buy`/`_paper_sell`):
  fee (`BACKTEST_FEE_RATE`) on the notional value — same formula as the backtest
  (`backtesting/engine.py`), so the `data/trades.csv` history in paper mode isn't systematically
  more optimistic than reality. `TRADING_MODE=live` is unaffected (real execution already pays
  real market cost).
- **Slippage measured against the real order book** (`execution/liquidity.py`
  `estimate_slippage_pct()`): with `REAL_SLIPPAGE_ENABLED` (default `true`), paper mode walks the
  real book — consuming levels from the top until the order is filled and comparing the average
  fill price against the best price. `BACKTEST_SLIPPAGE_PCT` becomes the **floor** (latency
  slippage between decision and execution, which walking the book can't capture) and the
  **fallback** when the book can't be read or is too shallow — unknown slippage must never become
  a silent zero. Rationale: a single flat constant is realistic only for the most liquid pairs,
  and execution cost is the variable this strategy proved most sensitive to. Order scale matters:
  at $100/order most pairs measure 0.000% (the constant is conservative), but at $10k+ real
  slippage reaches 0.5–1% on several pairs. Doesn't affect historical backtests (no past order
  book exists) nor `python main.py replay`, where it's forced to `false` so today's liquidity
  isn't applied to an old candle.

---

## Operational Safeguards — Reconciliation, Circuit Breaker, Kill Switch

- **Reconciliation** (`execution/reconciliation.py`): in `TRADING_MODE=live`, compares `state.json`
  against the real balance via `fetch_balance()` on startup and every ~30min
  (`RECONCILIATION_INTERVAL_CYCLES=30` cycles). A mismatch emits a
  `reconciliation_mismatch`/`reconciliation_error` event (JSONL) and a Telegram alert — never
  auto-corrects. Result shown in `python main.py status`. No-op in `paper` mode (no real account to
  compare against).
- **Circuit breaker** (`execution/order_manager.py`): global `consecutive_losses` counter over
  closed trades with `pnl < 0`, resets only on `pnl > 0`. Once `MAX_CONSECUTIVE_LOSSES` is reached,
  `circuit_breaker_active=true` blocks new entries (open positions keep being managed normally).
  Independent of and additive with `DAILY_DRAWDOWN_LIMIT`. Also auto-deactivates on its own after
  `CIRCUIT_BREAKER_COOLDOWN_HOURS` (`check_circuit_breaker_timeout()`, called once per cycle by
  `trading/runner.py` while the breaker is active) — without this timeout, a breaker that trips with
  zero open positions would lock the bot forever, since no trade would remain to generate the profit
  that resets the counter.
- **Kill switch** (`data/killswitch_store.py`): manual flag in its own `data/killswitch.json` file,
  not in `state.json` — keeps a normal write from the running bot from overwriting an external
  activation via `python main.py kill`. Toggled via `kill`/`resume`; the bot reads the file from disk
  once per cycle.
- **Live session confirmation** (`trading/runner.py`): before the main loop, in `TRADING_MODE=live`,
  prints a summary (pairs, real balance, `MAX_ORDER_SIZE_USDT`, `MAX_POSITIONS`, daily/weekly/monthly/
  consecutive-loss limits) and logs a `live_session_started` event. Does not block startup waiting
  for interactive confirmation — informational only, in addition to the already-required
  `LIVE_TRADING_CONFIRMATION`. Not shown in `paper`.
- **Weekly and monthly loss limits** (`execution/order_manager.py`): same pattern as the daily limit,
  each with its own real reference balance (`daily_reference_balance`/`weekly_reference_balance`/
  `monthly_reference_balance`, captured on each period reset via `_reference_balance()`) and
  independent reset (calendar day / ISO week / calendar month). `WEEKLY_DRAWDOWN_LIMIT` must be
  ≥ `DAILY_DRAWDOWN_LIMIT`; `MONTHLY_DRAWDOWN_LIMIT` must be ≥ `WEEKLY_DRAWDOWN_LIMIT` (validated in
  `validate_config()`). An unknown reference balance blocks conservatively instead of using a $0
  limit.
- **Liquidity check** (`execution/liquidity.py`): before each entry, `check_liquidity` queries the
  real order book and blocks with a specific reason (`"liquidez: ..."`) when the spread exceeds
  `MAX_SPREAD_PCT_ENTRY` or ask-side depth falls below `MIN_ORDERBOOK_DEPTH_USDT`. A failure to fetch
  the order book also blocks (`"liquidez indisponivel"`) — never approval by omission.
- **Position correlation risk** (`risk/correlation.py`): before each entry, `check_correlated_exposure`
  compares the candidate pair's returns (`CORRELATION_LOOKBACK` window) against every already-open
  position's; correlation ≥ `MAX_POSITION_CORRELATION` blocks with reason `"correlacionado com
  {pair}"`. `MAX_POSITIONS` limits position *count*, not directional exposure — several correlated
  altcoins open at once behave like one large concentrated position during a broad market drop.
  Unlike the other checks in this file, this one fails **open** per individual comparison (doesn't
  block the whole entry just because one specific open position's history failed to fetch).
- **Limit orders with partial-fill tracking** (`execution/order_manager.py`): opt-in via
  `USE_LIMIT_ORDERS` (default `false`, preserves the market-order behavior). When enabled, the entry
  uses the best ask already fetched by the liquidity check as the limit price; the order sits in
  `pending_limit_orders` until `check_pending_limit_orders()` (called once per cycle) confirms the
  fill — a full fill opens the position, a partial fill after `LIMIT_ORDER_TIMEOUT_CYCLES` cancels
  the remainder and opens with only the filled quantity, zero fill after the timeout cancels and
  discards.

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
| `reports/{command}_{timestamp}.{json,csv,md}` | JSON/CSV/Markdown | Auditable history of each `backtest`/`scan`/`multibacktest`/`optimize` run (params, period, metrics, ranking) |

Bot restores state from `state.json` on restart — open position and paper balance are preserved.

---

## Operational Observability

- **Operational portfolio** (`trading/portfolio.py` `compute_portfolio_snapshot()`): computes free
  cash, positions value (at current price), total equity, realized PnL, unrealized PnL, and total
  PnL — reused by `status` and `painel`. An unavailable price for a position propagates `None`
  across every aggregated field (never a silent `0.0`).
- **`python main.py painel`** (`trading/panel.py`): aggregates portfolio, open positions, recent
  trades (`data/trades.csv`), recent signals (`data/signals.csv`), and recent blockers
  (`analyze_decisions()`, already existing). Missing/empty history becomes an explicit empty state
  in each section, never an error.
- **`python main.py debug <PAIR>`** (`strategy/diagnostics.py` `full_diagnosis()`): extends the
  already-existing `signal_checks()` with MTF, regime, volatility, and cooldown — shows the value
  of each entry condition to diagnose why a pair is `BUY`/`SELL`/`HOLD`.
- **`python main.py performance`/`desempenho`** (`backtesting/performance_charts.py`): capital
  curve, drawdown, and PnL per pair from `data/trades.csv`, combined HTML opened in the browser.
  `python main.py chart` gains a layer of real-trade markers (distinct from the already-existing
  theoretical signal markers).
- **`python main.py replay <PAIR>`** (`trading/replay.py`): runs the real decision path
  (`handle_entry_candidate`/`handle_open_position`, the same ones used by the production loop)
  candle by candle over public history — not the simplified simulation in
  `backtesting/engine.py`. Isolated via `_isolated_order_manager_environment()`: never touches
  real `data/state.json`/`data/trades.csv`/`data/signals.csv`/`data/decisions.csv`, never sends a
  real order, never fires a real Telegram message, regardless of `TRADING_MODE` in `.env` (even on
  error). Compares the result against a simple backtest of the same period. Partial approximation
  of "compare paper vs backtest" (`ROADMAP.md` Fase 5 item 4) — does not replace real paper
  operation, has known limitations (cooldown, drawdown resets and circuit-breaker timeout run off
  the real clock; trade timestamps are the execution time, not the candle's). **MTF is
  point-in-time** since 2026-08-24 via `mtf_confirmed()`'s `as_of` parameter — before that the
  replay compared the historical price against *today's* trend EMA, a future-based filter that
  systematically blocked the older, cheaper entries.
- **Report export** (`utils/report_export.py` `export_report()`): `backtest` (including
  `--validate`), `scan`, `multibacktest`, and `optimize` (including `--walk-forward`) save their
  result to `reports/` (JSON/CSV/Markdown, timestamp in the filename avoids overwrites). Reuses
  `dataclasses.asdict()` on the already-existing result instead of a parallel schema.
- **Aggressive profile diagnosis** (`backtesting/approval.py` `diagnose_profile()`): complements
  the already-existing "defensive" profile — drawdown above the acceptable threshold and return
  significantly above buy-and-hold (threshold `buy_hold + abs(buy_hold) * 0.5`, robust to a
  negative buy-hold).
- **`python main.py edge --validate`**: reuses `run_backtest_with_validation()` (same path as
  `backtest --validate`) and computes the approval verdict on the out-of-sample validation slice
  instead of the single-window result, showing train and validation side by side. Without the
  flag, behavior is identical to before.
- **Average indicators by signal** (`data/decisions_analysis.py`): `python main.py decisions`
  shows average RSI grouped by signal (`BUY`/`SELL`/`HOLD`), from values already recorded in
  `data/decisions.csv`.

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

Conventional Commits in Portuguese. Every commit requires both a subject line and a body:

- **Subject:** `type: short description` (max 72 chars) — e.g. `feat: adicionar filtro de volatilidade`
- **Body:** one or more lines explaining *what changed and why* — list the key changes, decisions, or context a future reader would need

Types: `feat:` new capability, `fix:` bug fix or correction, `docs:` documentation, `refactor:` restructure without behavior change, `test:` tests, `chore:` tooling/config.

Example:
```
feat: adicionar regime detection via ADX

Calcula ADX(14) em strategy/ema_rsi.py. ADX > 25 = trending (mantém
crossover), ADX < 20 = sideways (suspende entradas). Regime registrado
em data/decisions.csv para análise posterior.
```

Pull requests should describe behavior changes, list validation commands, note config changes, and include screenshots or log excerpts when CLI/display output changes.

---

## Main Dependencies

```
ccxt          # exchange connection (Binance, etc.)
pandas        # time series manipulation
ta            # technical indicators (EMA, RSI, MACD)
python-dotenv # .env loading
colorlog      # colored terminal logs
requests      # Telegram notifications
plotly        # interactive charts
dash          # local web server for interactive chart
```

---

## Security & Important Warnings

- **Never commit `.env`** — it is in `.gitignore`
- **Never enable withdrawals on Binance API keys** — required permissions: Read + Spot Trading only
- Always validate in **paper mode for weeks** before going live
- Bot operates **long positions only** (buy). Short is not implemented.
- Treat `TRADING_MODE=live` changes as high risk — explicit confirmation required.
