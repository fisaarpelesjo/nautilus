# Implementation Plan: H20 — decompondo o custo de execução

**Branch**: `051-h20-decomposicao-custo` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/modelo.py::avaliar_par`, bloco "E6 — custo de giro":
adiciona duas chamadas irmãs de `_simular_com_sinais` (mesma função já
usada para `retorno_sem_custo_modelo`), cada uma zerando só um
parâmetro — `slippage_pct=0.0` (taxa real) e `fee_rate=0.0` (slippage
real) — populando `AvaliacaoH14.retorno_sem_slippage_modelo`/
`retorno_sem_taxa_modelo`. `cmd_geometria()` (`main.py`) ganha a
impressão dos dois novos campos ao lado do já existente.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `backtesting/modelo.py`,
`_simular_com_sinais`/`simulate_backtest` já aceitam `fee_rate`/
`slippage_pct` independentes

**Storage**: `reports/geometria_estendida_*.json` (extensão do já
existente)

**Testing**: pytest — extensão do teste de propagação de spec 049
(confirma que os dois novos campos usam a geometria correta) +
regressão do campo já existente

**Target Platform**: CLI local (`python main.py geometria`, extensão);
produção intocada

**Performance Goals**: 2 chamadas adicionais de `_simular_com_sinais`
por par (mesma ordem de grandeza da já existente, custo desprezível)

**Constraints**: FR-002 — `retorno_sem_custo_modelo` e todo resultado
já publicado permanecem inalterados

**Scale/Scope**: 2 campos novos em `AvaliacaoH14`, 2 chamadas novas no
bloco E6, extensão de `cmd_geometria()`

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** Teste confirma os dois novos campos zeram só o parâmetro pretendido antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Campos + teste + extensão CLI num tópico; execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, extensão do já existente. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Por que decompor (taxa é imutável por tipo de ordem, slippage não) e a ressalva sobre o teto otimista de "sem slippage" (ordens limit só afetam entrada) declaradas em spec.md/Contexto antes de qualquer código. Sem `research.md` — nada novo a decidir. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/051-h20-decomposicao-custo/
├── plan.md
└── quickstart.md
```

Sem `research.md`/`data-model.md` (extensão simétrica trivial, já
descrita em spec.md/plan.md) nem `contracts/`.

### Source Code (repository root)

```text
backtesting/
└── modelo.py     # ~AvaliacaoH14: +2 campos; ~avaliar_par (E6): +2 chamadas

main.py           # ~cmd_geometria: +2 colunas na comparacao de custo

tests/
└── test_modelo.py   # +teste de propagacao dos dois novos campos
```

## Complexity Tracking

Vazio.

## Fases

**Fase 1** — `tasks.md`.

**Fase 2** — implementação: campos + teste + extensão CLI num tópico;
execução real (VPS) + registro noutro.
