# Implementation Plan: H18 — Grid trading com gestão de cauda

**Branch**: `035-grid-trading` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/grid.py::simular_grade(df, params)` simula uma grade de 10
níveis (D1) entre as Bollinger Bands já calculadas, ativa só em regime
`"sideways"` (FR-002), liquidando tudo ao `close` quando o regime vira
`"trending"` (FR-003/D4 — a gestão de cauda que a objeção original de H18
apontava como ausente). Cada round-trip de nível e cada liquidação forçada
viram `Trade` (`backtesting/engine.py`, reusado sem alteração); o
`BacktestResult` agregado usa `_calculate_advanced_metrics` já existente, e
o veredito por par usa `evaluate_approval`/`edge_score` sem critério novo
(D6/FR-006). Avaliação sobre `UNIVERSO_H11` (D7), mesmo teto de 2000
candles de H14/H17/H20.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `backtesting/engine.py`
(`Trade`, `BacktestResult`, `_calculate_advanced_metrics`),
`backtesting/approval.py::evaluate_approval`, `strategy/ema_rsi.py`
(Bollinger Bands + regime, já calculados)

**Storage**: reusa `reports/grid_*.json` (padrão `export_report`)

**Testing**: pytest, `tests/test_grid.py` (novo)

**Target Platform**: CLI local (`python main.py grid`); produção intocada

**Performance Goals**: simulação candle a candle por par, mesma ordem de
grandeza de `simulate_backtest()` — sem chamada de rede além do fetch de
candles já existente

**Constraints**: FR-006 — o `BacktestResult` produzido MUST passar por
`evaluate_approval()` sem nenhuma alteração de assinatura ou critério;
FR-009 — nenhuma ordem real

**Scale/Scope**: 1 módulo novo (`backtesting/grid.py`), 1 comando CLI, 12
pares avaliados (`UNIVERSO_H11`)

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre a mecânica da grade (preenchimento, liquidação forçada, custo) com teste antes da implementação. |
| **IV. Incremental Delivery** | **Conforme.** Simulador + `Trade`/`BacktestResult` num tópico; comando CLI + execução real noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado de pesquisa via `export_report`, mesmo padrão de `modelo`/`onchain`/`barras`. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** D1-D7 commitados em `research.md` antes de qualquer código, com a mecânica de preenchimento (D3) e liquidação (D4) declaradas explicitamente. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/035-grid-trading/
├── plan.md              # este arquivo
├── research.md          # Fase 0 (D1-D7)
├── data-model.md         # Fase 1
└── quickstart.md         # Fase 1
```

Sem `contracts/`: comando de pesquisa segue o padrão já estabelecido por
`modelo`/`onchain`/`barras` (sem contrato formal separado).

### Source Code (repository root)

```text
backtesting/
└── grid.py               # NOVO: ParametrosGrade, NivelGrade,
                           # simular_grade(df, params) -> BacktestResult,
                           # run_grid_scan(pares) -> list[(par, resultado)]

main.py                   # +cmd_grid

tests/
└── test_grid.py           # NOVO
```

`backtesting/engine.py`, `backtesting/approval.py`, `strategy/ema_rsi.py`
**não são alterados** — só consumidos.

## Complexity Tracking

Vazio — nenhuma violação de princípio a justificar.

## Fases

**Fase 0 ✅** — D1 (N=10) → D2 (capital/nível) → D3 (mecânica de
preenchimento, vendas antes de compras) → D4 (liquidação forçada ao
close) → D5 (reabertura recalcula bandas) → D6 (reuso do motor de
métricas) → D7 (universo/período).

**Fase 1 ✅** — `data-model.md` + `quickstart.md`. Sem `contracts/`.

**Fase 2** — `tasks.md` (`/speckit-tasks`).

**Fase 3** — implementação (`/speckit-implement`), dois tópicos:
1. `backtesting/grid.py`: `NivelGrade`, `ParametrosGrade`,
   `simular_grade()` — mecânica de preenchimento, liquidação forçada,
   montagem do `BacktestResult`
2. `run_grid_scan()` + `cmd_grid()` (CLI) + execução real sobre
   `UNIVERSO_H11`, veredito registrado no registro-mestre
