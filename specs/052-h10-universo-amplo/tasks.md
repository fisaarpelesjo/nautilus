---

description: "Task list for H10 reavaliada com universo amplo de pares candidatos (spec 052)"
---

# Tasks: H10 reavaliada com universo amplo de pares candidatos

**Input**: Design documents from `/specs/052-h10-universo-amplo/`

**Prerequisites**: plan.md, spec.md, quickstart.md (sem research.md/data-model.md — reuso trivial)

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Reavaliar H10 com universo amplo de candidatos (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [US1] Teste em `tests/test_pairs_trading.py`: `selecionar_pares` sobre um cenário sintético com N colunas de preço encontra pelo menos tantos pares elegíveis quanto o mesmo cenário sobre um subconjunto de N-k colunas (monotonicidade — mais candidatos nunca reduz o conjunto elegível)

### Implementation

- [X] T002 [US1] Criar `cmd_pairs_amplo()` em `main.py`: chama `run_pairs_scan(pares=UNIVERSO_AMPLO)`, imprime treino/validação/veredito no mesmo formato de `cmd_pairs()`, e os números já publicados (12 pares, 6 trades na validação) lado a lado; registrar `"pairs_amplo": cmd_pairs_amplo` em `COMMANDS`; exportar via `export_report("pairs_amplo", ...)` (depende de T001)
- [ ] T003 Rodar `python main.py pairs_amplo` contra dados reais (34 pares, VPS `vps-limulus`/`nautilus-research`) — resultado real
- [ ] T004 Registrar o resultado real de T003 em `docs/research/registro-de-hipoteses.md` §4.11 (H10) — comparação explícita contra o já publicado (12 pares); atualizar §4.1 (quadro-resumo) e §6.1 (fila) se o veredito mudar; texto depende do resultado medido, não escrito antes de T003
- [ ] T005 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T002 implementação e testes) + (T003-T005 execução real e registro).

---

## Implementation Strategy

T001-T002 (teste + comando CLI) → commit → push;
T003-T005 (execução real + registro + suite completa) → commit → push.
