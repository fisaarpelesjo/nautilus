# CLI Contract: Comportamento Afetado

Fase 1 do `/speckit-plan`. Um comando novo (`compare`/`comparar`); demais mudanças são novas
variáveis de `.env` e novos campos calculados, todos aditivos.

## `python main.py compare` (novo, alias `comparar`)

- **Input**: sem argumentos nesta primeira versão (lista de estratégias/presets fixa no código,
  mesmo padrão de `PAIRS` em `backtesting/multi.py`).
- **Efeito**: roda `run_backtest(pair, timeframe, strategy=...)` para cada combinação
  estratégia×par configurada, reusando `evaluate_approval`/`edge_score`.
- **Output (stdout)**: tabela Rich com uma linha por estratégia/preset×par, incluindo veredito de
  aprovação — mesmo formato visual de `multibacktest`/`scan`.

## `python main.py backtest` / `multibacktest` / `scan`

- Sem mudança de comportamento — `run_backtest()` ganha um parâmetro `strategy` opcional (default
  `EmaRsiStrategy()`), 100% retrocompatível com as chamadas já existentes.

## Novas variáveis de `.env`

| Variável | Default | Descrição |
|---|---|---|
| `REGIME_ADX_THRESHOLD` | `20` | ADX mínimo para classificar o regime como `trending`. |
| `REGIME_FILTER_ENABLED` | `false` | Quando `true`, bloqueia novas entradas em regime `sideways`/`indefinido`. |
| `HIGH_VOLATILITY_ATR_RATIO` | `0.05` | `ATR_ratio` acima do qual o candle é considerado volatilidade elevada. |
| `HIGH_VOLATILITY_FILTER_ENABLED` | `false` | Quando `true`, bloqueia entradas em candles de volatilidade elevada. |
| `ADAPTIVE_BOLLINGER_ENABLED` | `false` | Quando `true`, permite entrada acima da banda superior com tendência/volume fortes. |
| `BREAKOUT_WINDOW` | `150` | Janela padrão (períodos) de `strategy/breakout.py` quando instanciada sem parâmetro explícito. |

Validação (`config/settings.py` `validate_config()`): `REGIME_ADX_THRESHOLD > 0`,
`0 < HIGH_VOLATILITY_ATR_RATIO <= 1`, `BREAKOUT_WINDOW >= 10` (janela mínima para o indicador fazer
sentido estatístico).

## `data/decisions.csv` (nova coluna)

`regime` (`"trending"`/`"sideways"`/`"indefinido"`) — mesmo formato de coluna já existente
(`blockers`), sem mudança de schema além da coluna adicional.
