---

description: "Task list for H8 funding rate revisao (spec 058)"
---

# Tasks: H8 — arbitragem de funding rate, revisão com universo amplo e eficiência de capital

**Input**: Design documents from `/specs/058-h8-funding-rate-revisao/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D5), quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Medir o retorno líquido sobre capital implantado por par (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [P] [US1] Testes em `tests/test_funding.py`: `perp_symbol` converte formato, par sem mercado perpétuo devolve DataFrame vazio (`BadSymbol`), histórico normal ordenado sem duplicatas, paginação supera o teto por chamada, cache de exchange
- [X] T002 [P] [US1] Testes em `tests/test_funding_carry.py`: `avaliar_par` calcula bruto/líquido/capital-implantado corretamente, exclui por falta de histórico ou cobertura abaixo do piso, sinaliza `supera_benchmark` corretamente, `avaliar_universo` pula pares sem resultado

### Implementation

- [X] T003 [US1] Criar `data/funding.py`: `perp_symbol`, `fetch_funding_rate_history` (paginado, exchange futures separada, `BadSymbol` → vazio) (depende de T001)
- [X] T004 [US1] Criar `backtesting/funding_carry.py`: `avaliar_par`/`avaliar_universo` com D1-D5 declarados no docstring (depende de T002, T003)
- [X] T005 [US1] Criar `cmd_funding()` em `main.py`: roda sobre `UNIVERSO_AMPLO`, imprime tabela ordenada por capital implantado, exporta via `export_report`; registrar `"funding": cmd_funding` em `COMMANDS`; sincronizar `CLAUDE.md`/`AGENTS.md` (depende de T004)
- [X] T006 Rodar `python main.py funding` contra dados reais (VPS `vps-limulus`/`nautilus-research`)
- [X] T007 Registrar o resultado real de T006 em `docs/research/registro-de-hipoteses.md` §4.9 (H8) — nova "Atualização" após a medição original de 2026-09-01
- [X] T008 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T005 implementação e testes) + (T006-T008 execução real e registro).

---

## Implementation Strategy

T001-T005 (testes + módulos + comando CLI) → commit → push;
T006-T008 (execução real + registro + suite completa) → commit → push.
