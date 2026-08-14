# Quickstart: Validando a Otimização Sem Overfitting

Fase 1 do `/speckit-plan`. Roteiro para validar manualmente cada User Story — todo comando usa só
dados públicos da Binance, sem exigir `.env`/API key.

Pré-requisitos: ambiente Python configurado (`.venv`), dependências instaladas.

## US1 — Split treino/validação no otimizador

1. Rodar `pytest tests/test_optimizer.py -v` e confirmar que os testes de split/validação passam.
2. Rodar `python main.py optimize --validate` e confirmar que a tabela mostra métricas de treino e
   validação lado a lado para cada candidato, e que algum candidato eventualmente mostra divergência
   visível entre as duas (sinal de que a comparação está realmente sendo calculada, não copiada).
3. Rodar `python main.py optimize` (sem flag) e confirmar que a saída é idêntica à de antes desta
   spec (FR-009).

## US2 — Validação walk-forward

1. Rodar `pytest tests/test_robustness.py -v` (funções de walk-forward) e confirmar que passam,
   incluindo o caso de histórico insuficiente para `min_windows`.
2. Rodar `python main.py optimize --walk-forward` sobre os pares default (`OPTIMIZE_PAIRS`, histórico
   longo o suficiente) e confirmar que a seção "VALIDAÇÃO WALK-FORWARD" mostra pelo menos 3 janelas e
   um resumo com média e pior janela.

## US3 — Análise Monte Carlo

1. Rodar `pytest tests/test_robustness.py -v` (funções de Monte Carlo) e confirmar que passam,
   incluindo o caso de amostra pequena (aviso de confiança baixa) e o de reprodutibilidade com seed
   fixo.
2. Rodar `python main.py backtest --montecarlo` sobre `PAIRS[0]`/`TIMEFRAME` e confirmar que a seção
   "ANÁLISE MONTE CARLO" mostra drawdown mediana/p95 e maior sequência de perdas esperada, com aviso
   de confiança baixa se o número de trades do backtest for menor que `EDGE_MIN_TRADES`.

## Checklist final antes de qualquer go-live

Esta spec não altera `risk/`, `execution/` nem `trading/position_lifecycle.py` — é só relatório de
otimização/backtest. Não há checklist de go-live novo; o checklist já existente em
`specs/001-hardening-incremental/tasks.md` (T037) continua sendo o de referência para
`TRADING_MODE=live`.
