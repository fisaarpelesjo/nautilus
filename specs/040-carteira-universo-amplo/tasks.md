---

description: "Task list for carteira de H14 sobre universo amplo (spec 040)"
---

# Tasks: Carteira de H14 sobre universo amplo

**Input**: Design documents from `/specs/040-carteira-universo-amplo/`

**Prerequisites**: plan.md, spec.md, data-model.md, research.md, quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.
`tests/test_portfolio_h14.py` (extensão pequena).

**Organization**: uma única user story (P1) — a mudança é uma constante
nova consumida pela mecânica já existente de spec 037, não há segunda
prioridade a decompor.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

Nenhuma — sem dependência nova.

---

## Phase 2: User Story 1 - Medir drawdown de carteira sobre o universo amplo (Priority: P1) 🎯 MVP

**Goal**: `simular_carteira(pares=UNIVERSO_AMPLO)` produz um
`BacktestResult` de carteira sobre 34 pares, mesma mecânica de spec 037
(`MAX_POSITIONS` fixo, D2).

**Independent Test**: confirmar que `UNIVERSO_AMPLO` tem exatamente 34
símbolos únicos, todos `/USDT`, e nenhum dos 5 pegged excluídos (D1).

### Tests for User Story 1

- [X] T001 [P] [US1] Teste em `tests/test_portfolio_h14.py`: `UNIVERSO_AMPLO` tem 34 símbolos únicos, todos terminam em `/USDT` (FR-001)
- [X] T002 [P] [US1] Teste: nenhum dos 5 pegged excluídos (USD1, RLUSD, EUR, XAUT, PAXG) aparece em `UNIVERSO_AMPLO` (D1)

### Implementation for User Story 1

- [X] T003 [US1] Adicionar `UNIVERSO_AMPLO` (lista de 34 símbolos, D1) em `backtesting/portfolio_h14.py` (depende de T001-T002)

**Checkpoint**: `pytest tests/test_portfolio_h14.py -v` — T001-T002
passam. MVP completo: universo declarado e pronto para consumo por
`simular_carteira` sem alteração de mecânica.

---

## Phase 3: Polish & Cross-Cutting Concerns

- [ ] T004 Criar `cmd_carteira_ampla()` em `main.py`: chama `simular_carteira(pares=UNIVERSO_AMPLO)`, imprime a curva de capital agregada, o veredito de `evaluate_approval()`, e o drawdown já publicado sobre 12 pares (28,66%, spec 037) lado a lado; registrar `"carteira_ampla": cmd_carteira_ampla` em `COMMANDS`; exportar via `export_report("carteira_ampla", ...)`
- [ ] T005 Rodar `python main.py carteira_ampla` contra dados reais (34 pares, VPS `vps-limulus`/`nautilus-research`) — validação manual do passo 2 do `quickstart.md`, resultado real
- [ ] T006 Registrar o resultado real de T005 em `docs/research/registro-de-hipoteses.md` §4.15 (H14) — comparação explícita contra o drawdown de 12 pares já publicado; texto depende do resultado medido, não escrito antes de T005
- [ ] T007 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão em `backtesting/portfolio_h14.py::simular_carteira`/`_simular_carteira_core` (intocados)

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: N/A
- **US1 (Phase 2)**: sem dependência — único tópico que declara `UNIVERSO_AMPLO`
- **Polish (Phase 3)**: depende de Phase 2 completa — T006 depende do resultado real de T005

### Parallel Opportunities

- T001-T002 (US1, testes) em paralelo

---

## Implementation Strategy

### MVP = Phase 2 (US1)

Um commit: T001-T002 (testes) → T003 (implementação) → commit → push.

### Incremental Delivery

1. Phase 2 (US1) → `UNIVERSO_AMPLO`, MVP
2. Phase 3 (Polish) → comando CLI, execução real (VPS), comparação
   registrada no registro-mestre, suite completa
