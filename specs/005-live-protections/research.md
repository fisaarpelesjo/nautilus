# Research: Proteções Finais para Live

Fase 0 do `/speckit-plan`. Nenhum item do Technical Context ficou como `NEEDS CLARIFICATION`. As
decisões abaixo resolvem as alternativas deixadas em aberto no `Assumptions` do `spec.md`.

## Banner de confirmação não-bloqueante (US1)

- **Decision**: `_print_live_confirmation_banner()` em `trading/runner.py`, chamado uma vez em `run()`
  quando `TRADING_MODE == "live"`, antes do loop principal — depois de `OrderManager()` já ter sido
  criado (para ter saldo real via `fetch_balance()`, pares ativos e todos os limites configurados
  disponíveis). Imprime via `console`/`rich` e grava via `log_event("live_session_started", ...)` —
  não usa `input()`/prompt interativo.
- **Rationale**: FR-003 e o Edge Case de processo não-interativo exigem explicitamente que o bot não
  trave esperando confirmação adicional além do `LIVE_TRADING_CONFIRMATION` já validado em
  `config/settings.py`. Gravar via `log_event` (não só `console.print`) garante que o resumo fique
  auditável mesmo rodando como serviço/cron sem terminal anexado.
- **Alternatives considered**: prompt interativo (`input("Confirma? [s/N]")`) — rejeitado
  explicitamente pelo Edge Case (bloquearia um processo não-interativo indefinidamente); banner só em
  log, sem `console.print` — rejeitado porque o caso de uso principal (SC-001) é o operador rodando
  manualmente e vendo o resumo na tela antes de sair do terminal.

## Limites semanal/mensal + correção do bug do limite diário (US2)

- **Decision**: mesmo padrão exato de `daily_pnl`/`daily_reset_date` já existente em
  `OrderManager`, duplicado para `weekly_pnl`/`weekly_reset_date` (chave: número ISO da semana,
  `datetime.now().strftime("%G-W%V")`) e `monthly_pnl`/`monthly_reset_date` (chave: `YYYY-MM`).
  **Corrige no mesmo commit** um bug real encontrado durante o planejamento: `is_daily_limit_hit()`
  hoje usa `DAILY_DRAWDOWN_LIMIT * 1000.0` — `1000.0` é o saldo paper *default*, hardcoded, não o
  saldo real da conta. Numa conta live com saldo diferente de $1000, o limite diário de "5% do saldo"
  não tem relação nenhuma com 5% do saldo de verdade. Correção: cada período (dia/semana/mês) captura
  um `*_reference_balance` no momento do reset (saldo real via `_reference_balance()`, novo método
  privado de `OrderManager` — paper usa `self.paper_balance_usdt`, live busca via `fetch_balance()`),
  e os três limites (`is_daily_limit_hit`, `is_weekly_limit_hit`, `is_monthly_limit_hit`) comparam
  contra esse saldo de referência, não um número fixo.
- **Rationale**: replicar o padrão já testado e validado (não inventar uma estrutura de dado nova)
  minimiza risco numa área crítica; a correção do bug do saldo de referência é inseparável de
  implementar corretamente os dois limites novos (copiar o bug seria pior que não corrigi-lo, já que
  triplica a superfície do problema).
- **Alternatives considered**: janela deslizante de N dias (não calendário) — rejeitada por
  complexidade extra sem pedido explícito na spec (`Assumptions` já define o padrão calendário);
  manter o bug do saldo de referência e só copiar o padrão para semanal/mensal — rejeitado, seria
  propagar conscientemente um bug de segurança financeira real para código novo.
- **`_reference_balance()` duplica parte da lógica de `trading/position_lifecycle.py`
  `_current_balance()`** (mesma bifurcação paper/live) em vez de reusá-la — aceito conscientemente:
  `position_lifecycle.py` já importa de `execution/order_manager.py`; a direção inversa criaria
  import circular. A duplicação é pequena (~6 linhas) e isolada num método privado.

## Checagem de liquidez e spread (US3)

- **Decision**: novo `execution/liquidity.py`, função `check_liquidity(symbol, order_size_usdt) ->
  LiquidityCheck` (aprovado/bloqueado + motivo). Usa `exchange.fetch_order_book(symbol, limit=20)`:
  spread = `(ask[0] - bid[0]) / bid[0]`, bloqueia se `> MAX_SPREAD_PCT_ENTRY` (novo, default `0.005` —
  mais permissivo que o `MAX_SPREAD_PCT` já existente em `config/settings.py`, que é usado na seleção
  dinâmica de pares, não na checagem por-ordem); profundidade = soma do volume em USDT nos primeiros N
  níveis do lado ask, bloqueia se `< MIN_ORDERBOOK_DEPTH_USDT` (novo, default 3× o
  `MAX_ORDER_SIZE_USDT` configurado, para garantir margem sobre o tamanho da própria ordem). Integrado
  em `handle_entry_candidate` como mais um item da lista de `blockers`, verificado depois do MTF
  (mesma posição na cadeia "checagem cara por último" já estabelecida) e antes do saldo (agrupando as
  duas chamadas de rede).
