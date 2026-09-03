# Implementation Plan: H20 — isolando o efeito do custo de execução

**Branch**: `050-h20-custo-de-execucao` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

Estende `cmd_geometria()` (`main.py`, specs 048/049): para cada `a` em
`avaliacoes` (já produzido por `run_modelo_scan`), imprime
`a.modelo.backtest.total_return_pct` (com custo, já impresso desde
spec 049) ao lado de `a.retorno_sem_custo_modelo` (sem custo, campo já
calculado por `avaliar_par`, nunca antes exposto) e a fração
consumida. Nenhuma mudança em `backtesting/modelo.py` — o campo já
existe e já reflete a geometria correta desde a correção de spec 049.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `backtesting/modelo.py`
(campo já existente), `main.py::cmd_geometria` (spec 048/049)

**Storage**: `reports/geometria_estendida_*.json` (extensão do já
existente)

**Testing**: pytest — teste mínimo confirmando que a fração consumida
é calculada corretamente sobre valores conhecidos

**Target Platform**: CLI local (`python main.py geometria`, extensão);
produção intocada

**Performance Goals**: nenhum custo adicional — reusa `avaliacoes` já
computado, nenhuma chamada de rede/backtest nova

**Constraints**: FR-001 — nenhum backtest novo, só exposição de campo
já calculado

**Scale/Scope**: extensão de ~15 linhas em `cmd_geometria()`

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** Teste da fórmula de fração consumida antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Extensão + teste num tópico; execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, extensão do já existente. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Por que este candidato primeiro (custo mais barato de medir, instrumento já pronto) declarado em spec.md/Contexto antes de qualquer código. Sem `research.md` — nada novo a decidir. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/050-h20-custo-de-execucao/
├── plan.md
└── quickstart.md
```

Sem `research.md` nem `data-model.md` (extensão trivial, já totalmente
descrita em spec.md/plan.md) nem `contracts/`.

### Source Code (repository root)

```text
main.py    # ~cmd_geometria: +comparacao com/sem custo por par
```

`backtesting/modelo.py` **não é alterado**.

## Complexity Tracking

Vazio.

## Fases

**Fase 1** — `tasks.md`.

**Fase 2** — implementação: extensão + teste num tópico; execução real
(VPS) + registro noutro.
