# Quickstart: Paridade de Custos entre Paper e Backtest

Fase 1 do `/speckit-plan`. Cenário de validação executável — sem depender de dados reais da
Binance nem tempo real passando.

## Pré-requisitos

- Ambiente Python já configurado (`.venv` do projeto).
- Nenhuma credencial necessária — `TRADING_MODE=paper` não faz chamada autenticada.

## Cenário 1 — Slippage e fee aplicados numa compra/venda paper conhecida

```bash
pytest tests/test_order_manager_safety.py -k "cost_parity or slippage or fee" -v
```

Esperado: testes cobrindo que, para um preço de mercado conhecido (`$100`, por exemplo), o
`Position.entry_price` gravado é `100 * (1 + BACKTEST_SLIPPAGE_PCT)`, o saldo debitado inclui a
taxa sobre o nocional, e o mesmo vale simetricamente na saída — todos passando.

## Cenário 2 — Paridade percentual com o backtest

```bash
pytest tests/test_order_manager_safety.py -k "parity_with_backtest" -v
```

Esperado: para o mesmo par de preços de entrada/saída de mercado e o mesmo
`BACKTEST_FEE_RATE`/`BACKTEST_SLIPPAGE_PCT`, o `pnl_pct` de um trade paper fechado bate (dentro de
tolerância de ponto flutuante) com o `pnl_pct` que `simulate_backtest()` produziria — ver
`research.md` para por que a comparação é percentual, não em dólar absoluto.

## Cenário 3 — Flags desligadas não mudam nada (regressão)

```bash
BACKTEST_FEE_RATE=0 BACKTEST_SLIPPAGE_PCT=0 pytest tests/test_order_manager_safety.py -v
```

Esperado: suíte inteira passa sem diferença de comportamento — confirma FR-008 (nenhuma regressão
para quem zerar as duas variáveis).

## Cenário 4 — Suíte completa

```bash
pytest -q
```

Esperado: todos os testes passam, incluindo os já existentes que hoje assumem custo exato sem
taxa (atualizados como parte desta spec, não contornados — ver `plan.md` Project Structure).
