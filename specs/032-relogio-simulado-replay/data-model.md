# Fase 1 — Modelo de dados: relógio simulado no replay

Nenhuma entidade nova. Um estado de módulo novo e um comportamento
ausente (chamada de timeout) passam a existir.

## `execution/order_manager.py` — estado de módulo novo

| Nome | Tipo | Default | Descrição |
|---|---|---|---|
| `_simulated_now` | `Optional[datetime]` | `None` | Quando `None`, `_now()` é `datetime.now()` real. Setado só por `trading/replay.py` dentro do ambiente isolado. |

## `_now() -> datetime` (nova função módulo)

```python
def _now() -> datetime:
    return _simulated_now if _simulated_now is not None else datetime.now()
```

**Invariante (FR-002, testado):** com `_simulated_now is None` (estado
default, todo o resto do processo), `_now()` retorna exatamente o que
`datetime.now()` retornaria — a diferença de milissegundos entre as duas
chamadas é a única diferença possível, irrelevante para qualquer
comparação de data/cooldown/período existente.

## Pontos de chamada migrados (D2, research.md)

14 ocorrências de `datetime.now()` em `execution/order_manager.py`
passam a `_now()`: `Position.opened_at` (default factory), ativação do
circuit breaker (×2), resets diário/semanal/mensal (×6), snapshot de
estado persistido, timeout do circuit breaker, cooldown (×2), registro de
trade fechado (×2). A chamada em `_generate_client_order_id` (linha 38,
salt de unicidade) permanece `datetime.now()` — fora do escopo declarado
em D2.

## `trading/replay.py` — comportamento novo

| Local | Mudança |
|---|---|
| `_isolated_order_manager_environment()` | `originals` ganha `"_simulated_now": order_manager._simulated_now`, restaurado no `finally` (FR-005) |
| `run_replay()`, início de cada iteração | `order_manager._simulated_now = window.index[-1].to_pydatetime()` (FR-003) — mesmo valor já usado por `as_of` |
| `run_replay()`, dentro do loop | `if manager.circuit_breaker_active: manager.check_circuit_breaker_timeout()` — chamada que hoje não existe (FR-004) |
| `compare_to_backtest()` | Nota de "limitações conhecidas" reescrita (FR-007, D5) |

Nenhuma mudança de assinatura pública — `run_replay(symbol, timeframe,
candle_limit)` continua igual.
