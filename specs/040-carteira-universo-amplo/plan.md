# Implementation Plan: Carteira de H14 sobre universo amplo

**Branch**: `040-carteira-universo-amplo` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/portfolio_h14.py::simular_carteira(pares=UNIVERSO_AMPLO)`
(reusa a função já existente da spec 037, só troca o argumento `pares`)
simula a carteira de H14 sobre 34 pares (D1) em vez de 12, mantendo
`MAX_POSITIONS`, barreiras, mecanismo de saída e dimensionamento
idênticos (FR-002/FR-003). `comparar_drawdown` (já existente) mostra o
resultado lado a lado com o já publicado sobre 12 pares.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `backtesting/portfolio_h14.py`
(`simular_carteira`, `_dados_da_carteira`, `comparar_drawdown`, todos já
existentes, spec 037), `backtesting/approval.py::evaluate_approval`

**Storage**: `reports/carteira_ampla_*.json` (padrão `export_report` já
existente)

**Testing**: pytest, `tests/test_portfolio_h14.py` (extensão pequena —
o universo é só uma lista de símbolos, a mecânica já está testada)

**Target Platform**: CLI local (`python main.py carteira_ampla`);
produção intocada

**Performance Goals**: ~34 fetches de 6.000 candles + 1 treino de modelo
pooled — mais pesado que a carteira de 12 pares (spec 037); rodar na VPS
(`vps-limulus`/`nautilus-research`)

**Constraints**: FR-003 — `MAX_POSITIONS` MUST permanecer no valor de
produção; FR-005 — nenhuma ordem real

**Scale/Scope**: 1 constante nova (`UNIVERSO_AMPLO`, 34 pares) em
`backtesting/portfolio_h14.py` ou módulo próprio, 1 comando CLI

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/` (FR-005). |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre a lista do universo e a chamada de `simular_carteira` com o novo universo antes da implementação do comando CLI. |
| **IV. Incremental Delivery** | **Conforme.** Universo + comando CLI num tópico; execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão de `carteira`/`pairs`/`leadlag`. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** D1 (universo de 34 pares, medido antes do código) e D2 (MAX_POSITIONS fixo, isolando a variável) declarados em `research.md`. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/040-carteira-universo-amplo/
├── plan.md              # este arquivo
├── research.md          # Fase 0 (D1-D2)
├── data-model.md         # Fase 1
└── quickstart.md         # Fase 1
```

Sem `contracts/`: comando de pesquisa segue o padrão já estabelecido.

### Source Code (repository root)

```text
backtesting/
└── portfolio_h14.py       # +UNIVERSO_AMPLO (34 pares, constante),
                            # simular_carteira/_dados_da_carteira/
                            # comparar_drawdown ja existentes, sem
                            # alteracao

main.py                    # +cmd_carteira_ampla

tests/
└── test_portfolio_h14.py   # +teste de UNIVERSO_AMPLO
```

`backtesting/engine.py`, `backtesting/approval.py`,
`backtesting/portfolio_h14.py::_simular_carteira_core`/`simular_carteira`
**não são alterados** — só consumidos com um argumento `pares` diferente.

## Complexity Tracking

Vazio — nenhuma violação de princípio a justificar.

## Fases

**Fase 0 ✅** — D1 (universo de 34 pares, medido) → D2 (`MAX_POSITIONS`
fixo, isola a variável de pool size).

**Fase 1 ✅** — `data-model.md` + `quickstart.md`. Sem `contracts/`.

**Fase 2** — `tasks.md` (`/speckit-tasks`).

**Fase 3** — implementação (`/speckit-implement`), dois tópicos:
1. `UNIVERSO_AMPLO` (constante) + teste de wiring
2. `cmd_carteira_ampla()` (CLI) + execução real (VPS) + comparação
   registrada em `docs/research/registro-de-hipoteses.md` §4.15
