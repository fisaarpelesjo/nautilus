---

description: "Task list for 006-evolucao-estrategia-novas"
---

# Tasks: Evolução da Estratégia

**Input**: Design documents from `/specs/006-evolucao-estrategia-novas/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/cli.md](./contracts/cli.md)

**Tests**: Incluídos — mesmo rigor test-first das specs anteriores (constitution III).

**Organization**: Tarefas agrupadas por User Story (US1-US5, ver `spec.md`).

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Foundational

**Purpose**: `run_backtest()` precisa aceitar uma estratégia como parâmetro antes de US4/US5
poderem existir — dependência compartilhada, não pertence a nenhuma User Story sozinha.

### Tests for Foundational ⚠️

- [ ] T001 [P] Teste: `run_backtest(symbol, timeframe, strategy=None)` sem `strategy` continua
      usando `EmaRsiStrategy()` (comportamento hoje) — `tests/test_backtesting_engine.py`
- [ ] T002 [P] Teste: `run_backtest(..., strategy=<outra estrategia>)` usa a estratégia passada,
      não `EmaRsiStrategy()` — `tests/test_backtesting_engine.py`

### Implementation for Foundational

- [ ] T003 `backtesting/engine.py` `run_backtest()` ganha parâmetro `strategy: Optional[BaseStrategy]
      = None`; usa `strategy or EmaRsiStrategy()` (depende de T001 falhando, T002 falhando)

**Checkpoint**: `run_backtest()` retrocompatível com os 3 chamadores atuais, pronto para receber
qualquer `BaseStrategy`.

---

## Phase 2: User Story 1 - Não perder dinheiro repetidamente em mercado lateral (Priority: P1) 🎯 MVP

**Goal**: Regime de mercado (trending/sideways/indefinido) via ADX(14), com bloqueio opcional de
entradas em lateralização.

**Independent Test**: Ver `quickstart.md` → US1.

### Tests for User Story 1 ⚠️

- [ ] T004 [P] [US1] Teste: `calculate_indicators()` calcula `adx` e `regime` corretamente para um
      candle com ADX conhecido acima/abaixo de `REGIME_ADX_THRESHOLD` — novo
      `tests/test_strategy_regime.py`
- [ ] T005 [P] [US1] Teste: `regime` é `"indefinido"` quando ADX não pode ser calculado (NaN,
      poucos candles) — `tests/test_strategy_regime.py`
- [ ] T006 [P] [US1] Teste: com `REGIME_FILTER_ENABLED=false` (default), um sinal de compra que
      ocorreria em regime `sideways` não é bloqueado — comportamento idêntico ao já validado —
      `tests/test_strategy_regime.py`
- [ ] T007 [P] [US1] Teste: com `REGIME_FILTER_ENABLED=true`, um sinal de compra em regime
      `sideways`/`indefinido` é bloqueado (`Signal.HOLD`, motivo explícito) —
      `tests/test_strategy_regime.py`
- [ ] T008 [P] [US1] Teste: `trading/decision_logger.py` grava a coluna `regime` em
      `data/decisions.csv` — `tests/test_decision_logger.py`

### Implementation for User Story 1

- [ ] T009 [US1] `REGIME_ADX_THRESHOLD` (default `20`), `REGIME_FILTER_ENABLED` (default `false`)
      em `config/settings.py`, com validação (`REGIME_ADX_THRESHOLD > 0`) (depende de T004
      falhando)
- [ ] T010 [US1] `strategy/ema_rsi.py` `calculate_indicators()`: `df["adx"]` via
      `ta.trend.ADXIndicator`; `df["regime"]` derivado de `adx` vs `REGIME_ADX_THRESHOLD`, NaN →
      `"indefinido"` (depende de T005 falhando, T009)
- [ ] T011 [US1] `generate_signal()`: quando `REGIME_FILTER_ENABLED=true` e regime do candle atual
      for `sideways`/`indefinido`, retorna `HOLD` com motivo explícito antes de avaliar as demais
      condições de compra (depende de T006 falhando, T007 falhando, T010)
- [ ] T012 [US1] `trading/decision_logger.py` grava `regime` (via `indicators.get("regime")`) na
      linha de `data/decisions.csv` (depende de T008 falhando, T010)

**Checkpoint**: US1 completa e testável isoladamente — `REGIME_FILTER_ENABLED=false` preserva 100%
o comportamento já validado.

---

## Phase 3: User Story 2 - Adaptar stops/alvos à volatilidade do momento (Priority: P2)

**Goal**: Bloqueio de entrada em candles de volatilidade elevada via `ATR_ratio`.

**Independent Test**: Ver `quickstart.md` → US2.

### Tests for User Story 2 ⚠️

- [ ] T013 [P] [US2] Teste: `calculate_indicators()` calcula `atr_ratio = atr / close` corretamente
      — novo `tests/test_strategy_volatility.py`
- [ ] T014 [P] [US2] Teste: com `HIGH_VOLATILITY_FILTER_ENABLED=false` (default), um sinal de
      compra num candle de `atr_ratio` alto não é bloqueado — comportamento idêntico ao já
      validado — `tests/test_strategy_volatility.py`
- [ ] T015 [P] [US2] Teste: com `HIGH_VOLATILITY_FILTER_ENABLED=true`, um sinal de compra num
      candle com `atr_ratio > HIGH_VOLATILITY_ATR_RATIO` é bloqueado com motivo explícito —
      `tests/test_strategy_volatility.py`
- [ ] T016 [P] [US2] Teste: bloqueio de volatilidade elevada tem precedência sobre a permissão de
      rompimento do Bollinger adaptativo (US3) no mesmo candle — regressão do Edge Case do
      `spec.md` — `tests/test_strategy_volatility.py` (depende de US3 já implementada; escrito
      aqui, verificado ao final de US3)

### Implementation for User Story 2

- [ ] T017 [US2] `HIGH_VOLATILITY_ATR_RATIO` (default `0.05`), `HIGH_VOLATILITY_FILTER_ENABLED`
      (default `false`) em `config/settings.py`, com validação
      (`0 < HIGH_VOLATILITY_ATR_RATIO <= 1`) (depende de T013 falhando)
- [ ] T018 [US2] `strategy/ema_rsi.py` `calculate_indicators()`: `df["atr_ratio"] = df["atr"] /
      df["close"]` (depende de T017)
- [ ] T019 [US2] `generate_signal()`: quando `HIGH_VOLATILITY_FILTER_ENABLED=true` e
      `atr_ratio > HIGH_VOLATILITY_ATR_RATIO`, bloqueia a entrada (checado ANTES do Bollinger
      adaptativo de US3, garantindo a precedência do Edge Case) (depende de T014 falhando, T015
      falhando, T018)

**Checkpoint**: US1 e US2 completas e independentes.

---

## Phase 4: User Story 3 - Permitir rompimentos fortes sem perder o filtro contra compra esticada (Priority: P3)

**Goal**: Filtro Bollinger adaptativo — permite entrada acima da banda superior com tendência/
volume fortes.

**Independent Test**: Ver `quickstart.md` → US3.

### Tests for User Story 3 ⚠️

- [ ] T020 [P] [US3] Teste: com `ADAPTIVE_BOLLINGER_ENABLED=false` (default), uma entrada acima da
      banda superior continua bloqueada mesmo com tendência/volume fortes — comportamento idêntico
      ao já validado — novo `tests/test_strategy_adaptive_bb.py`
- [ ] T021 [P] [US3] Teste: com `ADAPTIVE_BOLLINGER_ENABLED=true`, uma entrada acima da banda
      superior COM tendência forte (`above_trend`) e volume forte (`volume_ok`) não é bloqueada
      pelo Bollinger — `tests/test_strategy_adaptive_bb.py`
- [ ] T022 [P] [US3] Teste: com `ADAPTIVE_BOLLINGER_ENABLED=true`, uma entrada acima da banda
      superior SEM tendência ou SEM volume forte continua bloqueada — `tests/test_strategy_adaptive_bb.py`

### Implementation for User Story 3

- [ ] T023 [US3] `ADAPTIVE_BOLLINGER_ENABLED` (default `false`) em `config/settings.py` (depende
      de T020 falhando)
- [ ] T024 [US3] `generate_signal()`: `not_overextended` passa a ser `price <= bb_upper or
      (ADAPTIVE_BOLLINGER_ENABLED and above_trend and volume_ok)` (depende de T021 falhando, T022
      falhando, T023)
- [ ] T025 [US3] Rodar T016 (US2, precedência de bloqueios) e confirmar que passa agora que US3
      está implementada (depende de T019, T024)

**Checkpoint**: US1, US2 e US3 completas e independentes. Todos os filtros de `strategy/ema_rsi.py`
desligados por padrão preservam 100% o comportamento já validado (FR-010/SC-004).

---

## Phase 5: User Story 4 - Comparar EMA/RSI contra uma estratégia de rompimento (Priority: P4)

**Goal**: Nova `strategy/breakout.py` (Donchian channel), testável pela mesma infraestrutura de
backtest.

**Independent Test**: Ver `quickstart.md` → US4.

### Tests for User Story 4 ⚠️

- [ ] T026 [P] [US4] Teste: `BreakoutStrategy.calculate_indicators()` calcula `breakout_high`/
      `breakout_low` com `shift(1)` (não inclui o candle atual) — novo `tests/test_strategy_breakout.py`
- [ ] T027 [P] [US4] Teste: `generate_signal()` retorna `BUY` quando `close > breakout_high` da
      janela anterior — `tests/test_strategy_breakout.py`
- [ ] T028 [P] [US4] Teste: `generate_signal()` retorna `SELL` quando `close < breakout_low` —
      `tests/test_strategy_breakout.py`
- [ ] T029 [P] [US4] Teste: `generate_signal()` retorna `HOLD` com motivo explícito quando
      `len(df) < window` (dados insuficientes) — `tests/test_strategy_breakout.py`
- [ ] T030 [P] [US4] Teste: `calculate_indicators()` inclui `atr` (compatibilidade com
      `risk/manager.py`/trailing stop) — `tests/test_strategy_breakout.py`
- [ ] T031 [P] [US4] Teste: `run_backtest(symbol, timeframe, strategy=BreakoutStrategy())` produz
      um `BacktestResult` completo sem erros — `tests/test_backtesting_engine.py`

### Implementation for User Story 4

- [ ] T032 [US4] `BREAKOUT_WINDOW` (default `150`) em `config/settings.py`, com validação
      (`BREAKOUT_WINDOW >= 10`) (depende de T026 falhando)
- [ ] T033 [US4] Novo `strategy/breakout.py`: `BreakoutStrategy(BaseStrategy)`,
      `__init__(self, window: int = BREAKOUT_WINDOW)`, `calculate_indicators()` (breakout_high/low
      via `rolling().max()/.min().shift(1)`, mais `atr`), `generate_signal()` (depende de T027
      falhando, T028 falhando, T029 falhando, T030 falhando, T032)
- [ ] T034 [US4] Confirmar T031 passa (integração com `run_backtest`, depende da Foundational T003
      e de T033)

**Checkpoint**: US1-US4 completas. `strategy/breakout.py` funciona pela mesma infraestrutura de
backtest sem exigir mudanças no motor.

---

## Phase 6: User Story 5 - Escolher a estratégia/preset vencedor com um único comando (Priority: P5)

**Goal**: Comando `compare`/`comparar` rodando múltiplas estratégias/presets nas mesmas condições,
reusando `evaluate_approval`/`edge_score`.

**Independent Test**: Ver `quickstart.md` → US5.

### Tests for User Story 5 ⚠️

- [ ] T035 [P] [US5] Teste: `run_comparison({"EMA/RSI": EmaRsiStrategy(), "Breakout 150":
      BreakoutStrategy(150)}, pairs=["BTC/USDT"], timeframe="4h")` retorna uma linha de resultado
      por estratégia×par, cada uma com veredito de `evaluate_approval` — novo
      `tests/test_backtesting_compare.py`
- [ ] T036 [P] [US5] Teste: `run_comparison` com uma única estratégia funciona normalmente (Edge
      Case do `spec.md` — não exige mínimo de itens) — `tests/test_backtesting_compare.py`
- [ ] T037 [P] [US5] Teste: `main.py` registra o comando `compare`/`comparar` em `COMMANDS` —
      `tests/test_main_commands.py` (ou arquivo de teste de CLI já existente, se houver)

### Implementation for User Story 5

- [ ] T038 [US5] Novo `backtesting/compare.py`: `run_comparison(strategies: dict[str, BaseStrategy],
      pairs=None, timeframe=None)` — roda `run_backtest(pair, timeframe, strategy=strategy)` por
      combinação, aplica `evaluate_approval`/`edge_score`/`ranking_key`, imprime tabela Rich (mesmo
      padrão de `backtesting/multi.py`) (depende de T035 falhando, T036 falhando, Foundational T003)
- [ ] T039 [US5] `main.py`: `cmd_comparar()` chamando `run_comparison` com a lista fixa de
      estratégias/presets padrão (EMA/RSI + Breakout em pelo menos uma janela); registra
      `"compare"`/`"comparar"` em `COMMANDS` (depende de T037 falhando, T038)

**Checkpoint**: Todas as 5 User Stories completas e independentes.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T040 [P] Atualizar `ROADMAP.md` marcando Fase 4 itens 2-6 como concluídos, com link para
      esta spec (item 1, "validar preset operacional", permanece pendente — fora de escopo)
- [ ] T041 [P] Atualizar `specs/BACKLOG.md`: status da spec 006 para concluída (parte autônoma)
- [ ] T042 Sincronizar `CLAUDE.md` e `AGENTS.md` no mesmo commit: novas variáveis de `.env`
      (`REGIME_ADX_THRESHOLD`, `REGIME_FILTER_ENABLED`, `HIGH_VOLATILITY_ATR_RATIO`,
      `HIGH_VOLATILITY_FILTER_ENABLED`, `ADAPTIVE_BOLLINGER_ENABLED`, `BREAKOUT_WINDOW`), nova
      estratégia `strategy/breakout.py`, novo comando `compare`
- [ ] T043 Rodar `quickstart.md` (todos os passos são backtest com dados públicos, executáveis sem
      depender do operador) e registrar observações relevantes em `STRATEGY_REVIEW.md`/`ROADMAP.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: Bloqueia US4/US5 (precisam de `strategy` parametrizável em
  `run_backtest`). US1/US2/US3 não dependem da Foundational.
