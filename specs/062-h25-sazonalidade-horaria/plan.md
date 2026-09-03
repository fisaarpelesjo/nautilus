# Implementation Plan: H25 — sazonalidade por sessão de negociação (hora do dia)

**Branch**: `062-h25-sazonalidade-horaria` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/sazonalidade.py` (novo): `filtrar_por_sessao` (pura, mascara
`BUY` fora da janela declarada, nunca toca `SELL`) +
`avaliar_sazonalidade` (roda `precompute_signals` → `filtrar_por_sessao`
→ `split_train_validation` → `simulate_backtest` →
`backtesting.multimarket.classify`, reusando toda a infraestrutura de
confirmação fora da amostra já existente, sem critério novo).
`cmd_sazonalidade()` (novo, `main.py`) roda sobre `UNIVERSO_H11` × 3
janelas, imprime as 36 combinações.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `backtesting.engine::precompute_signals`/
`simulate_backtest`, `backtesting.validation::split_train_validation`,
`backtesting.multimarket::classify`, todos reusados sem alteração

**Storage**: `reports/sazonalidade_*.json` (padrão `export_report`)

**Testing**: pytest — `filtrar_por_sessao` pura (bloqueia BUY fora da
janela, nunca toca SELL, preserva HOLD), tratamento de erro de busca
não interrompe a varredura, janelas cobrem as 24h sem sobreposição

**Target Platform**: CLI local (`python main.py sazonalidade`);
produção intocada (`strategy/ema_rsi.py` nunca é modificado)

**Performance Goals**: 36 combinações (3 janelas × 12 pares), cada uma
um backtest completo com split — mesma ordem de custo de
`python main.py horizonte`, aceitável para comando de pesquisa

**Constraints**: FR-001 — só `BUY` é mascarado, nunca `SELL`; FR-002 —
as três janelas são pré-registradas, nenhuma seleção post-hoc; FR-003 —
classificação via `classify()` já existente, nenhum critério novo

**Scale/Scope**: 1 módulo novo (~100 linhas), 1 comando CLI novo, zero
mudança em `strategy/`/`config/`

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`; `strategy/ema_rsi.py` nunca é tocado. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre a lógica pura de filtro e o tratamento de erro antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Módulo + comando + testes num tópico; execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão dos comandos de pesquisa. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Hipótese (ao menos uma combinação confirma) e alternativa (nenhuma confirma, fecha a família) declaradas em `spec.md`/`research.md` antes de qualquer medição real. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/062-h25-sazonalidade-horaria/
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
└── sazonalidade.py   # novo: filtrar_por_sessao, avaliar_sazonalidade

main.py                 # +cmd_sazonalidade, +"sazonalidade" em COMMANDS

tests/
└── test_sazonalidade.py   # novo
```

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — D1 (janelas pré-registradas), D2 (universo), D3
(disciplina estatística contra a armadilha de H5) declarados em
`research.md` antes de qualquer medição.

**Fase 1** — sem `data-model.md`/`contracts/` formais (entidade
trivial, já descrita em `spec.md`).

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: módulo + comando + testes num tópico;
execução real + registro noutro.
