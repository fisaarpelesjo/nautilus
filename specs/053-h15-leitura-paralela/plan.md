# Implementation Plan: H15 — leitura das corretoras em paralelo

**Branch**: `053-h15-leitura-paralela` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/arbitragem.py::medir_ciclo` troca a comprehension
sequencial `{corretora: ler_livro(corretora, par) for corretora in
CORRETORAS}` por `ThreadPoolExecutor.map` — mesma assinatura de
`ler_livro`, mesmo tratamento de falha isolada, só a ordem de execução
muda. `_get_exchange_publico` ganha um `threading.Lock` ao redor da
escrita em `_exchange_cache` (defensivo).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: `concurrent.futures` (stdlib, já disponível),
`threading` (stdlib) — nenhuma dependência nova

**Storage**: `data/arbitragem.jsonl` (inalterado)

**Testing**: pytest, `tests/test_arbitragem.py` (extensão — tempo total
do ciclo com latência simulada, regressão de falha isolada)

**Target Platform**: CLI local (`python main.py arbitragem`, já
existente); produção intocada

**Performance Goals**: ciclo completo em ~1 leitura (paralelo) em vez
de ~6 leituras somadas (sequencial) — de ~32s medido para próximo do
tempo da corretora mais lenta

**Constraints**: FR-002 — falha isolada de uma corretora não pode
afetar as demais nem abortar o ciclo, mesmo comportamento de spec 029

**Scale/Scope**: ~10 linhas alteradas em `medir_ciclo` +
`_get_exchange_publico`

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre o tempo total (paralelismo real, não só aparente) e a regressão de falha isolada antes de qualquer medição real. |
| **IV. Incremental Delivery** | **Conforme.** Correção + testes num tópico; execução real (nova campanha) + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Mesmo `data/arbitragem.jsonl`/`export_report` já existentes. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Por que threads (não asyncio) e o risco declarado do cache sob concorrência estão em spec.md/Contexto antes de qualquer código. Sem `research.md` — decisão já totalmente declarada no spec.md, acionada por um achado (M15) já catalogado, não uma escolha de projeto nova. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/053-h15-leitura-paralela/
├── plan.md
└── quickstart.md
```

Sem `research.md`/`data-model.md` (correção pontual já totalmente
descrita em spec.md) nem `contracts/`.

### Source Code (repository root)

```text
backtesting/
└── arbitragem.py    # ~medir_ciclo (ThreadPoolExecutor)
                      # ~_get_exchange_publico (lock defensivo)

tests/
└── test_arbitragem.py   # +teste de tempo total paralelo
                          # +regressao de falha isolada sob paralelismo
```

## Complexity Tracking

Vazio.

## Fases

**Fase 1** — `tasks.md`.

**Fase 2** — implementação: correção + testes num tópico; execução
real (nova campanha na VPS) + registro noutro.
