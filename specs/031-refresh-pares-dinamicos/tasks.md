---

description: "Task list for refresh periodico de pares dinamicos (spec 031)"
---

# Tasks: Refresh periódico de pares dinâmicos

**Input**: Design documents from `/specs/031-refresh-pares-dinamicos/`

**Prerequisites**: plan.md, spec.md, data-model.md, research.md, quickstart.md

**Tests**: obrigatórios — Princípio III da constitution. Arquivo novo
`tests/test_runner_dynamic_pairs_refresh.py`, mesmo padrão de
`tests/test_runner_reconciliation.py` (`_FakeManager`, função extraída
testada isoladamente, não o loop `run()` inteiro).

**Organization**: US1 (refresh funciona) e US2 (posição aberta nunca some)
são implementadas juntas — `spec.md` já declara que são inseparáveis por
design (US1 sozinha reintroduziria o risco que hoje não existe). US3
(auditoria) é tópico separado.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [ ] T001 Adicionar `DYNAMIC_PAIRS_REFRESH_CYCLES = int(os.getenv("DYNAMIC_PAIRS_REFRESH_CYCLES", "1440"))` em `config/settings.py`, junto de `DYNAMIC_PAIRS_TOP_N`/`DYNAMIC_PAIRS_CANDIDATES` (D1, research.md)
- [ ] T002 Adicionar validação `DYNAMIC_PAIRS_REFRESH_CYCLES < 1` → erro em `config/settings.py::validate_config()`, mesmo padrão de `DYNAMIC_PAIRS_TOP_N`/`_CANDIDATES`

---

## Phase 2: User Story 1 + User Story 2 - Refresh periódico sem nunca abandonar posição aberta (Priority: P1) 🎯 MVP

**Goal**: `active_pairs` é re-selecionada a cada `DYNAMIC_PAIRS_REFRESH_CYCLES`
ciclos quando `DYNAMIC_PAIRS_ENABLED=true`, e nenhum símbolo com posição
aberta é removido, independente do resultado do seletor.

**Independent Test**: chamar `_refresh_active_pairs(manager, active_pairs)`
diretamente com um `_FakeManager` que simula posição aberta num símbolo fora
da nova seleção, e confirmar que ele permanece na lista retornada.

### Tests for User Story 1 + 2

> **NOTE**: escrever os testes primeiro, confirmar que o teste de posição
> aberta FALHA antes de `_refresh_active_pairs` existir (função não
> implementada) — depois confirmar que passa com a implementação correta e
> FALHARIA se a guarda fosse removida (mutar mentalmente: `nova_lista =
> selecionados` sem a união faria este teste específico falhar).

- [ ] T003 [P] [US1] Teste em `tests/test_runner_dynamic_pairs_refresh.py`: `_refresh_active_pairs` retorna a nova seleção quando ela difere de `active_pairs` e nenhum símbolo tem posição aberta — `nova_lista == selecionados`, `resumo["added"]`/`resumo["removed"]` corretos
- [ ] T004 [P] [US1] Teste: quando o seletor retorna exatamente os mesmos símbolos já ativos, `nova_lista == active_pairs`, `resumo["added"] == []`, `resumo["removed"] == []` (idempotência, Acceptance Scenario 2 de US1)
- [ ] T005 [P] [US2] Teste **crítico**: `_FakeManager` com posição aberta num símbolo que o seletor mockado não inclui mais — `nova_lista` MUST conter esse símbolo, `resumo["removed"]` MUST NOT contê-lo, `resumo["kept_for_open_position"]` MUST contê-lo
- [ ] T006 [P] [US2] Teste: símbolo sem posição aberta que o seletor não escolhe mais é removido normalmente (`resumo["removed"]` o contém) — confirma que a guarda de T005 é específica de posição aberta, não um bloqueio geral de remoção
- [ ] T007 [P] [US1][US2] Teste (D2): seletor mockado levanta exceção — `nova_lista == active_pairs` (lista vigente preservada, não `PAIRS` estático), `resumo["error"]` presente

### Implementation for User Story 1 + 2

