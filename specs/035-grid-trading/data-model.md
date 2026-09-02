# Fase 1 — Modelo de dados: H18

## `ParametrosGrade`

| Campo | Tipo | Padrão | Descrição |
|---|---|---|---|
| `n_niveis` | `int` | `10` (D1) | Níveis igualmente espaçados entre `bb_lower` e `bb_upper` |
| `capital_inicial` | `float` | `1000.0` | Mesmo default de `simulate_backtest` |

## `NivelGrade`

Estado de um nível durante a simulação — não persistido, só em memória
durante `simular_grade()`.

| Campo | Descrição |
|---|---|
| `preco_compra` | Preço fixo do nível (boundary), definido na abertura do episódio |
| `preco_venda` | `preco_compra` do próximo nível acima — o alvo de venda |
| `ocupado` | Se há posição aberta neste nível |
| `preco_entrada_ajustado` | Preço de compra já com slippage aplicado (D3), usado para calcular `pnl` na venda |
| `instante_entrada` | Timestamp do candle em que a compra preencheu |

## Episódio de grade

Não é uma classe própria — é o intervalo, dentro de `simular_grade()`,
entre a abertura (regime vira `"sideways"`, `NivelGrade`s recriados a
partir das bandas do candle atual) e o fechamento (liquidação forçada por
`"trending"`, D4, ou fim do histórico).

## `Trade` (reusado, `backtesting/engine.py`, sem campo novo)

| Campo | Preenchido como |
|---|---|
| `entry_price` | `preco_entrada_ajustado` do nível |
| `exit_price` | `preco_venda` (round-trip normal) ou `close` do candle de liquidação forçada, ambos ajustados por slippage |
| `quantity` | `capital_por_nivel / preco_entrada_ajustado` |
| `pnl` / `pnl_pct` | `(exit_price - entry_price) * quantity - fees`, mesma fórmula já usada pelo motor |
| `fees` | `BACKTEST_FEE_RATE` sobre o valor nocional de entrada + saída (D3/D4) |
| `entry_time` / `exit_time` | Timestamps dos candles de preenchimento |
| `exit_reason` | `"grid"` (round-trip normal) ou `"regime mudou para trending"` (liquidação forçada, distinguível — SC-002) |

## `BacktestResult` (reusado, `backtesting/engine.py`, sem campo novo)

Montado por `simular_grade()`:

| Campo | Origem |
|---|---|
| `trades` | Lista de `Trade` acumulada por todos os episódios do par |
| `initial_capital`/`final_capital` | `capital_inicial` / capital final após todos os round-trips |
| `total_return_pct` | `(final - inicial) / inicial * 100` |
| `buy_hold_return_pct` | `(close[-1] - close[0]) / close[0] * 100` — mesmo cálculo já usado pelo motor |
| `max_drawdown_pct` | Pico-a-vale sobre a curva de capital, mesma lógica de `simulate_backtest()` |
| Demais campos (`profit_factor`, `sharpe`, `sortino`, `calmar`, `edge_score`, ...) | `_calculate_advanced_metrics(trades, total_return_pct, buy_hold_return_pct, max_drawdown_pct, period_start, period_end)`, chamada sem modificação (D6) |
| `below_min_price` | Mesmo critério já usado por `run_backtest` — preço abaixo de `MIN_PRICE_USDT` |

## `run_grid_scan(pares=UNIVERSO_H11) -> list[tuple[str, BacktestResult, ApprovalVerdict]]`

Busca candles + indicadores por par (reusa `fetch_ohlcv` +
`EmaRsiStrategy.calculate_indicators`, mesmo padrão de `avaliar_par`/
`run_horizonte_scan`), chama `simular_grade`, aplica `evaluate_approval`
— sem critério novo (FR-006).
