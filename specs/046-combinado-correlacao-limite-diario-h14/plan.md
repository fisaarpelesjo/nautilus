# Implementation Plan: Combinação gate de correlação + limite de drawdown diário na carteira de H14

**Branch**: `046-combinado-correlacao-limite-diario-h14` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

Chama `simular_carteira(pares=UNIVERSO_H11, usar_gate_correlacao=True,
usar_limite_drawdown_diario=True)` — os dois parâmetros já existem
(spec 042, spec 045) e já são compostos corretamente dentro de
`_simular_carteira_core` (ordem declarada em
`specs/045-limite-drawdown-diario-h14/data-model.md`: limite diário
roda antes do circuit breaker e do gate de correlação). Nenhuma mudança
de código em `backtesting/portfolio_h14.py` — só um comando CLI novo e
uma medição.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `backtesting/portfolio_h14.py`
(spec 037/042/045), sem mudança de código

**Storage**: `reports/carteira_combo2_*.json` (padrão `export_report`
já existente)

**Testing**: pytest, `tests/test_portfolio_h14.py` (extensão mínima —
só confirmar que as duas flags juntas não quebram, mesmo padrão de
spec 043)

**Target Platform**: CLI local (`python main.py carteira_combo2`);
produção intocada

**Performance Goals**: mesma ordem de grandeza dos comandos
`carteira_*` anteriores (12 pares)

**Constraints**: FR-003 — nunca substituir os seis resultados já
publicados no registro

**Scale/Scope**: 1 teste de integração, 1 comando CLI — zero mudança em
`_simular_carteira_core`/`simular_carteira`

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre a combinação sintética antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Teste + comando CLI num tópico; execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão dos comandos `carteira_*` anteriores. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Nenhuma decisão de design nova — spec.md já declara a tese (mecanismos ortogonais, sobreposição esperada menor que em spec 043) antes de medir. Sem `research.md` — nada novo a decidir, mesmo padrão de spec 043. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/046-combinado-correlacao-limite-diario-h14/
├── plan.md              # este arquivo
├── data-model.md         # Fase 1
└── quickstart.md         # Fase 1
```

Sem `research.md` (nada novo a decidir, mesmo padrão de spec 043) nem
`contracts/`.

### Source Code (repository root)

```text
main.py                    # +cmd_carteira_combo2

tests/
└── test_portfolio_h14.py   # +teste de integracao das duas flags juntas
```

`backtesting/portfolio_h14.py` **não é alterado** — os dois parâmetros
já existem e já compõem corretamente.

## Complexity Tracking

Vazio — nenhuma violação de princípio a justificar.

## Fases

**Fase 1 ✅** — `data-model.md` + `quickstart.md`. Sem `research.md`
nem `contracts/`.

**Fase 2** — `tasks.md` (`/speckit-tasks`).

**Fase 3** — implementação (`/speckit-implement`), dois tópicos:
1. Teste de integração (duas flags juntas não quebram) +
   `cmd_carteira_combo2()` (CLI)
2. Execução real (VPS) + comparação registrada em
   `docs/research/registro-de-hipoteses.md` §4.15
