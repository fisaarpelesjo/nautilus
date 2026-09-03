---

description: "Task list for H29 pairs trading via copula (spec 066)"
---

# Tasks: H29 — pairs trading via cópula gaussiana

**Input**: Design documents from `/specs/066-h29-pairs-copula/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D5), quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Medir o resultado do sinal de cópula sobre os pares de H10 (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [P] [US1] Testes em `tests/test_pairs_copula.py`: forma fechada de `h_condicional` (independência devolve u1, ponto de equilíbrio devolve 0,5)
- [X] T002 [P] [US1] Teste: `ajustar_copula_gaussiana` recupera correlação forte construída e fica perto de zero com séries independentes
- [X] T003 [P] [US1] Teste: `run_pairs_copula_backtest` opera par cointegrado sintético sem exceção
- [X] T004 [P] [US1] Teste: histórico menor que a formação não estoura; menos de dois símbolos devolve resultado vazio
- [X] T005 [P] [US1] Teste: `run_pairs_copula_scan` aceita `dados=` sem rede

### Implementation

- [X] T006 [US1] Verificar precondição de cointegração com dado real (D1, `research.md`) antes de escrever qualquer código de cópula (depende de nada — é o primeiro passo)
- [X] T007 [US1] Criar `backtesting/pairs_copula.py`: `ajustar_copula_gaussiana`, `h_condicional`, `run_pairs_copula_backtest`, `run_pairs_copula_scan` — reusa `selecionar_pares`/`PairsParams`/`split_treino_validacao` de H10 sem alteração (depende de T001-T005, T006)
- [X] T008 [US1] Adicionar `scipy` a `requirements-dev.txt` (pesquisa apenas, mesmo padrão de `statsmodels`)
- [X] T009 [US1] Criar `cmd_pairs_copula()` em `main.py`: roda sobre `UNIVERSO_AMPLO_HISTORICO_COMPLETO`, imprime treino/validação ao lado do já publicado de H10, exporta via `export_report`; registrar `"pairs_copula": cmd_pairs_copula` em `COMMANDS` (depende de T007)
- [ ] T010 Rodar `python main.py pairs_copula` contra dados reais
- [ ] T011 Registrar o resultado real de T010 em `docs/research/registro-de-hipoteses.md` §6.1 (H29) — comparação explícita com o número já publicado de H10
- [ ] T012 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T009 implementação e testes) + (T010-T012 execução real e registro).

---

## Implementation Strategy

T001-T009 (precondição + testes + módulo + comando CLI) → commit → push;
T010-T012 (execução real + registro + suite completa) → commit → push.
