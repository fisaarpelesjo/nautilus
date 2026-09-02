# Implementation Plan: Histórico estendido para reavaliação de hipóteses

**Branch**: `036-historico-estendido` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

## Summary

Troca `2000` por `6000` (D1, medido para os 12 pares de `UNIVERSO_H11`)
nos chamadores de `fetch_ohlcv` de `backtesting/modelo.py`
(H14, `avaliar_par`/`coletar_eventos`), `backtesting/onchain_hipotese.py`
(H17, `avaliar_h17`) e `backtesting/horizonte.py` (H11,
`run_horizonte_scan`/`medir_disponibilidade`). `run_backtest`
(`backtesting/engine.py`, usado por comandos de uso geral) não muda
(D2). H10 fica fora do escopo (D3, sem CLI hoje). Reavalia H14/H17/H11
(4h/1d) com o histórico novo e registra os resultados no
registro-mestre, comparados explicitamente contra os já publicados.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `data/fetcher.py::fetch_ohlcv`
já pagina (spec 011)

**Storage**: N/A

**Testing**: pytest — testes existentes de `modelo.py`/
`onchain_hipotese.py`/`horizonte.py` continuam passando com o novo
default (a maioria já passa `df`/candles sintéticos diretamente, não
depende do valor de `2000`/`6000`)

**Target Platform**: CLI (`python main.py modelo`, `onchain`,
`horizonte`); produção e comandos de uso geral intocados

**Performance Goals**: ~35s adicionais por reavaliação completa do
universo (medido, research.md D1) — aceitável para execução pontual

**Constraints**: FR-005 — `run_backtest`/`backtest`/`edge`/`compare`/
`scan`/`optimize` MUST permanecer intocados

**Scale/Scope**: 3 arquivos (`modelo.py`, `onchain_hipotese.py`,
`horizonte.py`), ~5 constantes trocadas

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulos de pesquisa, sem import por `trading/`/`execution/`/`risk/`. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` roda a suite existente antes e depois de cada troca, confirmando zero regressão de comportamento nos testes que já fixam valores com `df` sintético. |
| **IV. Incremental Delivery** | **Conforme.** Um tópico por hipótese reavaliada (H17, H14, H11). |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, já existente. |
| **VI. Idempotency and Reconciliation** | **N/A.** |
| **VII. Explain Before Code** | **Conforme.** D1-D3 medidos e commitados antes de qualquer troca de constante. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/036-historico-estendido/
├── plan.md / research.md / data-model.md / quickstart.md
```

Sem `contracts/` — ajuste de constante em comandos já existentes, sem
interface nova.

### Source Code (repository root)

```text
backtesting/
├── modelo.py             # 2000 -> 6000 (avaliar_par, coletar_eventos)
├── onchain_hipotese.py   # 2000 -> 6000 (avaliar_h17)
└── horizonte.py          # 2000 -> 6000 (solicitado default)
```

`backtesting/engine.py`, `backtesting/pairs_trading.py`,
`backtesting/scanner.py`, `backtesting/grid.py`,
`backtesting/geometria.py` **não são tocados** (D2/D3 — fora do escopo
desta reavaliação específica; `grid.py`/`geometria.py` não estão entre
H10/H11/H14/H17 e ficam como estão).

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — D1 (6000, medido) → D2 (escopo dos chamadores) → D3 (H10
fora).

**Fase 1 ✅** — `data-model.md` + `quickstart.md`. Sem `contracts/`.

**Fase 2** — `tasks.md`.

**Fase 3** — implementação, três tópicos (um por hipótese reavaliada):
H17 → H14 → H11 (4h/1d), cada um com a troca de constante, execução real,
e registro do resultado comparado ao publicado.
