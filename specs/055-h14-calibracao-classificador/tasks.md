---

description: "Task list for H14 calibracao do classificador (spec 055)"
---

# Tasks: H14 — calibração do classificador de entrada

**Input**: Design documents from `/specs/055-h14-calibracao-classificador/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D3), quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Medir a razão de chances por corte de confiança (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [P] [US1] Teste em `tests/test_calibracao_h14.py`: `_faixas_por_corte` conta alvo/stop/tempo pelo `rotulo_bruto` corretamente (0 = tempo, não NaN)
- [X] T002 [P] [US1] Teste: corte `0.0` é sentinela e resolve para `limiar_de_decisao` real, não filtra em `prob>0`
- [X] T003 [P] [US1] Teste: `stop=0` produz razão infinita sem quebrar, `supera_empate` fica `False`
- [X] T004 [P] [US1] Teste: amostra grande com razão alta supera `supera_empate_com_confianca` (espelha o achado real medido)
- [X] T005 [P] [US1] Teste: mesma razão com amostra pequena NÃO supera — mesma lição de M9/M13 (ponto estimado sem banda de confiança)
- [X] T006 [P] [US1] Teste: `avaliar_calibracao` sem previsões pooladas devolve faixas vazias
- [X] T007 [P] [US1] Teste: `avaliar_calibracao` repassa `pares`/`params`/`cortes` para `_previsoes_pooladas` e `_faixas_por_corte` sem trocar valores

### Implementation

- [X] T008 [US1] Criar `backtesting/calibracao_h14.py`: `FaixaCalibracao`, `ResultadoCalibracao`, `_previsoes_pooladas` (glue de dados), `_faixas_por_corte` (pura), `avaliar_calibracao` (depende de T001-T007)
- [X] T009 [US1] Criar `cmd_calibracao()` em `main.py`: chama `avaliar_calibracao()`, imprime tabela por corte, exporta via `export_report("calibracao", ...)`; registrar `"calibracao": cmd_calibracao` em `COMMANDS` (depende de T008)
- [X] T010 Rodar `python main.py calibracao` contra dados reais (VPS `vps-limulus`/`nautilus-research`)
- [X] T011 Registrar o resultado real de T010 em `docs/research/registro-de-hipoteses.md` §4.15 (H14) — nova "Atualização" após spec 047, hipótese de filtro de confiança refutada
- [X] T012 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T009 implementação e testes) + (T010-T012 execução real e registro).

---

## Implementation Strategy

T001-T009 (testes + módulo + comando CLI) → commit → push;
T010-T012 (execução real + registro + suite completa) → commit → push.
