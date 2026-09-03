---

description: "Task list for combinacao total (teto) dos mecanismos de risco na carteira de H14 (spec 047)"
---

# Tasks: Combinação total (teto) dos mecanismos de risco não-degenerados

**Input**: Design documents from `/specs/047-combinado-total-h14/`

**Prerequisites**: plan.md, spec.md, data-model.md, quickstart.md (sem research.md)

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story, um único tópico.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Medir o teto dos três mecanismos ligados (Priority: P1) 🎯 MVP

### Tests

- [ ] T001 [US1] Teste em `tests/test_portfolio_h14.py`: `_simular_carteira_core` com `usar_dimensionamento_vol=True`, `usar_gate_correlacao=True` e `usar_limite_drawdown_diario=True` simultaneamente produz um `BacktestResult` válido sobre um cenário sintético, sem exceção

### Implementation

- [ ] T002 Criar `cmd_carteira_teto()` em `main.py`: chama `simular_carteira` com os três parâmetros, imprime a curva de capital agregada, o veredito de `evaluate_approval()`, e os sete resultados já publicados lado a lado; registrar `"carteira_teto": cmd_carteira_teto` em `COMMANDS`; exportar via `export_report("carteira_teto", ...)` (depende de T001)
- [ ] T003 Rodar `python main.py carteira_teto` contra dados reais (12 pares, VPS `vps-limulus`/`nautilus-research`) — resultado real
- [ ] T004 Registrar o resultado real de T003 em `docs/research/registro-de-hipoteses.md` §4.15 (H14) — comparação explícita contra os sete já publicados, e se confirma/refuta a expectativa declarada (perto do gate de correlação sozinho); texto depende do resultado medido, não escrito antes de T003
- [ ] T005 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada num único commit pequeno (T001-T002) + Polish (T003-T005).

---

## Implementation Strategy

Dois commits: T001-T002 (teste + CLI) → commit → push;
T003-T005 (execução real + registro + suite completa) → commit → push.