- **Rationale**: reusa `fetch_order_book`, já suportado pelo `ccxt`/Binance sem configuração adicional.
  Um novo `MAX_SPREAD_PCT_ENTRY` (em vez de reusar `MAX_SPREAD_PCT`) evita acoplar um limiar pensado
  para "vale a pena considerar este par" (seleção dinâmica, roda raramente) a um limiar de "vale a
  pena executar esta ordem agora" (checagem por ciclo, mais crítico).
- **Alternatives considered**: reusar `MAX_SPREAD_PCT` existente — rejeitado pelo motivo acima (dois
  contextos de decisão diferentes, mesmo limiar seria uma coincidência frágil se um dos dois mudar
  depois); checar liquidez só uma vez por ciclo para todos os pares candidatos, não por ordem —
  rejeitado porque o spread/profundidade pode mudar entre o sinal e o envio da ordem, e
  `MAX_ENTRIES_PER_CYCLE=1` já significa que no máximo 1 checagem por ciclo acontece de qualquer
  forma.
- **Falha de rede ao buscar order book**: tratada como bloqueio (`"liquidez indisponivel"`), mesmo
  princípio já usado para saldo desconhecido em `handle_entry_candidate` (spec 001) — nunca aprovar
  por omissão de dado.

## Ordens limit com rastreamento de preenchimento parcial (US4)

- **Decision**: capacidade nova, **desligada por padrão** (`USE_LIMIT_ORDERS=false`). Quando
  habilitada, `_live_buy` (em vez de `create_market_buy_order`) chama `create_limit_buy_order` com
  preço = melhor oferta de venda (`ask`) do order book já buscado pela checagem de liquidez de US3
  (reuso, não uma segunda chamada de rede). A ordem entra num dicionário novo
  `pending_limit_orders: Dict[str, PendingLimitOrder]` (symbol → clientOrderId, preço, quantidade
  solicitada, ciclo em que foi enviada), persistido em `state.json`. A cada ciclo subsequente,
  `trading/runner.py` chama `check_pending_limit_orders()` (novo método de `OrderManager`), que usa
  `fetch_order(clientOrderId)` para consultar o estado real: se `filled == amount` → posição aberta
  com a quantidade cheia (fluxo igual ao de mercado a partir daqui); se `0 < filled < amount` e o
  número de ciclos configurável (`LIMIT_ORDER_TIMEOUT_CYCLES`, default 3) foi atingido → cancela o
  restante (`cancel_order`) e abre a posição só com a quantidade já preenchida; se `filled == 0` e o
  timeout foi atingido → cancela e descarta (sinal perdido, reavaliado do zero no próximo ciclo se
  ainda válido).
- **Rationale**: reusa o mesmo ciclo de 60s já existente (nenhuma infraestrutura de polling nova) e o
  mesmo padrão de `clientOrderId` idempotente já validado em `_live_buy`/`_live_sell` — uma ordem
  limit pendente sobrevive a um restart do bot exatamente como uma compra/venda pendente já sobrevive
  hoje. Cancelar e assumir o preenchimento parcial (em vez de reverter para mercado) é a opção mais
  simples e mais segura: não introduz uma segunda ordem/segunda superfície de erro na mesma tentativa.
- **Alternatives considered**: reverter para ordem a mercado no timeout (a outra opção citada em
  FR-011) — mais completa mas dobra a superfície de teste/erro (duas chamadas de execução por
  tentativa); avaliada como possível evolução futura, não necessária para fechar o requisito ("um
  comportamento definido", não exige ser o mais sofisticado); aguardar preenchimento com polling
  assíncrono dentro do mesmo ciclo (não entre ciclos) — rejeitada por introduzir concorrência
  (threads/async) numa base de código hoje síncrona, mesmo non-goal já registrado no `research.md` da
  spec 001 para a reconciliação.
- **Posição residual abaixo do mínimo negociável (LOT_SIZE/MIN_NOTIONAL)**: não pré-computado via
  `exchange.markets[symbol]['limits']` nesta spec — tratado via o mesmo caminho de erro já existente
  (`_live_sell` captura exceção da exchange ao tentar fechar/ajustar e alerta) em vez de adicionar uma
  segunda fonte de verdade sobre limites do par. Registrado como observação para uma iteração futura
  se se provar um problema real em uso.

## Superfície de configuração nova

- `WEEKLY_DRAWDOWN_LIMIT` (default `0.10`, 10% — dobro do diário, mesmo espírito de limites em
  camadas), `MONTHLY_DRAWDOWN_LIMIT` (default `0.20`, 20%).
- `MAX_SPREAD_PCT_ENTRY` (default `0.005`, 0.5%), `MIN_ORDERBOOK_DEPTH_USDT` (default
  `3 * MAX_ORDER_SIZE_USDT`, calculado em `config/settings.py` a partir do valor já configurado, não
  um segundo número independente para o operador manter sincronizado).
- `USE_LIMIT_ORDERS` (default `false`), `LIMIT_ORDER_TIMEOUT_CYCLES` (default `3`, ~3 minutos no
  ciclo de 60s já existente).
- Validação em `validate_config()`: `WEEKLY_DRAWDOWN_LIMIT` MUST ser `>= DAILY_DRAWDOWN_LIMIT` e
  `MONTHLY_DRAWDOWN_LIMIT MUST ser >= WEEKLY_DRAWDOWN_LIMIT` (Edge Case do `spec.md` — limites
  inconsistentes rejeitados na configuração, não em runtime).
