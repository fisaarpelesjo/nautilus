---

description: "Task list for H23 futuros trimestrais vs funding perpetuo (spec 059)"
---

# Tasks: H23 — prêmio de futuros trimestrais (contango) vs. funding perpétuo

**Input**: Design documents from `/specs/059-h23-futuros-trimestrais/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D4), quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Medir o prêmio líquido sobre capital implantado por contrato (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [P] [US1] Testes em `tests/test_futures_basis.py`: listagem filtra por base/quote/tipo (exclui perpétuo, exclui coin-margined), ordena por vencimento, cálculo de dias até o vencimento
- [X] T002 [P] [US1] Testes em `tests/test_basis_carry.py`: `avaliar_contrato` calcula bruto/líquido/capital-implantado corretamente, `supera_benchmark` correto, backwardation (prêmio negativo) não quebra, `avaliar_universo` avalia cada contrato listado

### Implementation

- [X] T003 [US1] Criar `data/futures_basis.py`: `listar_contratos_trimestrais`, `fetch_basis_snapshot` (depende de T001)
- [X] T004 [US1] Criar `backtesting/basis_carry.py`: `avaliar_contrato`/`avaliar_universo`, reusa constantes de `funding_carry.py` (depende de T002, T003)
- [X] T005 [US1] Criar `cmd_basis()` em `main.py`: roda sobre BTC/ETH, imprime tabela ordenada por capital implantado, exporta via `export_report`; registrar `"basis": cmd_basis` em `COMMANDS`; sincronizar `CLAUDE.md`/`AGENTS.md` (depende de T004)
- [X] T006 Rodar `python main.py basis` contra dados reais (smoke test local já confirmou os 4 contratos)
- [X] T007 Registrar o resultado real de T006 em `docs/research/registro-de-hipoteses.md` §4.9 (H8) — nova "Atualização" para H23
- [X] T008 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T005 implementação e testes) + (T006-T008 execução real e registro).

---

## Implementation Strategy

T001-T005 (testes + módulos + comando CLI) → commit → push;
T006-T008 (execução real + registro + suite completa) → commit → push.
