---

description: "Task list for combinacao correlacao + limite diario na carteira de H14 (spec 046)"
---

# Tasks: Combinação gate de correlação + limite de drawdown diário

**Input**: Design documents from `/specs/046-combinado-correlacao-limite-diario-h14/`

**Prerequisites**: plan.md, spec.md, data-model.md, quickstart.md (sem research.md — nada novo a decidir)

**Tests**: obrigatórios — Princípio III da constitution.
`tests/test_portfolio_h14.py` (extensão mínima).

**Organization**: uma única user story, um único tópico — spec pequena
por natureza (zero mecânica nova).

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Medir a carteira com os dois mecanismos ligados (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [US1] Teste em `tests/test_portfolio_h14.py`: `_simular_carteira_core` com `usar_gate_correlacao=True` e `usar_limite_drawdown_diario=True` simultaneamente produz um `BacktestResult` válido sobre um cenário sintético, sem exceção

### Implementation

- [X] T002 Criar `cmd_carteira_combo2()` em `main.py`: chama `simular_carteira(pares=UNIVERSO_H11, usar_gate_correlacao=True, usar_limite_drawdown_diario=True)`, imprime a curva de capital agregada, o veredito de `evaluate_approval()`, e os seis resultados já publicados lado a lado; registrar `"carteira_combo2": cmd_carteira_combo2` em `COMMANDS`; exportar via `export_report("carteira_combo2", ...)` (depende de T001)
- [X] T003 Rodar `python main.py carteira_combo2` contra dados reais (12 pares, VPS `vps-limulus`/`nautilus-research`) — resultado real
- [X] T004 Registrar o resultado real de T003 em `docs/research/registro-de-hipoteses.md` §4.15 (H14) — comparação explícita contra os seis já publicados; texto depende do resultado medido, não escrito antes de T003
- [X] T005 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada num único commit pequeno (T001-T002) + Polish (T003-T005).

---

## Implementation Strategy

Dois commits: T001-T002 (teste + CLI) → commit → push;
T003-T005 (execução real + registro + suite completa) → commit → push.
