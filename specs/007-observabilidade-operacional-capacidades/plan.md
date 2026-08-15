# Implementation Plan: Observabilidade Operacional

**Branch**: `007-observabilidade-operacional-capacidades` | **Date**: 2026-08-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/007-observabilidade-operacional-capacidades/spec.md`

## Summary

Cinco capacidades de observabilidade, todas read-only (nenhuma toca execução de ordens ou dinheiro
real): (US1) patrimônio operacional (caixa/posições/patrimônio total, PnL realizado/não realizado/
total) centralizado em `trading/portfolio.py` e exibido em `status`; (US2) contexto explícito de
simulação no relatório de `edge`; (US3) novo comando `painel` agregando dados já existentes em CSVs/
`state.json`; (US4) novo comando `debug <PAR>` explicando cada condição de entrada, estendendo
`strategy/diagnostics.py` já existente; (US5) gráficos de performance (`python main.py performance`)
e marcadores de trades reais no gráfico de candles já existente.

## Technical Context

**Language/Version**: Python 3.12 (mesmo ambiente das specs 001-006)

**Primary Dependencies**: `rich` (painel/status/debug), `plotly` (gráficos de performance, mesma lib
já usada em `utils/chart.py`), `pytest`. Nenhuma dependência nova.

**Storage**: Nenhuma nova — leitura read-only de `state.json`, `data/trades.csv`,
`data/signals.csv`, `data/decisions.csv`, todos já existentes.

**Testing**: `pytest` (suíte existente, 232 testes após a spec 006). Toda validação funcional usa
fixtures sintéticas ou dados públicos de backtest (FR-010) — nenhuma parte depende de histórico real
de operação paper.

**Target Platform**: Mesma CLI (`python main.py <comando>`). `performance` abre um HTML local no
navegador, mesmo padrão de `utils/chart.py`.

**Project Type**: CLI + daemon de longa duração (mesmo monolito modular).

**Performance Goals**: Todos os comandos desta spec são sob demanda (não rodam no loop de 60s do
bot) — sem impacto no ciclo operacional. `debug <PAR>` faz uma chamada de rede extra (MTF), aceitável
para um comando de diagnóstico manual.

**Constraints**: Todas as capacidades são read-only e aditivas — nenhuma tarefa altera
`execution/order_manager.py`, `risk/manager.py` ou o comportamento do loop principal do bot
(`trading/runner.py`). Patrimônio/PnL não realizado MUST tratar preço indisponível como
"indisponível", nunca `0.0` silencioso (FR-009, mesmo princípio já usado em `_current_balance`).

**Scale/Scope**: Mesma escala das specs anteriores.

## Constitution Check

*GATE: Deve passar antes da Fase 0. Reavaliado após a Fase 1.*

Referência: `.specify/memory/constitution.md` v1.0.0.

| Princípio | Avaliação |
|---|---|
| I. Safety First | PASS — spec inteiramente read-only, sem tocar execução de ordens ou dinheiro real. |
| II. No Secrets in Code | PASS — nenhuma configuração nova envolve segredo. |
| III. Test Before Implement | PASS — cada tarefa em `tasks.md` terá teste escrito antes da implementação. |
| IV. Incremental Delivery | PASS — plano dividido em US1 → US2 → US3 → US4 → US5 → Polish, cada uma um commit pequeno. |
| V. Observability Mandatory | N/A direto (esta spec É observabilidade) — mas os próprios comandos novos seguem o padrão já estabelecido de tratar dado ausente/indisponível de forma explícita, não silenciosa. |
| VI. Idempotency and Reconciliation | N/A — nenhuma ordem, nenhum estado persistido novo. |
| VII. Explain Before Code | PASS — `research.md` documenta as decisões (patrimônio centralizado, contexto isolado ao edge, painel textual vs web, extensão de diagnostics.py, camada extra de marcadores no chart) antes de qualquer tarefa de implementação. |

Nenhuma violação identificada. Nenhuma entrada necessária em Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/007-observabilidade-operacional-capacidades/
├── spec.md / plan.md / research.md / data-model.md / quickstart.md
├── contracts/cli.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
trading/
├── portfolio.py        # NOVO (US1) -- compute_portfolio_snapshot()
└── panel.py             # NOVO (US3) -- print_panel()
data/
├── trade_store.py       # ✏️ leitor tolerante de data/trades.csv (US3)
└── signal_store.py      # ✏️ leitor tolerante de data/signals.csv (US3)
strategy/
└── diagnostics.py       # ✏️ full_diagnosis() (US4), estende signal_checks()
backtesting/
├── validation.py        # ✏️ run_edge_report() chama contexto de simulacao (US2)
└── performance_charts.py # NOVO (US5) -- curva de capital, drawdown, PnL por par
utils/
├── display.py            # ✏️ patrimonio no status (US1), contexto de simulacao (US2)
└── chart.py               # ✏️ camada de marcadores de trades reais (US5)
main.py                   # ✏️ cmd_painel, cmd_debug, cmd_performance novos
```

**Structure Decision**: Mesmo monolito modular já estabelecido. Nenhuma reestruturação de diretórios.

## Complexity Tracking

Nenhuma violação de Constitution Check — seção vazia, nenhuma justificativa necessária.
