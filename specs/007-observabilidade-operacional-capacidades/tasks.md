---

description: "Task list for 007-observabilidade-operacional-capacidades"
---

# Tasks: Observabilidade Operacional

**Input**: Design documents from `/specs/007-observabilidade-operacional-capacidades/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/cli.md](./contracts/cli.md)

**Tests**: Incluídos — mesmo rigor test-first das specs anteriores (constitution III).

**Organization**: Tarefas agrupadas por User Story (US1-US5, ver `spec.md`).

---

## Phase 1: User Story 1 - Não confundir caixa livre com patrimônio total (Priority: P1) 🎯 MVP

**Goal**: `trading/portfolio.py` centraliza caixa/posições/patrimônio/PnLs; `status` exibe os 6
valores distintos.

**Independent Test**: Ver `quickstart.md` → US1.

### Tests for User Story 1 ⚠️

- [X] T001 [P] [US1] Teste: `compute_portfolio_snapshot()` sem posições retorna
      `total_equity == free_cash` e `unrealized_pnl == 0.0` — novo `tests/test_portfolio.py`
- [X] T002 [P] [US1] Teste: com uma posição aberta e preço atual conhecido, `positions_value`,
      `total_equity`, `unrealized_pnl` e `total_pnl` calculados corretamente — `tests/test_portfolio.py`
- [X] T003 [P] [US1] Teste: quando `fetch_ticker` falha para uma posição, `positions_value`/
      `total_equity`/`unrealized_pnl`/`total_pnl` viram `None` (não `0.0`) e o símbolo aparece em
      `positions_with_unknown_price` — `tests/test_portfolio.py`
- [X] T004 [P] [US1] Teste: `cmd_status()` chama `compute_portfolio_snapshot()` e exibe caixa/
      posições/patrimônio/PnLs — `tests/test_main_status.py` (novo)

### Implementation for User Story 1

- [X] T005 [US1] Novo `trading/portfolio.py`: dataclass `PortfolioSnapshot` +
      `compute_portfolio_snapshot(manager)` — bifurcação paper/live igual a `_current_balance`/
      `_reference_balance`, preço indisponível vira `None` propagado (depende de T001 falhando, T002
      falhando, T003 falhando)
- [X] T006 [US1] `main.py`/`utils/display.py`: `cmd_status()` chama `compute_portfolio_snapshot()` e
      exibe os 6 valores; trata `None` como "indisponível" na exibição (depende de T004 falhando, T005)

**Checkpoint**: US1 completa e testável isoladamente — MVP desta spec.

---

## Phase 2: User Story 2 - Não confundir edge com saldo real (Priority: P2)

**Goal**: `python main.py edge` exibe contexto explícito de simulação.

**Independent Test**: Ver `quickstart.md` → US2.

### Tests for User Story 2 ⚠️

- [X] T007 [P] [US2] Teste: `run_edge_report()` chama uma função de contexto de simulação com
      symbol/timeframe/período/capital inicial antes de `print_report()` — novo
      `tests/test_backtesting_validation_context.py`

### Implementation for User Story 2

- [X] T008 [US2] `utils/display.py`: nova `simulation_context_banner(symbol, timeframe, period_start,
      period_end, initial_capital)` — modo "backtest simulado" + aviso de que não reflete
      `data/state.json` (depende de T007 falhando)
- [X] T009 [US2] `backtesting/validation.py` `run_edge_report()`: chama o banner antes de
      `print_report()` (depende de T008)

**Checkpoint**: US1 e US2 completas e independentes.

---

## Phase 3: User Story 3 - Painel único sem vasculhar múltiplos comandos (Priority: P3)

**Goal**: `python main.py painel` agrega patrimônio, posições, últimas operações, últimos sinais e
bloqueios recentes.

**Independent Test**: Ver `quickstart.md` → US3.

### Tests for User Story 3 ⚠️

- [X] T010 [P] [US3] Teste: novo leitor tolerante `data/trade_store.py` `load_recent_trades(n)` —
      arquivo ausente retorna lista vazia, não erro — novo `tests/test_trade_store.py`
- [X] T011 [P] [US3] Teste: novo leitor tolerante `data/signal_store.py` `load_recent_signals(n)` —
      mesmo comportamento — novo `tests/test_signal_store.py`
- [X] T012 [P] [US3] Teste: `print_panel()` com histórico completo (fixtures sintéticas) imprime
      todas as seções sem erro — novo `tests/test_panel.py`
- [X] T013 [P] [US3] Teste: `print_panel()` sem nenhum histórico mostra estado vazio explícito em
      cada seção, não lança exceção — `tests/test_panel.py`
- [X] T014 [P] [US3] Teste: `main.py` registra o comando `painel` — `tests/test_main_backtest.py`
      (mesmo arquivo já usado para outros comandos de `main.py`)

### Implementation for User Story 3

- [X] T015 [US3] `data/trade_store.py`: `load_recent_trades(n=10)`, mesmo padrão de
      `_load_decisions()` (`Path.exists()` → lista vazia) (depende de T010 falhando)
- [X] T016 [US3] `data/signal_store.py`: `load_recent_signals(n=10)`, mesmo padrão (depende de T011
      falhando)
- [X] T017 [US3] Novo `trading/panel.py`: `print_panel()` agrega `compute_portfolio_snapshot()`
      (US1), posições abertas, `load_recent_trades()`, `load_recent_signals()`,
      `analyze_decisions()` (já existente, spec 004) (depende de T012 falhando, T013 falhando, T015,
      T016)
- [X] T018 [US3] `main.py`: `cmd_painel()`, registra `"painel"` em `COMMANDS` (depende de T014
      falhando, T017)

**Checkpoint**: US1, US2 e US3 completas e independentes.

---

## Phase 4: User Story 4 - Entender por que um par não está entrando (Priority: P4)

**Goal**: `python main.py debug <PAR>` explica cada condição de entrada.

**Independent Test**: Ver `quickstart.md` → US4.

### Tests for User Story 4 ⚠️

- [X] T019 [P] [US4] Teste: `full_diagnosis()` inclui todos os campos de `signal_checks()` mais
      `mtf_ok`/`regime`/`high_volatility`/`cooldown_active` — novo `tests/test_strategy_diagnostics.py`
- [X] T020 [P] [US4] Teste: `full_diagnosis()` com `cooldown_active=True` identifica cooldown como
      motivo de bloqueio, não escondido atrás de outras condições — `tests/test_strategy_diagnostics.py`
- [X] T021 [P] [US4] Teste: `main.py` registra o comando `debug` — `tests/test_main_backtest.py`
- [X] T022 [P] [US4] Teste: `cmd_debug()` busca candles, calcula indicadores e imprime cada condição
      com seu valor — novo `tests/test_main_debug.py`

### Implementation for User Story 4

- [X] T023 [US4] `strategy/diagnostics.py`: `full_diagnosis(symbol, indicators, previous,
      current_price, strategy, mtf_ok, regime, high_volatility, cooldown_active) -> dict` — estende
      `signal_checks()`, não duplica (depende de T019 falhando, T020 falhando)
- [X] T024 [US4] `main.py`: `cmd_debug()` — busca par via `sys.argv`, `fetch_ohlcv`,
      `calculate_indicators`, `mtf_confirmed`, `manager.is_in_cooldown`, imprime `full_diagnosis()`
      formatado; registra `"debug"` em `COMMANDS` (depende de T021 falhando, T022 falhando, T023)

**Checkpoint**: US1-US4 completas e independentes.

---

## Phase 5: User Story 5 - Ver visualmente o que os números não mostram (Priority: P5)

**Goal**: `python main.py performance` gera gráficos de capital/drawdown/PnL por par; `chart` ganha
marcadores de trades reais.

**Independent Test**: Ver `quickstart.md` → US5.

### Tests for User Story 5 ⚠️

- [X] T025 [P] [US5] Teste: `build_performance_figures(trades)` retorna 3 figuras Plotly (capital,
      drawdown, PnL por par) a partir de uma lista sintética de `Trade` — novo
      `tests/test_performance_charts.py`
- [X] T026 [P] [US5] Teste: `build_performance_figures([])` (sem trades) retorna estado vazio
      explícito, não lança exceção — `tests/test_performance_charts.py`
- [X] T027 [P] [US5] Teste: `main.py` registra o comando `performance`/`desempenho` —
      `tests/test_main_backtest.py`
- [X] T028 [P] [US5] Teste: camada de marcadores reais em `utils/chart.py` `_build_figure()` lê
      trades de `data/trades.csv` (mockado) e adiciona um trace visualmente distinto dos marcadores
      teóricos já existentes — novo `tests/test_chart_real_trades.py`

### Implementation for User Story 5

- [X] T029 [US5] Novo `backtesting/performance_charts.py`: `build_performance_figures(trades)` —
      curva de capital, drawdown, PnL por par, via `plotly` (depende de T025 falhando, T026 falhando)
- [X] T030 [US5] `main.py`: `cmd_performance()` — lê `data/trades.csv` via `load_recent_trades`
      (ou leitura completa equivalente), gera HTML combinado, abre no navegador; registra
      `"performance"`/`"desempenho"` em `COMMANDS` (depende de T027 falhando, T029)
- [X] T031 [US5] `utils/chart.py` `_build_figure()`: nova camada de marcadores de trades reais lidos
      de `data/trades.csv`, trace Plotly distinto (cor/símbolo diferente) dos marcadores teóricos já
      existentes (depende de T028 falhando)

**Checkpoint**: Todas as 5 User Stories completas e independentes.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T032 [P] Atualizar `ROADMAP.md` marcando Fase 5 itens 2, 3, 5, 6, 7 como concluídos, com link
      para esta spec (itens 1 e 4 permanecem pendentes — fora de escopo)
- [X] T033 [P] Atualizar `specs/BACKLOG.md`: status da spec 007 para "parte autônoma concluída"
- [X] T034 Sincronizar `CLAUDE.md` e `AGENTS.md` no mesmo commit: novos comandos (`painel`, `debug`,
      `performance`), nova seção sobre patrimônio operacional/diagnóstico
- [ ] T035 Rodar `quickstart.md` (todos os passos usam fixtures sintéticas ou dados públicos,
      executáveis sem depender do operador) e registrar observações relevantes em
      `STRATEGY_REVIEW.md`/`ROADMAP.md`

---

## Dependencies & Execution Order

### User Story Dependencies

- **US1 (P1)**: Totalmente independente. MVP desta spec.
- **US2 (P2)**: Totalmente independente de US1/US3/US4/US5.
- **US3 (P3)**: Depende de US1 (`compute_portfolio_snapshot`) para a seção de patrimônio do painel.
- **US4 (P4)**: Totalmente independente das demais.
- **US5 (P5)**: Depende de US3 (`load_recent_trades`) para os gráficos de performance a partir de
  `data/trades.csv`, embora `build_performance_figures()` em si aceite uma lista de `Trade` direta
  (testável isoladamente).

### Parallel Opportunities

- T001-T004 (US1), T007 (US2), T010-T014 (US3), T019-T022 (US4), T025-T028 (US5) — testes dentro de
  cada fase podem ser escritos em paralelo.
- T032/T033 (Polish) podem rodar em paralelo.
- Seguindo o Fluxo Incremental do `CLAUDE.md`, a prática real é sequencial, tópico por tópico,
  commit por commit.

---

## Implementation Strategy

### MVP First (User Story 1)

1. Completar Phase 1 (US1 — patrimônio operacional). Corrige a confusão mais citada no ROADMAP —
   MVP desta spec.
2. Validar isoladamente (`quickstart.md` → US1) antes de seguir.

### Incremental Delivery

1. US1 (MVP) → validar.
2. US2 → validar.
3. US3 (depende de US1) → validar.
4. US4 → validar.
5. US5 (depende de US3) → validar.
6. Polish → documentação.

Cada etapa segue o Fluxo Incremental do `CLAUDE.md`: tarefa pequena → testes → commit Conventional
Commit em português → push para `origin/main` → próxima tarefa. `/code-review medium` roda sobre o
diff acumulado antes do commit final de cada User Story.

---

## Notes

- Toda esta spec é read-only — nenhuma tarefa toca `execution/`, `risk/manager.py` ou o loop
  principal do bot.
- PnL/patrimônio não realizado MUST propagar `None` (não `0.0`) quando um preço não pode ser
  buscado — consistente com o mesmo princípio já aplicado em `_current_balance`/`_reference_balance`.
