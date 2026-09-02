# Implementation Plan: Fonte de dados on-chain

**Branch**: `033-fonte-dados-onchain` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

## Summary

`data/onchain.py::fetch_onchain_series(metric, timespan="3years")` busca
qualquer série diária de `api.blockchain.info/charts/<metric>` (D1, testado
contra 6 séries reais), sem chave de API, reusando `requests` (D2, já
dependência do projeto). Falha de rede, nome inválido ou `status` não-ok
levantam exceção (D3, mesmo princípio de `DataSource`/`check_liquidity`);
série vazia por ausência real de dado é resultado válido, não erro. Módulo
próprio (D4) — não reusa o protocolo `DataSource` de `data/sources/`
(spec 023), que é para OHLCV, forma de dado estruturalmente diferente.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: `requests` (já existente, `utils/notifier.py`) —
nenhuma nova

**Storage**: N/A — busca direta, sem cache (Assumptions: cache fica para
quando a hipótese mostrar necessidade real)

**Testing**: pytest, `tests/test_onchain.py` (novo)

**Target Platform**: só pesquisa (`docs/research/`, futuras specs de
hipótese) — não é consumido por `trading/runner.py` nem qualquer caminho de
execução real

**Performance Goals**: uma requisição HTTP por chamada, sem paralelismo
necessário (uso é pesquisa pontual, não loop de produção)

**Constraints**: FR-005 (zero dependência nova), FR-006 (não altera
`data/fetcher.py`/`data/sources/`)

**Scale/Scope**: um módulo novo (~40 linhas), sem integração com nenhum
consumidor ainda — a spec da hipótese (H17) é quem integra

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme, e de baixo risco.** Módulo novo, sem nenhum import por `trading/`, `execution/` ou `risk/` — inacessível ao caminho de execução real por construção. |
| **II. No Secrets in Code** | **Conforme.** Nenhuma chave de API (FR-001). |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre US1/US2/US3 com teste antes da implementação. |
| **IV. Incremental Delivery** | **Conforme.** Spec pequena, um tópico. |
| **V. Observability Mandatory** | **N/A.** Não é decisão de risco nem evento operacional — busca de dado de pesquisa, mesma categoria de `data/fetcher.py::fetch_ohlcv` (não loga em `events-*.jsonl`). |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** D1-D4 commitados em `research.md`, com a API testada antes de qualquer código. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/033-fonte-dados-onchain/
├── plan.md              # este arquivo
├── research.md          # Fase 0 (D1-D4)
├── data-model.md         # Fase 1
└── quickstart.md         # Fase 1
```

Sem `contracts/`: função interna de biblioteca (não CLI, não API exposta) —
mesmo critério de 030/031.

### Source Code (repository root)

```text
data/
└── onchain.py            # NOVO: fetch_onchain_series(metric, timespan)

tests/
└── test_onchain.py        # NOVO
```

Nada em `data/fetcher.py`, `data/sources/`, `trading/`, `execution/` é
tocado.

## Complexity Tracking

Vazio — nenhuma violação de princípio a justificar.

## Fases

**Fase 0 ✅** — D1 (API testada em 6 séries reais), D2 (`requests` reusado),
D3 (taxonomia de erro), D4 (módulo e assinatura).

**Fase 1 ✅** — `data-model.md` (uma entidade: série on-chain) +
`quickstart.md`. Sem `contracts/`.

**Fase 2** — `tasks.md` (`/speckit-tasks`).

**Fase 3** — implementação (`/speckit-implement`), um único tópico:
`data/onchain.py` + `tests/test_onchain.py`.
