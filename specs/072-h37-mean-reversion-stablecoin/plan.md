# Implementation Plan: H37 — Mean reversion em par de stablecoin (USDC/USDT)

**Branch**: `072-h37-mean-reversion-stablecoin` | **Date**: 2026-09-06 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/mean_reversion_stablecoin.py` (novo, módulo fino): `gerar_resultado`
adapta `strategy/mean_reversion.py::MeanReversionStrategy` (H3, SEM
alteração) ao `GerarResultado` do harness comum, via `simulate_backtest`
(mesmo padrão de `backtesting/reversao_pos_liquidacao.py`, H34);
`teste_sanidade` usa série sintética de preço constante (zero
volatilidade, nunca toca a banda inferior); `avaliar()` busca `USDC/USDT`
e roda `bateria_hipotese.rodar_bateria`. `cmd_mean_reversion_stablecoin()`
(novo, `main.py`) imprime o `RelatorioBateria` único (não há loop de
universo — um só par, por desenho da hipótese).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — reusa `strategy/mean_reversion.py`
(inalterado), `backtesting.bateria_hipotese.rodar_bateria`,
`backtesting.engine.simulate_backtest`, `data.fetcher.fetch_ohlcv`

**Storage**: nenhuma nova — resultado só impresso via
`cmd_mean_reversion_stablecoin` (mesmo padrão de H34)

**Testing**: pytest — `teste_sanidade` devolve zero trades sobre série de
preço constante, `gerar_resultado` aplica custo zero corretamente,
`avaliar()` funciona com `fetch_ohlcv` mockado (sem rede)

**Target Platform**: CLI local (`python main.py stablecoin`); produção
intocada

**Performance Goals**: 1 par × 2000 candles × bateria E1-E6 (~9
simulações) — ordem de grandeza muito menor que H34/H35 (universo de 12
pares), por desenho (hipótese é sobre um símbolo específico)

**Constraints**: FR-001 — `MeanReversionStrategy` usada sem nenhuma
alteração de código; FR-002 — orquestra via `bateria_hipotese.rodar_bateria`;
FR-004 — veredito comparado explicitamente com o resultado original de H3

**Scale/Scope**: 1 módulo novo (~40 linhas), 1 comando CLI novo, zero
mudança em `strategy/`

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`. Estratégia de produção (`strategy/ema_rsi.py`) intocada. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre sanidade/custo/wiring antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Módulo + comando + testes num tópico; execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Nenhuma decisão de risco nova. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Hipótese e expectativa honesta declaradas em `spec.md`/`research.md` antes de qualquer medição real. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/072-h37-mean-reversion-stablecoin/
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
└── mean_reversion_stablecoin.py   # novo: gerar_resultado, teste_sanidade, avaliar

main.py                            # +cmd_mean_reversion_stablecoin, +"stablecoin" em COMMANDS

tests/
└── test_mean_reversion_stablecoin.py   # novo
```

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — hipótese, obstáculo e expectativa honesta declarados em
`research.md` antes de qualquer medição real.

**Fase 1** — sem `data-model.md`/`contracts/` formais (reusa
`BacktestResult`/`RelatorioBateria` já existentes).

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: módulo + comando + testes num tópico;
execução real + comparação com H3 + registro noutro.
