---

description: "Task list for H24 diferencial de funding entre corretoras (spec 061)"
---

# Tasks: H24 — diferencial de funding rate entre corretoras (perp × perp)

**Input**: Design documents from `/specs/061-h24-funding-cross-exchange/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D5), quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Medir o diferencial líquido por par de corretoras (Priority: P1) 🎯 MVP

### Research (antes de qualquer código)

- [X] R001 Verificar quais das 6 corretoras de H15 suportam `fetchFundingRateHistory` via `ccxt` para BTC/USDT e ETH/USDT perpétuo linear — 5 qualificadas, Kraken excluído (research.md D1)
- [X] R002 Verificar taxa de tomador real por corretora (busca, research.md D2)
- [X] R003 Investigar (não presumir) se a exigência de capital de H24 é menor que H8 — conclusão: igual, 2x nocional, sem margem cruzada (research.md D3)

### Tests

- [X] T001 [P] [US1] Testes em `tests/test_funding_cross.py`: `perp_symbol`, corretoras qualificadas não incluem Kraken, taxa de tomador por corretora, símbolo sem perpétuo, histórico normal, paginação, cache de exchange
- [X] T002 [P] [US1] Testes em `tests/test_funding_cross_carry.py`: cálculo de diferencial/direção, exclusão por histórico insuficiente, alinhamento absorve jitter de segundos, `avaliar_universo` cobre todas as combinações e pula as sem resultado

### Implementation

- [X] T003 [US1] Criar `data/funding_cross.py`: `fetch_funding_rate_history(corretora, par, dias)` paginado, parametrizado por corretora, `BadSymbol` → vazio (depende de T001, R001-R002)
- [X] T004 [US1] Criar `backtesting/funding_cross_carry.py`: `avaliar_par_corretoras`/`avaliar_universo` — alinhamento por hora, custo por corretora, capital implantado (D3) (depende de T002, T003)
- [X] T005 [US1] Criar `cmd_funding_cross()` em `main.py`: roda sobre 5 corretoras × {BTC, ETH}, imprime tabela ordenada por capital implantado, exporta via `export_report`; registrar `"funding_cross": cmd_funding_cross` em `COMMANDS`; sincronizar `CLAUDE.md`/`AGENTS.md` (depende de T004)
- [X] T006 [BUGFIX] Smoke test real revelou dois achados de instrumentação: (a) `MIN_DIAS_COBERTURA=90` com `dias=90` produz cobertura real de 89 dias (janela não alinha perfeitamente) — corrigido com `DIAS_PADRAO=95`; (b) Gate trunca cada chamada bem abaixo do limite pedido sem erro — a heurística "lote incompleto = fim do histórico" (usada para Binance em `data/funding.py`) estava errada para Gate, removida em `data/funding_cross.py`
- [X] T007 Rodar `python main.py funding_cross` contra dados reais (local — mais leve que VPS)
- [X] T008 Registrar o resultado real de T007 em `docs/research/registro-de-hipoteses.md` (H24, §6.2) — inclui os achados de profundidade de histórico (Bybit ~67 dias, KuCoin ~33 dias, ambos abaixo do piso)
- [X] T009 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T006 implementação, testes e correção de bugs reais) + (T007-T009 execução real e registro).

---

## Implementation Strategy

T001-T006 (testes + módulos + comando CLI + correções reais) → commit → push;
T007-T009 (execução real + registro + suite completa) → commit → push.
