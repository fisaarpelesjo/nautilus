---

description: "Task list for H37 mean reversion em stablecoin (spec 072)"
---

# Tasks: H37 — Mean reversion em par de stablecoin (USDC/USDT)

**Input**: Design documents from `/specs/072-h37-mean-reversion-stablecoin/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D3), quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Veredito completo E1-E6 sobre H3 aplicada a USDC/USDT (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [P] [US1] Testes em `tests/test_mean_reversion_stablecoin.py`: `teste_sanidade` devolve zero trades sobre série sintética de preço constante (sem volatilidade, nunca toca a banda inferior); `gerar_resultado` aplica fee/slippage zerados quando `custo_zero=True`; `avaliar()` funciona com `fetch_ohlcv` mockado (sem rede)

### Implementation

- [X] T002 [US1] Criar `backtesting/mean_reversion_stablecoin.py`: `gerar_resultado(candles, custo_zero)` (usa `simulate_backtest` com `MeanReversionStrategy` inalterada), `teste_sanidade()` (série de preço constante), `avaliar()` (fetch `USDC/USDT` + `bateria_hipotese.rodar_bateria`) (depende de T001)
- [X] T003 [US1] Criar `cmd_mean_reversion_stablecoin()` em `main.py`: roda `avaliar()`, imprime o status de cada etapa E1-E6 do `RelatorioBateria`; registrar `"stablecoin": cmd_mean_reversion_stablecoin` em `COMMANDS`; sincronizar `CLAUDE.md`/`AGENTS.md` (depende de T002)
- [ ] T004 Rodar `python main.py stablecoin` contra dados reais
- [ ] T005 Registrar o resultado real de T004 em `docs/research/registro-de-hipoteses.md` §6.1 (H37) — comparação explícita com o resultado original de H3 (FR-004), "Atualização — testada" no mesmo estilo das demais hipóteses desta rodada
- [ ] T006 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T003 implementação e testes) + (T004-T006 execução real e registro).

---

## Implementation Strategy

T001-T003 (testes + módulo + comando CLI) → commit → push;
T004-T006 (execução real + registro + suite completa) → commit → push.
