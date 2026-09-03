# Implementation Plan: H14 — saída por barreira tripla + gate de correlação

**Branch**: `057-h14-barreira-correlacao` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

Zero mecânica nova em `backtesting/portfolio_h14.py` — `usar_saida_barreira`
(spec 056) e `usar_gate_correlacao` (spec 042) já são parâmetros
independentes de `_simular_carteira_core`/`simular_carteira`.
`cmd_carteira_barreira_corr()` (novo, `main.py`) chama
`simular_carteira(usar_saida_barreira=True, usar_gate_correlacao=True)`
sobre `UNIVERSO_H11` e compara contra os três resultados já publicados
(baseline sem overlay, spec 037; só barreira, spec 056; só correlação,
spec 042).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — os dois mecanismos já existem
e são compostos sem alteração de código de produção

**Storage**: `reports/carteira_barreira_corr_*.json` (padrão `export_report`)

**Testing**: pytest — as duas flags juntas não quebram (gate ainda
bloqueia candidato correlacionado), stop continua fixo sob o modo
combinado (o gate não interfere na mecânica de saída)

**Target Platform**: CLI local (`python main.py carteira_barreira_corr`);
produção intocada

**Performance Goals**: mesma ordem de custo de `python main.py carteira`
(já publicado) — aceitável para comando de pesquisa

**Constraints**: FR-001 — nenhum parâmetro novo, nenhuma mecânica nova;
FR-004 — registro deve dizer explicitamente aditividade ou dominância

**Scale/Scope**: 1 comando CLI novo, 2 testes novos

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre a composição das duas flags antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Comando + testes num tópico; execução real (VPS) + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão dos comandos `carteira_*`. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Hipótese de aditividade e alternativa de dominância declaradas em `spec.md`/`research.md` antes de qualquer medição. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/057-h14-barreira-correlacao/
├── spec.md
├── plan.md
├── research.md
├── quickstart.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
main.py                 # +cmd_carteira_barreira_corr, +"carteira_barreira_corr" em COMMANDS

tests/
└── test_portfolio_h14.py   # +2 testes (combo nao quebra, stop continua fixo)
```

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — hipótese de aditividade e alternativa de dominância
declaradas em `spec.md`; `research.md` documenta por que esta
combinação difere estruturalmente das duas anteriores (043/046).

**Fase 1** — sem `data-model.md`/`contracts/` (zero entidade nova).

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: comando + testes num tópico; execução real
(VPS) + registro noutro.
