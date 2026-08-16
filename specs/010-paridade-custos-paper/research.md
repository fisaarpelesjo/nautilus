# Research: Paridade de Custos entre Paper e Backtest

Fase 0 do `/speckit-plan`. Uma decisão técnica principal: como aplicar slippage/fee em
`_paper_buy()`/`_paper_sell()` sem alterar `risk/manager.py` (fora de escopo desta spec).

## Mecânica de aplicação de slippage/fee em `_paper_buy()`/`_paper_sell()`

- **Decision**: `risk.quantity` (já calculado por `risk/manager.py` `calculate_risk()` sobre o
  preço de mercado bruto) permanece intocado. `_paper_buy()` calcula
  `entry_price_paper = risk.entry_price * (1 + BACKTEST_SLIPPAGE_PCT)`, usa esse preço para o
  `Position.entry_price` armazenado, calcula `notional = risk.quantity * entry_price_paper`,
  `fee = notional * BACKTEST_FEE_RATE`, e debita `notional + fee` do `paper_balance_usdt`.
  `_paper_sell()` espelha isso na saída: `exit_price_paper = exit_price_mercado * (1 -
  BACKTEST_SLIPPAGE_PCT)`, `gross_exit = quantity * exit_price_paper`,
  `exit_fee = gross_exit * BACKTEST_FEE_RATE`, credita `gross_exit - exit_fee` ao saldo, e o PnL
  gravado em `data/trades.csv` é `(gross_exit - exit_fee) - (notional_entrada + fee_entrada)`.
- **Rationale**: `backtesting/engine.py` (`_close_trade`, linha ~474) usa uma convenção diferente
  na entrada — fixa o **valor nocional em dólar** (`order_size`) e deixa a quantidade encolher
  (`quantity = order_size / entry_price_com_slippage`) — porque no backtest o tamanho da ordem é
  decidido no mesmo passo que o preço de entrada. No caminho de produção (paper e live), a
  quantidade já vem pronta de `risk/manager.py` antes de `_paper_buy()` ser chamado — refazer esse
  cálculo dentro de `order_manager.py` duplicaria a lógica de sizing (`MAX_ORDER_SIZE_USDT`,
  `capital * 0.95`) que já vive em `risk/manager.py`, e essa spec está deliberadamente restrita a
  `execution/order_manager.py` (ver `plan.md` Project Structure). Fixar a quantidade e deixar o
  valor nocional variar ligeiramente com o slippage é economicamente equivalente (mesma direção de
  custo: fica mais caro comprar, menos favorável vender) e não exige tocar `risk/manager.py`.
- **Consequência para SC-001** ("PnL líquido bate com o que `simulate_backtest()` produziria"): a
  paridade é verificada em **percentual** (`pnl_pct`), não em valor absoluto de dólar — as duas
  convenções de sizing (nocional fixo vs. quantidade fixa) produzem o mesmo `pnl_pct` para o mesmo
  par de preços de mercado e mesmos `fee_rate`/`slippage_pct`, porque fee e slippage são
  proporcionais (multiplicativos), não um valor fixo em dólar. O teste de paridade (T00X) compara
  `pnl_pct`, não `pnl` absoluto.
- **Alternatives considered**: (1) Refazer o sizing dentro de `_paper_buy()` para espelhar
  `order_size = min(MAX_ORDER_SIZE_USDT, saldo * 0.95)` exatamente como o backtest — rejeitado,
  duplicaria uma decisão de sizing que já existe em `risk/manager.py` e criaria uma segunda fonte
  de verdade sobre "quanto comprar" que pode divergir silenciosamente se uma spec futura mudar o
  sizing só num lugar. (2) Aplicar fee/slippage só na saída, não na entrada — rejeitado, o
  backtest sempre aplicou nos dois lados; aplicar só num lado reintroduziria metade do viés
  identificado na auditoria.

## Checagem de saldo suficiente (FR-007)

- **Decision**: a checagem de saldo em `_paper_buy()` (hoje `if cost > self.paper_balance_usdt`)
  passa a comparar contra `notional + fee` (o custo total), não só `notional`.
- **Rationale**: sem isso, uma compra poderia ser aprovada com saldo suficiente só para o nocional
  e faltar para a taxa, deixando `paper_balance_usdt` negativo — um estado que não existe hoje
  (porque hoje não há taxa) e que a spec não deve introduzir.
