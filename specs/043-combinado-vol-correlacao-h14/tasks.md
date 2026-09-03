---

description: "Task list for combinacao vol+correlacao na carteira de H14 (spec 043)"
---

# Tasks: Combinação dimensionamento por volatilidade + gate de correlação

**Input**: Design documents from `/specs/043-combinado-vol-correlacao-h14/`

**Prerequisites**: plan.md, spec.md, data-model.md, quickstart.md (sem research.md — nada novo a decidir)

**Tests**: obrigatórios — Princípio III da constitution.
`tests/test_portfolio_h14.py` (extensão mínima).

**Organization**: uma única user story, um único tópico — spec pequena
por natureza (zero mecânica nova).

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Medir a carteira com os dois mecanismos ligados (Priority: P1) 🎯 MVP

### Tests

- [ ] T001 [US1] Teste em `tests/test_portfolio_h14.py`: `_simular_carteira_core` com `usar_dimensionamento_vol=True` e `usar_gate_correlacao=True` simultaneamente produz um `BacktestResult` válido sobre um cenário sintético com posições correlacionadas e `atr_ratio` variável, sem exceção

### Implementation

- [ ] T002 Criar `cmd_carteira_combo()` em `main.py`: chama `simular_carteira(pares=UNIVERSO_H11, usar_dimensionamento_vol=True, usar_gate_correlacao=True)`, imprime a curva de capital agregada, o veredito de `evaluate_approval()`, e os três drawdowns já publicados (28,66%/23,04%/20,74%) lado a lado; registrar `"carteira_combo": cmd_carteira_combo` em `COMMANDS`; exportar via `export_report("carteira_combo", ...)` (depende de T001)
- [ ] T003 Rodar `python main.py carteira_combo` contra dados reais (12 pares, VPS `vps-limulus`/`nautilus-research`) — resultado real
- [ ] T004 Registrar o resultado real de T003 em `docs/research/registro-de-hipoteses.md` §4.15 (H14) — comparação explícita contra os três já publicados; texto depende do resultado medido, não escrito antes de T003
- [ ] T005 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada num único commit pequeno (T001-T002) + Polish (T003-T005).

---

## Implementation Strategy

Dado o tamanho, dois commits: T001-T002 (teste + CLI) → commit → push;
T003-T005 (execução real + registro + suite completa) → commit → push.
