# Implementation Plan: Motor de carteira para aprovação de H14

**Branch**: `037-motor-carteira-h14` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/portfolio_h14.py::simular_carteira()` reusa o modelo já
treinado por `run_modelo_scan()` (`backtesting/modelo.py`, sem retreinar,
D2) e simula os 12 pares de `UNIVERSO_H11` numa única linha do tempo
compartilhada, com um caixa único e `MAX_POSITIONS` como teto (FR-004/
FR-006). Cada entrada usa o dimensionamento já documentado em `CLAUDE.md`
(FR-005); cada saída usa as barreiras já declaradas de H14 (FR-003). O
resultado vira um `BacktestResult` (`backtesting/engine.py`, reusado sem
alteração), avaliado por `evaluate_approval()` (`backtesting/approval.py`,
sem critério novo, FR-009) — a resposta que faltava desde `specs/
036-historico-estendido/` §4.15.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `backtesting/modelo.py`
(`run_modelo_scan`, `AvaliacaoH14`, coeficientes já treinados),
`backtesting/engine.py` (`Trade`, `BacktestResult`,
`_calculate_advanced_metrics`), `backtesting/approval.py::evaluate_approval`

**Storage**: `reports/carteira_h14_*.json` (padrão `export_report` já
existente)

**Testing**: pytest, `tests/test_portfolio_h14.py` (novo)

**Target Platform**: CLI local (`python main.py carteira`); produção
intocada

**Performance Goals**: simulação candle a candle sobre a união das linhas
do tempo de 12 pares (mesma ordem de grandeza de `simulate_backtest()`
multiplicada por 12) — sem chamada de rede além do fetch já usado por
`run_modelo_scan`

**Constraints**: FR-003 — nenhum mecanismo de saída novo, só as barreiras
já declaradas; FR-007 — sem correlação/liquidez/trailing/circuit
breaker/limites de drawdown periódico; FR-009 — `BacktestResult` produzido
MUST passar por `evaluate_approval()` sem alteração de assinatura ou
critério; FR-010 — nenhuma ordem real

**Scale/Scope**: 1 módulo novo (`backtesting/portfolio_h14.py`), 1
extensão mínima em `backtesting/modelo.py` (probabilidade de teste
exposta, opt-in), 1 comando CLI, 12 pares (`UNIVERSO_H11`)

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/` (FR-010). |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre a mecânica de carteira (caixa compartilhado, teto de posições, desempate) com teste antes da implementação. |
| **IV. Incremental Delivery** | **Conforme.** Extensão de `modelo.py` + motor de carteira num tópico; comando CLI + execução real + comparação (US3) noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado de pesquisa via `export_report`, mesmo padrão de `modelo`/`grid`. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** D1-D6 (`research.md`) declaram capital inicial, extensão de `avaliar_par`, alinhamento de linha do tempo, desempate e arquivo novo antes de qualquer código. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/037-motor-carteira-h14/
├── plan.md              # este arquivo
├── research.md          # Fase 0 (D1-D6)
├── data-model.md         # Fase 1
└── quickstart.md         # Fase 1
```

Sem `contracts/`: comando de pesquisa segue o padrão já estabelecido por
`modelo`/`grid`/`onchain` (sem contrato formal separado).

### Source Code (repository root)

```text
backtesting/
├── modelo.py              # +parametro opt-in em avaliar_par (retorna
│                           # previsao_teste quando pedido; default
│                           # inalterado, regressao testada)
└── portfolio_h14.py        # NOVO: CarteiraH14, simular_carteira(pares,
                            # capital_inicial) -> BacktestResult

main.py                     # +cmd_carteira

tests/
├── test_modelo.py           # +regressao do novo parametro opt-in
└── test_portfolio_h14.py    # NOVO
```

`backtesting/engine.py`, `backtesting/approval.py` **não são alterados** —
só consumidos.

## Complexity Tracking

Vazio — nenhuma violação de princípio a justificar.

## Fases

**Fase 0 ✅** — D1 (capital inicial) → D2 (extensão opt-in de
`avaliar_par`) → D3 (alinhamento de linha do tempo entre pares) → D4
(critério de desempate) → D5 (buy-and-hold de carteira) → D6 (arquivo
novo, reuso do motor de métricas).

**Fase 1 ✅** — `data-model.md` + `quickstart.md`. Sem `contracts/`.

**Fase 2** — `tasks.md` (`/speckit-tasks`).

**Fase 3** — implementação (`/speckit-implement`), dois tópicos:
1. `avaliar_par` (parâmetro opt-in) + `backtesting/portfolio_h14.py`
   (`simular_carteira()` — caixa compartilhado, teto de posições,
   desempate, saída por barreira)
2. `run_modelo_scan` → `simular_carteira` (fluxo completo) + `cmd_carteira()`
   (CLI) + execução real sobre `UNIVERSO_H11`, veredito registrado em
   `docs/research/registro-de-hipoteses.md` §4.15
