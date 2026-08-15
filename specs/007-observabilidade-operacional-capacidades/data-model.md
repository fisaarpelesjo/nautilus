# Data Model: Observabilidade Operacional

Fase 1 do `/speckit-plan`. Apenas entidades transientes (nenhuma persistência nova) — todos os dados
já existem em `state.json`/CSVs já existentes.

## Snapshot de patrimônio (`trading/portfolio.py`, novo)

| Campo | Tipo | Regras |
|---|---|---|
| `free_cash` | float | Caixa livre — `paper_balance_usdt` (paper) ou saldo real (live). |
| `positions_value` | Optional[float] | Soma do valor das posições ao preço atual. `None` se algum preço não pôde ser buscado. |
| `total_equity` | Optional[float] | `free_cash + positions_value`, ou `None` se `positions_value` for `None`. |
| `realized_pnl` | float | `manager.realized_pnl`, já existente. |
| `unrealized_pnl` | Optional[float] | Soma do PnL não realizado das posições, `None` nas mesmas condições de `positions_value`. |
| `total_pnl` | Optional[float] | `realized_pnl + unrealized_pnl`, ou `None`. |
| `positions_with_unknown_price` | List[str] | Símbolos cujo preço atual não pôde ser buscado — para exibir "indisponível" em vez de omitir silenciosamente. |

## Contexto de simulação (`utils/display.py`, novo, transiente)

| Campo | Tipo | Regras |
|---|---|---|
| `symbol` / `timeframe` | string | Par e timeframe testados. |
| `period_start` / `period_end` | Timestamp | Primeiro/último candle do período testado. |
| `initial_capital` | float | Capital inicial simulado. |

## Painel operacional (`trading/panel.py`, novo, transiente)

Agrega, sem persistir nada novo:
- `PortfolioSnapshot` (acima)
- posições abertas (já em `manager.positions`)
- últimas N linhas de `data/trades.csv` (leitor tolerante novo em `data/trade_store.py`)
- últimas N linhas de `data/signals.csv` (leitor tolerante novo em `data/signal_store.py`)
- `DecisionsAnalysisResult` (já existente, spec 004) para bloqueios recentes

## Diagnóstico completo de sinal (`strategy/diagnostics.py`, extensão)

Estende o dict já retornado por `signal_checks()` com:

| Campo novo | Tipo | Regras |
|---|---|---|
| `mtf_ok` | Optional[bool] | Resultado de `mtf_confirmed()`, `None` se não avaliado. |
| `regime` | string | Valor já calculado nos indicadores (spec 006). |
| `high_volatility` | bool | `atr_ratio > HIGH_VOLATILITY_ATR_RATIO` (spec 006), informativo mesmo com o filtro desligado. |
| `cooldown_active` | bool | `manager.is_in_cooldown(symbol)`, passado pelo chamador. |

## Gráficos de performance (`backtesting/performance_charts.py`, novo, transiente)

Recebe uma lista de `Trade` (já existente, `backtesting/engine.py`) ou linhas equivalentes lidas de
`data/trades.csv`; produz 3 figuras Plotly (curva de capital, drawdown, PnL por par) — nenhuma
entidade de dados nova além do `Trade` já existente.
