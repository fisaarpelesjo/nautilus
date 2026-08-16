# Quickstart: Validando os Itens Remanescentes

Fase 1 do `/speckit-plan`. Toda validação usa dados públicos de backtest ou fixtures sintéticas.

## US1 — Exportação de relatórios

1. `python main.py backtest` e confirmar que `reports/backtest_<timestamp>.{json,csv,md}` aparecem
   com parâmetros, período, custos e métricas.
2. Rodar de novo e confirmar que um segundo conjunto de arquivos aparece, sem sobrescrever o
   primeiro.

## US2 — Diagnóstico agressivo

1. Teste unitário com `BacktestResult` sintético de drawdown alto e retorno bem acima do
   buy-and-hold — confirmar `"agressivo"` no diagnóstico.

## US3 — Out-of-sample no edge

1. `python main.py edge --validate` num par com histórico suficiente e confirmar que mostra
   treino e validação lado a lado, com veredito sobre a validação.
2. `python main.py edge` (sem a flag) e confirmar que o comportamento é idêntico ao já existente.

## US4 — Indicadores médios por decisão

1. `python main.py decisions` com fixture sintética contendo RSI variando por sinal, confirmando
   que a média por sinal aparece corretamente.

## Checklist final

- [ ] Suíte de testes completa passa.
- [ ] Nenhum passo exigiu histórico real de operação paper.