- **User Stories (Phase 2-6)**: US1, US2, US3 são independentes entre si (cada uma sua própria
  flag). US2 tem uma dependência de ORDEM de checagem com US3 (T016/T025 — volatilidade elevada
  checada antes do Bollinger adaptativo), não de implementação. US4 depende da Foundational. US5
  depende de US4 (para ter mais de uma estratégia real a comparar, embora `run_comparison` em si só
  dependa da Foundational).
- **Polish (Phase 7)**: Depende de todas as User Stories concluídas.

### Parallel Opportunities

- T004-T008 (testes US1), T013-T015 (testes US2), T020-T022 (testes US3), T026-T031 (testes US4),
  T035-T037 (testes US5) podem ser escritos em paralelo dentro de cada fase.
- T040/T041 (Polish) podem rodar em paralelo.
- Seguindo o Fluxo Incremental do `CLAUDE.md`, a prática real é sequencial, tópico por tópico,
  commit por commit.

---

## Implementation Strategy

### MVP First (User Story 1)

1. Completar Phase 1 (Foundational).
2. Completar Phase 2 (US1 — regime de mercado via ADX). Maior potencial de redução de perdas por
   esforço — MVP desta spec.
3. Validar isoladamente (`quickstart.md` → US1) antes de seguir.

### Incremental Delivery

1. Foundational → US1 (MVP) → validar.
2. US2 → validar.
3. US3 → validar (inclui confirmar a precedência de bloqueio sobre US2, T016/T025).
4. US4 → validar.
5. US5 → validar.
6. Polish → documentação.

Cada etapa segue o Fluxo Incremental do `CLAUDE.md`: tarefa pequena → testes → commit Conventional
Commit em português → push para `origin/main` → próxima tarefa. `/code-review medium` roda sobre o
diff acumulado antes do commit final de cada User Story.

---

## Notes

- Nenhuma tarefa desta spec toca `execution/`, `risk/manager.py` ou dinheiro real — risco de
  regressão concentrado em `strategy/ema_rsi.py`, mitigado por todos os filtros novos ficarem
  desligados por padrão.
- `strategy/breakout.py` é aditiva (arquivo novo) — não há risco de regressão na estratégia
  principal ao implementá-la.
