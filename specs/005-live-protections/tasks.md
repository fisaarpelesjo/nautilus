---

description: "Task list for 005-live-protections"
---

# Tasks: Proteções Finais para Live

**Input**: Design documents from `/specs/005-live-protections/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/cli.md](./contracts/cli.md)

**Tests**: Incluídos — a constitution (III. Test Before Implement) exige critério de teste definido
antes de cada implementação. Dado que esta spec toca `execution/`/`trading/position_lifecycle.py`,
o rigor de teste é o mesmo já aplicado na spec 001 (paper mode, `clientOrderId` idempotente,
isolamento de erro via `safe_step`).

**Organization**: Tarefas agrupadas por User Story (US1-US4, ver `spec.md`) para permitir
implementação e validação independentes de cada uma.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependência)
- **[Story]**: A qual User Story a tarefa pertence (US1, US2, US3, US4)
- Caminhos de arquivo reais do repositório incluídos em cada descrição

## Path Conventions

Projeto único na raiz do repositório (mesmo das specs 001-004) — ver `plan.md` → Project Structure
para o mapeamento completo de módulos.

---

## Phase 1: Setup

**Purpose**: Nenhuma — ambiente já configurado pelas specs anteriores.

**Checkpoint**: Ambiente já pronto.

---

## Phase 2: Foundational

**Purpose**: Nenhuma tarefa bloqueante cross-story — US1/US2/US3 são independentes entre si. US4
reusa a busca de order book de US3 para o preço da ordem limit (ver `research.md`), mas isso é uma
dependência direta de US4 em US3, não uma infraestrutura compartilhada nova.

**Checkpoint**: N/A.

---

## Phase 3: User Story 1 - Ver claramente o que está em jogo antes de operar (Priority: P1) 🎯 MVP

**Goal**: Um resumo (pares, saldo real, limites) é exibido antes do bot iniciar o loop principal em
`TRADING_MODE=live`.

**Independent Test**: Ver `quickstart.md` → US1.

### Tests for User Story 1 ⚠️

- [ ] T001 [P] [US1] Teste: `_print_live_confirmation_banner(...)` exibe pares, saldo,
      `MAX_ORDER_SIZE_USDT`, `MAX_POSITIONS` e os limites de perda configurados — novo
      `tests/test_runner_live_banner.py`
- [ ] T002 [P] [US1] Teste: `run()` (`trading/runner.py`) chama o banner quando
      `TRADING_MODE == "live"`, ANTES do loop principal — `tests/test_runner_live_banner.py`
- [ ] T003 [P] [US1] Teste: `run()` NÃO chama o banner quando `TRADING_MODE == "paper"` —
      `tests/test_runner_live_banner.py`
- [ ] T004 [P] [US1] Teste: o banner grava um evento `live_session_started` via `log_event`, além do
      `console.print` — `tests/test_runner_live_banner.py`

### Implementation for User Story 1

- [ ] T005 [US1] `_print_live_confirmation_banner(pairs, balance, manager)` em `trading/runner.py`:
      monta e imprime o resumo, chama `log_event("live_session_started", ...)` isolado via
      `safe_step` (depende de T001 falhando, T004 falhando)
- [ ] T006 [US1] `run()` chama o banner condicionalmente quando `TRADING_MODE == "live"`, depois de
      `OrderManager()` já criado (para ter saldo real) e antes do loop principal (depende de T002
      falhando, T003 falhando, T005)

**Checkpoint**: US1 completa e testável de forma independente — `python main.py bot` em live mostra o
resumo antes de qualquer ordem.

---

## Phase 4: User Story 2 - Bloquear entradas após degradação sustentada (Priority: P2)

**Goal**: Limites semanal e mensal de perda, independentes do diário/circuit breaker já existentes —
e correção do bug do saldo de referência hardcoded no limite diário.

**Independent Test**: Ver `quickstart.md` → US2.

### Tests for User Story 2 ⚠️

- [ ] T007 [P] [US2] Teste de regressão: `is_daily_limit_hit()` usa `daily_reference_balance` real
      (não `* 1000.0` hardcoded) — com saldo de referência $5000 e `DAILY_DRAWDOWN_LIMIT=0.05`, o
      limite deve ser $250, não $50 — em `tests/test_order_manager_safety.py`
- [ ] T008 [P] [US2] Teste: `is_weekly_limit_hit()`/`is_monthly_limit_hit()` calculam contra
      `weekly_reference_balance`/`monthly_reference_balance` — `tests/test_order_manager_safety.py`
- [ ] T009 [P] [US2] Teste: `weekly_pnl`/`monthly_pnl` resetam de forma independente um do outro e do
      diário, na virada do respectivo período — `tests/test_order_manager_safety.py`
- [ ] T010 [P] [US2] Teste: `handle_entry_candidate` bloqueia com `"limite semanal"`/`"limite mensal"`
      quando os respectivos limites são atingidos, mesmo com o diário e o circuit breaker OK — em
      `tests/test_position_lifecycle.py`
- [ ] T011 [P] [US2] Teste: `validate_config()` rejeita `WEEKLY_DRAWDOWN_LIMIT < DAILY_DRAWDOWN_LIMIT`
      e `MONTHLY_DRAWDOWN_LIMIT < WEEKLY_DRAWDOWN_LIMIT` — em `tests/test_settings_validation.py`

### Implementation for User Story 2

- [ ] T012 [US2] `WEEKLY_DRAWDOWN_LIMIT` (default `0.10`), `MONTHLY_DRAWDOWN_LIMIT` (default `0.20`)
      em `config/settings.py`, com a validação de consistência (depende de T011 falhando)
- [ ] T013 [US2] `OrderManager._reference_balance()`: saldo real, paper via `self.paper_balance_usdt`,
      live via `fetch_balance()` — mesma bifurcação de `trading/position_lifecycle.py`
      `_current_balance()`, duplicada conscientemente para evitar import circular (ver `research.md`)
- [ ] T014 [US2] Campos novos em `OrderManager`/`state.json`: `daily_reference_balance`,
      `weekly_pnl`/`weekly_reset_date`/`weekly_reference_balance`,
      `monthly_pnl`/`monthly_reset_date`/`monthly_reference_balance` — `_restore_state`/
      `_persist_state` estendidos (depende de T013)
- [ ] T015 [US2] `is_daily_limit_hit()` corrigido para usar `daily_reference_balance` (fecha o bug de
      T007); `is_weekly_limit_hit()`/`is_monthly_limit_hit()` novos, mesmo padrão (depende de T007
      falhando, T008 falhando, T014)
- [ ] T016 [US2] `_check_weekly_reset()`/`_check_monthly_reset()` (mesmo padrão de
      `_check_daily_reset`), capturando novo `*_reference_balance` a cada reset (depende de T009
      falhando, T015)
- [ ] T017 [US2] `_paper_sell`/`_live_sell` acumulam `weekly_pnl`/`monthly_pnl` junto com `daily_pnl`
      já existente (depende de T016)
- [ ] T018 [US2] `handle_entry_candidate` (`trading/position_lifecycle.py`) ganha blockers
      `"limite semanal"`/`"limite mensal"` (depende de T010 falhando, T017)

**Checkpoint**: US1 e US2 completas e independentes. Bug do limite diário corrigido.

---

## Phase 5: User Story 3 - Evitar slippage severo em pares com pouca liquidez (Priority: P3)

**Goal**: Entradas são bloqueadas quando o spread ou a profundidade do order book estão fora dos
limites configurados.

**Independent Test**: Ver `quickstart.md` → US3.

### Tests for User Story 3 ⚠️

- [ ] T019 [P] [US3] Teste: `check_liquidity(symbol, order_size_usdt)` bloqueia (`approved=False`)
      quando o spread do order book mockado excede `MAX_SPREAD_PCT_ENTRY` — novo
      `tests/test_liquidity.py`
- [ ] T020 [P] [US3] Teste: `check_liquidity` bloqueia quando a profundidade do lado ask fica abaixo
      de `MIN_ORDERBOOK_DEPTH_USDT` — `tests/test_liquidity.py`
- [ ] T021 [P] [US3] Teste: `check_liquidity` trata falha ao buscar o order book (exceção) como
      bloqueio (`approved=False`, motivo `"liquidez indisponivel"`), não aprovação por omissão —
      `tests/test_liquidity.py`
- [ ] T022 [P] [US3] Teste: `check_liquidity` aprova quando spread e profundidade estão dentro dos
      limites — `tests/test_liquidity.py`
- [ ] T023 [P] [US3] Teste: `handle_entry_candidate` inclui o blocker `"liquidez"` (com o motivo de
      `check_liquidity`) quando reprovado, verificado depois do MTF na ordem de checagens — em
      `tests/test_position_lifecycle.py`

### Implementation for User Story 3

- [ ] T024 [US3] `MAX_SPREAD_PCT_ENTRY` (default `0.005`), `MIN_ORDERBOOK_DEPTH_USDT` (default
      `3 * MAX_ORDER_SIZE_USDT`) em `config/settings.py`
- [ ] T025 [US3] Novo `execution/liquidity.py`: dataclass `LiquidityCheck` + `check_liquidity(symbol,
      order_size_usdt)` via `exchange.fetch_order_book` (depende de T019 falhando, T020 falhando,
      T021 falhando, T022 falhando, T024)
- [ ] T026 [US3] `handle_entry_candidate` chama `check_liquidity` depois do MTF confirmado e antes do
      saldo (mesma posição "checagem cara por último" já estabelecida), adiciona `"liquidez"` aos
      `blockers` quando reprovado (depende de T023 falhando, T025)

**Checkpoint**: US1, US2 e US3 completas e independentes.

---

## Phase 6: User Story 4 - Ordens limit com rastreamento de preenchimento parcial (Priority: P4)

**Goal**: Capacidade opcional (`USE_LIMIT_ORDERS=false` por padrão) de enviar ordens limit em vez de
mercado, com rastreamento correto de preenchimento parcial ao longo de ciclos.

**Independent Test**: Ver `quickstart.md` → US4. Validação final de comportamento real de
preenchimento parcial fica em Binance Testnet — nunca com fundos reais (Constitution, princípio I).

### Tests for User Story 4 ⚠️

- [ ] T027 [P] [US4] Teste: com `USE_LIMIT_ORDERS=false` (default), `_live_buy` continua chamando
      `create_market_buy_order` exatamente como hoje — comportamento idêntico ao já validado —
      novo `tests/test_limit_orders.py`
- [ ] T028 [P] [US4] Teste: com `USE_LIMIT_ORDERS=true`, `_live_buy` chama `create_limit_buy_order`
      com preço = melhor `ask` do order book e `clientOrderId` idempotente (reusa
      `pending_open_client_order_ids`, mesmo padrão já existente) — `tests/test_limit_orders.py`
- [ ] T029 [P] [US4] Teste: `check_pending_limit_orders()` abre a posição com a quantidade cheia
      quando `fetch_order` reporta `filled == amount` — `tests/test_limit_orders.py`
- [ ] T030 [P] [US4] Teste: preenchimento parcial (`0 < filled < amount`) + `LIMIT_ORDER_TIMEOUT_CYCLES`
      atingido → cancela o restante e abre a posição só com a quantidade preenchida —
      `tests/test_limit_orders.py`
- [ ] T031 [P] [US4] Teste: sem nenhum preenchimento (`filled == 0`) + timeout atingido → cancela e
      descarta a ordem pendente, sem posição aberta — `tests/test_limit_orders.py`
- [ ] T032 [P] [US4] Teste: `pending_limit_orders` sobrevive a um restart simulado (persistido em
      `state.json`, `clientOrderId` reusado na consulta seguinte, não gerado de novo) —
      `tests/test_limit_orders.py`

### Implementation for User Story 4

- [ ] T033 [US4] `USE_LIMIT_ORDERS` (default `false`), `LIMIT_ORDER_TIMEOUT_CYCLES` (default `3`) em
      `config/settings.py` (depende de T027 falhando)
- [ ] T034 [US4] Dataclass `PendingLimitOrder` (`symbol`, `client_order_id`, `limit_price`,
      `requested_quantity`, `placed_at_cycle`) + `pending_limit_orders: Dict[str, PendingLimitOrder]`
      em `OrderManager`, persistido em `state.json` (depende de T032 falhando)
- [ ] T035 [US4] `_live_buy` ganha caminho de ordem limit quando `USE_LIMIT_ORDERS=true`: reusa o
      order book já buscado por `check_liquidity` (US3) para o preço, envia `create_limit_buy_order`
      com `clientOrderId` idempotente, registra em `pending_limit_orders` em vez de `positions`
      diretamente (depende de T028 falhando, T033, T034, T025)
- [ ] T036 [US4] `OrderManager.check_pending_limit_orders()`: para cada ordem pendente, `fetch_order`
      via `clientOrderId`; preenchimento completo → move para `positions`; parcial + timeout →
      `cancel_order` do restante, abre posição com quantidade preenchida; zero + timeout → cancela e
      remove de `pending_limit_orders` (depende de T029 falhando, T030 falhando, T031 falhando, T034)
- [ ] T037 [US4] `trading/runner.py` chama `manager.check_pending_limit_orders()` uma vez por ciclo,
      mesmo padrão de chamada da reconciliação periódica (depende de T036)

**Checkpoint**: US1, US2, US3 e US4 funcionam de forma independente (à parte da dependência
documentada de US4 no order book de US3). `USE_LIMIT_ORDERS=false` preserva 100% do comportamento
a mercado já validado — suíte completa deve passar sem nenhuma mudança de comportamento default.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentação — não altera comportamento do bot além do já implementado nas User Stories.

- [ ] T038 [P] Atualizar `ROADMAP.md` marcando Fase 6 itens 1 (confirmação explícita), 3
      (liquidez/spread), 4 (execução inteligente — parcial, ver nota abaixo) e 5 (limites
      semanal/mensal) como concluídos/atualizados, com link para esta spec
- [ ] T039 [P] Atualizar `specs/BACKLOG.md`: status da spec 005 para concluída
- [ ] T040 Sincronizar `CLAUDE.md` e `AGENTS.md` no mesmo commit: novas variáveis de `.env`
      (`WEEKLY_DRAWDOWN_LIMIT`, `MONTHLY_DRAWDOWN_LIMIT`, `MAX_SPREAD_PCT_ENTRY`,
      `MIN_ORDERBOOK_DEPTH_USDT`, `USE_LIMIT_ORDERS`, `LIMIT_ORDER_TIMEOUT_CYCLES`), banner de
      confirmação live, nova seção sobre liquidez/ordens limit
- [ ] T041 Rodar `quickstart.md` (US1-US3 em paper mode/mockado; US4 só a máquina de estado
      mockada — preenchimento parcial real fica pendente de validação em Testnet pelo operador,
      registrado explicitamente como pendência, não como concluído) e registrar observações
      relevantes em `STRATEGY_REVIEW.md` ou `ROADMAP.md` conforme o caso

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem tarefas.
- **Foundational (Phase 2)**: Sem tarefas — nenhuma infraestrutura compartilhada nova além do que
  cada User Story já traz.
- **User Stories (Phase 3+)**: US1, US2, US3 são totalmente independentes entre si. US4 depende de
  US3 (T025, `check_liquidity`/order book) para o preço da ordem limit.
- **Polish (Phase 7)**: Depende das User Stories que forem concluídas.

### User Story Dependencies

- **US1 (P1)**: Totalmente independente. MVP desta spec.
- **US2 (P2)**: Totalmente independente de US1/US3/US4.
- **US3 (P3)**: Totalmente independente de US1/US2. US4 depende dela.
- **US4 (P4)**: Depende de US3 (T025) para reusar o order book já buscado. Não depende de US1/US2.

### Within Each User Story

- Testes MUST ser escritos e falhar antes da implementação (constitution III).
- Dentro de US2: T012/T013 podem ser paralelas; T014 depende de T013; T015 depende de T014; T016
  depende de T015; T017 depende de T016; T018 depende de T017.
- Dentro de US3: T024/T025 antes de T026 (checagem precisa existir antes de integrar ao blocker).
- Dentro de US4: T033/T034 antes de T035; T035 antes de T036; T036 antes de T037. T035 depende
  também de T025 (US3), a única dependência cross-story real desta spec.

### Parallel Opportunities

- T001-T004 (testes de US1) podem ser escritos em paralelo.
- T007-T011 (testes de US2) podem ser escritos em paralelo.
- T019-T023 (testes de US3) podem ser escritos em paralelo.
- T027-T032 (testes de US4) podem ser escritos em paralelo.
- T038, T039 (Polish) podem rodar em paralelo.
- Seguindo o Fluxo Incremental do `CLAUDE.md`, a prática real é sequencial, tópico por tópico, commit
  por commit — com atenção redobrada dentro de US2/US4 dado o toque em `execution/`.

---

## Implementation Strategy

### MVP First (User Story 1)

1. Completar Phase 1/2: Setup/Foundational — nenhuma tarefa.
2. Completar Phase 3: User Story 1 (banner de confirmação).
3. Validar US1 isoladamente (`quickstart.md` → US1, em Testnet) antes de seguir.

### Incremental Delivery

1. US1 → validar → é o MVP desta spec (mais simples, maior redução de risco por esforço).
2. US2 → validar → limites semanal/mensal + bug do limite diário corrigido.
3. US3 → validar → checagem de liquidez/spread.
4. US4 → validar (paper mode para a máquina de estado; Testnet para o comportamento real de
   preenchimento parcial) → ordens limit, capacidade opcional desligada por padrão.
5. Polish → documentação (`ROADMAP.md`, `BACKLOG.md`, `CLAUDE.md`/`AGENTS.md`).

Cada etapa segue o Fluxo Incremental do `CLAUDE.md`: tarefa pequena → testes → commit Conventional
Commit em português → push para `origin/main` → próxima tarefa. Seguindo o padrão estabelecido nas
specs 001-004, `/code-review medium` roda sobre o diff acumulado antes do commit final de cada etapa
significativa — com possível uso de `/code-review high` especificamente para US2/US4 (achado direto
em `execution/order_manager.py`), dado o histórico de achados críticos que essa área já teve na
spec 001.

---

## Notes

- [P] = arquivos diferentes, sem dependência.
- [Story] mapeia a tarefa à User Story correspondente, para rastreabilidade.
- Verificar que os testes falham antes de implementar (constitution III).
- Commit após cada tarefa ou grupo lógico pequeno — nunca uma User Story inteira em um commit só.
- **Nenhuma tarefa desta lista habilita `TRADING_MODE=live` automaticamente** — isso continua sendo
  sempre uma decisão manual do operador, após o checklist de go-live (spec 001, T037) revisado com os
  itens novos desta spec.
- `USE_LIMIT_ORDERS=false` é o default em toda tarefa desta spec — a suíte de testes completa deve
  continuar passando sem nenhuma mudança de comportamento quando essa flag não é alterada.
