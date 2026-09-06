# Implementation Plan: H38 — Gate por volatilidade implícita (Deribit DVOL)

**Branch**: `074-h38-dvol-gate` | **Date**: 2026-09-06 | **Spec**: [spec.md](spec.md)

## Summary

`data/deribit.py` (novo): `fetch_dvol_history(currency, dias, resolution)`
via a API pública `get_volatility_index_data` (sem chave, confirmada por
probe real). `backtesting/dvol_gate.py` (novo): `avaliar_precondicao_dvol`
reconstrói a MESMA população de eventos "entrada primária" que
`backtesting/meta_labeling.py::avaliar_precondicao` já usa (mesmos blocos:
`EmaRsiStrategy`, `precompute_signals`, `rotular`, `UNIVERSO_H11`), sem
importar/alterar o módulo H27 (já publicado — mesma cautela de não
retroagir sobre módulo já citado), e adiciona o corte por DVOL sobre essa
população; chama `meta_labeling.avaliar_precondicao()` uma vez só para
reportar o número já publicado de H27 lado a lado (comparação, FR-009).
`cmd_dvol_gate()` (novo, `main.py`) imprime os dois subgrupos e o
veredito de precondição.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova como pacote (`requests` já é
dependência do projeto) — reusa `backtesting.horizonte.{UNIVERSO_H11,preparar}`,
`backtesting.engine.precompute_signals`, `backtesting.modelo.{limiar_de_empate,supera_empate_com_confianca}`,
`strategy.barreira_tripla.rotular`, `strategy.ema_rsi.EmaRsiStrategy`,
`backtesting.meta_labeling.avaliar_precondicao` (chamado, não alterado)

**Storage**: `reports/dvol_gate_*.json` (padrão `export_report`)

**Testing**: pytest — `fetch_dvol_history` devolve DataFrame vazio em
falha silenciosa nunca (levanta exceção), decil calibrado sobre a própria
série de DVOL, alinhamento causal D-1, divisão dos eventos exige DVOL
alinhável (evento sem DVOL é excluído, não presumido), `avaliar_precondicao_dvol`
funciona com fetchers mockados (sem rede), par sem evento com DVOL é
pulado sem abortar os demais

**Target Platform**: CLI local (`python main.py dvolgate`); produção
intocada

**Performance Goals**: mesma ordem de custo de `python main.py
meta_labeling` (H27) — 12 pares × 6000 candles + 1 fetch de DVOL

**Constraints**: FR-002 — mesma população de eventos que H27, sem
reimplementar a extração com critério diferente; FR-003 — alinhamento
causal D-1; FR-004 — decil calibrado sobre a própria série de DVOL;
FR-006 — precondição declarada explicitamente; FR-007 — evento sem DVOL
alinhável é excluído

**Scale/Scope**: 2 módulos novos (~35 + ~90 linhas), 1 comando CLI novo,
zero alteração em `backtesting/meta_labeling.py`

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** API pública, sem chave. |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre decil/alinhamento/exclusão antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Módulos + comando + testes num tópico; execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Hipótese, precondição e expectativa honesta (dado o resultado já publicado de H27, 0,5011 quase no empate) declaradas em `spec.md`/`research.md` antes de qualquer medição nova. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/074-h38-dvol-gate/
├── spec.md
├── plan.md
├── research.md
├── quickstart.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
data/
└── deribit.py            # novo: fetch_dvol_history

backtesting/
└── dvol_gate.py           # novo: avaliar_precondicao_dvol

main.py                    # +cmd_dvol_gate, +"dvolgate" em COMMANDS

tests/
└── test_dvol_gate.py       # novo
```

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — precondição, decil e alinhamento declarados em
`research.md` antes de qualquer medição real.

**Fase 1** — sem `data-model.md`/`contracts/` formais (entidade trivial,
já descrita em `spec.md`).

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: fetcher + módulo de precondição + comando +
testes num tópico; execução real + comparação com H27 + registro noutro.
