# Implementation Plan: Proteções Finais para Live

**Branch**: `005-live-protections` | **Date**: 2026-08-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-live-protections/spec.md`

## Summary

Quatro capacidades sobre a base de segurança já existente (specs 001/002): (US1) banner de
confirmação visível antes do loop principal em `TRADING_MODE=live`; (US2) limites de perda semanal e
mensal, extensão direta do `daily_pnl`/circuit breaker já existente em
`execution/order_manager.py` — inclui corrigir um bug real encontrado no planejamento (o limite diário
usa `* 1000.0` hardcoded como base, não o saldo real, o que torna o limite sem sentido para uma conta
live com saldo diferente de $1000); (US3) checagem de liquidez/spread do order book antes de uma
ordem, integrada à cadeia de `blockers` já existente em `handle_entry_candidate`; (US4) ordens limit
com rastreamento de preenchimento parcial, como capacidade adicional **desligada por padrão**
(`USE_LIMIT_ORDERS=false`), preservando 100% do comportamento a mercado já validado em paper mode.

## Technical Context

**Language/Version**: Python 3.12 (mesmo ambiente das specs 001-004)

**Primary Dependencies**: `ccxt` (order book via `fetch_order_book`, ordens limit via
`create_limit_buy_order`/`fetch_order`), `rich` (banner), `pytest`. Nenhuma dependência nova.

**Storage**: Extensão de `state.json` já existente (`execution/order_manager.py` `_persist_state`) —
novos campos (`weekly_pnl`, `monthly_pnl`, referências de saldo, ordens limit pendentes), mesmo
mecanismo de escrita atômica já em uso.

**Testing**: `pytest` (suíte existente, 167 testes após a spec 004). Toda a lógica de US1-US3 e a
máquina de estado de US4 são testáveis em paper mode/mockado; o comportamento real de preenchimento
parcial (US4) só é confirmável de fato em Binance Testnet — fora do escopo de teste automatizado desta
sessão, documentado como validação em camadas (mesmo padrão já usado nas specs 001/003 para o que não
pode ser confirmado só com dados públicos).

**Target Platform**: Mesma CLI/daemon local (`python main.py bot`). Nenhuma mudança de plataforma.

**Project Type**: CLI + daemon de longa duração (mesmo monolito modular).

**Performance Goals**: A checagem de liquidez (US3) adiciona uma chamada de rede (`fetch_order_book`)
só quando nenhum bloqueio mais barato já descartou a entrada (mesmo princípio "checagem cara por
último" já estabelecido em `handle_entry_candidate` para MTF/saldo) — cabe dentro do orçamento de 60s
por ciclo já usado pelo bot. A verificação de ordens limit pendentes (US4) roda uma vez por ciclo,
mesmo padrão da reconciliação periódica (spec 001).

**Constraints**: Constitution princípio I (Safety First) é o gate mais importante desta spec — nenhuma
tarefa habilita `TRADING_MODE=live` nem contorna `LIVE_TRADING_CONFIRMATION`; `USE_LIMIT_ORDERS`
default `false` preserva o comportamento a mercado já validado; toda mudança em `execution/`
`risk/`/`trading/position_lifecycle.py` segue o mesmo padrão de isolamento de erro (`safe_step`,
`_persist_state_with_retry`) já estabelecido nesses arquivos.

**Scale/Scope**: Mesma escala das specs anteriores — até `MAX_POSITIONS` posições simultâneas, até
~30 pares monitorados.

## Constitution Check

*GATE: Deve passar antes da Fase 0. Reavaliado após a Fase 1.*

Referência: `.specify/memory/constitution.md` v1.0.0.

| Princípio | Avaliação |
|---|---|
| I. Safety First | PASS com atenção redobrada — esta é a primeira spec desde a 001 a tocar `execution/order_manager.py` e `trading/position_lifecycle.py` diretamente. `USE_LIMIT_ORDERS` default `false`; nenhuma tarefa habilita live; validação em paper mode + Testnet antes de qualquer uso real (FR-013, checklist go-live já existente T037 da spec 001 continua sendo a referência). |
| II. No Secrets in Code | PASS — nenhuma configuração nova envolve segredo. |
| III. Test Before Implement | PASS — cada tarefa em `tasks.md` terá teste escrito antes da implementação. |
| IV. Incremental Delivery | PASS — plano dividido em US1 → US2 → US3 → US4 → Polish, cada uma um commit pequeno; dentro de US4, sub-tópicos ainda menores dado o risco. |
| V. Observability Mandatory | PASS — limites semanal/mensal (US2) e liquidez bloqueada (US3) geram evento no mesmo pipeline JSONL/Telegram já existente (`log_event`/`send_telegram`), mesmo padrão do circuit breaker (spec 001 US2). Ordens limit (US4) reusam os eventos `live_order_opened`/`live_order_error` já existentes, com campo novo indicando tipo de ordem. |
| VI. Idempotency and Reconciliation | Diretamente relevante a US4 — ordens limit MUST usar `clientOrderId` idempotente, mesmo padrão já estabelecido em `_live_buy`/`_live_sell` (reusar ID pendente entre tentativas/ciclos, não gerar um novo a cada chamada). |
| VII. Explain Before Code | PASS — este `plan.md` documenta as decisões de design (banner não-bloqueante, correção do bug do limite diário, máquina de estado de ordens limit) antes de qualquer tarefa de implementação. |

Nenhuma violação identificada. Nenhuma entrada necessária em Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/005-live-protections/
├── spec.md                       # Especificação (User Stories, requisitos, sucesso)
├── plan.md                       # Este arquivo
├── research.md                   # Fase 0 — decisões técnicas e alternativas consideradas
├── data-model.md                 # Fase 1 — entidades novas/alteradas
├── quickstart.md                 # Fase 1 — como validar cada User Story manualmente
├── contracts/
│   └── cli.md                    # Fase 1 — contrato do comportamento de `bot`/config afetados
├── checklists/
│   └── requirements.md           # Checklist de qualidade da spec
└── tasks.md                      # Fase 2 (/speckit-tasks) — tarefas executáveis
```

