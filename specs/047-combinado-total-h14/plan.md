# Implementation Plan: Combinação total (teto) dos mecanismos de risco não-degenerados na carteira de H14

**Branch**: `047-combinado-total-h14` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

Chama `simular_carteira(pares=UNIVERSO_H11, usar_dimensionamento_vol=True,
usar_gate_correlacao=True, usar_limite_drawdown_diario=True)` — os três
parâmetros já existem (specs 041/042/045) e já compõem corretamente
dentro de `_simular_carteira_core`. Nenhuma mudança de código em
`backtesting/portfolio_h14.py` — só um comando CLI novo e uma medição.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `backtesting/portfolio_h14.py`
(spec 037/041/042/045), sem mudança de código

**Storage**: `reports/carteira_teto_*.json` (padrão `export_report` já
existente)

**Testing**: pytest, `tests/test_portfolio_h14.py` (extensão mínima —
só confirmar que as três flags juntas não quebram)

**Target Platform**: CLI local (`python main.py carteira_teto`);
produção intocada

**Performance Goals**: mesma ordem de grandeza dos comandos
`carteira_*` anteriores (12 pares)

**Constraints**: FR-003 — nunca substituir os sete resultados já
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
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** A expectativa (resultado perto do gate de correlação sozinho, não soma aditiva) já declarada em spec.md antes de medir. Sem `research.md` — nada novo a decidir. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/047-combinado-total-h14/
├── plan.md
├── data-model.md
└── quickstart.md
```

### Source Code (repository root)

```text
main.py                    # +cmd_carteira_teto

tests/
└── test_portfolio_h14.py   # +teste de integracao das tres flags juntas
```

`backtesting/portfolio_h14.py` **não é alterado**.

## Complexity Tracking

Vazio.

## Fases

**Fase 1 ✅** — `data-model.md` + `quickstart.md`.

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: teste + CLI num tópico; execução real +
registro noutro.
