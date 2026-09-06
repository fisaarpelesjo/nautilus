---

description: "Task list for H36 hash ribbons (spec 073)"
---

# Tasks: H36 — Hash Ribbons: capitulação de mineradores (BTC-only)

**Input**: Design documents from `/specs/073-h36-hash-ribbons/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D5), quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Veredito completo E1-E6 sobre o cruzamento de hashrate (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [P] [US1] Testes em `tests/test_hash_ribbons.py`: `HashRibbonsStrategy` gera BUY no dia seguinte a um cruzamento de alta das médias de 30/60 dias do hashrate, SELL no cruzamento de baixa simétrico, HOLD sem cruzamento; alinhamento causal usa o valor de D-1, nunca o dia corrente; `teste_sanidade` devolve zero trades sobre série de hashrate monotônica (sem cruzamento); `gerar_resultado` aplica custo zero corretamente; `avaliar()` descarta candles anteriores ao início real do hashrate disponível, funciona com fetchers mockados (sem rede)

### Implementation

- [X] T002 [P] [US1] Criar `strategy/hash_ribbons.py`: `HashRibbonsStrategy` (subclasse de `BaseStrategy`, recebe a série diária de hashrate pré-buscada) — `calculate_indicators` computa médias de 30/60 dias, cruzamentos e ATR14; `generate_signal` aplica D2 (BUY no cruzamento de alta, SELL no de baixa, alinhamento causal D-1 via `_merge_causal`) (depende de T001)
- [X] T003 [US1] Criar `backtesting/hash_ribbons.py`: docstring com D1-D5 declarados antes de medir; `gerar_resultado(candles, custo_zero)` (usa `simulate_backtest` com a estratégia de T002); `teste_sanidade()` (série de hashrate monotônica); `avaliar()` (busca hashrate + candles, descarta candles antes do início real do hashrate — D3, roda `bateria_hipotese.rodar_bateria` sobre `BTC/USDT`) (depende de T002)
- [X] T004 [US1] Criar `cmd_hash_ribbons()` em `main.py`: roda `avaliar()`, imprime o status de cada etapa E1-E6 do `RelatorioBateria`, exporta via `export_report`; registrar `"hashribbons": cmd_hash_ribbons` em `COMMANDS`; sincronizar `CLAUDE.md`/`AGENTS.md` (depende de T003)
- [X] T005 Rodar `python main.py hashribbons` contra dados reais
- [X] T006 Registrar o resultado real de T005 em `docs/research/registro-de-hipoteses.md` §6.1 (H36) — comparação explícita com H17/H32 (FR-008), "Atualização — testada" no mesmo estilo das demais hipóteses desta rodada
- [X] T007 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T004 implementação e testes) + (T005-T007 execução real e registro).

---

## Implementation Strategy

T001-T004 (testes + estratégia + módulo de avaliação + comando CLI) → commit → push;
T005-T007 (execução real + registro + suite completa) → commit → push.
