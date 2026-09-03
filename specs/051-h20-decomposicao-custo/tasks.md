---

description: "Task list for H20 decomposicao de custo -- taxa vs slippage (spec 051)"
---

# Tasks: H20 — decompondo o custo de execução

**Input**: Design documents from `/specs/051-h20-decomposicao-custo/`

**Prerequisites**: plan.md, spec.md, quickstart.md (sem research.md/data-model.md — extensão simétrica trivial)

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Decompor o custo em taxa e slippage, por par (Priority: P1) 🎯 MVP

### Tests

- [ ] T001 [US1] Teste em `tests/test_modelo.py`: `avaliar_par` popula `retorno_sem_slippage_modelo` (spy confirma `slippage_pct=0.0`, `fee_rate` real) e `retorno_sem_taxa_modelo` (spy confirma `fee_rate=0.0`, `slippage_pct` real) — reusa o fixture de spec 049 (n=2000, semente=7)
- [ ] T002 [P] [US1] Confirmar que `retorno_sem_custo_modelo` (já existente) permanece inalterado — regressão explícita (FR-002)

### Implementation

- [ ] T003 [US1] Adicionar `retorno_sem_slippage_modelo`/`retorno_sem_taxa_modelo` (`Optional[float] = None`) a `AvaliacaoH14` e as duas chamadas correspondentes no bloco E6 de `avaliar_par` (`backtesting/modelo.py`) (depende de T001-T002)
- [ ] T004 [US1] Estender `cmd_geometria()` em `main.py`: imprime os dois novos campos ao lado do já existente (com custo / sem custo) por par; adiciona ao `export_report` (depende de T003)
- [ ] T005 Rodar `python main.py geometria` contra dados reais (12 pares, VPS `vps-limulus`/`nautilus-research`) — resultado real
- [ ] T006 Registrar o resultado real de T005 em `docs/research/registro-de-hipoteses.md` §4.16 (H20) — qual componente (taxa ou slippage) domina, com a ressalva sobre o teto otimista; texto depende do resultado medido, não escrito antes de T005
- [ ] T007 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T004 implementação e testes) + (T005-T007 execução real e registro).

---

## Implementation Strategy

T001-T004 (testes + campos + extensão CLI) → commit → push;
T005-T007 (execução real + registro + suite completa) → commit → push.
