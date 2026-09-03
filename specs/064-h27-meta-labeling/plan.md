# Implementation Plan: H27 — meta-labeling, pré-condição sobre o sinal primário

**Branch**: `064-h27-meta-labeling` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/meta_labeling.py` (novo): `avaliar_precondicao(pares, params)`
gera os eventos de entrada do sinal primário (`precompute_signals`),
rotula via barreira tripla (`rotular`), compara a razão de chances da
entrada primária contra o baseline de todos os candles, aplicando
`supera_empate_com_confianca` (reuso de `backtesting/modelo.py`, sem
alteração). `cmd_meta_labeling()` (novo, `main.py`) imprime o veredito.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `backtesting/engine.py::precompute_signals`,
`strategy/barreira_tripla.py::rotular`, `backtesting/modelo.py::limiar_de_empate`/
`supera_empate_com_confianca`, todos reusados sem alteração

**Storage**: `reports/meta_labeling_*.json` (padrão `export_report`)

**Testing**: pytest — contagem por rótulo bruto, razão infinita sem stop,
pré-condição atendida com amostra grande e razão alta, pré-condição não
atendida espelhando o achado real medido, pares sem prep são excluídos,
`ValueError` quando nenhum par produz dado, pares passados são
respeitados (não o universo default)

**Target Platform**: CLI local (`python main.py meta_labeling`); produção
intocada

**Performance Goals**: mesma ordem de custo de `python main.py modelo`
(12 pares × 6.000 candles) — aceitável para comando de pesquisa

**Constraints**: FR-005 — nenhum modelo secundário nesta spec, só a
pré-condição; FR-003 — significância sempre via `supera_empate_com_confianca`

**Scale/Scope**: 1 módulo novo (~90 linhas), 1 comando CLI novo

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre a lógica de comparação antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Módulo + comando + testes num tópico; execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Hipótese (H1 já reprovado isoladamente, risco de filtrar ruído) e critério de pré-condição declarados em `spec.md`/`research.md` antes de qualquer medição. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/064-h27-meta-labeling/
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
└── meta_labeling.py    # novo: avaliar_precondicao, _resumo

main.py                 # +cmd_meta_labeling, +"meta_labeling" em COMMANDS

tests/
└── test_meta_labeling.py   # novo
```

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — hipótese e risco (H1 já reprovado isoladamente)
declarados em `spec.md`; `research.md` documenta o diagnóstico ad-hoc que
motivou a spec e o resultado real medido.

**Fase 1** — sem `data-model.md`/`contracts/` formais (entidades
triviais, já descritas em `spec.md`).

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: módulo + comando + testes num tópico;
execução real + registro noutro.
