# Implementation Plan: H14 — calibração do classificador de entrada

**Branch**: `055-h14-calibracao-classificador` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/calibracao_h14.py` (novo): `avaliar_calibracao(pares, params, cortes)`
reusa `avaliar_par(..., retornar_previsao=True)` + `rotular` para poolar
previsão/rótulo bruto de `UNIVERSO_H11`, agrupa por corte de probabilidade
(`_faixas_por_corte`, pura e testável sem dado real) e aplica
`supera_empate_com_confianca` por faixa. `cmd_calibracao()` (novo,
`main.py`) imprime a tabela e exporta via `export_report`.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `backtesting/modelo.py`
(`avaliar_par`, `coletar_eventos`, `limiar_de_decisao`, `limiar_de_empate`,
`supera_empate_com_confianca`, todos sem alteração),
`strategy/barreira_tripla.py::rotular` (sem alteração)

**Storage**: `reports/calibracao_*.json` (padrão `export_report`)

**Testing**: pytest — `_faixas_por_corte` pura (contagem alvo/stop/tempo,
sentinela de corte 0, razão infinita sem stop, significância via amostra
grande vs. pequena) + `avaliar_calibracao` com `_previsoes_pooladas`
mockada (sem buscar dado real)

**Target Platform**: CLI local (`python main.py calibracao`); produção
intocada

**Performance Goals**: mesma ordem de custo de `python main.py modelo`
(12 pares × `avaliar_par` sobre 6.000 candles) — aceitável para comando
de pesquisa, já rodado antes em specs 036/037

**Constraints**: FR-002 — contagem via `rotulo_bruto`, não `rotulo`
(que colapsa stop e tempo); FR-003 — significância sempre por faixa via
`supera_empate_com_confianca`, nunca razão pontual isolada

**Scale/Scope**: 1 módulo novo (~100 linhas), 1 comando CLI novo

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre a lógica pura de binning antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Módulo + comando + testes num tópico; execução real (VPS) + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão dos comandos de pesquisa. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Hipótese (cauda de alta confiança) e alternativa (achatada) declaradas em `spec.md`/`research.md` antes de qualquer medição nova. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/055-h14-calibracao-classificador/
├── spec.md
├── plan.md
├── research.md
├── quickstart.md
└── checklists/
    └── requirements.md
```

Sem `data-model.md` formal separado (entidades já descritas em
`spec.md`) nem `contracts/` (sem interface externa).

### Source Code (repository root)

```text
backtesting/
└── calibracao_h14.py   # novo: avaliar_calibracao, _faixas_por_corte

main.py                 # +cmd_calibracao, +"calibracao" em COMMANDS

tests/
└── test_calibracao_h14.py   # novo
```

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — D1 (diagnóstico ad-hoc que motivou a spec, incluindo o
bug de rotulagem corrigido no meio do processo), D2 (hipótese declarada
antes da medição final).

**Fase 1** — sem `data-model.md`/`contracts/` formais (entidades
triviais, já descritas em `spec.md`).

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: módulo + comando + testes num tópico;
execução real (VPS) + registro noutro.
