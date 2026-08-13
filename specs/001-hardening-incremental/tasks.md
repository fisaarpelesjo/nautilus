---

description: "Task list for 001-hardening-incremental"
---

# Tasks: Hardening Incremental do Bot de Daytrade

**Input**: Design documents from `/specs/001-hardening-incremental/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/cli.md](./contracts/cli.md)

**Tests**: Incluídos — a constitution (III. Test Before Implement) exige critério de teste definido
antes de cada implementação.

**Organization**: Tarefas agrupadas por User Story (US1/US2/US3, ver `spec.md`) para permitir
implementação e validação independentes de cada uma.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependência)
- **[Story]**: A qual User Story a tarefa pertence (US1, US2, US3)
- Caminhos de arquivo reais do repositório incluídos em cada descrição

## Path Conventions

Projeto único na raiz do repositório (não é `src/`/`frontend`/`backend`) — ver `plan.md` → Project
Structure para o mapeamento completo de módulos existentes.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar o ambiente de desenvolvimento e a base de lint, sem tocar lógica de trading.

- [x] T001 Instalar Python 3.12 e criar `.venv` no ambiente de desenvolvimento (não havia Python
      instalado na máquina de desenvolvimento)
- [x] T002 Instalar dependências de `requirements.txt` na `.venv` e corrigir gap encontrado: `rich`
      era usado em 6 arquivos mas não estava listado — commit `fix: adicionar dependencia rich
      faltante no requirements.txt`
- [x] T003 [P] Configurar `ruff` em `pyproject.toml` (regras E, F, B; E501 ignorada por ora) e
      corrigir lint básico (imports não usados, dead code trivial, `zip(..., strict=True)`) — commit
      `chore: configurar ruff e corrigir lint basico`. Achado no processo: `backtesting/scanner.py`
      calculava uma cor de tabela e nunca aplicava — corrigido em commit separado
      (`fix: aplicar cor no titulo da tabela do relatorio de scan`)

**Checkpoint**: Ambiente pronto, lint básico limpo.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Rede de segurança (type-check, cobertura, CI) que deve existir antes de mexer em
`risk/manager.py` e `execution/order_manager.py` nas User Stories seguintes.

**⚠️ CRITICAL**: Nenhuma tarefa de US1/US2/US3 que toque `risk/` ou `execution/` deve começar antes
de T007 (CI) estar concluída.

- [x] T004 Configurar `mypy` em `pyproject.toml` escopado em `risk/manager.py` e
      `execution/order_manager.py` (`check_untyped_defs=true`, `ignore_missing_imports=true`) —
      commit `chore: configurar mypy para risk manager e order manager`
- [x] T005 Configurar `pytest-cov` e registrar baseline de cobertura (66% geral, 93% em
      `risk/manager.py`, 36% em `execution/order_manager.py`) em `ROADMAP.md` — commit
      `chore: adicionar pytest-cov e registrar baseline de cobertura`
- [x] T006 [P] Instalar e validar `pre-commit` (`.pre-commit-config.yaml` com hooks de ruff --fix,
      mypy nos módulos críticos e pytest): `pre-commit install` + `pre-commit run --all-files`
      passando, documentado no `README.md`. Achado no processo: `pytest` rodado direto (sem
      `python -m`) quebrava por import error (`ModuleNotFoundError`) — corrigido com
      `[tool.pytest.ini_options] pythonpath = ["."]` em `pyproject.toml`
- [x] T007 Criar `.github/workflows/ci.yml`: jobs `lint` (ruff) → `typecheck` (mypy) → `test`
      (pytest), rodando em `push`/`pull_request` para `main`

**Checkpoint**: Foundational concluída — CI configurada, pre-commit funcionando localmente. Phase 3
(User Story 1) pode começar em uma próxima sessão.

---

## Phase 3: User Story 1 - Ordens nunca duplicam nem ficam fora de sincronia (Priority: P1) 🎯 MVP

**Goal**: Toda ordem tem `clientOrderId` único; `state.json` é reconciliado contra a conta real na
Binance na inicialização e periodicamente, com alerta (não correção automática) em caso de
divergência.

**Independent Test**: Ver `quickstart.md` → US1.

### Tests for User Story 1 ⚠️

> Escrever estes testes primeiro; devem falhar antes da implementação.

- [x] T008 [P] [US1] Teste: `clientOrderId` único gerado e persistido por ordem (paper e live) em
      `tests/test_order_manager_safety.py`
- [x] T009 [P] [US1] Teste: reconciliação detecta divergência entre `state.json` e conta real
      (mockada) em `tests/test_reconciliation.py` (novo arquivo)
- [x] T010 [P] [US1] Teste: reconciliação não roda quando `TRADING_MODE=paper` em
      `tests/test_reconciliation.py`

### Implementation for User Story 1

- [x] T011 [US1] Gerar e persistir `client_order_id` em toda ordem criada em
      `execution/order_manager.py` (`_generate_client_order_id()`; paper e live, passado à Binance
      via `params={"newClientOrderId": ...}`)
- [x] T012 [US1] Persistir `client_order_id` no registro de trade fechado em `data/trade_store.py`
      (novo campo em `TRADE_HEADERS`)
- [x] T013 [US1] Implementar `execution/reconciliation.py` — compara posições locais (`state.json`)
      com saldo real via `ccxt fetch_balance()` (não `fetch_positions`: Binance Spot não tem conceito
      de "position", só saldo do ativo base), retorna `ReconciliationResult` `ok`/`mismatch` com
      tolerância de 1% para taxas/arredondamento
- [x] T014 [US1] Chamar reconciliação na inicialização do bot em `trading/runner.py` (`_run_reconciliation`,
      que já é um no-op em paper mode via `reconcile()` retornando `None`)
- [x] T015 [US1] Chamar reconciliação periódica dentro do loop existente de 60s em
      `trading/runner.py` — a cada `RECONCILIATION_INTERVAL_CYCLES=30` ciclos (~30min)
- [x] T016 [US1] Evento `reconciliation_mismatch` (e `reconciliation_error` para falha de API) em
      `utils/logger.py` (JSONL) e alerta em `utils/notifier.py` (Telegram) via `_run_reconciliation`;
      último resultado persistido em `OrderManager.last_reconciliation` (`record_reconciliation`)
- [x] T017 [US1] Exibir resultado da última reconciliação em `python main.py status`
      (`cmd_status` em `main.py`, só quando `TRADING_MODE=live`)

**Checkpoint**: US1 completa e testável de forma independente — gap P6 da constitution fechado.
47 testes passando, ruff/mypy limpos.

`/code-review high` rodado antes do commit encontrou 4 problemas reais, todos corrigidos antes de
comitar:
1. `_live_sell` apagava a posição local mesmo quando a venda falhava — corrigido: só remove a
   posição no caminho de sucesso; erro mantém a posição local e alerta via Telegram.
2. `reconcile()` só detectava posição local sem saldo real, não o inverso (saldo real sem posição
   local) — corrigido: novo parâmetro `tracked_symbols` checa os dois sentidos, limitado aos pares
   que o bot acompanha (evita alertar sobre outros ativos da mesma conta).
3. `ensure_csv` não migrava o cabeçalho de um CSV já existente ao adicionar `client_order_id` —
   corrigido de forma genérica em `data/csv_utils.py` (afeta trades/signals/decisions).
4. Chamada de reconciliação na inicialização não estava protegida por `try/except` como a
   periódica — corrigido: todo o corpo de `_run_reconciliation` agora está dentro do try.

---

## Phase 4: User Story 2 - Circuit breaker além do limite diário de drawdown (Priority: P2)

**Goal**: Bot suspende novas entradas após N perdas consecutivas configuráveis; operador pode
suspender/retomar novas entradas manualmente via CLI a qualquer momento.

**Independent Test**: Ver `quickstart.md` → US2.

### Tests for User Story 2 ⚠️

- [ ] T018 [P] [US2] Teste: `consecutive_losses` incrementa em trade com prejuízo e reseta em trade
      com lucro em `tests/test_risk_manager.py`
- [ ] T019 [P] [US2] Teste: `circuit_breaker_active` vira `true` ao atingir `MAX_CONSECUTIVE_LOSSES`
      e bloqueia novas entradas em `tests/test_risk_manager.py`
- [ ] T020 [P] [US2] Teste: `killswitch_active` bloqueia novas entradas e persiste entre reinícios
      simulados (recarregar `state.json`) em `tests/test_order_manager_safety.py` ou novo arquivo

### Implementation for User Story 2

- [ ] T021 [US2] Nova variável `MAX_CONSECUTIVE_LOSSES` em `config/settings.py`, incluindo validação
      em `validate_config()` (depende de T018 falhando)
- [ ] T022 [US2] Campos `consecutive_losses` e `circuit_breaker_active` em `data/state_store.py`
- [ ] T023 [US2] Lógica de incremento/reset do contador ao fechar um trade, em `risk/manager.py` ou
      `trading/position_lifecycle.py` (depende de T021, T022)
- [ ] T024 [US2] Bloquear abertura de novas posições em `trading/runner.py` quando
      `circuit_breaker_active` (depende de T023)
- [ ] T025 [US2] Campo `killswitch_active` em `data/state_store.py` (depende de T020 falhando)
- [ ] T026 [US2] Subcomandos `kill` e `resume` em `main.py`, seguindo `contracts/cli.md`
      (depende de T025)
- [ ] T027 [US2] Bloquear abertura de novas posições em `trading/runner.py` quando
      `killswitch_active` (depende de T026)
- [ ] T028 [US2] Eventos `circuit_breaker_triggered` e `killswitch_toggled` em `utils/logger.py`
      (JSONL) e `utils/notifier.py` (Telegram)

**Checkpoint**: US1 e US2 funcionam de forma independente uma da outra.

---

## Phase 5: User Story 3 - Validação de estratégia fora da amostra (Priority: P3)

**Goal**: Relatório de backtest mostra métricas separadas para a janela de treino/otimização e para
a janela de validação out-of-sample, com veredito de aprovação automática baseado só na validação.

**Independent Test**: Ver `quickstart.md` → US3.

### Tests for User Story 3 ⚠️

- [ ] T029 [P] [US3] Teste: split treino/validação divide o histórico em janelas contíguas e não
      sobrepostas em `tests/test_backtesting_engine.py`
- [ ] T030 [P] [US3] Teste: critérios de aprovação automática (retorno > buy-hold, profit factor >
      1.2, drawdown aceitável, nº mínimo de trades) avaliados sobre `validation_metrics`, não
      `train_metrics`, em `tests/test_backtesting_engine.py`

### Implementation for User Story 3

- [ ] T031 [US3] Função de split treino/validação sobre o DataFrame de candles em
      `backtesting/engine.py` (ou novo `backtesting/validation.py` se o escopo justificar um arquivo
      separado — decisão na hora da implementação) (depende de T029 falhando)
- [ ] T032 [US3] Formalizar função de aprovação automática (já esboçada como item do `ROADMAP.md`
      Fase 1) aplicada à janela de validação (depende de T030 falhando, T031)
- [ ] T033 [US3] Exibir métricas in-sample vs out-of-sample lado a lado no relatório de backtest
      (`backtesting/engine.py` / `utils/display.py`) (depende de T031, T032)

**Checkpoint**: US1, US2 e US3 funcionam de forma independente.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentação e checklist de go-live — não altera comportamento do bot.

- [ ] T034 [P] Atualizar `ROADMAP.md` marcando os itens de reconciliação/circuit breaker/split
      treino-teste como concluídos, com link para esta spec
- [ ] T035 [P] Atualizar `STRATEGY_REVIEW.md` com o primeiro resultado real de validação
      out-of-sample rodado
- [ ] T036 Sincronizar `CLAUDE.md` e `AGENTS.md` no mesmo commit: novos comandos `kill`/`resume`,
      variável `MAX_CONSECUTIVE_LOSSES`, comportamento de reconciliação
- [ ] T037 Checklist de go-live antes de qualquer uso em `TRADING_MODE=live` desta feature:
      confirmar API key sem permissão de saque, rodar em paper mode por período mínimo definido pelo
      usuário, testar kill switch manualmente, documentar processo de rollback (`git revert` +
      restaurar backup de `state.json`)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências — CONCLUÍDA.
- **Foundational (Phase 2)**: Depende de Setup — BLOQUEIA todas as User Stories. T006/T007 ainda
  pendentes.
- **User Stories (Phase 3+)**: Todas dependem de Foundational completa.
  - US1 (P1) primeiro — é o MVP desta spec (gap P6 da constitution).
  - US2 (P2) e US3 (P3) são independentes entre si e de US1; podem seguir em paralelo ou em ordem de
    prioridade (P1 → P2 → P3), conforme `CLAUDE.md` prefere fatias pequenas e sequenciais.
- **Polish (Phase 6)**: Depende das User Stories que forem concluídas.

### User Story Dependencies

- **US1 (P1)**: Pode começar após Foundational. Sem dependência de US2/US3.
- **US2 (P2)**: Pode começar após Foundational. Sem dependência de US1/US3 (usa `state.json`, mas
  campos diferentes dos de US1 — sem conflito de merge esperado se implementadas em commits
  separados).
- **US3 (P3)**: Pode começar após Foundational. Sem dependência de US1/US2 (só toca
  `backtesting/engine.py`).

### Within Each User Story

- Testes MUST ser escritos e falhar antes da implementação (constitution III).
- Dentro de US1: T011/T012 (order manager) antes de T013 (reconciliação) fazer sentido de ponta a
  ponta, mas T013 não depende tecnicamente de T011/T012 — podem ser feitas em qualquer ordem.
- Dentro de US2: contador de perdas (T021-T024) e kill switch (T025-T027) são independentes entre
  si; T028 (eventos) depende de ambos existirem.
- Dentro de US3: T031 antes de T032 antes de T033 (cada uma depende da anterior).

### Parallel Opportunities

- T008, T009, T010 (testes de US1) podem ser escritos em paralelo — arquivos diferentes.
- T018, T019, T020 (testes de US2) podem ser escritos em paralelo.
- T029, T030 (testes de US3) podem ser escritos em paralelo.
- T034, T035 (Polish) podem rodar em paralelo.
- Seguindo o Fluxo Incremental do `CLAUDE.md`, mesmo com oportunidades de paralelismo, este projeto
  é mantido por uma pessoa — a prática real é sequencial, tópico por tópico, commit por commit.

---

## Implementation Strategy

### MVP First (User Story 1)

1. Completar Phase 1: Setup — CONCLUÍDA.
2. Completar Phase 2: Foundational (T006, T007 pendentes) — CRÍTICO, bloqueia tudo abaixo.
3. Completar Phase 3: User Story 1 (idempotência + reconciliação).
4. Validar US1 isoladamente em paper mode (`quickstart.md` → US1) antes de seguir.

### Incremental Delivery

1. Setup + Foundational → base pronta.
2. US1 → validar → é o MVP desta spec (fecha o gap P6 da constitution).
3. US2 → validar → circuit breaker mais completo.
4. US3 → validar → validação de estratégia mais rigorosa.
5. Polish → documentação e checklist de go-live.

Cada etapa segue o Fluxo Incremental do `CLAUDE.md`: tarefa pequena → testes → commit Conventional
Commit em português → push para `origin/main` → próxima tarefa.

---

## Notes

- [P] = arquivos diferentes, sem dependência.
- [Story] mapeia a tarefa à User Story correspondente, para rastreabilidade.
- Verificar que os testes falham antes de implementar (constitution III).
- Commit após cada tarefa ou grupo lógico pequeno — nunca uma User Story inteira em um commit só.
- Nenhuma tarefa desta lista habilita `TRADING_MODE=live` automaticamente — isso é sempre uma
  decisão manual do operador, após o checklist de T037.
