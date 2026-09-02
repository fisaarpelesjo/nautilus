# Fase 1 — Modelo de dados: fonte de dados on-chain

## Série on-chain

Retorno de `fetch_onchain_series(metric, timespan)`.

| Campo | Tipo | Descrição |
|---|---|---|
| índice | `DatetimeIndex` (UTC, granularidade dia) | Data do ponto, crescente, sem duplicatas (FR-002) |
| `value` | `float` | Valor da métrica naquele dia |

Sem outras colunas — ao contrário de OHLCV (open/high/low/close/volume),
uma métrica on-chain é um único valor por dia. Forçar as cinco colunas de
`DataSource` aqui exigiria inventar four campos falsos; é exatamente o
motivo de D4 (research.md) para não reusar aquele protocolo.

**Vazio é um valor válido**: `fetch_onchain_series` pode retornar um
DataFrame vazio quando a métrica existe mas não tem dado no período pedido
(FR-004) — o chamador decide o que fazer (ex.: tratar como amostra
insuficiente), a função não decide por ele.

## Erros

`fetch_onchain_series` levanta exceção (nunca retorna dado inválido) em:

| Causa | Quando |
|---|---|
| Falha de rede / timeout | Requisição não completa em 15s ou erro de conexão |
| HTTP não-200 | Resposta de erro do servidor |
| `status` no corpo ≠ `"ok"` | API reconhece a chamada mas recusa (ex. nome de métrica inválido) |

Não há uma classe de exceção nova — `RuntimeError` com mensagem
específica por causa, mesmo padrão já usado em `execution/liquidity.py`
(`check_liquidity` retorna estado explícito em vez de inventar hierarquia de
exceção nova para um módulo pequeno).
