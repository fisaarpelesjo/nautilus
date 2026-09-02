---

description: "Task list for historico estendido (spec 036)"
---

# Tasks: Histórico estendido para reavaliação de hipóteses

**Input**: Design documents from `/specs/036-historico-estendido/`

**Prerequisites**: plan.md, spec.md, data-model.md, research.md, quickstart.md

**Tests**: obrigatórios — Princípio III. Reusa as suites já existentes de
`test_modelo.py`/`test_onchain_hipotese.py`/`test_horizonte.py` (a
maioria já usa `df`/candles sintéticos, não depende do valor de
`2000`/`6000` — a garantia é que continuam passando sem alteração).

**Organization**: uma troca de constante por hipótese, cada uma seguida
da execução real e do registro comparado ao publicado (US1 → US2 → US3).

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Reavaliar H17 (Priority: P1) 🎯 primeiro

- [ ] T001 [US1] Trocar `fetch_ohlcv(par, TIMEFRAME, 2000)` por `fetch_ohlcv(par, TIMEFRAME, 6000)` em `backtesting/onchain_hipotese.py::avaliar_h17` (D1, research.md)
- [ ] T002 [US1] Rodar `pytest tests/test_onchain_hipotese.py -v` — confirma 0 regressão (testes usam `df` sintético, não o default)
- [ ] T003 [US1] Rodar `python main.py onchain` contra dados reais — confirma que a linha de base de regras atinge `EDGE_MIN_TRADES` (era 7, mínimo 10)
- [ ] T004 [US1] Registrar o resultado de T003 em `docs/research/registro-de-hipoteses.md` §6.3 (H17), comparado explicitamente contra o valor publicado (7 operações, inconclusivo) — texto depende do resultado real, não escrito antes de T003

**Checkpoint**: H17 reavaliada, resultado comparado e registrado.

---

## Phase 2: User Story 2 - Reavaliar H14 (Priority: P1)

- [ ] T005 [US2] Trocar os dois `fetch_ohlcv(par, TIMEFRAME, 2000)` por `..., 6000)` em `backtesting/modelo.py` (`avaliar_par`, `coletar_eventos`)
- [ ] T006 [US2] Rodar `pytest tests/test_modelo.py -v` — confirma 0 regressão
- [ ] T007 [US2] Rodar `python main.py modelo` contra dados reais — compara `n_treino`/`n_teste`/`razao_chances_decidido` por par contra os já publicados
- [ ] T008 [US2] Registrar o resultado de T007 em `docs/research/registro-de-hipoteses.md` §4.15 (H14), comparado ao publicado — texto depende do resultado real

**Checkpoint**: H14 reavaliada, resultado comparado e registrado.

---

## Phase 3: User Story 3 - Reavaliar H11 em 4h/1d (Priority: P2)

- [ ] T009 [US3] Trocar `solicitado: int = 2000` por `= 6000` em `backtesting/horizonte.py` (`run_horizonte_scan`, `medir_disponibilidade`)
- [ ] T010 [US3] Rodar `pytest tests/test_horizonte.py -v` — confirma 0 regressão
- [ ] T011 [US3] Rodar `python main.py horizonte 4h 1d` contra dados reais — compara candles obtidos/cobertura contra o já publicado; `1w` não é rodado (fora do escopo, D1)
- [ ] T012 [US3] Registrar o resultado de T011 em `docs/research/registro-de-hipoteses.md` §4.12 (H11), comparado ao publicado

**Checkpoint**: as três hipóteses reavaliadas.

---

## Phase 4: Polish & Cross-Cutting Concerns

- [ ] T013 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão em `backtesting/engine.py`/comandos de uso geral (intocados, D2)

---

## Dependencies & Execution Order

- **US1 (Phase 1)**: sem dependência — primeira, resolve o bloqueio de hoje
- **US2 (Phase 2)**: sem dependência de US1, mas sequencial no Fluxo Incremental
- **US3 (Phase 3)**: sem dependência de US1/US2
- **Polish (Phase 4)**: depende das três completas

### Parallel Opportunities

Cada user story toca um arquivo diferente — poderiam rodar em paralelo,
mas o Fluxo Incremental do `CLAUDE.md` (tópico → teste → commit → push)
favorece sequencial aqui, dado que cada uma já é pequena.

---

## Implementation Strategy

Três commits pequenos, um por hipótese (T001-T004, T005-T008, T009-T012),
mais um de polish (T013). Cada um: trocar constante → testes existentes
→ execução real → registro comparado → commit → push.
