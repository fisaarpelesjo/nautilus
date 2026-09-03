---

description: "Task list for H26 reversao contra funding extremo (spec 063)"
---

# Tasks: H26 — reversão contra funding extremo (crowding/liquidação)

**Input**: Design documents from `/specs/063-h26-reversao-funding-extremo/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D5), quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Medir se funding extremo prevê reversão suficiente para pagar a barreira (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [P] [US1] Teste em `tests/test_funding_reversao.py`: limiar de extremo calibrado exclusivamente sobre a fatia de treino (não muda se a validação mudar)
- [X] T002 [P] [US1] Teste: alinhamento funding→candle é forward-fill causal (candle nunca herda leitura futura)
- [X] T003 [P] [US1] Teste: eventos extremos são rotulados corretamente pela barreira tripla existente
- [X] T004 [P] [US1] Teste: `agregar_pooled` soma alvo/stop entre pares e delega a `supera_empate_com_confianca` sem reimplementar Wilson CI
- [X] T005 [P] [US1] Teste: par sem mercado perpétuo é excluído do universo, nunca contado como zero
- [X] T006 [P] [US1] Teste: sem eventos extremos na validação, razão fica `inf`/indefinida sem quebrar

### Implementation

- [X] T007 [US1] Criar `backtesting/funding_reversao.py`: `avaliar_par`, `avaliar_universo`, `agregar_pooled` (depende de T001-T006)
- [X] T008 [US1] Criar `cmd_funding_extremo()` em `main.py`: roda sobre `UNIVERSO_H11`, imprime resultado pooled, exporta via `export_report`; registrar `"funding_extremo": cmd_funding_extremo` em `COMMANDS` (depende de T007)
- [X] T009 Rodar `python main.py funding_extremo` contra dados reais
- [X] T010 Registrar o resultado real de T009 em `docs/research/registro-de-hipoteses.md` §6.3 (H26) — atualizar a entrada existente com o resultado medido
- [X] T011 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T008 implementação e testes) + (T009-T011 execução real e registro).

---

## Implementation Strategy

T001-T008 (testes + módulo + comando CLI) → commit → push;
T009-T011 (execução real + registro + suite completa) → commit → push.
