---

description: "Task list for 010-paridade-custos-paper"
---

# Tasks: Paridade de Custos entre Paper e Backtest

**Input**: Design documents from `/specs/010-paridade-custos-paper/`

**Tests**: Incluídos — mesmo rigor test-first das specs anteriores (constitution III).

---

## Phase 1: User Story 1 - Slippage realista em entradas e saídas paper (Priority: P1) 🎯 MVP

- [X] T001 [P] [US1] Teste: `open_long()` em paper mode grava `Position.entry_price = preco_mercado *
      (1 + BACKTEST_SLIPPAGE_PCT)` para um preço conhecido — `tests/test_order_manager_safety.py`
- [X] T002 [P] [US1] Teste: `close_position(..., current_price=X)` em paper mode usa
      `X * (1 - BACKTEST_SLIPPAGE_PCT)` como preço de saída efetivo (afeta PnL registrado) —
      `tests/test_order_manager_safety.py`
- [X] T003 [P] [US1] Teste: `close_position()` sem `current_price` (fallback para
      `pos.stop_loss`/`pos.take_profit`) também aplica slippage ao preço de saída — mesmo
      tratamento que `backtesting/engine.py` já dá a saídas por stop/take —
      `tests/test_order_manager_safety.py`
- [X] T004 [US1] `execution/order_manager.py` `_paper_buy()`/`_paper_sell()`: aplica
      `BACKTEST_SLIPPAGE_PCT` ao preço de entrada/saída (depende de T001-T003 falhando)
- [X] T005 [P] [US1] Teste: com `BACKTEST_SLIPPAGE_PCT=0`, preço de entrada/saída paper é idêntico
      ao preço de mercado bruto (FR-008, regressão) — `tests/test_order_manager_safety.py`

**Checkpoint**: US1 completa — slippage já reflete no PnL paper, mesmo sem a taxa ainda.

---

## Phase 2: User Story 2 - Taxa realista em entradas e saídas paper (Priority: P1)

- [X] T006 [P] [US2] Teste: `open_long()` em paper mode debita `notional + (notional *
      BACKTEST_FEE_RATE)` do `paper_balance_usdt`, não só o nocional — `tests/test_order_manager_safety.py`
- [X] T007 [P] [US2] Teste: `close_position()` em paper mode credita `gross_exit - (gross_exit *
      BACKTEST_FEE_RATE)` ao `paper_balance_usdt`, e o `pnl_usdt` gravado em `data/trades.csv`
      (via `log_trade`) desconta taxa de entrada e de saída — `tests/test_order_manager_safety.py`
- [X] T008 [P] [US2] Teste: saldo paper insuficiente para `notional + fee` (mas suficiente só para
      o nocional) bloqueia a compra — FR-007 — `tests/test_order_manager_safety.py`
- [X] T009 [US2] `execution/order_manager.py` `_paper_buy()`/`_paper_sell()`: aplica
      `BACKTEST_FEE_RATE` sobre o nocional de entrada/saída, atualiza a checagem de saldo
      suficiente para considerar `notional + fee` (depende de T006-T008 falhando)
- [X] T010 [P] [US2] Teste: com `BACKTEST_FEE_RATE=0`, custo/proceeds paper são idênticos ao
      nocional puro (FR-008, regressão) — `tests/test_order_manager_safety.py`
- [X] T011 [US2] Teste: paridade percentual — para o mesmo par de preços de mercado
      entrada/saída e mesmos `BACKTEST_FEE_RATE`/`BACKTEST_SLIPPAGE_PCT`, o `pnl_pct` de um trade
      paper fechado bate com o `pnl_pct` que `simulate_backtest()` produz (SC-001; comparação
      percentual, não em dólar absoluto — ver `research.md` para o porquê) —
      `tests/test_order_manager_safety.py`

**Checkpoint**: US1 e US2 completas — MVP desta spec (paridade de custo total paper vs backtest).

---

## Phase 3: Polish & Cross-Cutting Concerns

- [X] T012 Auditar `tests/test_order_manager_safety.py` (e qualquer outro teste que chame
      `open_long`/`close_position` em paper mode) por asserções que assumem custo exato sem
      taxa/slippage; atualizar os valores esperados (não contornar com mocks que escondem a
      mudança)
- [X] T013 [P] Adicionar `BACKTEST_FEE_RATE`/`BACKTEST_SLIPPAGE_PCT` à tabela de variáveis de
      ambiente em `CLAUDE.md`/`AGENTS.md`, atualizando a descrição para deixar claro que agora
      afetam paper mode também, não só backtest
- [X] T014 [P] Atualizar `specs/BACKLOG.md`: marcar spec 010 concluída, registrar como achado de
      auditoria (fora do `ROADMAP.md` original, mesmo padrão da spec 008/009)
- [X] T015 Marcar `spec.md` desta spec como Concluída

---

## Dependencies & Execution Order

US1 e US2 são fortemente relacionadas (mesma dupla de funções, mesmo par de commits pequenos) mas
tecnicamente independentes — US1 (slippage) pode ser implementada e commitada sem US2 (fee), e
vice-versa. T011 (paridade com o backtest) só faz sentido depois de ambas estarem implementadas,
por isso vive em US2 como o item de fechamento.

## Notes

- Nenhuma task toca `risk/manager.py` nem `_live_buy()`/`_live_sell()` — ver `research.md` para a
  decisão de manter `risk.quantity` intocado.
- Toda validação é unitária, sem dependência de dados reais da Binance nem tempo real passando
  (FR de independência já expresso na spec).
