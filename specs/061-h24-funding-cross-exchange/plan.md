# Implementation Plan: H24 — diferencial de funding rate entre corretoras (perp × perp)

**Branch**: `061-h24-funding-cross-exchange` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`data/funding_cross.py` (novo): `fetch_funding_rate_history(corretora,
par, dias)` busca histórico de funding via `ccxt`, parametrizado por
corretora (5 qualificadas: binance/bybit/okx/kucoinfutures/gate),
paginado, `BadSymbol`-seguro. `backtesting/funding_cross_carry.py`
(novo): `avaliar_par_corretoras`/`avaliar_universo` alinham dois
históricos por hora arredondada, calculam diferencial bruto/líquido/
capital-implantado reusando `BENCHMARK_RENDA_FIXA_AA` de
`backtesting/funding_carry.py`. `cmd_funding_cross()` (novo,
`main.py`) roda sobre os 10 pares de corretoras × {BTC, ETH}.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: `ccxt` (já dependência do projeto,
`fetchFundingRateHistory` verificado em 5 corretoras 2026-09-03) --
nenhuma dependência nova

**Storage**: `reports/funding_cross_*.json` (padrão `export_report`)

**Testing**: pytest -- fetch por corretora (símbolo sem perpétuo,
histórico normal, paginação) sem rede via fake exchange; alinhamento
de dois históricos com jitter de segundos; cálculo de diferencial
bruto/líquido/capital-implantado sobre histórico sintético; direção
correta (qual corretora vender/comprar) conforme o sinal do
diferencial

**Target Platform**: CLI local (`python main.py funding_cross`);
produção intocada, nenhuma permissão de API muda

**Performance Goals**: 5 corretoras × 2 ativos = 10 buscas de
histórico, mais leve que o scan de 34 pares de H8 -- roda local, sem
precisar de VPS

**Constraints**: FR-002 -- alinhamento por hora arredondada, não
timestamp exato; FR-003 -- taxa real por corretora, não uma taxa
única reusada; FR-004 -- conclusão sobre capital declarada
explicitamente (D3: igual a H8, não menor); FR-005 -- Kraken excluído

**Scale/Scope**: 2 módulos novos (~150 linhas), 1 comando CLI novo

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Só leitura de dado público (funding rate history), sem credencial, sem import por `trading/`, `execution/` ou `risk/`. Nenhuma permissão de API muda. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre fetch e cálculo antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Módulos + comando + testes num tópico; execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão dos comandos de pesquisa. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada, nenhuma permissão de API alterada. |
| **VII. Explain Before Code** | **Conforme.** D1-D5 (corretoras qualificadas, taxas, capital, universo, benchmark) declarados em `research.md` antes de qualquer medição real -- incluindo a investigação de capital (D3) que refuta a hipótese de entrada de eficiência melhorada. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/061-h24-funding-cross-exchange/
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
└── funding_cross.py         # novo: fetch_funding_rate_history(corretora, par, dias)

backtesting/
└── funding_cross_carry.py   # novo: avaliar_par_corretoras, avaliar_universo

main.py                      # +cmd_funding_cross, +"funding_cross" em COMMANDS

tests/
├── test_funding_cross.py         # novo
└── test_funding_cross_carry.py   # novo
```

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** -- D1-D5 declarados em `research.md`, incluindo a
investigação real de capital (D3) feita ANTES de escrever o módulo de
medição.

**Fase 1** -- sem `data-model.md`/`contracts/` formais (entidade
trivial, já descrita em `spec.md`).

**Fase 2** -- `tasks.md`.

**Fase 3** -- implementação: módulos + comando + testes num tópico;
execução real (local, mais leve que VPS) + registro noutro.
