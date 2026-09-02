# Fase 1 — Modelo de dados: H21 (lead-lag BTC → altcoins)

## `btc_retorno_no_candle(btc_close: pd.Series) -> pd.Series`

Retorno de fechamento-a-fechamento do BTC no mesmo candle (D1):
`btc_close.pct_change(1)`, sem deslocamento — índice idêntico ao de
`btc_close`.

## `_sinais_lead_lag(retorno_btc: pd.Series, indice_par: pd.DatetimeIndex) -> pd.Series`

| Passo | Descrição |
|---|---|
| Alinhamento | `retorno_btc.reindex(indice_par)` — candle da altcoin sem retorno de BTC correspondente vira `NaN` (FR-008) |
| Sinal | `Signal.BUY` onde o valor alinhado é `> 0`; `Signal.HOLD` no resto (inclui `NaN`, `0`, negativo — D2) |

Saída: `pd.Series` de `Signal`, mesmo índice de `indice_par` — formato
exigido por `precomputed_signals` em `simulate_backtest`.

## `avaliar_lead_lag(par: str, df_alt=None, retorno_btc=None) -> Optional[BacktestResult]`

| Passo | Origem |
|---|---|
| `df_alt` | `fetch_ohlcv(par, TIMEFRAME, 6000)` se não fornecido (FR-005) |
| `retorno_btc` | `btc_retorno_no_candle(fetch_ohlcv("BTC/USDT", TIMEFRAME, 6000)["close"])` se não fornecido |
| `prep` | `preparar(df_alt, EmaRsiStrategy())` — indicadores, inclusive ATR (necessário para take-profit/stop trailing, D4) |
| `sinais` | `_sinais_lead_lag(retorno_btc, prep.index)` |
| `BacktestResult` | `_simular_com_sinais(prep, EmaRsiStrategy(), sinais)` (D4, reusa `backtesting.modelo`) |

`df_alt`/`retorno_btc` como parâmetros opcionais (não default `None`
implícito) permitem teste sem rede — mesmo padrão de `avaliar_par(df=...)`
(H14).

## `run_lead_lag_scan(pares=None) -> List[Tuple[str, Optional[BacktestResult], ApprovalVerdict]]`

Busca `BTC/USDT` UMA vez (reusado entre os 11 pares — evita 11 fetches
redundantes do mesmo par-sinal), itera `UNIVERSO_H11` menos `"BTC/USDT"`
(D3, ou `pares` explícito para testes), chama `avaliar_lead_lag`, aplica
`evaluate_approval` — sem critério novo (FR-006).

## `Trade`/`BacktestResult` (reusados, `backtesting/engine.py`, sem campo novo)

Preenchidos inteiramente por `_simular_com_sinais`/`simulate_backtest` —
nenhum campo novo, nenhuma lógica de trade duplicada (D4).

## `cmd_leadlag()` (CLI, `main.py`)

Chama `run_lead_lag_scan()`, imprime tabela por par (trades, retorno,
buy-hold, drawdown, profit factor, veredito) — mesmo padrão de
`cmd_grid`/`cmd_carteira` — e o resumo de consistência (US2: quantos dos
11 pares superam o buy-hold, quantos têm profit factor > 1,0). Reusa
`export_report("leadlag", ...)`.
