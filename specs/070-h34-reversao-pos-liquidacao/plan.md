# Implementation Plan: H34 — Reversão pós-liquidação (padrão de vela: pavio + pico de volume)

**Branch**: `070-h34-reversao-pos-liquidacao` | **Date**: 2026-09-06 | **Spec**: [spec.md](spec.md)

## Summary

`strategy/reversao_pos_liquidacao.py` (novo): `ReversaoPosLiquidacaoStrategy`
(subclasse de `BaseStrategy`, mesmo padrão de `strategy/breakout.py`) gera
BUY quando um candle bate o proxy de reversão pós-liquidação — pavio
inferior ≥ fração declarada do range, volume ≥ múltiplo declarado da média,
fechamento de recuperação (close > open) — sem SELL próprio; saída fica a
cargo do SL/TP/trailing por ATR já genérico em `simulate_backtest`.
`backtesting/reversao_pos_liquidacao.py` (novo): `gerar_resultado` (adapta a
estratégia ao `GerarResultado` do harness comum), `teste_sanidade` (série
sintética sem pavio/volume — zero trades esperado), `avaliar_par`/
`avaliar_universo` (roda `bateria_hipotese.rodar_bateria` por par de
`UNIVERSO_H11`, D3). `cmd_liquidacao()` (novo, `main.py`) imprime o
`RelatorioBateria` por par.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — reusa `backtesting.bateria_hipotese`
(harness E1-E6, spec 069-adjacent), `backtesting.engine.simulate_backtest`,
`backtesting.horizonte.UNIVERSO_H11`, `strategy.base.BaseStrategy`

**Storage**: nenhuma nova — resultado só impresso via `cmd_liquidacao`
(sem `export_report` nesta fase; ver Assumptions)

**Testing**: pytest — detecção do padrão (bate os três critérios / erra cada
um isoladamente / candle em warmup), `gerar_resultado` aplica custo zero
corretamente, `teste_sanidade` devolve zero trades sobre série sintética sem
pavio/volume, `avaliar_par`/`avaliar_universo` com `fetch_ohlcv` mockado
(sem rede)

**Target Platform**: CLI local (`python main.py liquidacao`); produção
intocada

**Performance Goals**: 12 pares (`UNIVERSO_H11`) × ~2000 candles × bateria
E1-E6 (janela única + busca/confirmação + 5 folds walk-forward + com/sem
custo ≈ 9 simulações por par) — mesma ordem de custo das demais hipóteses
recentes da bateria

**Constraints**: FR-001 — limiares de pavio/volume declarados no docstring
do módulo antes de qualquer medição real (D1/D2 abaixo); FR-003 — orquestra
via `bateria_hipotese.rodar_bateria`, não reimplementa E1-E6; FR-004 —
sanidade com série sintética sem o padrão

**Scale/Scope**: 2 módulos novos (~60 + ~90 linhas), 1 comando CLI novo

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/`, `risk/` ou pela estratégia em produção (`strategy/ema_rsi.py`). |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre detecção do padrão e sanidade antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Módulo + estratégia + comando + testes num tópico; execução real + registro noutro (mesmo padrão do commit de H30). |
| **V. Observability Mandatory** | **N/A direto.** Nenhuma decisão de risco nova; resultado é só de pesquisa. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** D1-D4 (limiar de pavio, limiar de volume, universo, janela) declarados no docstring do módulo antes de qualquer medição real. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/070-h34-reversao-pos-liquidacao/
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
└── reversao_pos_liquidacao.py       # novo: ReversaoPosLiquidacaoStrategy

backtesting/
└── reversao_pos_liquidacao.py       # novo: gerar_resultado, teste_sanidade, avaliar_par, avaliar_universo

main.py                              # +cmd_liquidacao, +"liquidacao" em COMMANDS

tests/
└── test_reversao_pos_liquidacao.py  # novo
```

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — D1-D4 declarados no docstring de
`backtesting/reversao_pos_liquidacao.py` antes de qualquer medição real
(ver `research.md`).

**Fase 1** — sem `data-model.md`/`contracts/` formais: reusa `BacktestResult`/
`RelatorioBateria` já existentes, nenhuma entidade nova.

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: estratégia + módulo de avaliação + comando +
testes num tópico; execução real + comparação com H3 + registro no
`docs/research/registro-de-hipoteses.md` noutro.
