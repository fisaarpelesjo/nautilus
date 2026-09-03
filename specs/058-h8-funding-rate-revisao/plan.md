# Implementation Plan: H8 — arbitragem de funding rate, revisão com universo amplo e eficiência de capital

**Branch**: `058-h8-funding-rate-revisao` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`data/funding.py` (novo): `fetch_funding_rate_history` busca histórico de
funding via `ccxt` (exchange futures separada, endpoint público) com
paginação, devolve DataFrame vazio (nunca lança) para pares sem
perpétuo. `backtesting/funding_carry.py` (novo): `avaliar_par`/
`avaliar_universo` calculam bruto/líquido/capital-implantado por par
com as taxas atuais e o benchmark declarado. `cmd_funding()` (novo,
`main.py`) roda sobre `UNIVERSO_AMPLO`, imprime tabela ordenada.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: `ccxt` (já dependência do projeto,
`fetch_funding_rate_history` já suportado nativamente — verificado
2026-09-03) — nenhuma dependência nova

**Storage**: `reports/funding_*.json` (padrão `export_report`)

**Testing**: pytest — fetch de funding (símbolo sem perpétuo,
histórico normal, paginação, cache de exchange) sem rede via fake
exchange; cálculo de bruto/líquido/capital-implantado sobre histórico
sintético, exclusão por cobertura mínima, universo pula pares sem
resultado

**Target Platform**: CLI local (`python main.py funding`); produção
intocada, nenhuma permissão de API muda

**Performance Goals**: ~34 pares × paginação de funding rate (até
1.095 registros/par) — mais lento que um scan de candles único, mas
aceitável para comando de pesquisa rodado uma vez

**Constraints**: FR-002 — cobertura mínima de 90 dias exclui em vez de
zerar; FR-003 — capital implantado é sempre metade do líquido sobre
nocional (sem alavancagem); FR-004 — taxas atuais verificadas, não as
de 0,04% da medição original; FR-006 — zero execução real

**Scale/Scope**: 2 módulos novos (~130 linhas), 1 comando CLI novo

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Só leitura de dado público (funding rate history), sem credencial, sem import por `trading/`, `execution/` ou `risk/`. Nenhuma permissão de API muda. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre fetch e cálculo antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Módulos + comando + testes num tópico; execução real (VPS) + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão dos comandos de pesquisa. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada, nenhuma permissão de API alterada. |
| **VII. Explain Before Code** | **Conforme.** As cinco decisões (D1-D5: taxas, custo, capital, benchmark, universo) declaradas em `funding_carry.py`/`research.md` antes de qualquer medição real. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/058-h8-funding-rate-revisao/
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
└── funding.py          # novo: fetch_funding_rate_history, perp_symbol

backtesting/
└── funding_carry.py    # novo: avaliar_par, avaliar_universo

main.py                 # +cmd_funding, +"funding" em COMMANDS

tests/
├── test_funding.py         # novo
└── test_funding_carry.py   # novo
```

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — D1-D5 (taxas atuais, custo, eficiência de capital,
benchmark, universo) declarados em `research.md` antes de qualquer
medição real.

**Fase 1** — sem `data-model.md`/`contracts/` formais (entidade
trivial, já descrita em `spec.md`).

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: módulos + comando + testes num tópico;
execução real (VPS) + registro noutro.
