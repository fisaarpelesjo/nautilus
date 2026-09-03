# Implementation Plan: H23 — prêmio de futuros trimestrais (contango) vs. funding perpétuo

**Branch**: `059-h23-futuros-trimestrais` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`data/futures_basis.py` (novo): `listar_contratos_trimestrais`/
`fetch_basis_snapshot` via `ccxt` (reusa a exchange futures já
instanciada por `data/funding.py`). `backtesting/basis_carry.py`
(novo): `avaliar_contrato`/`avaliar_universo` — reusa
`CUSTO_ABERTURA_FECHAMENTO`/`BENCHMARK_RENDA_FIXA_AA` de
`backtesting/funding_carry.py` (spec 058) sem duplicar. `cmd_basis()`
(novo, `main.py`) imprime tabela ordenada.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: `ccxt` (já dependência do projeto) —
nenhuma dependência nova; reusa `data.funding._get_futures_exchange`
e `data.fetcher.get_exchange`

**Storage**: `reports/basis_*.json` (padrão `export_report`)

**Testing**: pytest — listagem filtra por base/quote/tipo (exclui
perpétuo, exclui coin-margined), ordena por vencimento, cálculo de
dias até o vencimento, bruto/líquido/capital-implantado sobre snapshot
sintético, backwardation (prêmio negativo) não quebra

**Target Platform**: CLI local (`python main.py basis`); produção
intocada, nenhuma permissão de API muda

**Performance Goals**: 4 contratos (2 bases × 2 vencimentos) — 2
chamadas de rede por contrato (ticker futuro + ticker spot), instant

**Constraints**: FR-003 — reusa constantes de H8, não duplica; FR-004 —
capital implantado é sempre metade do líquido sobre nocional

**Scale/Scope**: 2 módulos novos (~90 linhas), 1 comando CLI novo

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Só leitura de dado público (tickers), sem credencial, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre listagem e cálculo antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Módulos + comando + testes num tópico; execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** D1-D4 (universo, instantâneo vs. série, custo/capital, benchmark) declarados em `research.md` antes de qualquer medição real. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/059-h23-futuros-trimestrais/
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
└── futures_basis.py    # novo: listar_contratos_trimestrais, fetch_basis_snapshot

backtesting/
└── basis_carry.py       # novo: avaliar_contrato, avaliar_universo

main.py                  # +cmd_basis, +"basis" em COMMANDS

tests/
├── test_futures_basis.py   # novo
└── test_basis_carry.py     # novo
```

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — D1-D4 declarados em `research.md` antes de qualquer
medição real (reusam D1-D4 de H8 onde aplicável).

**Fase 1** — sem `data-model.md`/`contracts/` formais (entidade
trivial, já descrita em `spec.md`).

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: módulos + comando + testes num tópico;
execução real + registro noutro.
