# Data Model: Paridade de Custos entre Paper e Backtest

Fase 1 do `/speckit-plan`. Nenhuma entidade nova — muda o **valor** calculado em campos já
existentes, não a estrutura.

## `Position` (`execution/order_manager.py`, já existente)

| Campo | Mudança |
|---|---|
| `entry_price` | Passa a armazenar o preço já ajustado por slippage (`market_price * (1 + BACKTEST_SLIPPAGE_PCT)`) em vez do preço de mercado bruto, em `TRADING_MODE=paper`. Em `live`, continua vindo da execução real, sem mudança. |

## `Trade` (`data/trade_store.py` / linha gravada em `data/trades.csv`, já existente)

| Campo | Mudança |
|---|---|
| `pnl_usdt` | Passa a refletir PnL líquido (nocional de saída menos taxa de saída, menos nocional de entrada mais taxa de entrada) em vez do PnL bruto de diferença de preço, em `TRADING_MODE=paper`. |

Sem contrato de CLI novo — nenhum comando/flag é adicionado ou muda de assinatura; a mudança é
inteiramente interna ao caminho `TRADING_MODE=paper` de `execution/order_manager.py`.
