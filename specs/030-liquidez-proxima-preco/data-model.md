# Fase 1 — Modelo de dados: profundidade de liquidez próxima ao preço

Não há entidade nova. Um campo já existente muda de **definição** (o que
mede), não de **forma** (tipo/nome).

## `LiquidityCheck` (já existente, `execution/liquidity.py`)

| Campo | Tipo | Antes | Depois |
|---|---|---|---|
| `approved` | `bool` | — | sem mudança |
| `reason` | `Optional[str]` | — | mensagem de profundidade passa a citar "perto do preço" quando o motivo é `depth_usdt` |
| `spread_pct` | `float` | — | sem mudança |
| `depth_usdt` | `float` | soma de **todos** os níveis do lado ask retornados pelo book (até 20) | soma só dos níveis com `preço ≤ best_ask × (1 + MAX_SPREAD_PCT_ENTRY)` (D1) |
| `best_ask` | `float` | — | sem mudança |

**Invariante nova:** `depth_usdt` (depois) `<= depth_usdt` (antes), para o
mesmo book — o critério novo nunca soma mais do que a soma bruta já somava,
só descarta níveis fora do desvio de preço aceito. É essa propriedade que
torna a mudança estritamente mais conservadora (nunca aprova o que a versão
anterior recusaria) e o motivo pelo qual não há necessidade de um novo
estado/campo: `depth_usdt` continua sendo "quanto está disponível", só que
medido corretamente.

## Sem mudança de contrato de chamada

`check_liquidity(symbol: str, order_size_usdt: float) -> LiquidityCheck` —
mesma assinatura, mesmo `required_depth = max(MIN_ORDERBOOK_DEPTH_USDT, 3 ×
order_size_usdt)` (FR-002). Os consumidores (`trading/position_lifecycle.py`)
não precisam de nenhuma alteração.
