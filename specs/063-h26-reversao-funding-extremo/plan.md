# Implementation Plan: H26 — reversão contra funding extremo (crowding/liquidação)

**Branch**: `063-h26-reversao-funding-extremo` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/funding_reversao.py` (novo): `avaliar_par` busca preço
(`fetch_ohlcv`) e funding (`data.funding.fetch_funding_rate_history`),
divide cronologicamente em treino/validação (`DEFAULT_VALIDATION_RATIO`
já existente), calibra o limiar de extremo (decil mais negativo) só no
treino, rotula eventos extremos da validação pela barreira tripla
(`strategy/barreira_tripla.py::rotular`, sem alteração) e aplica
`supera_empate_com_confianca` (`backtesting/modelo.py`, sem alteração)
sobre a contagem agregada. `cmd_funding_extremo()` (novo, `main.py`)
roda sobre `UNIVERSO_H11` e imprime o pooled.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `data/funding.py` (spec 058),
`strategy/barreira_tripla.py`, `backtesting/modelo.py`
(`limiar_de_empate`/`supera_empate_com_confianca`),
`backtesting/validation.py` (`DEFAULT_VALIDATION_RATIO`), todos sem
alteração

**Storage**: `reports/funding_extremo_*.json` (padrão `export_report`)

**Testing**: pytest — calibração do limiar só no treino (não vaza
validação), alinhamento causal funding→candle (forward-fill), rotulagem
correta de eventos extremos, agregação pooled, `supera_empate_com_confianca`
delegado sem reimplementar Wilson CI

**Target Platform**: CLI local (`python main.py funding_extremo`);
produção intocada

**Performance Goals**: mesma ordem de custo de `python main.py
calibracao` (spec 055) — 12 pares × busca de preço + funding — aceitável
para comando de pesquisa

**Constraints**: FR-001 — limiar calibrado só no treino; FR-003 —
alinhamento forward-fill causal; FR-004 — significância sempre via
`supera_empate_com_confianca`, nunca razão pontual isolada; FR-005 — só
lado long

**Scale/Scope**: 1 módulo novo (~100 linhas), 1 comando CLI novo

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre calibração/alinhamento/rotulagem/agregação antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Módulo + comando + testes num tópico; execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão dos comandos de pesquisa. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Hipótese (reversão prevista) e expectativa honesta (REPROVADA, base histórica de §6.3-b) declaradas em `spec.md`/`research.md` antes de qualquer medição. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/063-h26-reversao-funding-extremo/
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
└── funding_reversao.py   # novo: avaliar_par, avaliar_universo, agregar_pooled

main.py                   # +cmd_funding_extremo, +"funding_extremo" em COMMANDS

tests/
└── test_funding_reversao.py   # novo
```

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — D1-D5 (limiar, mecânica de trade, universo, disciplina
estatística, tamanho de janela) declarados em `research.md` antes de
qualquer medição real.

**Fase 1** — sem `data-model.md`/`contracts/` formais (entidade
trivial, já descrita em `spec.md`).

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: módulo + comando + testes num tópico;
execução real + registro noutro.
