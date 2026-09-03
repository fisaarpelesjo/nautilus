---

description: "Task list for H20 custo de execucao isolado (spec 050)"
---

# Tasks: H20 — isolando o efeito do custo de execução

**Input**: Design documents from `/specs/050-h20-custo-de-execucao/`

**Prerequisites**: plan.md, spec.md, quickstart.md (sem research.md/data-model.md — extensão trivial)

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Comparar retorno com e sem custo, por par (Priority: P1) 🎯 MVP

### Tests

- [ ] T001 [US1] Teste em `tests/test_modelo.py` (ou novo `tests/test_geometria.py`): função de fração consumida `(sem_custo - com_custo) / sem_custo` produz o mesmo resultado do exemplo já publicado de H10 (+3,96% com custo, +5,56% sem custo → 29% consumido)

### Implementation

- [ ] T002 [US1] Estender `cmd_geometria()` em `main.py`: para cada `a` em `avaliacoes`, imprime `total_return_pct` (com custo) e `retorno_sem_custo_modelo` (sem custo) lado a lado, com a fração consumida quando aplicável; agrega quantos pares teriam PF/retorno diferentes sem custo; adiciona ao `export_report` (depende de T001)
- [ ] T003 Rodar `python main.py geometria` contra dados reais (12 pares, VPS `vps-limulus`/`nautilus-research`) — resultado real
- [ ] T004 Registrar o resultado real de T003 em `docs/research/registro-de-hipoteses.md` §4.16 (H20) — se o custo explica toda, parte ou nenhuma fração observável da divergência de spec 049; texto depende do resultado medido, não escrito antes de T003
- [ ] T005 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T002 implementação e testes) + (T003-T005 execução real e registro).

---

## Implementation Strategy

T001-T002 (teste + extensão CLI) → commit → push;
T003-T005 (execução real + registro + suite completa) → commit → push.
