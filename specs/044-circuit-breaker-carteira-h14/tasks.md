---

description: "Task list for circuit breaker de perdas consecutivas na carteira de H14 (spec 044)"
---

# Tasks: Circuit breaker de perdas consecutivas na carteira de H14

**Input**: Design documents from `/specs/044-circuit-breaker-carteira-h14/`

**Prerequisites**: plan.md, spec.md, research.md (D1), data-model.md, quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.
`tests/test_portfolio_h14.py` (extensão).

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Medir a carteira com o circuit breaker isolado (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [US1] Teste em `tests/test_portfolio_h14.py`: cenário sintético com `MAX_CONSECUTIVE_LOSSES` trades perdedores consecutivos seguidos de um candidato elegível — com `usar_circuit_breaker=True` a entrada NÃO abre enquanto o contador está no limite
- [X] T002 [P] [US1] Teste em `tests/test_portfolio_h14.py`: mesmo cenário, após um trade fechado com `pnl > 0` o contador reseta e a próxima entrada elegível abre normalmente
- [X] T003 [P] [US1] Teste de regressão em `tests/test_portfolio_h14.py`: `usar_circuit_breaker=False` (default) produz resultado idêntico ao já publicado — nenhuma mudança no caminho default

### Implementation

- [X] T004 [US1] Adicionar contador `perdas_consecutivas` e parâmetro `usar_circuit_breaker: bool = False` em `_simular_carteira_core`/`simular_carteira` (`backtesting/portfolio_h14.py`), ordem de aplicação conforme `data-model.md` (depende de T001-T003)
- [X] T005 [US1] Criar `cmd_carteira_breaker()` em `main.py`: chama `simular_carteira(pares=UNIVERSO_H11, usar_circuit_breaker=True)`, imprime a curva de capital agregada, o veredito de `evaluate_approval()`, e os quatro drawdowns já publicados (28,66%/23,04%/20,74%/20,24%) lado a lado; registrar `"carteira_breaker": cmd_carteira_breaker` em `COMMANDS`; exportar via `export_report("carteira_breaker", ...)` (depende de T004)
- [X] T006 Rodar `python main.py carteira_breaker` contra dados reais (12 pares, VPS `vps-limulus`/`nautilus-research`) — resultado real
- [X] T007 Registrar o resultado real de T006 em `docs/research/registro-de-hipoteses.md` §4.15 (H14) — comparação explícita contra os quatro já publicados; texto depende do resultado medido, não escrito antes de T006
- [X] T008 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T005 implementação e testes) + (T006-T008 execução real e registro).

---

## Implementation Strategy

T001-T005 (testes + mecânica + CLI) → commit → push;
T006-T008 (execução real + registro + suite completa) → commit → push.
