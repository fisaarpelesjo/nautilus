---

description: "Task list for lead-lag BTC para altcoins (H21, spec 038)"
---

# Tasks: H21 — Lead-lag BTC para altcoins

**Input**: Design documents from `/specs/038-lead-lag-btc-altcoins/`

**Prerequisites**: plan.md, spec.md, data-model.md, research.md, quickstart.md

**Tests**: obrigatórios — Princípio III da constitution. `tests/test_lead_lag.py`
(novo).

**Organization**: US1 (sinal + backtest por par) e US2 (resumo de
consistência) são quase a mesma implementação — US2 só lê o resultado que
US1 já produz, não precisa de mecânica nova.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

Nenhuma — sem dependência nova.

---

## Phase 2: User Story 1 - Medir o lead-lag com o motor de backtest já existente (Priority: P1) 🎯 MVP

**Goal**: `avaliar_lead_lag(par)` produz um `BacktestResult` cujo único
sinal de entrada é "BTC fechou em alta no mesmo candle" (D1/D2), saída
via take-profit ATR/stop trailing (D4, `_simular_com_sinais`, sem motor
novo).

**Independent Test**: rodar `avaliar_lead_lag` sobre uma altcoin
sintética com uma série de BTC sintética determinística e confirmar que o
sinal dispara exatamente nos candles com retorno de BTC positivo.

### Tests for User Story 1

> **NOTE**: escrever os testes primeiro — `backtesting/lead_lag.py` ainda
> não existe.

- [ ] T001 [P] [US1] Teste em `tests/test_lead_lag.py`: `_sinais_lead_lag` devolve `Signal.BUY` exatamente onde `retorno_btc > 0`, `Signal.HOLD` onde `<= 0` (D2)
- [ ] T002 [P] [US1] Teste: candle da altcoin sem retorno de BTC correspondente (`NaN` após `reindex`) devolve `Signal.HOLD`, nunca `BUY` (FR-008)
- [ ] T003 [P] [US1] Teste **crítico** (ausência de *lookahead*): alterar `close_btc` em qualquer candle POSTERIOR a `t` não muda o sinal calculado em `t` — só candles `<= t` podem influenciá-lo (D1)
- [ ] T004 [P] [US1] Teste: o sinal na linha `t` usa `close_btc[t]/close_btc[t-1]-1` (retorno do MESMO candle `t`), não `close_btc[t-1]/close_btc[t-2]-1` — regressão contra o erro de defasagem capturado em `research.md` D1
- [ ] T005 [P] [US1] Teste: `avaliar_lead_lag` aceita `df_alt`/`retorno_btc` explícitos (sem rede) e devolve um `BacktestResult` cujos trades vêm de `_simular_com_sinais` (D4) — sem duplicar lógica de simulação
- [ ] T006 [P] [US1] Teste: o `BacktestResult` retornado é aceito por `evaluate_approval()` sem exceção, produzindo um `ApprovalVerdict` válido

### Implementation for User Story 1

- [ ] T007 [US1] Implementar `btc_retorno_no_candle(btc_close)` e `_sinais_lead_lag(retorno_btc, indice_par)` em `backtesting/lead_lag.py` (D1/D2, `data-model.md`)
- [ ] T008 [US1] Implementar `avaliar_lead_lag(par, df_alt=None, retorno_btc=None) -> Optional[BacktestResult]` em `backtesting/lead_lag.py`: busca dados se não fornecidos (FR-005, 6000 candles), `preparar()` para indicadores/ATR, monta o sinal (T007), chama `_simular_com_sinais` de `backtesting.modelo` (D4) (depende de T001-T006)

**Checkpoint**: `pytest tests/test_lead_lag.py -v` — T001-T006 passam. MVP
completo: o lead-lag mede com o motor existente, sem *lookahead*.

---

## Phase 3: User Story 2 - Confirmar consistência entre pares (Priority: P2)

**Goal**: `run_lead_lag_scan()` varre os 11 pares e o resumo reporta
quantos superam o buy-hold e quantos têm profit factor > 1,0 — números
descritivos, sem veredito agregado novo.

**Independent Test**: sobre uma lista de `BacktestResult` sintéticos com
retornos/PF conhecidos, confirmar que a contagem bate exatamente.

### Tests for User Story 2

- [ ] T009 [P] [US2] Teste em `tests/test_lead_lag.py`: função de resumo conta corretamente quantos resultados têm `total_return_pct > buy_hold_return_pct` e quantos têm `profit_factor > 1.0`, sobre uma lista de `BacktestResult` conhecida (SC-002)
- [ ] T010 [P] [US2] Teste: `run_lead_lag_scan()` busca `BTC/USDT` **uma única vez** e reusa entre os 11 pares — não 11 fetches redundantes do par-sinal (verificável via contagem de chamadas de `fetch_ohlcv` com um mock/spy)

### Implementation for User Story 2

- [ ] T011 [US2] Implementar `run_lead_lag_scan(pares=None) -> list[tuple[str, Optional[BacktestResult], ApprovalVerdict]]` em `backtesting/lead_lag.py`: busca BTC uma vez, itera `UNIVERSO_H11` menos `"BTC/USDT"` (D3) ou `pares` explícito, chama `avaliar_lead_lag`, aplica `evaluate_approval` (depende de T009-T010)
- [ ] T012 [US2] Implementar a função de resumo de consistência (contagem de T009) — pode viver em `backtesting/lead_lag.py` ou em `cmd_leadlag()` diretamente, se simples o bastante para não precisar de função separada

**Checkpoint**: as duas user stories passam juntas.

---

## Phase 4: Polish & Cross-Cutting Concerns

- [ ] T013 Criar `cmd_leadlag()` em `main.py`: chama `run_lead_lag_scan()`, imprime tabela por par (trades, retorno, buy-hold, drawdown, profit factor, veredito) e o resumo de consistência (US2); registrar `"leadlag": cmd_leadlag` em `COMMANDS`; exportar via `export_report("leadlag", ...)`
- [ ] T014 Rodar `python main.py leadlag` contra dados reais (11 pares, VPS `vps-limulus`/`nautilus-research` se demorar — ver `quickstart.md`) — validação manual do passo 2 do `quickstart.md`, resultado real
- [ ] T015 Registrar o resultado real de T014 em `docs/research/registro-de-hipoteses.md` como H21 (nova entrada em §4 ou §6, conforme o veredito) — texto depende do resultado medido, não escrito antes de T014
- [ ] T016 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão em `backtesting/engine.py`/`backtesting/approval.py`/`backtesting/modelo.py` (intocados, D4)

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: N/A
- **US1 (Phase 2)**: sem dependência — único tópico que cria o sinal e `avaliar_lead_lag`
- **US2 (Phase 3)**: depende de T008 (Phase 2) já produzir `BacktestResult` por par
- **Polish (Phase 4)**: depende de Phase 2+3 completas — T015 depende do resultado real de T014

### Parallel Opportunities

- T001-T006 (US1, testes) em paralelo
- T009-T010 (US2, testes) em paralelo, após T008

---

## Implementation Strategy

### MVP = Phase 2 (US1)

Um commit: T001-T006 (testes) → T007-T008 (implementação) → commit →
push. É a mecânica inteira que responde a pergunta da hipótese por par.

### Incremental Delivery

1. Phase 2 (US1) → sinal + backtest por par, MVP
2. Phase 3 (US2) → varredura dos 11 pares + resumo de consistência
3. Phase 4 (Polish) → comando CLI, execução real (VPS se longa), veredito
   registrado no registro-mestre, suite completa
