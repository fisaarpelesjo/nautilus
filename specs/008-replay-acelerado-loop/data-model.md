# Data Model: Replay Acelerado do Loop Real

Fase 1 do `/speckit-plan`. Nenhuma persistência nova — tudo transiente, em memória, descartado ao
fim da execução (por design, ver `research.md` isolamento).

## Resultado de replay (`trading/replay.py`, novo, transiente)

| Campo | Tipo | Regras |
|---|---|---|
| `symbol` / `timeframe` | string | Par e timeframe usados. |
| `trades` | List[dict] | Trades produzidos pelo caminho de decisão real (coletados via `log_trade` isolado, nunca escritos em `data/trades.csv`). |
| `total_trades` | int | `len(trades)`. |
| `total_pnl` | float | Soma de `pnl_usdt` dos trades. |
| `blocked_cycles` | int | Ciclos em que uma entrada foi avaliada e bloqueada (para contexto). |

## Relatório de comparação (`trading/replay.py`, novo, transiente)

| Campo | Tipo | Regras |
|---|---|---|
| `replay_trades` / `backtest_trades` | int | Número de trades de cada lado. |
| `replay_return_pct` / `backtest_return_pct` | float | Retorno de cada lado. |
| `notes` | List[str] | Observações textuais fixas sobre divergências conhecidas (cooldown, MTF, etc.). |
