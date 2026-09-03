# Implementation Plan: H10 reavaliada com universo amplo de pares candidatos

**Branch**: `052-h10-universo-amplo` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

Chama `run_pairs_scan(pares=UNIVERSO_AMPLO)` — `run_pairs_scan` já
aceita `pares` como parâmetro (spec 039), `UNIVERSO_AMPLO` já existe e
já foi medido/validado para liquidez (spec 040). Nenhuma mudança de
código em `backtesting/pairs_trading.py` — só um comando CLI novo e
uma medição.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `backtesting/pairs_trading.py`
(spec 039), `backtesting/portfolio_h14.py::UNIVERSO_AMPLO` (spec 040),
sem mudança de código em nenhum dos dois

**Storage**: `reports/pairs_amplo_*.json` (padrão `export_report` já
existente)

**Testing**: pytest — teste mínimo confirmando que `selecionar_pares`
sobre mais colunas nunca encontra menos pares elegíveis que sobre um
subconjunto delas (monotonicidade)

**Target Platform**: CLI local (`python main.py pairs_amplo`);
produção intocada

**Performance Goals**: C(34,2)=561 combinações testadas por ciclo de
reseleção contra 66 de `UNIVERSO_H11` — ~8,5x mais trabalho de
estimação de cointegração por ciclo, mesma ordem de grandeza dos
demais comandos de pesquisa (sem chamada de rede adicional por par
além do fetch já necessário)

**Constraints**: FR-002 — `PairsParams` idênticos aos já publicados em
spec 039, só o universo candidato muda

**Scale/Scope**: 1 comando CLI novo — zero mudança em
`backtesting/pairs_trading.py`

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre a monotonicidade de `selecionar_pares` antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Teste + comando CLI num tópico; execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão dos comandos de pesquisa. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Por que isto não repete spec 040 (pergunta de amostra, não de risco de carteira) declarado em spec.md/Contexto antes de qualquer código. Sem `research.md` — nada novo a decidir, `UNIVERSO_AMPLO` e `PairsParams` já declarados noutras specs. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/052-h10-universo-amplo/
├── plan.md
└── quickstart.md
```

Sem `research.md`/`data-model.md` (reuso trivial, já descrito em
spec.md/plan.md) nem `contracts/`.

### Source Code (repository root)

```text
main.py    # +cmd_pairs_amplo

tests/
└── test_pairs_trading.py   # +teste de monotonicidade de selecionar_pares
```

`backtesting/pairs_trading.py` **não é alterado**.

## Complexity Tracking

Vazio.

## Fases

**Fase 1** — `tasks.md`.

**Fase 2** — implementação: teste + comando CLI num tópico; execução
real (VPS) + registro noutro.
