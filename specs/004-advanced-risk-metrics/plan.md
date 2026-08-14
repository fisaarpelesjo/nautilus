# Implementation Plan: Métricas de Risco Avançadas

**Branch**: `004-advanced-risk-metrics` | **Date**: 2026-08-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-advanced-risk-metrics/spec.md`

## Summary

Duas frentes independentes: (US1/US2) estender `BacktestResult`/`_calculate_advanced_metrics` em
`backtesting/engine.py` com Sortino Ratio, Calmar Ratio, retorno anualizado e retorno por tempo
exposto — sempre exibidas no relatório de backtest já existente, sem flag nova (diferente das specs
001-003: aqui não há custo computacional extra nem mudança de fluxo, só mais números derivados de
dados já calculados); (US3) novo módulo `data/decisions_analysis.py` (espelhando
`backtesting/analysis.py`, que já faz o mesmo para `trades.csv`) para resumir `data/decisions.csv` —
novo comando `python main.py decisions`.

## Technical Context

**Language/Version**: Python 3.12 (mesmo ambiente das specs 001-003)

**Primary Dependencies**: `pandas`/`statistics` (stdlib, para desvio padrão do downside no Sortino),
`rich` (relatórios), `pytest`. Nenhuma dependência nova.

**Storage**: N/A para US1/US2 (métricas derivadas em memória). US3 só lê `data/decisions.csv`
(CSV já existente, gravado por `data/decision_store.py`) — nenhuma escrita nova.

**Testing**: `pytest` (suíte existente, 148 testes após a spec 003), estendida por esta feature. US3
testada com fixtures CSV sintéticas (ver `spec.md` → Assumptions: este ambiente não tem
`data/decisions.csv` real).

**Target Platform**: Mesma CLI local. US1/US2 sem flag nova (métricas sempre aparecem). US3:
`python main.py decisions`.

**Project Type**: CLI (mesmo monolito modular).

**Performance Goals**: Sortino/Calmar/anualizado/por-exposição são cálculos O(n) sobre dados já em
memória (mesma lista de trades usada por Sharpe/profit factor) — custo desprezível. Leitura de
`decisions.csv` é sequencial sobre um CSV local, sem rede.

**Constraints**: FR-010 exige que as métricas novas de US1/US2 sejam aditivas (aparecem a mais no
relatório já existente, sem substituir nada) — ao contrário das specs 001-003, aqui NÃO há uma flag
opcional escondendo o comportamento novo, porque não há trade-off de custo/compatibilidade a proteger
(são só mais linhas no mesmo relatório, sempre computáveis a partir de dados já calculados).

**Scale/Scope**: Mesma escala das specs anteriores para US1/US2. US3 opera sobre o volume de
`decisions.csv` que o bot já gera (1 linha por par por ciclo de 60s) — leitura sequencial simples,
sem necessidade de otimização especial no volume esperado deste bot pessoal.

## Constitution Check

*GATE: Deve passar antes da Fase 0. Reavaliado após a Fase 1.*

Referência: `.specify/memory/constitution.md` v1.0.0.

| Princípio | Avaliação |
|---|---|
| I. Safety First | PASS — feature é só de relatório/análise (leitura), não toca `risk/manager.py`, `execution/order_manager.py` nem `trading/position_lifecycle.py`. |
| II. No Secrets in Code | PASS — nenhuma configuração nova envolve segredo. |
| III. Test Before Implement | PASS — cada tarefa em `tasks.md` terá teste escrito antes da implementação, mesmo padrão das specs 001-003. |
| IV. Incremental Delivery | PASS — plano dividido em US1 → US2 → US3 → Polish, cada uma um commit pequeno. |
| V. Observability Mandatory | N/A — feature não introduz decisão de risco operacional; é relatório/análise, fora do pipeline de eventos JSONL/Telegram. |
| VI. Idempotency and Reconciliation | N/A — não toca execução de ordens. |
| VII. Explain Before Code | PASS — este `plan.md` documenta a decisão de não usar flag (US1/US2) e o novo comando `decisions` (US3) antes de qualquer tarefa de implementação. |

Nenhuma violação identificada. Nenhuma entrada necessária em Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/004-advanced-risk-metrics/
├── spec.md                       # Especificação (User Stories, requisitos, sucesso)
├── plan.md                       # Este arquivo
├── research.md                   # Fase 0 — decisões técnicas e alternativas consideradas
├── data-model.md                 # Fase 1 — entidades novas/alteradas
├── quickstart.md                 # Fase 1 — como validar cada User Story manualmente
├── contracts/
│   └── cli.md                    # Fase 1 — contrato da saída/comando afetados
├── checklists/
│   └── requirements.md           # Checklist de qualidade da spec
└── tasks.md                      # Fase 2 (/speckit-tasks) — tarefas executáveis
```

### Source Code (repository root)

```text
backtesting/
└── engine.py                  # ✏️ BacktestResult ganha sortino, calmar,
                                  annualized_return_pct, return_per_exposure_pct;
                                  _calculate_advanced_metrics calcula os 4;
                                  print_report exibe as novas linhas
data/
├── decisions_analysis.py      # NOVO — espelha backtesting/analysis.py (mesmo padrao,
│                                 mas para decisions.csv em vez de trades.csv)
└── paths.py                   # sem alteracao — DECISIONS_FILE ja existe
main.py                        # ✏️ novo comando `decisions` (+ alias `decisoes`)
tests/
├── test_backtesting_engine.py  # ✏️ estende para Sortino/Calmar/anualizado/exposicao
└── test_decisions_analysis.py  # NOVO — fixtures CSV sinteticas (sem decisions.csv real
                                   neste ambiente, ver spec.md Assumptions)
```

**Structure Decision**: `data/decisions_analysis.py` (não `backtesting/`) porque `decisions.csv` é um
log operacional do bot rodando (gravado por `data/decision_store.py`), não um artefato de backtest —
mesma divisão de responsabilidade já usada no projeto entre `data/` (persistência/leitura) e
`backtesting/` (simulação histórica). Estrutura interna espelha `backtesting/analysis.py`
deliberadamente (mesmo padrão dataclass + `_load_*` + `print_*` + `run()`) para manter os dois
comandos de análise (`analyze` para trades, `decisions` para ciclos) consistentes entre si.

## Complexity Tracking

*Nenhuma violação da Constitution Check — seção vazia intencionalmente.*
