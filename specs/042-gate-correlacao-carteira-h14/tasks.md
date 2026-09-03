---

description: "Task list for gate de correlacao na carteira de H14 (spec 042)"
---

# Tasks: Gate de correlação na carteira de H14

**Input**: Design documents from `/specs/042-gate-correlacao-carteira-h14/`

**Prerequisites**: plan.md, spec.md, data-model.md, research.md, quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.
`tests/test_portfolio_h14.py` (extensão).

**Organization**: uma única user story (P1) — função nova + parâmetro
opt-in, sem segunda prioridade a decompor.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

Nenhuma — sem dependência nova.

---

## Phase 2: User Story 1 - Medir a carteira de H14 com o gate de correlação (Priority: P1) 🎯 MVP

**Goal**: `_correlacionado_com_posicao_aberta` bloqueia candidatos
correlacionados com posições já abertas, ponto-no-tempo;
`_simular_carteira_core(usar_gate_correlacao=True)` usa essa checagem
antes de dimensionar; `False` (default) reproduz o resultado já
publicado byte a byte.

**Independent Test**: cenário sintético com dois pares de retornos
quase idênticos e um terceiro descorrelacionado — confirma bloqueio
seletivo.

### Tests for User Story 1

- [X] T001 [P] [US1] Teste em `tests/test_portfolio_h14.py`: com uma posição aberta e um candidato de retornos quase idênticos (correlação ≥ 0,7) na janela de 50 candles, `_correlacionado_com_posicao_aberta` devolve o símbolo da posição aberta (FR-003)
- [X] T002 [P] [US1] Teste: candidato com retornos descorrelacionados nunca é bloqueado, mesmo com posições abertas (FR-003)
- [X] T003 [P] [US1] Teste: sem posições abertas, `_correlacionado_com_posicao_aberta` sempre devolve `None` (FR-004)
- [X] T004 [P] [US1] Teste: candidato ou posição aberta com menos de `lookback // 2` candles de histórico falha aberta (não bloqueia por dado insuficiente, FR-004)
- [X] T005 [P] [US1] Teste: `usar_gate_correlacao=False` (default) reproduz exatamente os valores de referência já capturados para os testes existentes de `_simular_carteira_core` — regressão explícita (FR-005)
- [X] T006 [P] [US1] Teste: com `usar_gate_correlacao=True`, um candidato bloqueado por correlação nunca abre posição, mas o próximo candidato da fila (não correlacionado) pode abrir no mesmo candle

### Implementation for User Story 1

- [X] T007 [US1] Implementar `_correlacionado_com_posicao_aberta(par, preparados, posicoes_abertas, t, lookback=CORRELATION_LOOKBACK, limiar=MAX_POSITION_CORRELATION)` em `backtesting/portfolio_h14.py` (D1, `data-model.md`) (depende de T001-T004)
- [X] T008 [US1] Adicionar `usar_gate_correlacao: bool = False` a `_simular_carteira_core`/`simular_carteira`: pula candidato correlacionado antes de dimensionar (depende de T005-T007)

**Checkpoint**: `pytest tests/test_portfolio_h14.py -v` — T001-T006
passam. MVP completo: gate de correlação disponível na carteira de H14,
sem alterar o resultado default.

---

## Phase 3: Polish & Cross-Cutting Concerns

- [X] T009 Criar `cmd_carteira_corr()` em `main.py`: chama `simular_carteira(pares=UNIVERSO_H11, usar_gate_correlacao=True)`, imprime a curva de capital agregada, o veredito de `evaluate_approval()`, e o drawdown já publicado sem o gate (28,66%, spec 037) lado a lado; registrar `"carteira_corr": cmd_carteira_corr` em `COMMANDS`; exportar via `export_report("carteira_corr", ...)`
- [ ] T010 Rodar `python main.py carteira_corr` contra dados reais (12 pares, VPS `vps-limulus`/`nautilus-research`) — validação manual do passo 2 do `quickstart.md`, resultado real
- [ ] T011 Registrar o resultado real de T010 em `docs/research/registro-de-hipoteses.md` §4.15 (H14) — comparação explícita contra os 28,66% já publicados e contra o resultado de dimensionamento por volatilidade (23,04%, spec 041); texto depende do resultado medido, não escrito antes de T010
- [ ] T012 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão em `risk/correlation.py`/`backtesting/engine.py`/`backtesting/approval.py` (intocados)

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: N/A
- **US1 (Phase 2)**: sem dependência — único tópico que adiciona a checagem e o parâmetro
- **Polish (Phase 3)**: depende de Phase 2 completa — T011 depende do resultado real de T010

### Parallel Opportunities

- T001-T006 (US1, testes) em paralelo

---

## Implementation Strategy

### MVP = Phase 2 (US1)

Um commit: T001-T006 (testes) → T007-T008 (implementação) → commit →
push.

### Incremental Delivery

1. Phase 2 (US1) → gate de correlação ponto-no-tempo, MVP
2. Phase 3 (Polish) → comando CLI, execução real (VPS), comparação
   registrada no registro-mestre, suite completa
