# Implementation Plan: Limite de drawdown diário na carteira de H14

**Branch**: `045-limite-drawdown-diario-h14` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/portfolio_h14.py::_simular_carteira_core` ganha
`usar_limite_drawdown_diario: bool = False`. Quando `True`, um saldo de
referência diário reseta ao patrimônio corrente no primeiro candle de
cada novo dia de calendário (`t.date()`), independente de resultado;
enquanto o patrimônio corrente estiver abaixo de
`saldo_referencia_diario × (1 - DAILY_DRAWDOWN_LIMIT)`, nenhum
candidato novo abre. Diferente do circuit breaker (spec 044): reset por
**calendário**, não por trade lucrativo — não pode ficar preso
indefinidamente.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `config/settings.py`
(`DAILY_DRAWDOWN_LIMIT`, já existente), `backtesting/portfolio_h14.py`
(spec 037/041/042/043/044)

**Storage**: `reports/carteira_dd_diario_*.json` (padrão `export_report`
já existente)

**Testing**: pytest, `tests/test_portfolio_h14.py` (extensão)

**Target Platform**: CLI local (`python main.py carteira_dd_diario`);
produção intocada

**Performance Goals**: mesma ordem de grandeza dos comandos
`carteira_*` anteriores (12 pares) — saldo de referência é estado local
em memória, sem custo de rede adicional

**Constraints**: FR-001 — comportamento default idêntico byte a byte ao
já publicado quando `usar_limite_drawdown_diario=False`; FR-003 — o
limite bloqueia só entradas novas, nunca gestão de posição já aberta

**Scale/Scope**: 1 par de estado local novo (saldo de referência + dia
do último reset), 1 parâmetro novo em função já existente, 1 comando CLI

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/` (FR-007) — o saldo de referência é estado local da simulação, distinto do limite de produção. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre bloqueio abaixo do limite, reset no novo dia (mesmo sem trade lucrativo) e a regressão do caminho default antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Estado + parâmetro + regressão num tópico; comando CLI + execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão dos comandos `carteira_*` anteriores. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** D1 (por que só o limite diário, não semanal/mensal, e por que "reset por calendário" é uma família diferente do circuit breaker) declarado em `research.md` antes de qualquer código. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/045-limite-drawdown-diario-h14/
├── plan.md              # este arquivo
├── research.md          # Fase 0 (D1)
├── data-model.md         # Fase 1
└── quickstart.md         # Fase 1
```

Sem `contracts/`: comando de pesquisa segue o padrão já estabelecido.

### Source Code (repository root)

```text
backtesting/
└── portfolio_h14.py       # ~_simular_carteira_core/simular_carteira
                            # ganham usar_limite_drawdown_diario=False (opt-in)

main.py                    # +cmd_carteira_dd_diario

tests/
└── test_portfolio_h14.py   # +testes de bloqueio/reset-por-dia +regressao
```

`execution/order_manager.py` **não é alterado** — só consultado como
referência de semântica/limiar.

## Complexity Tracking

Vazio — nenhuma violação de princípio a justificar.

## Fases

**Fase 0 ✅** — D1 (por que só o limite diário, e por que "reset por
calendário" é uma família estruturalmente diferente do circuit breaker
de perdas consecutivas).

**Fase 1 ✅** — `data-model.md` + `quickstart.md`. Sem `contracts/`.

**Fase 2** — `tasks.md` (`/speckit-tasks`).

**Fase 3** — implementação (`/speckit-implement`), dois tópicos:
1. Saldo de referência diário + `usar_limite_drawdown_diario` +
   regressão do caminho default
2. `cmd_carteira_dd_diario()` (CLI) + execução real (VPS) + comparação
   registrada em `docs/research/registro-de-hipoteses.md` §4.15
