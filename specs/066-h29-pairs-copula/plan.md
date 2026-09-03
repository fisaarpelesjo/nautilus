# Implementation Plan: H29 — pairs trading via cópula gaussiana

**Branch**: `066-h29-pairs-copula` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/pairs_copula.py` (novo): `ajustar_copula_gaussiana`/
`h_condicional` (cópula gaussiana bivariada, forma fechada) +
`run_pairs_copula_backtest`/`run_pairs_copula_scan` (mesma estrutura de
`run_pairs_backtest`/`run_pairs_scan` de H10, sinal trocado de z-score
para h condicional). `cmd_pairs_copula()` (novo, `main.py`) roda sobre
`UNIVERSO_AMPLO_HISTORICO_COMPLETO` e compara contra H10 (spec 054).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: `scipy.stats.norm` — já instalado como
dependência transitiva, mas nunca declarado; adicionado a
`requirements-dev.txt` (mesmo padrão de `statsmodels`/H10: pesquisa
apenas, nunca entra em `requirements.txt` de produção). Nenhuma
biblioteca de cópula dedicada — a forma fechada da cópula gaussiana é
simples o bastante para não justificar isso.
`selecionar_pares`/`PairsParams`/`split_treino_validacao` de
`backtesting/pairs_trading.py` reusados sem alteração

**Storage**: `reports/pairs_copula_*.json` (padrão `export_report`)

**Testing**: pytest — forma fechada de `h_condicional` em casos
analíticos (rho=0, ponto de equilíbrio), `ajustar_copula_gaussiana`
recupera correlação forte/fraca construída, backtest opera par
cointegrado sintético sem exceção, histórico insuficiente não estoura,
`run_pairs_copula_scan` aceita dados sem rede

**Target Platform**: CLI local (`python main.py pairs_copula`);
produção intocada

**Performance Goals**: mesma ordem de custo de `python main.py
pairs_reselecao` (22 pares, 6.000 candles) — aceitável para comando de
pesquisa

**Constraints**: FR-001 — seleção de pares de H10 intocada; FR-002 —
sem vazamento de candle futuro no ajuste da cópula; FR-003 — uma
família de cópula, um corte, declarados antes de medir

**Scale/Scope**: 1 módulo novo (~230 linhas), 1 comando CLI novo

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre a forma fechada e o backtest sintético antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Módulo + comando + testes num tópico; execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão dos comandos `pairs_*`. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Precondição de cointegração verificada com dado real ANTES de escrever o módulo (D1, `research.md`) — hipótese e alternativa declaradas antes de medir. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/066-h29-pairs-copula/
├── spec.md
├── plan.md
├── research.md
├── quickstart.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
backtesting/
└── pairs_copula.py     # novo: ajustar_copula_gaussiana, h_condicional,
                          # run_pairs_copula_backtest, run_pairs_copula_scan

main.py                  # +cmd_pairs_copula, +"pairs_copula" em COMMANDS

tests/
└── test_pairs_copula.py    # novo
```

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — precondição de cointegração verificada com dado real
antes de qualquer código; hipótese e alternativa declaradas em
`spec.md`/`research.md`.

**Fase 1** — sem `data-model.md`/`contracts/` formais (entidade
trivial, já descrita em `spec.md`).

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: módulo + comando + testes num tópico;
execução real + registro noutro.
