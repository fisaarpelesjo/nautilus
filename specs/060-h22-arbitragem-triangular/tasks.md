---

description: "Task list for H22 arbitragem triangular intra-corretora (spec 060)"
---

# Tasks: H22 — arbitragem triangular intra-corretora

**Input**: Design documents from `/specs/060-h22-arbitragem-triangular/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D5), quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Medir o diferencial líquido de um ciclo triangular (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [P] [US1] Testes em `tests/test_arbitragem_triangular.py`: `_comprar`/`_vender` puros (preenchimento total e parcial), `_preenchido`
- [X] T002 [P] [US1] Teste: ciclo balanceado produz diferencial bruto ≈ 0, estado `sem_oportunidade` após custo
- [X] T003 [P] [US1] Teste: ciclo desbalanceado detecta `oportunidade`
- [X] T004 [P] [US1] Teste: perna indisponível aborta o ciclo inteiro sem medição parcial
- [X] T005 [P] [US1] Teste: profundidade insuficiente numa perna produz `profundidade_insuficiente`
- [X] T006 [P] [US1] Teste: ciclos são persistidos (JSONL por acréscimo)
- [X] T007 [P] [US1] Testes: `agregar` conta por (triângulo, direção), exige o mínimo na direção MENOS coberta

### Implementation

- [X] T008 [US1] Criar `data/paths.py::ARBITRAGEM_TRIANGULAR_FILE` + `data/arbitragem_triangular_store.py` (mesmo padrão de `data/arbitragem_store.py`) (depende de T006)
- [X] T009 [US1] Criar `backtesting/arbitragem_triangular.py`: `ler_livro`, `_comprar`, `_vender`, `_preenchido`, `medir_triangulo`, `agregar` (depende de T001-T005, T007-T008)
- [X] T010 [US1] Criar `cmd_triangular()` em `main.py`: mede um ciclo, imprime as duas direções e o agregado histórico, exporta via `export_report`; registrar `"triangular": cmd_triangular` em `COMMANDS`; sincronizar `CLAUDE.md`/`AGENTS.md` (depende de T009)
- [X] T011 Smoke test local contra dado real (Binance, BTC/USDT×ETH/BTC×ETH/USDT) confirmando intervalo de latência bem abaixo do teto (D3)
- [X] T012 Rodar campanha real (≥ 30 ciclos, VPS `vps-limulus`/`nautilus-research`)
- [X] T013 Registrar o resultado real de T012 em `docs/research/registro-de-hipoteses.md` §6.1 (H22) — "campanha real rodada" no mesmo estilo de H15
- [X] T014 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T011 implementação e testes) + (T012-T014 campanha real e registro).

---

## Implementation Strategy

T001-T011 (testes + módulos + comando CLI + smoke test) → commit → push;
T012-T014 (campanha real + registro + suite completa) → commit → push.
