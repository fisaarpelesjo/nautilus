---

description: "Task list for H15 leitura das corretoras em paralelo (spec 053)"
---

# Tasks: H15 — leitura das corretoras em paralelo

**Input**: Design documents from `/specs/053-h15-leitura-paralela/`

**Prerequisites**: plan.md, spec.md, quickstart.md (sem research.md — correção pontual já declarada)

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Ler as seis corretoras em paralelo, não sequencial (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [US1] Teste em `tests/test_arbitragem.py`: `ler_livro` simulado com `time.sleep(0.2)` por corretora — `medir_ciclo` para 6 corretoras completa em menos de ~2× esse tempo (paralelo), não perto de 6× (sequencial)
- [X] T002 [P] [US1] Confirmar que `test_medir_ciclo_falha_isolada_nao_aborta` (pré-existente) continua passando sem alteração sob paralelismo (FR-002) — mais um teste explícito equivalente adicionado

### Implementation

- [X] T003 [US1] Trocar a comprehension sequencial por `ThreadPoolExecutor.map` em `medir_ciclo` (`backtesting/arbitragem.py`); adicionar `threading.Lock` em `_get_exchange_publico` ao redor da escrita em `_exchange_cache` (depende de T001-T002)
- [ ] T004 Rodar `python main.py arbitragem BTC/USDT` contra dados reais (VPS `vps-limulus`/`nautilus-research`) — confirmar `intervalo_ms` bem menor entre a maioria das combinações
- [ ] T005 Registrar em `docs/research/registro-de-hipoteses.md` §5 (M15) que o instrumento foi corrigido — texto depende do resultado medido em T004, não escrito antes
- [ ] T006 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T003 implementação e testes) + (T004-T006 validação real e registro).

---

## Implementation Strategy

T001-T003 (testes + correção) → commit → push;
T004-T006 (validação real + registro + suite completa) → commit → push.

Uma nova campanha de acumulação de amostra (repetir o padrão de 40
ciclos da campanha anterior) é trabalho separado, spec futura —
condicionado a esta correção estar validada primeiro.
