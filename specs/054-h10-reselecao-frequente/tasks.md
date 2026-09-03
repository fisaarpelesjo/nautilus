---

description: "Task list for H10 reselecao de pares desacoplada da formacao (spec 054)"
---

# Tasks: H10 — reseleção de pares desacoplada da formação

**Input**: Design documents from `/specs/054-h10-reselecao-frequente/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D3), quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Reavaliar H10 com reseleção mais frequente (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [US1] Teste em `tests/test_pairs_trading.py`: `run_pairs_scan(reselecionar_a_cada=None)` reproduz byte a byte o resultado já publicado (regressão do default) — já coberto pelo teste pré-existente `test_run_pairs_scan_usa_formacao_500_por_padrao`
- [X] T002 [P] [US1] Teste em `tests/test_pairs_trading.py`: `run_pairs_scan(reselecionar_a_cada=120)` repassa o valor explícito sem trocá-lo por `p.formacao` (spy sobre `run_pairs_backtest`), confirmando que o parâmetro desacopla de fato

### Implementation

- [X] T003 [US1] Adicionar `reselecionar_a_cada: Optional[int] = None` a `run_pairs_scan` (`backtesting/pairs_trading.py`) — `None` preserva `= p.formacao` (depende de T001-T002)
- [X] T004 [US1] Criar `cmd_pairs_reselecao()` em `main.py`: chama `run_pairs_scan(pares=UNIVERSO_AMPLO_HISTORICO_COMPLETO, reselecionar_a_cada=120)`, imprime treino/validação/veredito e os dois números já publicados (6 trades, specs 039/052) lado a lado; registrar `"pairs_reselecao": cmd_pairs_reselecao` em `COMMANDS`; exportar via `export_report("pairs_reselecao", ...)` (depende de T003)
- [ ] T005 Rodar `python main.py pairs_reselecao` contra dados reais (VPS `vps-limulus`/`nautilus-research`) — resultado real
- [ ] T006 Registrar o resultado real de T005 em `docs/research/registro-de-hipoteses.md` §4.11 (H10) — comparação explícita contra os dois já publicados; atualizar §4.1/§6.1 se o veredito mudar; texto depende do resultado medido, não escrito antes de T005
- [ ] T007 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T004 implementação e testes) + (T005-T007 execução real e registro).

---

## Implementation Strategy

T001-T004 (testes + parâmetro + comando CLI) → commit → push;
T005-T007 (execução real + registro + suite completa) → commit → push.
