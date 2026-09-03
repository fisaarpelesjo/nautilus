---

description: "Task list for H25 sazonalidade por sessao de negociacao (spec 062)"
---

# Tasks: H25 — sazonalidade por sessão de negociação (hora do dia)

**Input**: Design documents from `/specs/062-h25-sazonalidade-horaria/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D3), quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Medir o efeito do filtro por sessão, confirmado fora da amostra (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [P] [US1] Teste em `tests/test_sazonalidade.py`: `filtrar_por_sessao` bloqueia BUY fora da janela declarada
- [X] T002 [P] [US1] Teste: `filtrar_por_sessao` nunca bloqueia SELL
- [X] T003 [P] [US1] Teste: `filtrar_por_sessao` preserva HOLD original e não afeta BUY dentro da janela
- [X] T004 [P] [US1] Teste: janelas cobrem as 24h UTC sem sobreposição
- [X] T005 [P] [US1] Teste: erro de busca de dado marca status `erro` sem lançar exceção
- [X] T006 [P] [US1] Teste: `avaliar_sazonalidade` continua avaliando os demais pares após um erro

### Implementation

- [X] T007 [US1] Criar `backtesting/sazonalidade.py`: `JANELAS`, `filtrar_por_sessao` (pura), `_avaliar_par_janela`, `avaliar_sazonalidade` — reusa `precompute_signals`/`simulate_backtest`/`split_train_validation`/`multimarket.classify` sem alteração (depende de T001-T006)
- [X] T008 [US1] Criar `cmd_sazonalidade()` em `main.py`: roda `avaliar_sazonalidade()` sobre `UNIVERSO_H11` × `JANELAS`, imprime as 36 combinações e o resumo por status, exporta via `export_report`; registrar `"sazonalidade": cmd_sazonalidade` em `COMMANDS`; sincronizar `CLAUDE.md`/`AGENTS.md` (depende de T007)
- [ ] T009 Rodar `python main.py sazonalidade` contra dados reais
- [ ] T010 Registrar o resultado real de T009 em `docs/research/registro-de-hipoteses.md` §6.3 (H25) — write-up datado, full transparência sobre quantas combinações confirmaram
- [ ] T011 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T008 implementação e testes) + (T009-T011 execução real e registro).

---

## Implementation Strategy

T001-T008 (testes + módulo + comando CLI) → commit → push;
T009-T011 (execução real + registro + suite completa) → commit → push.
