# Quickstart — validar a spec 035 (H18)

## Pré-requisitos

- Ambiente configurado (`pip install -r requirements.txt`).
- Acesso de rede à Binance (candles).

## 1. Rodar a suite (sem rede, mockada)

```bash
pytest tests/test_grid.py -v
```

Cobre: preenchimento de compra quando o low cruza um nível; preenchimento
de venda quando o high cruza o próximo nível acima; vendas processadas
antes de compras no mesmo candle (D3); liquidação forçada de todos os
níveis ocupados ao `close` quando o regime vira `"trending"` (D4), com
`exit_reason` distinguível; grade não abre em regime `"indefinido"`;
`BacktestResult` produzido passa por `evaluate_approval()` sem erro.

## 2. Rodar a avaliação real

```bash
python main.py grid
```

Espera-se, para cada par de `UNIVERSO_H11`:

- Número de episódios de grade (aberturas/fechamentos por regime).
- Número de trades (`"grid"` + `"regime mudou para trending"`).
- `total_return_pct`, `buy_hold_return_pct`, `max_drawdown_pct`,
  `profit_factor` — mesmos campos que qualquer outro resultado deste
  projeto.
- Veredito (`evaluate_approval`): aprovado/reprovado/inconclusivo.

## 3. Confirmar que o custo está sendo aplicado (US3)

Comparar (manualmente, passando `fee_rate=0`/`slippage_pct=0` a
`simular_grade`) o retorno com e sem custo sobre o mesmo par — a
diferença MUST crescer com o número de trades, não ser uma constante.

## 4. Rodar a suite completa

```bash
pytest -q
```

Nenhuma regressão — `backtesting/engine.py`, `backtesting/approval.py`,
`strategy/ema_rsi.py` não são alterados.

## O que este quickstart não valida

Não decide se H18 deveria mudar a operação do bot — o bot só opera a
estratégia de regras (`strategy/ema_rsi.py`), nunca grid trading, aprovado
ou não. O quickstart valida a medição.
