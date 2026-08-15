---

description: "Task list for 008-replay-acelerado-loop"
---

# Tasks: Replay Acelerado do Loop Real

**Input**: Design documents from `/specs/008-replay-acelerado-loop/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/cli.md](./contracts/cli.md)

**Tests**: Incluídos — o foco de teste mais crítico desta spec é negativo (isolamento nunca falha),
mesmo rigor test-first das specs anteriores (constitution III).

**Organization**: Tarefas agrupadas por User Story (US1-US2, ver `spec.md`).

---

## Phase 1: User Story 1 - Motor de decisão real com isolamento total (Priority: P1) 🎯 MVP

**Goal**: `trading/replay.py` roda o caminho de decisão real candle a candle, com garantia
absoluta de que os arquivos reais do bot nunca são tocados, mesmo em erro.

**Independent Test**: Ver `quickstart.md` → US1.

### Tests for User Story 1 ⚠️

- [X] T001 [P] [US1] Teste: `_isolated_order_manager_environment()` restaura
      `load_state`/`save_state`/`log_trade`/`log_event`/`send_telegram`/`TRADING_MODE` originais
      de `execution.order_manager` ao sair do context manager normalmente — novo
      `tests/test_replay.py`
- [X] T002 [P] [US1] Teste: `_isolated_order_manager_environment()` restaura os mesmos atributos
      MESMO quando uma exceção é levantada dentro do bloco — `tests/test_replay.py`
- [X] T003 [P] [US1] Teste: dentro do context manager, `OrderManager()` nunca chama a
      `load_state`/`save_state`/`log_trade`/`log_event`/`send_telegram` REAIS (mockadas com
      sentinelas que falham o teste se chamadas) — `tests/test_replay.py`
- [X] T004 [P] [US1] Teste: dentro do context manager, `TRADING_MODE` fica forçado `"paper"`
      independente do valor real configurado — `OrderManager` nunca entra no caminho
      `_live_buy`/`_live_sell` — `tests/test_replay.py`
- [X] T005 [P] [US1] Teste: `run_replay(symbol, timeframe, historical_df)` itera candle a candle
      chamando `handle_entry_candidate`/`handle_open_position` reais (mockados com spies) e
      retorna uma lista de trades coletados via `log_trade` isolado — `tests/test_replay.py`
- [X] T006 [P] [US1] Teste de integração: `run_replay()` com dados históricos reais (fixture
      sintética ampla, sem rede) produz um resultado coerente (trades com entry/exit/pnl válidos)
      sem lançar exceção — `tests/test_replay.py`

### Implementation for User Story 1

- [X] T007 [US1] Novo `trading/replay.py`: `_isolated_order_manager_environment()` (context
      manager, `try/finally`) — troca `TRADING_MODE`/`load_state`/`save_state`/`log_trade`/
      `log_event`/`send_telegram` em `execution.order_manager` (depende de T001 falhando, T002
      falhando, T003 falhando, T004 falhando)
- [X] T008 [US1] `trading/replay.py`: `run_replay(symbol, timeframe, candle_limit)` -- busca
      histórico via `fetch_ohlcv`, itera com `OrderManager` isolado chamando
      `handle_entry_candidate`/`handle_open_position` reais (mesmo padrão de iteração de
      `simulate_backtest`), coleta trades via `log_trade` isolado (depende de T005 falhando, T006
      falhando, T007)

**Checkpoint**: US1 completa e testável isoladamente — MVP desta spec. Isolamento comprovado por
teste, não só por design.

---

## Phase 2: User Story 2 - Comparação contra backtest (Priority: P2)

**Goal**: Relatório final compara replay contra um backtest simples do mesmo período.

**Independent Test**: Ver `quickstart.md` → US2.

### Tests for User Story 2 ⚠️

- [X] T009 [P] [US2] Teste: função de comparação recebe resultado do replay + resultado de
      `run_backtest` e retorna número de trades/retorno de cada lado — novo teste em
      `tests/test_replay.py`
- [X] T010 [P] [US2] Teste: comparação sem divergência relevante indica isso claramente, sem
      inventar diferenças — `tests/test_replay.py`

### Implementation for User Story 2

- [X] T011 [US2] `trading/replay.py`: função de comparação replay vs `run_backtest()` (já
      existente), notas textuais fixas para divergências conhecidas (depende de T009 falhando,
      T010 falhando)
- [X] T012 [US2] `main.py`: `cmd_replay()`, registra `"replay"` em `COMMANDS`, imprime relatório
      final via Rich (depende de T008, T011)

**Checkpoint**: US1 e US2 completas.

---

## Phase 3: Polish & Cross-Cutting Concerns

- [X] T013 Rodar `quickstart.md` completo (hash dos 4 arquivos reais antes/depois, inclusive
      forçando um erro) e confirmar isolamento total na prática, não só nos testes mockados
- [X] T014 [P] Atualizar `ROADMAP.md` Fase 5 item 4 com nota sobre o replay como aproximação
      parcial (não substitui forward test real, mas fecha parte do gap)
- [X] T015 [P] Atualizar `specs/BACKLOG.md` com a spec 008 (fora do backlog original, criada em
      resposta a uma pergunta do operador sobre alternativas a esperar operação paper real)
- [X] T016 Sincronizar `CLAUDE.md`/`AGENTS.md` com o novo comando `replay` e a nota de limitações
      conhecidas (cooldown, MTF)

---

## Dependencies & Execution Order

- **US1 (P1)**: MVP, independente.
- **US2 (P2)**: Depende de US1 (precisa do resultado do replay para comparar).
- **Polish**: Depende de US1+US2.

## Notes

- O requisito de isolamento (T001-T004) MUST ser verificado por teste antes de qualquer outra
  tarefa desta spec ser considerada segura para uso real — não é opcional, é o gate de segurança
  central (constitution Principle I).
- `execution/order_manager.py` e `trading/position_lifecycle.py` permanecem inalterados por esta
  spec inteira.
