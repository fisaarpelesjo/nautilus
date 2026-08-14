# Quickstart: Validando as Proteções Finais para Live

Fase 1 do `/speckit-plan`. **Nenhum passo abaixo exige `TRADING_MODE=live` com dinheiro real** — toda
validação funcional é feita em paper mode ou com mocks; a confirmação final de comportamento real de
ordens limit (US4) é a única exceção, e mesmo essa fica em Binance Testnet, nunca com fundos reais.

Pré-requisitos: ambiente Python configurado (`.venv`), dependências instaladas.

## US1 — Banner de confirmação live

1. Rodar `pytest tests/test_runner_live_banner.py -v` e confirmar que passam, incluindo o caso de
   `TRADING_MODE=paper` (banner NÃO aparece).
2. Validar manualmente só em Binance Testnet (`TRADING_MODE=live` apontando para Testnet, nunca conta
   real): confirmar que o banner aparece com dados reais antes de qualquer ordem poder ser enviada.

## US2 — Limites semanal e mensal

1. Rodar `pytest tests/test_order_manager_safety.py -v` (testes de `weekly_pnl`/`monthly_pnl`/
   `*_reference_balance`) e confirmar que passam, incluindo o teste de regressão do bug do saldo de
   referência hardcoded.
2. Em paper mode, simular perdas acumuladas que ultrapassam o limite semanal mas não o diário nem o
   circuit breaker, e confirmar que `python main.py status` mostra o bloqueio semanal ativo.

## US3 — Checagem de liquidez e spread

1. Rodar `pytest tests/test_liquidity.py -v` e confirmar que passam, incluindo falha de rede
   (bloqueio conservador) e os dois motivos de bloqueio (spread e profundidade) separadamente.
2. Em paper mode, com um order book mockado de spread alto, confirmar que a entrada é bloqueada com
   motivo `"liquidez"` em `data/decisions.csv`.

## US4 — Ordens limit com preenchimento parcial

1. Rodar `pytest tests/test_limit_orders.py -v` (máquina de estado: enviar, checar preenchimento
   parcial/total, timeout) e confirmar que passam — tudo mockado, sem rede real.
2. Confirmar que `USE_LIMIT_ORDERS=false` (default) mantém `python main.py bot` idêntico ao
   comportamento já validado (ordem a mercado) — rodar a suíte completa e comparar.
3. Validação final (só Testnet, nunca live real): habilitar `USE_LIMIT_ORDERS=true` contra Binance
   Testnet e confirmar que uma ordem limit é enviada, preenchimento parcial é refletido corretamente
   na posição local, e o timeout cancela/assume conforme configurado.

## Checklist final antes de qualquer go-live

Esta spec toca `execution/order_manager.py` e `trading/position_lifecycle.py` diretamente — o
checklist de go-live já existente em `specs/001-hardening-incremental/tasks.md` (T037) continua sendo
a referência obrigatória, com os itens novos desta spec adicionados: `USE_LIMIT_ORDERS` revisado
conscientemente (ligado ou não), `WEEKLY_DRAWDOWN_LIMIT`/`MONTHLY_DRAWDOWN_LIMIT` ajustados ao apetite
de risco real do operador (não só os defaults), e o banner de confirmação testado em Testnet pelo
menos uma vez antes de qualquer uso com saldo real.
