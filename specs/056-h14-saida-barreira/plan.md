# Implementation Plan: H14 — saída por barreira tripla em vez de trailing stop

**Branch**: `056-h14-saida-barreira` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/portfolio_h14.py`: `PosicaoCarteira` ganha
`velas_decorridas: int = 0`. `_simular_carteira_core`/`simular_carteira`
ganham `usar_saida_barreira: bool = False` + `limite_velas: int =
LIMITE_VELAS_PADRAO`. No laço de fechamento, quando ligado: pula a
atualização de trailing (stop fica fixo) e fecha a mercado com motivo
próprio quando `velas_decorridas >= limite_velas` sem tocar alvo/stop.
`cmd_carteira_barreira()` (novo, `main.py`) roda sobre `UNIVERSO_H11`,
sem nenhum outro overlay, e compara contra o resultado sem overlay já
publicado (spec 037).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `strategy/barreira_tripla.py::LIMITE_VELAS_PADRAO`
(import, sem alteração), `backtesting/engine.py::_close_trade`/`_take_profit_price`/
`_stop_price` (já reusados, sem alteração)

**Storage**: `reports/carteira_barreira_*.json` (padrão `export_report`)

**Testing**: pytest — fecha no limite de velas sem tocar barreira, stop
NÃO sobe sob o novo modo (regressão do cenário trailing existente
invertida), barreiras fixas ainda disparam antes do limite, default
`False` reproduz o comportamento trailing existente sem mudança

**Target Platform**: CLI local (`python main.py carteira_barreira`);
produção intocada

**Performance Goals**: mesma ordem de custo de `python main.py carteira`
(já publicado, specs 037-047) — aceitável para comando de pesquisa

**Constraints**: FR-001 — `False` reproduz os nove resultados já
publicados byte a byte; FR-002/FR-003 — stop fixo e fechamento por
tempo são as duas únicas diferenças de mecânica

**Scale/Scope**: 1 campo novo em dataclass existente, 2 parâmetros
novos em função existente, 1 comando CLI novo

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre os três invariantes de mecânica antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Mecânica + comando + testes num tópico; execução real (VPS) + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão dos comandos `carteira_*`. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Hipótese (descasamento explica PF baixo) e alternativa (não explica) declaradas em `spec.md` antes de qualquer medição real. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/056-h14-saida-barreira/
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
└── portfolio_h14.py   # ~PosicaoCarteira, ~_simular_carteira_core, ~simular_carteira

main.py                 # +cmd_carteira_barreira, +"carteira_barreira" em COMMANDS

tests/
└── test_portfolio_h14.py   # +4 testes (limite de velas, sem trailing, barreira fixa, default)
```

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — hipótese e alternativa declaradas em `spec.md`;
`research.md` documenta o cálculo de expectativa em ATR que motivou a
spec.

**Fase 1** — sem `data-model.md`/`contracts/` formais (única entidade
nova, um campo em dataclass existente, já descrita em `spec.md`).

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: mecânica + comando + testes num tópico;
execução real (VPS) + registro noutro.
