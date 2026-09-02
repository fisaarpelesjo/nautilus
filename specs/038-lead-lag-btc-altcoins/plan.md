# Implementation Plan: H21 — Lead-lag BTC para altcoins

**Branch**: `038-lead-lag-btc-altcoins` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/lead_lag.py::avaliar_lead_lag(par)` calcula o retorno de
BTC/USDT no mesmo candle avaliado (`close[t]/close[t-1] - 1`, D1),
constrói um sinal BUY-only (`Signal.BUY` quando o retorno é positivo,
`Signal.HOLD` no resto — FR-002) e reusa
`backtesting/modelo.py::_simular_com_sinais` (que já envolve
`simulate_backtest`) para produzir um `BacktestResult` — mesmo mecanismo
de saída (take-profit ATR + stop trailing) de toda avaliação do projeto,
sem reimplementar o motor de backtest. `run_lead_lag_scan()` varre os 11
pares de `UNIVERSO_H11` menos BTC/USDT (FR-004), aplica
`evaluate_approval()` sem critério novo (FR-006).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `backtesting/horizonte.py`
(`preparar`), `backtesting/modelo.py::_simular_com_sinais` (reusa
`simulate_backtest` sem duplicar), `backtesting/approval.py::evaluate_approval`,
`strategy/ema_rsi.py` (só para indicadores/ATR, não para o sinal)

**Storage**: `reports/leadlag_*.json` (padrão `export_report` já existente)

**Testing**: pytest, `tests/test_lead_lag.py` (novo)

**Target Platform**: CLI local (`python main.py leadlag`); produção
intocada

**Performance Goals**: 1 fetch de BTC/USDT + 1 fetch por altcoin (11),
mesma ordem de grandeza de `run_grid_scan`/`run_modelo_scan` — sem
treino de modelo, mais leve que H14/H37

**Constraints**: FR-002 — sinal binário sobre o sinal do retorno, sem
limiar de magnitude; FR-003 — nenhum mecanismo de saída novo; FR-007 —
nenhuma ordem real

**Scale/Scope**: 1 módulo novo (`backtesting/lead_lag.py`), 1 comando
CLI, 11 pares avaliados (`UNIVERSO_H11` menos BTC/USDT)

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/` (FR-007). |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre o alinhamento de sinal BTC→altcoin e a ausência de *lookahead* com teste antes da implementação. |
| **IV. Incremental Delivery** | **Conforme.** Sinal + avaliação por par num tópico; comando CLI + execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado de pesquisa via `export_report`, mesmo padrão de `modelo`/`grid`/`carteira`. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** D1-D4 (`research.md`) declaram a defasagem, a fórmula exata (corrigida para não ter *lookahead* nem um candle de atraso a mais do que o medido), o universo e a reutilização do motor, antes de qualquer código. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/038-lead-lag-btc-altcoins/
├── plan.md              # este arquivo
├── research.md          # Fase 0 (D1-D4)
├── data-model.md         # Fase 1
└── quickstart.md         # Fase 1
```

Sem `contracts/`: comando de pesquisa segue o padrão já estabelecido por
`modelo`/`grid`/`onchain`/`carteira` (sem contrato formal separado).

### Source Code (repository root)

```text
backtesting/
└── lead_lag.py            # NOVO: btc_retorno_no_candle(btc_close),
                            # _sinais_lead_lag(btc_ret, indice_par),
                            # avaliar_lead_lag(par, ...) -> BacktestResult,
                            # run_lead_lag_scan(pares=UNIVERSO_H11 menos BTC)

main.py                     # +cmd_leadlag

tests/
└── test_lead_lag.py         # NOVO
```

`backtesting/engine.py`, `backtesting/approval.py`, `backtesting/modelo.py`
**não são alterados** — só consumidos.

## Complexity Tracking

Vazio — nenhuma violação de princípio a justificar.

## Fases

**Fase 0 ✅** — D1 (defasagem N=1, fórmula corrigida sem *lookahead*) →
D2 (sinal binário sobre o sinal, não magnitude) → D3 (universo: 11 pares,
sem BTC) → D4 (reuso de `_simular_com_sinais`, sem motor novo).

**Fase 1 ✅** — `data-model.md` + `quickstart.md`. Sem `contracts/`.

**Fase 2** — `tasks.md` (`/speckit-tasks`).

**Fase 3** — implementação (`/speckit-implement`), dois tópicos:
1. `backtesting/lead_lag.py`: sinal + `avaliar_lead_lag()` — mecânica de
   alinhamento BTC↔altcoin, ausência de *lookahead*, `BacktestResult` via
   `_simular_com_sinais`
2. `run_lead_lag_scan()` + `cmd_leadlag()` (CLI) + execução real sobre os
   11 pares, veredito registrado no registro-mestre (H21)
