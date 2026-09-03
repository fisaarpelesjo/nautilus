---

description: "Task list for dimensionamento por volatilidade na carteira de H14 (spec 041)"
---

# Tasks: Dimensionamento por volatilidade na carteira de H14

**Input**: Design documents from `/specs/041-volatilidade-carteira-h14/`

**Prerequisites**: plan.md, spec.md, data-model.md, research.md, quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.
`tests/test_portfolio_h14.py` (extensão).

**Organization**: uma única user story (P1) — parâmetro opt-in numa
função já existente, sem segunda prioridade a decompor.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

Nenhuma — sem dependência nova.

---

## Phase 2: User Story 1 - Medir a carteira de H14 com dimensionamento por volatilidade (Priority: P1) 🎯 MVP

**Goal**: `_simular_carteira_core(usar_dimensionamento_vol=True)`
dimensiona cada entrada por `fator_volatilidade`, aplicado depois do
dimensionamento já existente; `False` (default) reproduz o resultado já
publicado byte a byte.

**Independent Test**: cenário sintético com `atr_ratio` alto num par e
baixo noutro, confirmar que a entrada no par de `atr_ratio` alto fica
estritamente menor.

### Tests for User Story 1

- [ ] T001 [P] [US1] Teste em `tests/test_portfolio_h14.py`: `usar_dimensionamento_vol=False` (default) reproduz exatamente os valores de referência já capturados para os testes existentes de `_simular_carteira_core` — regressão explícita (FR-004)
- [ ] T002 [P] [US1] Teste: com `usar_dimensionamento_vol=True` e `atr_ratio` acima do alvo (0,02) num candle de entrada, o tamanho da posição fica estritamente menor que com a flag desligada, nunca maior (FR-003)
- [ ] T003 [P] [US1] Teste: com `atr_ratio` ausente/`NaN` no candle de entrada, `usar_dimensionamento_vol=True` não muda o tamanho (fator 1,0, mesma política de falha de `fator_volatilidade`)
- [ ] T004 [P] [US1] Teste: o fator é aplicado **depois** do teto por ordem e da reserva de caixa — nunca permite que a posição exceda `MAX_ORDER_SIZE_USDT` mesmo com `atr_ratio` muito baixo (D1/FR-002)

### Implementation for User Story 1

- [ ] T005 [US1] Adicionar `usar_dimensionamento_vol: bool = False` a `_simular_carteira_core`/`simular_carteira` em `backtesting/portfolio_h14.py`: multiplica `order_size` por `fator_volatilidade(row.get("atr_ratio"))` (`backtesting/volatilidade.py`, D1) depois do dimensionamento já existente (depende de T001-T004)

**Checkpoint**: `pytest tests/test_portfolio_h14.py -v` — T001-T004
passam. MVP completo: dimensionamento por volatilidade disponível na
carteira de H14, sem alterar o resultado default.

---

## Phase 3: Polish & Cross-Cutting Concerns

- [ ] T006 Criar `cmd_carteira_vol()` em `main.py`: chama `simular_carteira(pares=UNIVERSO_H11, usar_dimensionamento_vol=True)`, imprime a curva de capital agregada, o veredito de `evaluate_approval()`, e o drawdown já publicado sem dimensionamento (28,66%, spec 037) lado a lado; registrar `"carteira_vol": cmd_carteira_vol` em `COMMANDS`; exportar via `export_report("carteira_vol", ...)`
- [ ] T007 Rodar `python main.py carteira_vol` contra dados reais (12 pares, VPS `vps-limulus`/`nautilus-research`) — validação manual do passo 2 do `quickstart.md`, resultado real
- [ ] T008 Registrar o resultado real de T007 em `docs/research/registro-de-hipoteses.md` §4.13 (H12) e §4.15 (H14) — comparação explícita contra os 28,66% já publicados; texto depende do resultado medido, não escrito antes de T007
- [ ] T009 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão em `backtesting/volatilidade.py`/`backtesting/engine.py`/`backtesting/approval.py` (intocados)

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: N/A
- **US1 (Phase 2)**: sem dependência — único tópico que adiciona `usar_dimensionamento_vol`
- **Polish (Phase 3)**: depende de Phase 2 completa — T008 depende do resultado real de T007

### Parallel Opportunities

- T001-T004 (US1, testes) em paralelo

---

## Implementation Strategy

### MVP = Phase 2 (US1)

Um commit: T001-T004 (testes) → T005 (implementação) → commit → push.

### Incremental Delivery

1. Phase 2 (US1) → `usar_dimensionamento_vol`, MVP
2. Phase 3 (Polish) → comando CLI, execução real (VPS), comparação
   registrada no registro-mestre, suite completa
