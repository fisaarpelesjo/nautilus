---

description: "Task list for reavaliar H10 pairs trading (spec 039)"
---

# Tasks: Reavaliar H10 (pairs trading) com histórico estendido

**Input**: Design documents from `/specs/039-reavaliar-h10-pairs-trading/`

**Prerequisites**: plan.md, spec.md, data-model.md, research.md, quickstart.md

**Tests**: obrigatórios — Princípio III da constitution. `tests/test_pairs_trading.py`
(extensão).

**Organization**: uma única user story (P1) — a correção é pontual
(formação + split), não há segunda prioridade a decompor.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

Nenhuma — sem dependência nova.

---

## Phase 2: User Story 1 - Rodar H10 com formação de 500 candles (Priority: P1) 🎯 MVP

**Goal**: `run_pairs_scan()` produz `BacktestResult` de treino e
validação com `formacao=500` sobre 6.000 candles, aquecimento causal na
validação, veredito via `evaluate_approval()` sem critério novo.

**Independent Test**: rodar sobre dados sintéticos com um par
cointegrado construído e confirmar que a validação tem `period_start`
exatamente no corte 70/30, não antes.

### Tests for User Story 1

- [ ] T001 [P] [US1] Teste em `tests/test_pairs_trading.py`: split por corte de tempo compartilhado — `dados_treino`/`dados_validacao` cobrem exatamente 70%/30% dos timestamps comuns aos pares, sem sobreposição além do aquecimento (FR-003)
- [ ] T002 [P] [US1] Teste: `resultado_validacao.trades` (via `_montar`/`period_start`) reporta candles a partir do corte real — os `formacao` candles de aquecimento prepostos não aparecem como parte do período reportado (FR-004/D2)
- [ ] T003 [P] [US1] Teste: `run_pairs_scan` chama `run_pairs_backtest` com `PairsParams(formacao=500, reselecionar_a_cada=500)` — sem alterar a assinatura ou o comportamento de `run_pairs_backtest`/`selecionar_pares` (FR-001/FR-005)
- [ ] T004 [P] [US1] Teste: o `BacktestResult` de validação é aceito por `evaluate_approval()` sem exceção, produzindo um `ApprovalVerdict` válido

### Implementation for User Story 1

- [ ] T005 [US1] Implementar `run_pairs_scan(pares=None, params=None)` em `backtesting/pairs_trading.py`: busca 6000 candles por par (FR-002), split 70/30 por corte de tempo comum (D2), monta `dados_validacao` com aquecimento (`formacao` candles finais do treino prepostos), chama `run_pairs_backtest` duas vezes (treino/validação), aplica `evaluate_approval` (depende de T001-T004)

**Checkpoint**: `pytest tests/test_pairs_trading.py -v` — T001-T004 passam.
MVP completo: H10 mede com o instrumento corrigido.

---

## Phase 3: Polish & Cross-Cutting Concerns

- [ ] T006 Criar `cmd_pairs()` em `main.py`: chama `run_pairs_scan()`, imprime treino e validação lado a lado (trades, retorno, buy-hold, drawdown, profit factor) e o veredito de `evaluate_approval()` sobre a validação; registrar `"pairs": cmd_pairs` em `COMMANDS`; exportar via `export_report("pairs", ...)`
- [ ] T007 Rodar `python main.py pairs` contra dados reais (12 pares, VPS `vps-limulus`/`nautilus-research`) — validação manual do passo 2 do `quickstart.md`, resultado real
- [ ] T008 Registrar o resultado real de T007 em `docs/research/registro-de-hipoteses.md` §4.11 (H10) — substitui "inconclusiva, requer reavaliação" por um status definitivo (ou nova limitação específica); texto depende do resultado medido, não escrito antes de T007
- [ ] T009 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão em `backtesting/engine.py`/`backtesting/approval.py`/`backtesting/pairs_trading.py::run_pairs_backtest` (intocados)

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: N/A
- **US1 (Phase 2)**: sem dependência — único tópico que cria `run_pairs_scan`
- **Polish (Phase 3)**: depende de Phase 2 completa — T008 depende do resultado real de T007

### Parallel Opportunities

- T001-T004 (US1, testes) em paralelo

---

## Implementation Strategy

### MVP = Phase 2 (US1)

Um commit: T001-T004 (testes) → T005 (implementação) → commit → push. É a
mecânica inteira que corrige o instrumento e produz o resultado.

### Incremental Delivery

1. Phase 2 (US1) → `run_pairs_scan`, MVP
2. Phase 3 (Polish) → comando CLI, execução real (VPS), veredito
   registrado no registro-mestre, suite completa
