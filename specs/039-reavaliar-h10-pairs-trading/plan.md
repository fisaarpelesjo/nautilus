# Implementation Plan: Reavaliar H10 (pairs trading) com histórico estendido

**Branch**: `039-reavaliar-h10-pairs-trading` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/pairs_trading.py::run_pairs_scan()` (novo) busca 6.000
candles de 4h para os 12 pares de `UNIVERSO_H11` (FR-002), divide num
corte de tempo compartilhado 70/30 (FR-003), monta a fatia de validação
com `formacao` candles de aquecimento prepostos (FR-004), e chama
`run_pairs_backtest(..., PairsParams(formacao=500))` (FR-001) — já
existente, sem alteração — separadamente sobre treino e validação.
`evaluate_approval()` decide sobre a validação, sem critério novo
(FR-005).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `backtesting/pairs_trading.py`
(`run_pairs_backtest`, `PairsParams`, já existentes),
`backtesting/approval.py::evaluate_approval`, `backtesting/horizonte.py::UNIVERSO_H11`

**Storage**: `reports/pairs_*.json` (padrão `export_report` já existente)

**Testing**: pytest, `tests/test_pairs_trading.py` (extensão — já existe,
cobre `run_pairs_backtest`/seleção)

**Target Platform**: CLI local (`python main.py pairs`); produção intocada

**Performance Goals**: 1 fetch por par (12), sem treino de modelo — mais
leve que H14/H37; execução longa se rodar na VPS (`vps-limulus`)

**Constraints**: FR-001 — `formacao=500` já medido, não ajustável sem
nova medição de poder; FR-006 — nenhuma ordem real

**Scale/Scope**: 1 função nova (`run_pairs_scan`) em módulo existente, 1
comando CLI, 12 pares (`UNIVERSO_H11`)

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/` (FR-006). |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre o split treino/validação com aquecimento antes da implementação. |
| **IV. Incremental Delivery** | **Conforme.** Split + scan num tópico; CLI + execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão de `modelo`/`grid`/`carteira`/`leadlag`. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Os parâmetros centrais (`formacao=500`, 6.000 candles, split 70/30) já estavam declarados e medidos em `docs/research/registro-de-hipoteses.md` §4.11 antes desta spec — `research.md` só consolida, não decide de novo. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/039-reavaliar-h10-pairs-trading/
├── plan.md              # este arquivo
├── research.md          # Fase 0 (D1-D2, consolida §4.11)
├── data-model.md         # Fase 1
└── quickstart.md         # Fase 1
```

Sem `contracts/`: comando de pesquisa segue o padrão já estabelecido por
`modelo`/`grid`/`carteira`/`leadlag`.

### Source Code (repository root)

```text
backtesting/
└── pairs_trading.py       # +run_pairs_scan(pares=UNIVERSO_H11) ->
                            # tuple[BacktestResult treino, BacktestResult
                            # validacao, ApprovalVerdict]

main.py                    # +cmd_pairs

tests/
└── test_pairs_trading.py   # +testes do split com aquecimento
```

`backtesting/engine.py`, `backtesting/approval.py`,
`backtesting/pairs_trading.py::run_pairs_backtest`/`selecionar_pares`
**não são alterados** — só consumidos.

## Complexity Tracking

Vazio — nenhuma violação de princípio a justificar.

## Fases

**Fase 0 ✅** — D1 (formação 500, já medida em §4.11) → D2 (split 70/30
com aquecimento causal, mesmo princípio de `preparar()`/H14).

**Fase 1 ✅** — `data-model.md` + `quickstart.md`. Sem `contracts/`.

**Fase 2** — `tasks.md` (`/speckit-tasks`).

**Fase 3** — implementação (`/speckit-implement`), dois tópicos:
1. `run_pairs_scan()` (split + aquecimento + chamada de
   `run_pairs_backtest` existente)
2. `cmd_pairs()` (CLI) + execução real (VPS) + veredito registrado em
   `docs/research/registro-de-hipoteses.md` §4.11
