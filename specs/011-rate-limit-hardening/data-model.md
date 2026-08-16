# Data Model: Singleton de Exchange + Retry de Rate Limit

Fase 1 do `/speckit-plan`. Nenhuma persistência nova — só estado em memória do processo.

## Cache de exchange (`data/fetcher.py`, novo)

| Campo | Tipo | Regras |
|---|---|---|
| `_exchange_cache` | `Dict[bool, ccxt.binance]` | Chave = `sandbox` (`True`/`False`); uma instância por chave, criada na primeira chamada de `get_exchange()` para aquele modo. |

Sem contrato de CLI novo — nenhum comando/flag é adicionado; a mudança é interna a
`data/fetcher.py` e `backtesting/scanner.py`.
