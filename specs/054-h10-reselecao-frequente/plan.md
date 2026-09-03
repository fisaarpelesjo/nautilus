# Implementation Plan: H10 — reseleção de pares desacoplada da formação

**Branch**: `054-h10-reselecao-frequente` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`run_pairs_scan` ganha `reselecionar_a_cada: Optional[int] = None`,
repassado a `run_pairs_backtest` (já aceita o parâmetro
independentemente) — `None` preserva `= p.formacao` (comportamento já
publicado). `cmd_pairs_reselecao()` (novo, `main.py`) chama com
`reselecionar_a_cada=120` (`meia_vida_max`, D3) sobre
`UNIVERSO_AMPLO_HISTORICO_COMPLETO` (spec 052).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `backtesting/pairs_trading.py`
(spec 039/052), `run_pairs_backtest` já aceita o parâmetro

**Storage**: `reports/pairs_reselecao_*.json` (padrão `export_report`)

**Testing**: pytest — regressão do default (`None` reproduz
`p.formacao` byte a byte) + teste confirmando que
`reselecionar_a_cada` explícito muda de fato quantas vezes
`selecionar_pares` é chamado

**Target Platform**: CLI local (`python main.py pairs_reselecao`);
produção intocada

**Performance Goals**: mais chamadas de `selecionar_pares` (231
combinações cada) por reseleção mais frequente — aceitável para
comando de pesquisa

**Constraints**: FR-001 — `None` reproduz o comportamento já
publicado; FR-003 — `formacao` e demais `PairsParams` intocados

**Scale/Scope**: 1 parâmetro novo em função já existente, 1 comando
CLI novo

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre a regressão do default e a mudança real de cadência antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Parâmetro + testes + comando CLI num tópico; execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão dos comandos `pairs_*`. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Diagnóstico (D1), por que desacoplar não perde poder de detecção (D2), e por que 120 (`meia_vida_max`, D3) declarados em `research.md` antes de qualquer código. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/054-h10-reselecao-frequente/
├── plan.md
├── research.md
└── quickstart.md
```

Sem `data-model.md` (extensão trivial já descrita) nem `contracts/`.

### Source Code (repository root)

```text
backtesting/
└── pairs_trading.py    # ~run_pairs_scan: +reselecionar_a_cada

main.py                 # +cmd_pairs_reselecao

tests/
└── test_pairs_trading.py   # +regressao do default
                              # +teste de cadencia explicita
```

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — D1 (diagnóstico), D2 (por que desacoplar não perde
poder de detecção), D3 (valor testado: `meia_vida_max`).

**Fase 1** — sem Fase 1 formal (`data-model.md`/`contracts/`
desnecessários, extensão trivial já descrita).

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: parâmetro + testes + comando CLI num
tópico; execução real (VPS) + registro noutro.
