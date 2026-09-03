# Implementation Plan: H20 reavaliada com histórico estendido

**Branch**: `048-h20-historico-estendido` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

Muda o argumento de `fetch_ohlcv(par, TIMEFRAME, 2000)` para `6000` em
`backtesting/geometria.py::run_geometria_scan` (linha 204) — mesmo
valor de `specs/036-historico-estendido/`. Roda `run_geometria_scan()`
(seleção de geometria) e, sobre a geometria selecionada, `run_modelo_
scan(params=ParametrosBarreira(tp_mult=..., sl_mult=1.5))` (avaliação
estatística, já migrada para 6.000 por spec 036) — mesmo procedimento
de `specs/028-geometria-de-barreira/`, D3/D4, intocado.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `backtesting/geometria.py`
(spec 028), `backtesting/modelo.py` (já migrado, spec 036)

**Storage**: `reports/geometria_estendida_*.json` (padrão
`export_report` já existente)

**Testing**: pytest, `tests/test_geometria.py` (extensão mínima — só
confirmar que o teto mudou; a lógica de seleção não muda)

**Target Platform**: CLI local (`python main.py geometria`, novo
comando — H20 nunca teve um); produção intocada

**Performance Goals**: mesma ordem de grandeza dos módulos já migrados
por spec 036 (12 pares, 6.000 candles, ~35s de fetch)

**Constraints**: FR-002 — a regra de seleção de geometria não muda;
FR-003 — o procedimento de avaliação estatística não muda

**Scale/Scope**: 1 constante alterada (`2000`→`6000`), 1 comando CLI
novo (H20 nunca foi wired ao `main.py`)

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre a mudança do teto antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Mudança do teto + comando CLI num tópico; execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão dos demais comandos de pesquisa. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** D1 (reuso do teto sem remedição), D2 (nenhuma mudança na avaliação estatística) e D3 (correção da premissa inicial sobre M13) declarados em `research.md` antes de qualquer código. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/048-h20-historico-estendido/
├── plan.md
├── research.md
├── data-model.md
└── quickstart.md
```

### Source Code (repository root)

```text
backtesting/
└── geometria.py           # ~run_geometria_scan: 2000 -> 6000

main.py                    # +cmd_geometria (H20 nunca teve comando CLI)

tests/
└── test_geometria.py       # ~teste do teto de candles
```

`backtesting/modelo.py` **não é alterado** — já migrado por spec 036.

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — D1 (reuso do teto), D2 (avaliação estatística
inalterada), D3 (correção da premissa sobre M13).

**Fase 1 ✅** — `data-model.md` + `quickstart.md`. Sem `contracts/`.

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: mudança do teto + teste + comando CLI num
tópico; execução real (VPS) + registro noutro.
