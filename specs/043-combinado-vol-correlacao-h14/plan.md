# Implementation Plan: Combinação dimensionamento por volatilidade + gate de correlação na carteira de H14

**Branch**: `043-combinado-vol-correlacao-h14` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`simular_carteira(pares=UNIVERSO_H11, usar_dimensionamento_vol=True,
usar_gate_correlacao=True)` — chamada direta com os dois parâmetros já
existentes (spec 041/042) simultaneamente. Nenhuma mudança em
`backtesting/portfolio_h14.py` além de, se necessário, um teste de
integração confirmando que as duas flags coexistem sem conflito.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `backtesting/portfolio_h14.py`
(`simular_carteira`, `usar_dimensionamento_vol`/`usar_gate_correlacao`,
já existentes)

**Storage**: `reports/carteira_combo_*.json` (padrão `export_report` já
existente)

**Testing**: pytest, `tests/test_portfolio_h14.py` (1 teste de
integração)

**Target Platform**: CLI local (`python main.py carteira_combo`);
produção intocada

**Performance Goals**: mesma ordem de grandeza de `carteira_corr`
(spec 042, o mais pesado dos overlays individuais)

**Constraints**: nenhuma nova — herda as de spec 041/042

**Scale/Scope**: 1 comando CLI, 1 teste de integração — sem mudança de
mecânica

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Sem import por `trading/`, `execution/` ou `risk/` (FR-004). |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** 1 teste de integração confirma coexistência das duas flags antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Teste + comando CLI + execução real + registro, um único tópico dado o tamanho pequeno. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão das demais. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Nada novo a declarar — os dois mecanismos já foram declarados e medidos individualmente (spec 041/042). |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/043-combinado-vol-correlacao-h14/
├── plan.md              # este arquivo
├── data-model.md         # Fase 1 (sem Fase 0/research.md -- nada novo a decidir)
└── quickstart.md         # Fase 1
```

Sem `research.md`: todas as decisões relevantes já estão em spec
037/041/042. Sem `contracts/`.

### Source Code (repository root)

```text
main.py                    # +cmd_carteira_combo

tests/
└── test_portfolio_h14.py   # +1 teste de integracao (as duas flags juntas)
```

`backtesting/portfolio_h14.py` **não é alterado** — os dois parâmetros já
existem, só são chamados juntos.

## Complexity Tracking

Vazio — nenhuma violação de princípio a justificar.

## Fases

**Fase 1 ✅** — `data-model.md` + `quickstart.md`. Sem Fase 0
(`research.md`) — nada novo a decidir. Sem `contracts/`.

**Fase 2** — `tasks.md` (`/speckit-tasks`).

**Fase 3** — implementação (`/speckit-implement`), um único tópico:
teste de integração + `cmd_carteira_combo()` (CLI) + execução real (VPS)
+ comparação registrada em
`docs/research/registro-de-hipoteses.md` §4.15.
