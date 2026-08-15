# Implementation Plan: Replay Acelerado do Loop Real

**Branch**: `008-replay-acelerado-loop` | **Date**: 2026-08-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/008-replay-acelerado-loop/spec.md`

## Summary

Duas capacidades: (US1, MVP) motor de replay que roda `handle_entry_candidate`/
`handle_open_position` reais (não a simulação simplificada de backtest) candle a candle sobre
histórico público, com isolamento total garantido via context manager (nunca toca os arquivos reais
do bot, nunca envia ordem real, nunca dispara Telegram real — mesmo em erro); (US2) comparação do
resultado do replay contra um backtest simples do mesmo par/período, fechando parcialmente o gap do
`ROADMAP.md` Fase 5 item 4 sem exigir operação paper real por semanas.

## Technical Context

**Language/Version**: Python 3.12 (mesmo ambiente das specs 001-007)

**Primary Dependencies**: Nenhuma nova — reusa `OrderManager`, `handle_entry_candidate`/
`handle_open_position`, `EmaRsiStrategy`, `run_backtest` já existentes.

**Storage**: Nenhuma — todo o estado do replay é em memória, descartado ao final. Isolamento
garantido via monkeypatch scoped (context manager) das funções de I/O de `execution.order_manager`.

**Testing**: `pytest`. O foco de teste mais crítico desta spec é negativo: confirmar que os arquivos
reais NUNCA são tocados, inclusive em caminhos de erro — testado via monkeypatch dos próprios
`load_state`/`save_state`/`log_trade`/`log_event`/`send_telegram` reais com sentinelas que falham o
teste se forem chamados fora do escopo esperado.

**Target Platform**: Mesma CLI (`python main.py replay <PAR>`).

**Project Type**: CLI + daemon de longa duração (mesmo monolito modular) — esta spec só adiciona um
comando novo, não toca o daemon.

**Performance Goals**: Replay itera candle a candle recomputando indicadores a cada ciclo (mesmo
custo já aceito em `simulate_backtest` sem `precomputed_signals`) — aceitável para uma ferramenta
sob demanda, não roda no loop de produção.

**Constraints**: Constitution Principle I (Safety First) é o gate central e não-negociável desta
spec — FR-002/FR-003 (isolamento total, nunca ordem real) MUST passar em todos os testes antes de
qualquer commit. `execution/order_manager.py` e `trading/position_lifecycle.py` NÃO são modificados
por esta spec — reusados como estão, isolamento vive inteiramente em `trading/replay.py`.

**Scale/Scope**: Um par por execução (MVP) — múltiplos pares fica como evolução futura se o valor
for confirmado em uso.

## Constitution Check

*GATE: Deve passar antes da Fase 0. Reavaliado após a Fase 1.*

Referência: `.specify/memory/constitution.md` v1.0.0.

| Princípio | Avaliação |
|---|---|
| I. Safety First | PASS com atenção máxima — todo o design desta spec existe para satisfazer este princípio (isolamento total, nunca ordem real, mesmo em erro). Testado explicitamente, não só assumido. |
| II. No Secrets in Code | PASS — nenhuma configuração nova. |
| III. Test Before Implement | PASS — testes de isolamento escritos e confirmados falhando antes da implementação, mesmo padrão das specs anteriores. |
| IV. Incremental Delivery | PASS — US1 (isolamento + motor) antes de US2 (comparação). |
| V. Observability Mandatory | PASS — relatório final do replay documenta explicitamente suas próprias limitações (cooldown, MTF), não esconde a fidelidade parcial. |
| VI. Idempotency and Reconciliation | N/A — replay não envia ordens, não há nada para reconciliar. |
| VII. Explain Before Code | PASS — `research.md` documenta a decisão de isolamento e as limitações conhecidas (cooldown/MTF) antes de qualquer tarefa de implementação. |

Nenhuma violação identificada. Nenhuma entrada necessária em Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/008-replay-acelerado-loop/
├── spec.md / plan.md / research.md / data-model.md / quickstart.md
├── contracts/cli.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
trading/
└── replay.py            # NOVO -- run_replay(), isolamento via context manager,
                            reusa handle_entry_candidate/handle_open_position sem modifica-los
main.py                   # ✏️ cmd_replay novo
```

**Structure Decision**: Um único módulo novo (`trading/replay.py`), sem tocar nenhum arquivo de
execução crítica existente. Mínima superfície de mudança possível dado o requisito de segurança.

## Complexity Tracking

Nenhuma violação de Constitution Check — seção vazia, nenhuma justificativa necessária.