### Source Code (repository root)

```text
config/
└── settings.py                 # ✏️ WEEKLY_DRAWDOWN_LIMIT, MONTHLY_DRAWDOWN_LIMIT,
                                   MAX_SPREAD_PCT_ENTRY, MIN_ORDERBOOK_DEPTH_USDT,
                                   USE_LIMIT_ORDERS, LIMIT_ORDER_TIMEOUT_CYCLES
execution/
├── order_manager.py            # ✏️ weekly_pnl/monthly_pnl (mesmo padrao de daily_pnl,
│                                  reference balance real em vez do bug `* 1000.0`
│                                  hardcoded); pending_limit_orders (US4); _live_buy ganha
│                                  caminho de ordem limit quando USE_LIMIT_ORDERS=true
└── liquidity.py                # NOVO (US3) — check_liquidity(symbol) via fetch_order_book
data/
└── state_store.py               # sem alteracao de schema (campos novos vivem dentro do
                                    dict ja generico persistido por order_manager.py)
trading/
├── runner.py                    # ✏️ banner de confirmacao live (US1) antes do loop;
│                                   checagem de ordens limit pendentes por ciclo (US4)
└── position_lifecycle.py        # ✏️ handle_entry_candidate ganha blocker de liquidez
                                    (US3) e dos limites semanal/mensal (US2)
main.py                          # sem novo comando -- tudo dentro do fluxo de `bot` ja
                                    existente
tests/
├── test_order_manager_safety.py # ✏️ estende para weekly/monthly limits, reference balance
├── test_liquidity.py             # NOVO
├── test_position_lifecycle.py   # ✏️ estende para os novos blockers
├── test_runner_live_banner.py    # NOVO
└── test_limit_orders.py          # NOVO (US4)
```

**Structure Decision**: `execution/liquidity.py` novo (não dentro de `order_manager.py`, já grande e
crítico) para a checagem de order book — mesmo critério de extração já usado nas specs 002/003
(módulo focado, testável isoladamente). Ordens limit (US4) ficam dentro de `order_manager.py` (não um
módulo separado) porque manipulam o mesmo estado (`positions`, `pending_open_client_order_ids`) que
`_live_buy` já gerencia — separar aumentaria o risco de os dois ficarem dessincronizados.

## Complexity Tracking

*Nenhuma violação da Constitution Check — seção vazia intencionalmente.*
