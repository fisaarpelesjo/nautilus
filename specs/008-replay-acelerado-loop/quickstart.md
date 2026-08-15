# Quickstart: Validando o Replay Acelerado

Fase 1 do `/speckit-plan`. Toda validação usa dados públicos de backtest — nenhum passo exige
credenciais ou `TRADING_MODE=live`.

## US1 — Isolamento e motor de decisão real

1. Antes de rodar: `sha256sum data/state.json data/trades.csv data/signals.csv data/decisions.csv`
   (ou equivalente) para registrar o estado atual desses arquivos (se existirem).
2. `python main.py replay BTC/USDT` — confirmar que roda sem erro e produz uma lista de trades.
3. Depois de rodar: repetir o hash dos 4 arquivos e confirmar que são **idênticos** ao passo 1 —
   nenhum byte alterado (SC-001).
4. Forçar uma exceção durante o replay (ex: par inexistente) e confirmar que os 4 arquivos
   continuam idênticos mesmo no caminho de erro.

## US2 — Comparação contra backtest

1. `python main.py replay BTC/USDT` e confirmar que o relatório final mostra número de trades e
   retorno do replay lado a lado com um backtest do mesmo período, com observações textuais quando
   houver divergência.

## Checklist final

- [ ] `data/state.json`/`data/trades.csv`/`data/signals.csv`/`data/decisions.csv` reais
  permanecem inalterados antes/depois de qualquer execução do replay, inclusive em erro (SC-001).
- [ ] Nenhum passo exigiu credenciais ou `TRADING_MODE=live` (SC-003).