- [ ] T008 [US1][US2] Implementar `_refresh_active_pairs(manager, active_pairs: list[str]) -> tuple[list[str], dict]` em `trading/runner.py`: chama `select_dynamic_pairs()`/`selected_symbols()`, calcula `nova_lista = selecionados ∪ {s in active_pairs se manager.has_position(s)}`, monta `resumo` (`added`, `removed`, `kept_for_open_position`); captura exceção do seletor e retorna `(active_pairs, {"added": [], "removed": [], "kept_for_open_position": [], "error": str(exc)})` (D2) (depende de T003-T007)
- [ ] T009 [US1] Integrar no loop principal de `trading/runner.py::run()`: quando `DYNAMIC_PAIRS_ENABLED` e `cycle_id % DYNAMIC_PAIRS_REFRESH_CYCLES == 0`, chamar `_refresh_active_pairs(manager, active_pairs)` e reatribuir `active_pairs` — mesmo padrão de posição do `if cycle_id % RECONCILIATION_INTERVAL_CYCLES == 0` já existente (depende de T008, T001)

**Checkpoint**: `pytest tests/test_runner_dynamic_pairs_refresh.py -v` —
T003-T007 passam. MVP completo: refresh funciona e nunca abandona posição.

---

## Phase 3: User Story 3 - Refresh auditável (Priority: P2)

**Goal**: todo refresh grava um evento estruturado (D3), inclusive quando
nada muda.

**Independent Test**: rodar um refresh via `_refresh_active_pairs` seguido
da gravação do evento, e ler `logs/events-*.jsonl` (ou o mock de
`log_event`) confirmando os três campos.

### Tests for User Story 3

- [ ] T010 [P] [US3] Teste em `tests/test_runner_dynamic_pairs_refresh.py`: após um refresh que muda a lista, `log_event` (mockado) é chamado com `"dynamic_pairs_refreshed"`, `mode=TRADING_MODE`, `added`, `removed`, `kept_for_open_position` corretos
- [ ] T011 [P] [US3] Teste: refresh sem nenhuma mudança ainda grava o evento, com os três campos vazios (Acceptance Scenario 2 de US3 — nunca omitido)

### Implementation for User Story 3

- [ ] T012 [US3] Chamar `log_event("dynamic_pairs_refreshed", mode=TRADING_MODE, added=resumo["added"], removed=resumo["removed"], kept_for_open_position=resumo["kept_for_open_position"])` em `trading/runner.py::run()`, logo após `_refresh_active_pairs` (T009), envolto em `safe_step` (mesmo padrão de outros eventos do loop) (depende de T010, T011, T009)

**Checkpoint**: as três user stories passam juntas.

---

## Phase 4: Polish & Cross-Cutting Concerns

- [ ] T013 [P] Teste em `tests/test_runner_dynamic_pairs_refresh.py`: com `DYNAMIC_PAIRS_ENABLED=false` (monkeypatch), `select_dynamic_pairs` mockado nunca é chamado durante o loop, mesmo após `DYNAMIC_PAIRS_REFRESH_CYCLES` ciclos simulados (FR-006)
- [ ] T014 Validar manualmente o passo 3 do `quickstart.md` (custo real de `select_dynamic_pairs()`) para confirmar que a ordem de grandeza medida em `research.md` (~36s) ainda vale neste ambiente
- [ ] T015 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão em `trading/runner.py` (boot, reconciliação, ciclo principal) e `market/selector.py` (intocado)

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: sem dependências
- **US1+US2 (Phase 2)**: depende de T001 (constante existir) — é o único tópico que cria `_refresh_active_pairs`
- **US3 (Phase 3)**: depende de T008/T009 (Phase 2) — grava evento sobre o resultado que a Phase 2 produz
- **Polish (Phase 4)**: depende de Phase 2 e Phase 3 completas

### Parallel Opportunities

- T003-T007 (testes de `_refresh_active_pairs`, funções independentes) em paralelo
- T010-T011 (testes de evento) em paralelo
- T013 e T014 (verificações independentes) em paralelo

---

## Implementation Strategy

### MVP = Phase 1 + Phase 2 (US1+US2)

Um commit: T001-T002 (constante) → T003-T007 (testes falhando) → T008-T009
(implementação, testes passam) → commit → push. É a mudança que fecha o
gap com segurança. US3 é auditoria sobre um mecanismo que já funciona
corretamente sem ela.

### Incremental Delivery

1. Setup + Phase 2 (US1+US2) → MVP, refresh funciona e nunca abandona posição
2. Phase 3 (US3) → auditoria
3. Phase 4 (Polish) → guarda de flag desligada + validação manual + suite completa

Fluxo Incremental do `CLAUDE.md`: dois tópicos/commits (Phase 2 primeiro,
Phase 3+4 depois), dado que Phase 3 depende do resultado de Phase 2 mas é
logicamente separável (auditoria não muda a decisão, só a registra).
