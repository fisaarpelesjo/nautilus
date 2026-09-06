# Implementation Plan: H39 — Arbitragem estatística via PCA/eigenportfolio (Avellaneda-Lee)

**Branch**: `075-h39-pca-eigenportfolio` | **Date**: 2026-09-06 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/pca_eigenportfolio.py` (novo): `avaliar_universo()` busca os
22 pares de `UNIVERSO_AMPLO_HISTORICO_COMPLETO`, alinha pelo índice comum
(mesma correção de M14/spec 052), corta treino/validação com
`backtesting.validation.split_train_validation` (mesmo corte usado por
qualquer outra hipótese da bateria), decompõe os retornos padronizados de
TREINO via PCA (`numpy.linalg.eigh` sobre a matriz de covariância — sem
dependência nova), regride cada ativo contra os fatores (OLS,
`numpy.linalg.lstsq`), integra o resíduo e ajusta um processo
Ornstein-Uhlenbeck (AR(1) próprio, mais
`pairs_trading.py::meia_vida_reversao` reusado para o filtro de faixa).
`ResiduoStrategy` (nova, `strategy/base.BaseStrategy`) usa o s-score
pré-calculado como sinal de entrada/saída. Cada ativo dentro da faixa de
meia-vida é avaliado individualmente via
`backtesting.bateria_hipotese.rodar_bateria`. `cmd_pca_eigenportfolio()`
(novo, `main.py`) imprime por ativo e um resumo agregado.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `numpy` já é dependência do
projeto, cobre PCA (`eigh`) e OLS (`lstsq`) sem precisar de `scikit-learn`;
reusa `backtesting.pairs_trading.{UNIVERSO_AMPLO_HISTORICO_COMPLETO,meia_vida_reversao}`,
`backtesting.validation.split_train_validation`,
`backtesting.bateria_hipotese.rodar_bateria`, `backtesting.engine.simulate_backtest`

**Storage**: `reports/pca_eigenportfolio_*.json` (padrão `export_report`)

**Testing**: pytest — PCA sobre matriz sintética com estrutura de fator
conhecida recupera o número esperado de componentes; ajuste OU recupera
média/sigma de uma série sintética gerada com parâmetros conhecidos;
filtro de meia-vida exclui ativo com resíduo não-revertente (passeio
aleatório) sem abortar os demais; `ResiduoStrategy`/`precompute_signals`
geram BUY/SELL exatamente nos cruzamentos de limiar declarados;
`teste_sanidade` devolve zero trades sobre s-score constante;
`avaliar_universo` funciona com `fetch_ohlcv` mockado (sem rede)

**Target Platform**: CLI local (`python main.py pcaeigen`); produção
intocada

**Performance Goals**: 22 pares × 6.000 candles, PCA/OLS/OU calculados
uma única vez sobre o painel completo (não por candle) — ordem de custo
similar a `python main.py fator_tamanho`/`pairs`

**Constraints**: FR-001/D2 — componentes até 55% de variância, teto 10;
FR-002/D3 — parâmetros travados no treino, aplicados sem reajuste na
validação; FR-003/D4 — filtro de meia-vida reusa
`meia_vida_reversao` sem reimplementar; FR-004/D5 — limiares de
entrada/saída fixos; FR-006/D6 — limitação de não-hedge relatada
explicitamente no resultado e no registro

**Scale/Scope**: 1 módulo novo (~180 linhas), 1 comando CLI novo

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre PCA/OU/filtro/sinal antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Módulo + comando + testes num tópico; execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Hipótese, limitação de não-hedge e expectativa honesta (literatura já reporta resultado negativo) declaradas em `spec.md`/`research.md` antes de qualquer medição real. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/075-h39-pca-eigenportfolio/
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
└── pca_eigenportfolio.py   # novo: avaliar_universo, ResiduoStrategy, precompute_signals

main.py                     # +cmd_pca_eigenportfolio, +"pcaeigen" em COMMANDS

tests/
└── test_pca_eigenportfolio.py   # novo
```

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — decomposição, filtro de meia-vida, limiares e limitação
de não-hedge declarados em `research.md` antes de qualquer medição real.

**Fase 1** — sem `data-model.md`/`contracts/` formais (reusa
`BacktestResult`/`RelatorioBateria` já existentes).

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: estratégia + módulo de avaliação + comando +
testes num tópico; execução real + comparação com a literatura +
registro noutro.
