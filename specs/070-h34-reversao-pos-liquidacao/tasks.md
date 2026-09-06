---

description: "Task list for H34 reversao pos-liquidacao (spec 070)"
---

# Tasks: H34 — Reversão pós-liquidação (padrão de vela: pavio + pico de volume)

**Input**: Design documents from `/specs/070-h34-reversao-pos-liquidacao/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D4), quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Veredito completo E1-E6 sobre o padrão pavio+volume (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [P] [US1] Testes em `tests/test_reversao_pos_liquidacao.py`: `ReversaoPosLiquidacaoStrategy` gera BUY quando pavio/volume/fechamento batem os três critérios simultaneamente, HOLD quando cada critério falha isoladamente (pavio insuficiente / volume insuficiente / fechamento em queda), HOLD durante o warmup da média de volume; `gerar_resultado` aplica fee/slippage zerados quando `custo_zero=True`; `teste_sanidade` devolve `True` (zero trades) sobre série sintética sem pavio nem pico de volume; `avaliar_par`/`avaliar_universo` funcionam com `fetch_ohlcv` mockado (sem rede), `avaliar_par` devolve `None` para série curta demais

### Implementation

- [X] T002 [P] [US1] Criar `strategy/reversao_pos_liquidacao.py`: `ReversaoPosLiquidacaoStrategy` (subclasse de `BaseStrategy`, mesmo padrão de `strategy/breakout.py`) — `calculate_indicators` adiciona `volume_ma` (janela própria do módulo, D2) e `atr`(14, para o SL/TP/trailing genérico de `simulate_backtest`); `generate_signal` aplica D1 (pavio ≥ 50% do range) + D2 (volume ≥ 3x a média) + fechamento de recuperação (`close > open`) → BUY, sem SELL próprio (depende de T001)
- [X] T003 [US1] Criar `backtesting/reversao_pos_liquidacao.py`: docstring com D1-D4 declarados antes de medir; `gerar_resultado(candles, custo_zero)` (usa `simulate_backtest` com a estratégia de T002, fee/slippage zerados quando `custo_zero=True`); `teste_sanidade()` (série sintética sem pavio/volume); `avaliar_par(par)` (fetch + `bateria_hipotese.rodar_bateria`); `avaliar_universo(pares=None)` (loop sobre `UNIVERSO_H11`, D3) (depende de T002)
- [X] T004 [US1] Criar `cmd_liquidacao()` em `main.py`: roda `avaliar_universo()`, imprime por par o status de cada etapa E1-E6 do `RelatorioBateria`; registrar `"liquidacao": cmd_liquidacao` em `COMMANDS`; sincronizar `CLAUDE.md`/`AGENTS.md` (depende de T003)
- [ ] T005 Rodar `python main.py liquidacao` contra dados reais
- [ ] T006 Registrar o resultado real de T005 em `docs/research/registro-de-hipoteses.md` §6.1 (H34) — comparação explícita com H3 (FR-005), "Atualização — testada" no mesmo estilo das demais hipóteses desta rodada
- [ ] T007 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T004 implementação e testes) + (T005-T007 execução real e registro).

---

## Implementation Strategy

T001-T004 (testes + estratégia + módulo de avaliação + comando CLI) → commit → push;
T005-T007 (execução real + registro + suite completa) → commit → push.
