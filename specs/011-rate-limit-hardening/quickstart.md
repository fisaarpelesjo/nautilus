# Quickstart: Singleton de Exchange + Retry de Rate Limit

Fase 1 do `/speckit-plan`. Sem dependência de dados reais da Binance nem tempo real passando.

## Cenário 1 — Singleton

```bash
pytest tests/test_fetcher.py -k "singleton or same_instance" -v
```

Esperado: múltiplas chamadas a `get_exchange()` retornam a mesma instância; `sandbox=True` e
`sandbox=False` recebem instâncias diferentes; `reset_exchange_cache()` força uma instância nova.

## Cenário 2 — Retry de rate limit

```bash
pytest tests/test_fetcher.py -k "retry or rate_limit" -v
```

Esperado: uma falha isolada de `RateLimitExceeded`/`DDoSProtection` seguida de sucesso não propaga
erro; falhas persistentes até o limite de tentativas propagam; erros que não são de rate limit não
disparam retry.

## Cenário 3 — `backtesting/scanner.py` reusa `get_exchange()`

```bash
pytest tests/test_scanner.py -v
```

Esperado: suíte já existente continua passando (os testes mockam `get_top_pairs`/`_get_volume`
inteiros, não exercitam a instanciação da exchange diretamente).

## Cenário 4 — Suíte completa

```bash
pytest -q
```

Esperado: todos os testes passam, sem regressão.
