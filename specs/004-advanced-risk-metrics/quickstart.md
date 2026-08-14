# Quickstart: Validando as Métricas de Risco Avançadas

Fase 1 do `/speckit-plan`. Roteiro para validar manualmente cada User Story.

Pré-requisitos: ambiente Python configurado (`.venv`), dependências instaladas.

## US1 — Sortino e Calmar Ratio

1. Rodar `pytest tests/test_backtesting_engine.py -v` (testes de Sortino/Calmar) e confirmar que
   passam, incluindo os casos de denominador zero (sem perdas, sem drawdown).
2. Rodar `python main.py backtest` (dados públicos da Binance, sem `.env`) e confirmar que o relatório
   mostra "Sortino" e "Calmar" ao lado do "Sharpe simplif." já existente.

## US2 — Retorno anualizado e por tempo exposto

1. Rodar `pytest tests/test_backtesting_engine.py -v` (testes de anualização/exposição) e confirmar
   que passam, incluindo o caso de exposição zero (`return_per_exposure_pct is None`, exibido "n/a").
2. Rodar `python main.py backtest` novamente e confirmar que o relatório mostra retorno anualizado e
   retorno por tempo exposto, coerentes com o período testado e a exposição já exibida.

## US3 — Análise de `data/decisions.csv`

1. Rodar `pytest tests/test_decisions_analysis.py -v` (fixtures CSV sintéticas — este ambiente não tem
   um `decisions.csv` real, ver `spec.md` → Assumptions) e confirmar que passam, incluindo os casos de
   arquivo ausente/vazio e linhas com schema antigo.
2. Rodar `python main.py decisions` neste ambiente e confirmar que informa claramente que não há dados
   (arquivo não existe). Se o operador já tiver rodado o bot e tiver um `data/decisions.csv` real,
   rodar novamente com esse arquivo e confirmar que os bloqueios mais frequentes fazem sentido.

## Checklist final antes de qualquer go-live

Esta spec não altera `risk/`, `execution/` nem `trading/position_lifecycle.py` — é só relatório/
análise. Não há checklist de go-live novo; o checklist já existente em
`specs/001-hardening-incremental/tasks.md` (T037) continua sendo o de referência para
`TRADING_MODE=live`.
