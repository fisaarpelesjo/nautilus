# Implementation Plan: H20 — geometria propaga ao backtest real

**Branch**: `049-h20-backtest-real` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/modelo.py::avaliar_par` passa `atr_tp_multiplier=p.tp_mult,
atr_sl_multiplier=p.sl_mult` na chamada de `_resultado_modelo(...)` (as
duas ocorrências, "modelo" e "embaralhado"), que já repassa `**kwargs`
para `_simular_com_sinais` → `simulate_backtest` — parâmetros que já
existem em `simulate_backtest` (`atr_tp_multiplier`, `atr_sl_multiplier`),
nunca antes conectados ao `ParametrosBarreira` usado para rotular.
Depois, `cmd_geometria()` (`main.py`, spec 048) ganha a impressão do
backtest real por par da geometria selecionada.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `backtesting/modelo.py`,
`backtesting/engine.py` (parâmetros já existentes)

**Storage**: `reports/geometria_estendida_*.json` (extensão do já
existente em spec 048)

**Testing**: pytest, `tests/test_modelo.py` (extensão — propagação de
multiplicadores) e `tests/test_geometria.py` (extensão — impressão do
backtest real, se aplicável)

**Target Platform**: CLI local (`python main.py geometria`, já
existente); produção intocada

**Performance Goals**: mesma ordem de grandeza de `run_modelo_scan` já
usado por `cmd_geometria` (spec 048)

**Constraints**: FR-002 — `params=None`/default MUST reproduzir H14/H17
byte a byte; FR-006 — não decide aprovação operacional

**Scale/Scope**: 2 linhas alteradas em `avaliar_par` (kwargs
adicionados às duas chamadas de `_resultado_modelo`), extensão de
`cmd_geometria()` para imprimir backtest por par

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre a propagação (cenário sintético de TP em 2×ATR) e a regressão do caminho default antes de qualquer medição real. |
| **IV. Incremental Delivery** | **Conforme.** Correção + testes num tópico; medição real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, extensão do já existente. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** A lacuna (D1) e por que é retrocompatível por construção (D2) declaradas no `spec.md`/Contexto antes de qualquer código — auditoria de código feita antes de escrever a spec, não depois de um resultado estranho. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/049-h20-backtest-real/
├── plan.md
├── data-model.md
└── quickstart.md
```

Sem `research.md`: a decisão já está totalmente declarada em
`spec.md`/Contexto (achado de auditoria, não escolha de projeto).
Sem `contracts/`.

### Source Code (repository root)

```text
backtesting/
└── modelo.py               # ~avaliar_par: propaga atr_tp_multiplier/
                             # atr_sl_multiplier de ParametrosBarreira

main.py                     # ~cmd_geometria: +backtest real por par

tests/
├── test_modelo.py           # +teste de propagacao +regressao do default
└── test_geometria.py        # ~teste de cmd_geometria, se aplicavel
```

## Complexity Tracking

Vazio.

## Fases

**Fase 1 ✅** — `data-model.md` + `quickstart.md`. Sem `research.md`
nem `contracts/`.

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: propagação + testes + extensão de
`cmd_geometria` num tópico; execução real (VPS) + registro noutro.
