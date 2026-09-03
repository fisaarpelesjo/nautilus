---

description: "Task list for H20 backtest real -- geometria propaga ao motor de simulacao (spec 049)"
---

# Tasks: H20 — geometria propaga ao backtest real

**Input**: Design documents from `/specs/049-h20-backtest-real/`

**Prerequisites**: plan.md, spec.md, data-model.md, quickstart.md (sem research.md — achado já declarado em spec.md)

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - A geometria rotulada é a geometria simulada (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [US1] Teste em `tests/test_modelo.py`: `avaliar_par(params=ParametrosBarreira(tp_mult=2.0, sl_mult=1.5))` chama `simulate_backtest` com `atr_tp_multiplier=2.0`/`atr_sl_multiplier=1.5` (spy sobre `backtesting.engine.simulate_backtest`) — para as linhas de base decididas pelo modelo (achado adicional durante a implementação: o bloco de "custo de giro", `_simular_com_sinais` fora de `_resultado_modelo`, tinha a mesma lacuna e também foi corrigido — a linha de base de REGRAS continua de propósito nos multiplicadores de produção)
- [X] T002 [P] [US1] Confirmar que `test_avaliar_par_sem_parametros_novos_reproduz_resultado_atual` (pré-existente) continua passando sem alteração — regressão do caminho default (FR-002)

### Implementation

- [X] T003 [US1] Adicionar `atr_tp_multiplier=p.tp_mult, atr_sl_multiplier=p.sl_mult` às duas chamadas de `_resultado_modelo(...)` E ao bloco de custo de giro em `backtesting/modelo.py::avaliar_par` (depende de T001-T002)
- [X] T004 [US1] Estender `cmd_geometria()` em `main.py`: roda `avaliar_par` por par sobre `UNIVERSO_H11` com a geometria selecionada, imprime backtest real por par (trades/retorno/drawdown/profit factor), comparado aos números por-par já publicados de H14 onde disponíveis (depende de T003)
- [X] T005 Rodar `python main.py geometria` contra dados reais (12 pares, VPS `vps-limulus`/`nautilus-research`) — resultado real do backtest por par
- [X] T006 Registrar o resultado real de T005 em `docs/research/registro-de-hipoteses.md` §4.16 (H20) — comparação por par contra H14 (`tp=3,0`); texto depende do resultado medido, não escrito antes de T005
- [X] T007 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T004 implementação e testes) + (T005-T007 execução real e registro).

---

## Implementation Strategy

T001-T004 (testes + correção + extensão CLI) → commit → push;
T005-T007 (execução real + registro + suite completa) → commit → push.
