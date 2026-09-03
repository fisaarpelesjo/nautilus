---

description: "Task list for H32 on-chain mais rico (spec 069)"
---

# Tasks: H32 — on-chain mais rico (valor transacionado)

**Input**: Design documents from `/specs/069-h32-onchain-rico/`

## Phase 1: User Story 1 - Medir colinearidade e desempenho isolado (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [P] Teste: `onchain_txn_volume_growth_7d` reproduz a mesma fórmula de `onchain_addr_growth_7d` sobre série sintética
- [X] T002 [P] Teste: colinearidade acima do limiar (0,80) interrompe antes de medir desempenho
- [X] T003 [P] Teste: colinearidade abaixo do limiar prossegue para comparação com/sem atributo

### Implementation

- [X] T004 Criar `backtesting/onchain_volume_hipotese.py`: reusa `_merge_causal`/`construir_extrator_onchain`-style de `onchain_hipotese.py`, transformação de T001 (depende de T001-T003)
- [X] T005 Criar `cmd_onchain_volume()` em `main.py`, registrar em `COMMANDS`, sincronizar `CLAUDE.md`/`AGENTS.md` (depende de T004)
- [X] T006 Rodar `python main.py onchain_volume` contra dados reais
- [X] T007 Registrar o resultado real em `docs/research/registro-de-hipoteses.md` §6.2 (H32)
- [X] T008 Rodar a suite completa (`pytest -q`)

## Implementation Strategy

T001-T005 → commit → push; T006-T008 → commit → push.
