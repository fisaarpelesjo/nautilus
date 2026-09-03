---

description: "Task list for limite de drawdown diario na carteira de H14 (spec 045)"
---

# Tasks: Limite de drawdown diário na carteira de H14

**Input**: Design documents from `/specs/045-limite-drawdown-diario-h14/`

**Prerequisites**: plan.md, spec.md, research.md (D1), data-model.md, quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.
`tests/test_portfolio_h14.py` (extensão).

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Medir a carteira com o limite de drawdown diário isolado (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [US1] Teste em `tests/test_portfolio_h14.py`: cenário sintético com perda intradiária que ultrapassa `DAILY_DRAWDOWN_LIMIT` — com `usar_limite_drawdown_diario=True` a entrada NÃO abre pelo resto do dia de calendário
- [X] T002 [P] [US1] Teste em `tests/test_portfolio_h14.py`: mesmo cenário, no primeiro candle do dia seguinte o saldo de referência reseta e a entrada abre normalmente — MESMO sem nenhum trade lucrativo ter fechado (distingue do circuit breaker, spec 044)
- [X] T003 [P] [US1] Teste de regressão em `tests/test_portfolio_h14.py`: `usar_limite_drawdown_diario=False` (default) produz resultado idêntico ao já publicado

### Implementation

- [X] T004 [US1] Adicionar `dia_referencia`/`saldo_referencia_diario` e parâmetro `usar_limite_drawdown_diario: bool = False` em `_simular_carteira_core`/`simular_carteira` (`backtesting/portfolio_h14.py`), ordem de aplicação conforme `data-model.md` (depende de T001-T003)
- [X] T005 [US1] Criar `cmd_carteira_dd_diario()` em `main.py`: chama `simular_carteira(pares=UNIVERSO_H11, usar_limite_drawdown_diario=True)`, imprime a curva de capital agregada, o veredito de `evaluate_approval()`, e os cinco resultados já publicados (drawdown e total_trades) lado a lado; registrar `"carteira_dd_diario": cmd_carteira_dd_diario` em `COMMANDS`; exportar via `export_report("carteira_dd_diario", ...)` (depende de T004)
- [X] T006 Rodar `python main.py carteira_dd_diario` contra dados reais (12 pares, VPS `vps-limulus`/`nautilus-research`) — resultado real
- [X] T007 Registrar o resultado real de T006 em `docs/research/registro-de-hipoteses.md` §4.15 (H14) — comparação explícita contra os cinco já publicados, incluindo se `total_trades` colapsou como no circuit breaker ou não; texto depende do resultado medido, não escrito antes de T006
- [X] T008 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T005 implementação e testes) + (T006-T008 execução real e registro).

---

## Implementation Strategy

T001-T005 (testes + mecânica + CLI) → commit → push;
T006-T008 (execução real + registro + suite completa) → commit → push.
