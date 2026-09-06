# Implementation Plan: H36 — Hash Ribbons: capitulação de mineradores (BTC-only)

**Branch**: `073-h36-hash-ribbons` | **Date**: 2026-09-06 | **Spec**: [spec.md](spec.md)

## Summary

`strategy/hash_ribbons.py` (novo): `HashRibbonsStrategy` (subclasse de
`BaseStrategy`) recebe a série diária de hashrate pré-buscada, calcula
médias móveis de 30/60 dias e os cruzamentos, alinha ao candle via
`backtesting.onchain_hipotese._merge_causal` (reuso, sem alteração) —
BUY no cruzamento de alta, SELL no cruzamento de baixa, sem SL/TP
artificial (o ATR do motor permanece ativo). `backtesting/hash_ribbons.py`
(novo): `gerar_resultado` busca o hashrate uma vez e fecha sobre a
estratégia; `teste_sanidade` usa série de hashrate monotônica (sem
cruzamento); `avaliar()` busca candles cobrindo a janela real de hashrate
(descarta o que vem antes) e roda `bateria_hipotese.rodar_bateria` sobre
`BTC/USDT`. `cmd_hash_ribbons()` (novo, `main.py`) imprime o
`RelatorioBateria`.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — reusa `data.onchain.fetch_onchain_series`
(spec 033, já usada por H17/H32), `backtesting.onchain_hipotese._merge_causal`,
`backtesting.bateria_hipotese.rodar_bateria`, `backtesting.engine.simulate_backtest`

**Storage**: `reports/hash_ribbons_*.json` (padrão `export_report`)

**Testing**: pytest — detecção de cruzamento de alta/baixa sobre série
sintética com posições conhecidas, alinhamento causal D-1 (mesmo padrão de
`_merge_causal` já testado em `tests/test_onchain_hipotese.py`), `teste_sanidade`
devolve zero trades sobre série de hashrate sem cruzamento, `avaliar()`
descarta candles anteriores ao início real do hashrate, `gerar_resultado`
aplica custo zero corretamente

**Target Platform**: CLI local (`python main.py hashribbons`); produção
intocada

**Performance Goals**: 1 par (`BTC/USDT`) × ~7000 candles (cobre a janela
real de hashrate com margem, confirmado por probe real) × bateria E1-E6 —
ordem de grandeza similar a H34, sem universo multi-par

**Constraints**: FR-002/FR-003 — alinhamento causal D-1, candles antes do
início real do hashrate descartados; FR-004 — SL/TP por ATR do motor
permanece ativo sem alteração; FR-005 — orquestra via
`bateria_hipotese.rodar_bateria`; FR-006 — sanidade com série sem
cruzamento

**Scale/Scope**: 2 módulos novos (~50 + ~60 linhas), 1 comando CLI novo

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** Fonte pública já integrada, sem chave. |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre detecção de cruzamento e sanidade antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Módulos + comando + testes num tópico; execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão dos comandos de pesquisa. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Hipótese, achado empírico do probe e expectativa sobre amostra/holding declarados em `spec.md`/`research.md` antes de qualquer medição de estratégia. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/073-h36-hash-ribbons/
├── spec.md
├── plan.md
├── research.md
├── quickstart.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
strategy/
└── hash_ribbons.py         # novo: HashRibbonsStrategy

backtesting/
└── hash_ribbons.py         # novo: gerar_resultado, teste_sanidade, avaliar

main.py                     # +cmd_hash_ribbons, +"hashribbons" em COMMANDS

tests/
└── test_hash_ribbons.py    # novo
```

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — hipótese, achado empírico do probe (16 cruzamentos em
~2,7 anos) e riscos de amostra/holding declarados em `research.md` antes
de qualquer medição real.

**Fase 1** — sem `data-model.md`/`contracts/` formais (reusa
`BacktestResult`/`RelatorioBateria` já existentes).

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: estratégia + módulo de avaliação + comando +
testes num tópico; execução real + comparação com H17/H32 + registro
noutro.
