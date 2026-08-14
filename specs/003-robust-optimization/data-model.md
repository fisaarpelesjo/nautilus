# Data Model: Otimização Sem Overfitting

Fase 1 do `/speckit-plan`. Todas as entidades abaixo são transientes — existem só durante a execução
de `optimize`/`backtest`, nunca persistidas em disco. Nenhum `state.json`/CSV novo.

## Resultado de otimização com validação (extensão de `MultiOptResult`, `backtesting/optimizer.py`)

Campos novos adicionados à dataclass já existente — os campos atuais (`avg_score`, `avg_return`,
`avg_winrate`, `avg_drawdown`, `total_trades`, `per_pair`) continuam existindo, inalterados, e passam
a refletir só a fatia de treino quando `--validate` está ativo (antes, refletiam o histórico inteiro).

| Campo | Tipo | Regras |
|---|---|---|
| `validation_avg_return` | float ou `None` | Retorno médio do mesmo conjunto de parâmetros na fatia de validação, entre os símbolos onde a validação foi possível. `None` quando `--validate` não foi usado. |
| `validation_avg_drawdown` | float ou `None` | Idem, drawdown médio de validação. |
| `validation_total_trades` | int | Soma de trades na fatia de validação, entre os símbolos válidos. |
| `validation_symbols_skipped` | lista de string | Símbolos onde a validação não foi possível (histórico insuficiente) — não contam nas médias acima. |

## Janela walk-forward (nova, transiente)

| Campo | Tipo | Regras |
|---|---|---|
| `window_index` | inteiro ≥ 0 | Posição da janela na sequência temporal (0 = mais antiga). |
| `period_start` / `period_end` | timestamp | Intervalo coberto pela janela. |
| `result` | `BacktestResult` (já existente) | Métricas do conjunto de parâmetros avaliado nessa janela. |

## Resultado walk-forward agregado (novo, transiente)

| Campo | Tipo | Regras |
|---|---|---|
| `windows` | lista de Janela walk-forward | Sempre ≥ `min_windows` quando `status="ok"`. |
| `status` | enum(`ok`, `dados_insuficientes`) | `dados_insuficientes` quando o histórico não cobre `min_windows` janelas de tamanho mínimo — nesse caso `windows` fica vazia. |
| `avg_return_pct` | float | Média de `total_return_pct` entre as janelas. |
| `worst_window` | Janela walk-forward | Janela com pior `total_return_pct` — nunca escondida atrás da média (FR-005). |

## Estimativa de risco por reamostragem (nova, transiente — `backtesting/robustness.py`)

| Campo | Tipo | Regras |
|---|---|---|
| `n_simulations` | inteiro | Número de reamostragens bootstrap rodadas (default 1000). |
| `max_drawdown_median_pct` | float | Mediana do drawdown máximo entre as simulações. |
| `max_drawdown_p95_pct` | float | Percentil 95 do drawdown máximo — pior 5% dos cenários simulados. |
| `worst_losing_streak_median` | int | Mediana da maior sequência de perdas entre as simulações. |
| `low_confidence` | booleano | `true` quando o número de trades de entrada é menor que `EDGE_MIN_TRADES` (`config/settings.py`, spec 002). |
| `sample_size` | inteiro | Número de trades usado como base para a reamostragem (não `n_simulations`). |
