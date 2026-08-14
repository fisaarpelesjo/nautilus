# Data Model: Métricas de Risco Avançadas

Fase 1 do `/speckit-plan`. US1/US2 estendem uma entidade já existente (`BacktestResult`), transiente
como sempre. US3 introduz uma entidade nova, também transiente (lida sob demanda de
`data/decisions.csv`, nunca persistida separadamente).

## Métricas de risco ajustado (extensão de `BacktestResult`, `backtesting/engine.py`)

Campos novos — os campos já existentes (`sharpe`, `max_drawdown_pct`, `exposure_pct`, etc.) continuam
inalterados.

| Campo | Tipo | Regras |
|---|---|---|
| `sortino` | float | Retorno médio dos trades sobre o desvio padrão só dos retornos negativos. `inf` quando não há desvio calculável (menos de 2 trades com prejuízo) e a média é positiva; `0.0` caso contrário. |
| `calmar` | float | `annualized_return_pct / max_drawdown_pct`. `inf` quando `max_drawdown_pct == 0` e `annualized_return_pct > 0`; `0.0` caso contrário. |
| `annualized_return_pct` | float | Retorno total anualizado (juros compostos, base 365 dias). `0.0` quando o período testado for menor que 1 dia. |
| `return_per_exposure_pct` | `Optional[float]` | `total_return_pct / (exposure_pct / 100)`. `None` (não `0.0`/`inf`) quando `exposure_pct == 0` — ausência de dado, não um resultado de zero. |

## Resumo de decisões (novo, transiente — `data/decisions_analysis.py`)

| Campo | Tipo | Regras |
|---|---|---|
| `total_cycles` | inteiro | Número de linhas lidas de `decisions.csv` (após filtro de símbolo/período, se aplicado). |
| `signal_counts` | dict(string → inteiro) | Contagem de ciclos por `signal` (`BUY`/`SELL`/`HOLD`). |
| `blocked_entries` | inteiro | Ciclos onde um sinal de compra existia mas a entrada foi bloqueada (`entry_opened=False` com `signal=BUY`, ou equivalente). |
| `blocker_counts` | lista ordenada de (string, inteiro) | Bloqueios (`blockers`) mais frequentes, ranqueados por contagem desc. |
| `status` | enum(`ok`, `sem_dados`) | `sem_dados` quando `decisions.csv` não existe ou está vazio — `signal_counts`/`blocker_counts` ficam vazios nesse caso, sem erro. |

Linhas com colunas ausentes (schema antigo, ver `research.md`) contam para `total_cycles` mas suas
colunas ausentes não contribuem para as contagens que dependem delas (ex: uma linha sem `blockers`
não aparece em `blocker_counts`, mas conta em `total_cycles`/`signal_counts` se `signal` estiver
presente).
