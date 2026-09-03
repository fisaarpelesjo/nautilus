# Implementation Plan: Gate de correlação na carteira de H14

**Branch**: `042-gate-correlacao-carteira-h14` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/portfolio_h14.py::_correlacionado_com_posicao_aberta(par,
preparados, posicoes_abertas, t)` — nova função, mesma semântica e
mesmos limiares de `risk/correlation.py::check_correlated_exposure`,
mas sobre dados já carregados e fatiados até `t` (sem fetch, sem
vazamento de futuro, D1). `_simular_carteira_core` ganha
`usar_gate_correlacao: bool = False`; quando `True`, pula (não abre) um
candidato correlacionado com qualquer posição já aberta, antes do
dimensionamento.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `config/settings.py`
(`MAX_POSITION_CORRELATION`, `CORRELATION_LOOKBACK`, já existentes),
`backtesting/portfolio_h14.py` (spec 037/041)

**Storage**: `reports/carteira_corr_*.json` (padrão `export_report` já
existente)

**Testing**: pytest, `tests/test_portfolio_h14.py` (extensão)

**Target Platform**: CLI local (`python main.py carteira_corr`);
produção intocada

**Performance Goals**: mesma ordem de grandeza de `carteira`/`carteira_vol`
(spec 037/041, 12 pares) — a checagem de correlação é sobre dados já em
memória, sem custo de rede adicional

**Constraints**: FR-002 — a checagem MUST usar só dados até `t`; FR-005 —
comportamento default idêntico byte a byte ao já publicado

**Scale/Scope**: 1 função nova (ponto-no-tempo), 1 parâmetro novo em
função já existente, 1 comando CLI

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/` (FR-007) — a checagem ponto-no-tempo é código de pesquisa novo, distinto do gate de produção. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre bloqueio/não-bloqueio e a regressão do caminho default antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Função + parâmetro + regressão num tópico; comando CLI + execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão de `carteira`/`carteira_vol`. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** D1 (por que não chamar `check_correlated_exposure` direto, e como a versão ponto-no-tempo preserva a mesma semântica/limiares) declarado em `research.md` antes de qualquer código. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/042-gate-correlacao-carteira-h14/
├── plan.md              # este arquivo
├── research.md          # Fase 0 (D1)
├── data-model.md         # Fase 1
└── quickstart.md         # Fase 1
```

Sem `contracts/`: comando de pesquisa segue o padrão já estabelecido.

### Source Code (repository root)

```text
backtesting/
└── portfolio_h14.py       # +_correlacionado_com_posicao_aberta(...);
                            # ~_simular_carteira_core/simular_carteira
                            # ganham usar_gate_correlacao=False (opt-in)

main.py                    # +cmd_carteira_corr

tests/
└── test_portfolio_h14.py   # +testes de bloqueio/nao-bloqueio +regressao
```

`risk/correlation.py`, `backtesting/engine.py`, `backtesting/approval.py`
**não são alterados** — só consultados como referência de limiares.

## Complexity Tracking

Vazio — nenhuma violação de princípio a justificar.

## Fases

**Fase 0 ✅** — D1 (checagem ponto-no-tempo em vez de chamar
`check_correlated_exposure` direto — por quê, e como preserva a mesma
semântica/limiares).

**Fase 1 ✅** — `data-model.md` + `quickstart.md`. Sem `contracts/`.

**Fase 2** — `tasks.md` (`/speckit-tasks`).

**Fase 3** — implementação (`/speckit-implement`), dois tópicos:
1. `_correlacionado_com_posicao_aberta` + `usar_gate_correlacao` +
   regressão do caminho default
2. `cmd_carteira_corr()` (CLI) + execução real (VPS) + comparação
   registrada em `docs/research/registro-de-hipoteses.md` §4.15
