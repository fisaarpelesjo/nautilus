---

description: "Task list for H14 saida por barreira + gate de correlacao (spec 057)"
---

# Tasks: H14 — saída por barreira tripla + gate de correlação

**Input**: Design documents from `/specs/057-h14-barreira-correlacao/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D3), quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Medir o efeito combinado (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [P] [US1] Teste em `tests/test_portfolio_h14.py`: `usar_saida_barreira` e `usar_gate_correlacao` juntos não quebram — gate ainda bloqueia candidato correlacionado
- [X] T002 [P] [US1] Teste: stop continua fixo (sem trailing) sob o modo combinado — o gate não interfere na mecânica de saída

### Implementation

- [X] T003 [US1] Criar `cmd_carteira_barreira_corr()` em `main.py`: chama `simular_carteira(usar_saida_barreira=True, usar_gate_correlacao=True)` sobre `UNIVERSO_H11`, imprime resultado ao lado dos três já publicados, exporta via `export_report`; registrar `"carteira_barreira_corr": cmd_carteira_barreira_corr` em `COMMANDS` (depende de T001-T002)
- [ ] T004 Rodar `python main.py carteira_barreira_corr` contra dados reais (VPS `vps-limulus`/`nautilus-research`)
- [ ] T005 Registrar o resultado real de T004 em `docs/research/registro-de-hipoteses.md` §4.15 (H14) — nova "Atualização" após spec 056, confirma aditividade ou dominância
- [ ] T006 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T003 implementação e testes) + (T004-T006 execução real e registro).

---

## Implementation Strategy

T001-T003 (testes + comando CLI) → commit → push;
T004-T006 (execução real + registro + suite completa) → commit → push.
