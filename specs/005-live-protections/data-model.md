# Data Model: Proteções Finais para Live

Fase 1 do `/speckit-plan`. Extensões de `state.json` (já persistido por
`execution/order_manager.py`) e entidades transientes novas.

## Contadores de perda por período (extensão de `OrderManager`/`state.json`)

Mesmo padrão já existente para `daily_pnl`/`daily_reset_date`, agora também para semana e mês —
`daily_reference_balance` é novo mesmo para o diário (correção do bug do `* 1000.0` hardcoded, ver
`research.md`).

| Campo | Tipo | Regras |
|---|---|---|
| `daily_reference_balance` | float | Saldo real capturado no momento do último reset diário (era hardcoded `1000.0` antes desta spec). |
| `weekly_pnl` | float | PnL acumulado na semana ISO corrente. |
| `weekly_reset_date` | string | Semana ISO corrente (`YYYY-Www`), usada para detectar virada. |
| `weekly_reference_balance` | float | Saldo real capturado no início da semana corrente. |
| `monthly_pnl` | float | PnL acumulado no mês corrente. |
| `monthly_reset_date` | string | Mês corrente (`YYYY-MM`), usada para detectar virada. |
| `monthly_reference_balance` | float | Saldo real capturado no início do mês corrente. |

## Ordem limit pendente (nova, extensão de `state.json` — só quando `USE_LIMIT_ORDERS=true`)

| Campo | Tipo | Regras |
|---|---|---|
| `symbol` | string | Par da ordem pendente. |
| `client_order_id` | string | Mesmo `clientOrderId` idempotente reusado em todas as consultas/tentativas desta ordem. |
| `limit_price` | float | Preço limite enviado (melhor `ask` do order book no momento do envio). |
| `requested_quantity` | float | Quantidade solicitada originalmente. |
| `placed_at_cycle` | inteiro | Contador de ciclo em que a ordem foi enviada — usado para calcular `LIMIT_ORDER_TIMEOUT_CYCLES`. |

## Resultado de checagem de liquidez (novo, transiente — `execution/liquidity.py`)

| Campo | Tipo | Regras |
|---|---|---|
| `approved` | booleano | `false` bloqueia a entrada. |
| `reason` | string ou `None` | Motivo específico quando `approved=False` (ex: "spread 0.8% acima do limite 0.5%", "profundidade $150 abaixo do minimo $300", "liquidez indisponivel"). |
| `spread_pct` | float | Spread observado no momento da checagem, para log/auditoria mesmo quando aprovado. |
| `depth_usdt` | float | Profundidade observada no lado ask, para log/auditoria mesmo quando aprovado. |

## Resumo de confirmação live (novo, transiente — `trading/runner.py`)

Não persistido — só existe durante a impressão/log do banner na inicialização.

| Campo | Tipo | Regras |
|---|---|---|
| `pairs` | lista de string | Pares ativos configurados. |
| `balance_usdt` | float | Saldo real no momento da inicialização. |
| `max_order_size_usdt` / `max_positions` | float / inteiro | Limites já configurados, exibidos como estão. |
| `daily_limit_pct` / `weekly_limit_pct` / `monthly_limit_pct` / `max_consecutive_losses` | float / float / float / inteiro | Os quatro limites de perda configurados. |
