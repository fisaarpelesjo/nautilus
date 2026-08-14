# Quickstart: Validando o Hardening Incremental

Fase 1 do `/speckit-plan`. Roteiro para validar manualmente cada User Story em paper mode, antes de
considerar qualquer uma delas pronta para `TRADING_MODE=live` (Constitution, princípio I).

Pré-requisitos: ambiente Python configurado (`.venv`), dependências instaladas
(`pip install -r requirements-dev.txt`), `.env` com `TRADING_MODE=paper`.

## US1 — Idempotência e reconciliação

1. Rodar `pytest tests/test_order_manager_safety.py -v` e confirmar que os novos testes de
   `clientOrderId` único passam.
2. Abrir uma posição em paper mode (`python main.py bot` ou um script de teste que force um sinal de
   compra) e inspecionar `state.json` — o campo `client_order_id` deve estar presente e não vazio.
3. Simular reconciliação: com `TRADING_MODE=live` e Binance Testnet configurada, editar manualmente
   uma posição em `state.json` para não bater com a conta real, reiniciar o bot e confirmar que um
   evento `reconciliation_mismatch` aparece em `logs/events-YYYY-MM-DD.jsonl` e que nenhuma correção
   automática ocorre.

## US2 — Circuit breaker e kill switch

1. Rodar `pytest tests/test_order_manager_safety.py tests/test_killswitch_store.py
   tests/test_position_lifecycle.py -v` e confirmar que os testes de perdas consecutivas e kill
   switch passam (contador de perdas fica em `OrderManager`/`state.json`; kill switch em arquivo
   próprio, `data/killswitch.json` — ver nota de design em `tasks.md` Fase 4).
2. Em paper mode, forçar N trades consecutivos com prejuízo (via backtest de um cenário conhecido
   ruim, ou editando `state.json` para simular o histórico) e confirmar que `circuit_breaker_active`
   vira `true` e que o bot para de abrir novas posições no próximo ciclo.
3. Rodar `python main.py kill`, confirmar mensagem de confirmação e evento `killswitch_toggled` no
   log. Rodar `python main.py status` e confirmar que o kill switch aparece ativo. Rodar
   `python main.py resume` e confirmar que volta a `false`.

## US3 — Validação out-of-sample

1. Rodar `pytest tests/test_backtesting_validation.py tests/test_main_backtest.py -v` e confirmar
   que os testes de split treino/validação e do dispatch do CLI passam.
2. Rodar `python main.py backtest --validate` sobre um par com histórico suficiente (pelo menos ~500
   candles no timeframe configurado, para que as duas fatias passem de `MIN_WINDOW_CANDLES=150`) e
   confirmar que o relatório no terminal mostra métricas de treino e de validação lado a lado, com um
   veredito aprovado/reprovado/inconclusivo. `python main.py backtest` sem a flag deve continuar
   idêntico ao comportamento anterior a esta spec (FR-009).

## Checklist final antes de qualquer go-live

Ver `plan.md` → Constitution Check (princípio I) e `specs/001-hardening-incremental/tasks.md` →
Fase de Polish (T037) para o checklist completo de go-live.
