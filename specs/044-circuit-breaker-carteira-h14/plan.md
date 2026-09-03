# Implementation Plan: Circuit breaker de perdas consecutivas na carteira de H14

**Branch**: `044-circuit-breaker-carteira-h14` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/portfolio_h14.py::_simular_carteira_core` ganha
`usar_circuit_breaker: bool = False`. Quando `True`, um contador local
`perdas_consecutivas` (carteira inteira, não por par) incrementa a cada
fechamento de posição com `pnl < 0` e reseta a zero no primeiro
fechamento com `pnl > 0`; ao atingir `MAX_CONSECUTIVE_LOSSES`
(`config/settings.py`), nenhum candidato novo abre até o contador
resetar. Mesma semântica de `execution/order_manager.py`, sem o
cooldown por tempo (D1, `research.md`).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `config/settings.py`
(`MAX_CONSECUTIVE_LOSSES`, já existente), `backtesting/portfolio_h14.py`
(spec 037/041/042/043)

**Storage**: `reports/carteira_breaker_*.json` (padrão `export_report`
já existente)

**Testing**: pytest, `tests/test_portfolio_h14.py` (extensão)

**Target Platform**: CLI local (`python main.py carteira_breaker`);
produção intocada

**Performance Goals**: mesma ordem de grandeza de
`carteira`/`carteira_vol`/`carteira_corr` (12 pares) — contador é estado
local em memória, sem custo de rede adicional

**Constraints**: FR-001 — comportamento default idêntico byte a byte ao
já publicado quando `usar_circuit_breaker=False`; FR-003 — o breaker
bloqueia só entradas novas, nunca gestão de posição já aberta

**Scale/Scope**: 1 contador local novo, 1 parâmetro novo em função já
existente, 1 comando CLI

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/` (FR-007) — o contador é estado local da simulação, distinto do circuit breaker de produção. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre bloqueio ao atingir o limite, reset em trade lucrativo e a regressão do caminho default antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Contador + parâmetro + regressão num tópico; comando CLI + execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão dos comandos `carteira_*` anteriores. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** D1 (por que reduzir o escopo em relação ao circuit breaker de produção — sem cooldown por tempo — e por que isso não muda a semântica testada) declarado em `research.md` antes de qualquer código. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/044-circuit-breaker-carteira-h14/
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
                            # ganham usar_circuit_breaker=False (opt-in)

main.py                    # +cmd_carteira_breaker

tests/
└── test_portfolio_h14.py   # +testes de bloqueio/reset +regressao
```

`execution/order_manager.py`, `backtesting/engine.py`,
`backtesting/approval.py` **não são alterados** — só consultados como
referência de semântica/limiar.

## Complexity Tracking

Vazio — nenhuma violação de princípio a justificar.

## Fases

**Fase 0 ✅** — D1 (por que o circuit breaker desta spec não inclui o
cooldown por tempo de produção, e por que isso preserva a mesma
semântica testável).

**Fase 1 ✅** — `data-model.md` + `quickstart.md`. Sem `contracts/`.

**Fase 2** — `tasks.md` (`/speckit-tasks`).

**Fase 3** — implementação (`/speckit-implement`), dois tópicos:
1. Contador `perdas_consecutivas` + `usar_circuit_breaker` + regressão
   do caminho default
2. `cmd_carteira_breaker()` (CLI) + execução real (VPS) + comparação
   registrada em `docs/research/registro-de-hipoteses.md` §4.15
