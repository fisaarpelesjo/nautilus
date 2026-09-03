# Implementation Plan: H32 — on-chain mais rico (valor transacionado)

**Branch**: `069-h32-onchain-rico` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/onchain_volume_hipotese.py` (novo, mesmo formato de
`backtesting/onchain_hipotese.py`): declara `onchain_txn_volume_growth_7d`
(mesma transformação de H17, série `estimated-transaction-volume-usd`
em vez de `n-unique-addresses`), checa colinearidade contra os 5
atributos de H14 + `onchain_addr_growth_7d`, e — só se abaixo do limiar
— compara o modelo com/sem o atributo, isolado sobre BTC/USDT.
`cmd_onchain_volume()` (novo, `main.py`).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `data/onchain.py`
(`fetch_onchain_series`, já genérico por nome de métrica, sem
alteração), `backtesting/modelo.py` (`avaliar_par`, sem alteração)

**Storage**: `reports/onchain_volume_*.json`

**Testing**: pytest — transformação de crescimento sobre série
sintética, checagem de colinearidade (acima e abaixo do limiar),
merge causal (D-1, reusa `_merge_causal` de H17 sem duplicar)

**Target Platform**: CLI local (`python main.py onchain_volume`);
produção intocada

**Constraints**: FR-002 — colinearidade sempre checada antes de
qualquer leitura de desempenho; FR-003 — comparação sempre isolada
(nunca contra o pooled de 12 pares)

**Scale/Scope**: 1 módulo novo (~70 linhas, reusa quase tudo de
`onchain_hipotese.py`), 1 comando CLI novo

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | Conforme — só leitura de dado público, sem credencial, sem import por `trading/`/`execution/`/`risk/`. |
| **III. Test Before Implement** | Conforme — `tasks.md` cobre transformação e colinearidade antes da execução real. |
| **IV. Incremental Delivery** | Conforme — módulo+comando+testes num tópico; execução real+registro noutro. |
| **VII. Explain Before Code** | Conforme — D1-D5 declarados em `research.md` antes de qualquer medição. |

Nenhuma violação a justificar.

## Project Structure

```text
specs/069-h32-onchain-rico/
├── spec.md / plan.md / research.md / quickstart.md / tasks.md
└── checklists/requirements.md

backtesting/onchain_volume_hipotese.py   # novo
main.py                                   # +cmd_onchain_volume
tests/test_onchain_volume_hipotese.py     # novo
```

## Fases

**Fase 0 ✅** — D1-D5 declarados em `research.md`.
**Fase 1** — sem `data-model.md`/`contracts/` formais (entidade
trivial, mesma de H17).
**Fase 2** — `tasks.md`.
**Fase 3** — implementação: módulo+comando+testes; execução real+registro.
