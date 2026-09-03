---

description: "Task list for H27 meta-labeling precondicao (spec 064)"
---

# Tasks: H27 — meta-labeling, pré-condição sobre o sinal primário

**Input**: Design documents from `/specs/064-h27-meta-labeling/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D3), quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Verificar se o sinal primário carrega informação suficiente (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [P] [US1] Testes em `tests/test_meta_labeling.py`: `_resumo` conta alvo/stop/tempo pelo rótulo bruto, razão infinita sem stop
- [X] T002 [P] [US1] Teste: pré-condição atendida com amostra grande e razão alta
- [X] T003 [P] [US1] Teste: pré-condição NÃO atendida espelhando o achado real medido (razão ~0,50, n~740)
- [X] T004 [P] [US1] Teste: pares sem `preparar` são excluídos; `ValueError` quando nenhum par produz dado; pares passados são respeitados (não o universo default)

### Implementation

- [X] T005 [US1] Criar `backtesting/meta_labeling.py`: `_resumo`, `avaliar_precondicao` (depende de T001-T004)
- [X] T006 [US1] Criar `cmd_meta_labeling()` em `main.py`: roda `avaliar_precondicao()`, imprime baseline/entrada primária/veredito, exporta via `export_report`; registrar `"meta_labeling": cmd_meta_labeling` em `COMMANDS`; sincronizar `CLAUDE.md`/`AGENTS.md` (depende de T005)
- [X] T007 Rodar `python main.py meta_labeling` contra dados reais (já confirmado via diagnóstico ad-hoc, D2)
- [X] T008 Registrar o resultado real de T007 em `docs/research/registro-de-hipoteses.md` §6.1 (H27) — pré-condição não atendida, mesma categoria de H12
- [X] T009 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T006 implementação e testes) + (T007-T009 execução real e registro).

---

## Implementation Strategy

T001-T006 (testes + módulo + comando CLI) → commit → push;
T007-T009 (execução real + registro + suite completa) → commit → push.
