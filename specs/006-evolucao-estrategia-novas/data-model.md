# Data Model: Evolução da Estratégia

Fase 1 do `/speckit-plan`. Extensões de indicadores calculados (não persistidos além do já existente
`data/decisions.csv`) e uma nova entidade de estratégia.

## Indicadores novos (extensão de `strategy/ema_rsi.py` `calculate_indicators()`)

| Campo | Tipo | Regras |
|---|---|---|
| `adx` | float | ADX(14), via `ta.trend.ADXIndicator`. `NaN` quando não calculável (poucos candles). |
| `regime` | string | Derivado de `adx` vs `REGIME_ADX_THRESHOLD`: `"trending"` / `"sideways"` / `"indefinido"` (NaN → tratado como bloqueio conservador). |
| `atr_ratio` | float | `atr / close`, derivado do `atr` já existente. |

## `data/decisions.csv` (extensão)

Nova coluna `regime` (mesmo formato de coluna já existente, ex: `blockers`) — valor do regime de
mercado do candle avaliado naquele ciclo. Sem mudança de schema além da coluna adicional (mesma
decisão de design já validada na spec 005 para `blockers`).

## Estratégia de rompimento (`strategy/breakout.py`, nova)

| Campo | Tipo | Regras |
|---|---|---|
| `window` | int | Janela de rompimento (períodos), parametrizável no `__init__` — testável em 50/150/200. |
| `breakout_high` | float (coluna do df) | Máxima das últimas `window` velas, deslocada 1 candle (`shift(1)`) para excluir o candle atual. |
| `breakout_low` | float (coluna do df) | Mínima das últimas `window` velas, mesma regra de `shift(1)`. |
| `atr` | float (coluna do df) | ATR(14), mesmo indicador já usado por `EmaRsiStrategy`, para compatibilidade com `risk/manager.py` e trailing stop. |

## Relatório de comparação (`backtesting/compare.py`, novo, transiente)

Reusa `MultiResult`-like row (mesmos campos de `backtesting/multi.py`: `trades`, `win_rate`,
`retorno_pct`, `drawdown_pct`, `edge_score`, `verdict`) com um campo adicional:

| Campo | Tipo | Regras |
|---|---|---|
| `strategy_name` | string | Identificador legível da estratégia/preset comparado (ex: `"EMA/RSI padrao"`, `"Breakout 150"`). |
