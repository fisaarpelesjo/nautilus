# CLI Contract: Comportamento Afetado

Fase 1 do `/speckit-plan`. Nenhum comando novo — todas as mudanças são no comportamento de
`python main.py bot` e nas variáveis de `.env`.

## `python main.py bot` em `TRADING_MODE=live`

- **Input**: sem mudança de argumentos.
- **Efeito**: antes do loop principal, exibe um resumo (pares, saldo real, `MAX_ORDER_SIZE_USDT`,
  `MAX_POSITIONS`, limites diário/semanal/mensal/perdas-consecutivas) e grava um evento
  `live_session_started` com os mesmos dados.
- **Output (stdout)**: banner informativo, não interativo — não espera input do operador além do
  `LIVE_TRADING_CONFIRMATION` já exigido em `.env` antes do processo sequer iniciar.
- **Efeito colateral observável**: nenhum além do já existente (mesmo comportamento de execução de
  ordens de hoje, só com mais um evento de log na inicialização).

## `python main.py bot` em `TRADING_MODE=paper`

- Sem mudança de comportamento — o banner de confirmação (acima) é específico de live (FR-002).

## Novas variáveis de `.env`

| Variável | Default | Descrição |
|---|---|---|
| `WEEKLY_DRAWDOWN_LIMIT` | `0.10` | Limite de perda semanal (fração do saldo de referência da semana). |
| `MONTHLY_DRAWDOWN_LIMIT` | `0.20` | Limite de perda mensal (fração do saldo de referência do mês). |
| `MAX_SPREAD_PCT_ENTRY` | `0.005` | Spread máximo aceitável no order book para permitir uma entrada. |
| `MIN_ORDERBOOK_DEPTH_USDT` | `3 * MAX_ORDER_SIZE_USDT` | Profundidade mínima (lado ask) exigida para permitir uma entrada. |
| `USE_LIMIT_ORDERS` | `false` | Quando `true`, entradas usam ordem limit em vez de mercado. Default preserva 100% do comportamento já validado. |
| `LIMIT_ORDER_TIMEOUT_CYCLES` | `3` | Ciclos (de 60s) antes de cancelar uma ordem limit não preenchida (ou assumir o preenchimento parcial já obtido). |

Validação (`config/settings.py` `validate_config()`): `WEEKLY_DRAWDOWN_LIMIT >= DAILY_DRAWDOWN_LIMIT`
e `MONTHLY_DRAWDOWN_LIMIT >= WEEKLY_DRAWDOWN_LIMIT` — erro claro na inicialização se inconsistente,
nunca uma inconsistência silenciosa em runtime.

## `data/decisions.csv` (`blockers`)

Dois motivos novos podem aparecer na coluna `blockers` (já existente, spec 001):
`"limite semanal"` / `"limite mensal"` (US2) e `"liquidez"` (US3) — mesmo formato dos bloqueios já
existentes (`"cooldown"`, `"sem slot"`, etc.), sem mudança de schema do CSV.
