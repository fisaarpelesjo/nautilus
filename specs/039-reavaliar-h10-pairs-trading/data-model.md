# Fase 1 — Modelo de dados: reavaliar H10

## `run_pairs_scan(pares=UNIVERSO_H11, params=None) -> Tuple[BacktestResult, BacktestResult, ApprovalVerdict]`

| Passo | Descrição |
|---|---|
| Busca | `fetch_ohlcv(par, TIMEFRAME, 6000)` para cada par (FR-002) |
| Corte | `split_idx = int(n * 0.7)` sobre o índice comum (interseção de timestamps entre os 12 pares) — mesmo corte para todos (FR-003) |
| `dados_treino[par]` | `df.iloc[:split_idx]` |
| `dados_validacao[par]` | `df.iloc[split_idx - formacao : ]` — inclui aquecimento (D2/FR-004) |
| `resultado_treino` | `run_pairs_backtest(dados_treino, PairsParams(formacao=500, reselecionar_a_cada=500))` — já existente, sem alteração |
| `resultado_validacao` | `run_pairs_backtest(dados_validacao, mesmos params)` — `period_start` interno alinha exatamente ao início real da validação (D2) |
| `veredito` | `evaluate_approval(resultado_validacao)` — sem critério novo (FR-005) |

Devolve os três — treino é reportado ao lado da validação para
comparação (mesmo padrão de `backtest --validate`), mas o veredito usa
só a validação (nunca a janela de treino, mesma regra já documentada em
`evaluate_approval`).

## `PairsParams`/`ParCointegrado`/`run_pairs_backtest` (reusados, `backtesting/pairs_trading.py`, sem alteração)

Nenhum campo novo — `run_pairs_scan` só decide QUANDO chamar
`run_pairs_backtest` (duas vezes, treino e validação) e COM QUE fatia de
`dados`.

## `cmd_pairs()` (CLI, `main.py`)

Chama `run_pairs_scan()`, imprime treino e validação lado a lado (trades,
retorno, buy-hold, drawdown, profit factor) e o veredito de
`evaluate_approval()` sobre a validação — mesmo padrão visual de
`cmd_grid`/`cmd_carteira`/`cmd_leadlag`. Reusa `export_report("pairs", ...)`.
