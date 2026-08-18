# 07 — Configuração

[← Sumário](README.md)

Todas as variáveis são lidas de `.env` por `config/settings.py`, que roda `validate_config()` na importação — config fora do intervalo esperado derruba o processo imediatamente com a lista completa de erros. `.env.example` tem o template sem valores reais; `.env` nunca é commitado (`.gitignore`).

Todo default abaixo foi conferido linha a linha contra `config/settings.py` nesta revisão da documentação.

## Credenciais e modo

| Variável | Default | Descrição |
|---|---|---|
| `BINANCE_API_KEY` | — | API key da Binance |
| `BINANCE_API_SECRET` | — | API secret da Binance |
| `TRADING_MODE` | `paper` | `paper` (simulado) ou `live` (dinheiro real) |
| `LIVE_TRADING_CONFIRMATION` | — | Obrigatório para live: deve ser exatamente `I_UNDERSTAND_LIVE_TRADING_RISK` |

> Permissões necessárias na API key da Binance: **Leitura + Trading Spot**. Nunca habilite saque.

## Pares negociados

| Variável | Default | Descrição |
|---|---|---|
| `PAIRS` | `ENSO/USDT,AAVE/USDT,ZEC/USDT,LDO/USDT,TON/USDT` | Lista separada por vírgula; `SYMBOL` = `PAIRS[0]` |
| `BLACKLIST_PAIRS` | — | Pares ou bases bloqueadas mesmo se selecionados dinamicamente |
| `TIMEFRAME` | `4h` | Timeframe dos candles |
| `DYNAMIC_PAIRS_ENABLED` | `false` | Seleciona pares automaticamente ao iniciar, em vez de usar `PAIRS` fixo |
| `DYNAMIC_PAIRS_TOP_N` | `5` | Número de pares dinâmicos a selecionar |
| `DYNAMIC_PAIRS_CANDIDATES` | `20` | Candidatos avaliados na seleção dinâmica |
| `MIN_VOLUME_USDT` | `10000000` | Volume mínimo diário em USDT para entrar como candidato |
| `MIN_PRICE_USDT` | `0.001` | Preço mínimo do ativo para ser candidato |
| `MAX_SPREAD_PCT` | `0.003` | Spread máximo aceitável na **seleção** de pares (distinto de `MAX_SPREAD_PCT_ENTRY`, ver abaixo) |
| `MIN_VOLATILITY_PCT` | `1.0` | Volatilidade diária mínima (%) para ser candidato |

## Estratégia — EMA / RSI

| Variável | Default | Descrição |
|---|---|---|
| `EMA_FAST` | `9` | Período da EMA rápida |
| `EMA_SLOW` | `21` | Período da EMA lenta |
| `EMA_TREND` | `50` | Período da EMA de tendência |
| `RSI_PERIOD` | `14` | Período do RSI |
| `RSI_OVERSOLD` | `35` | RSI mínimo para permitir sinal de venda |
| `RSI_OVERBOUGHT` | `70` | RSI máximo para permitir entrada |
| `VOLUME_MA_PERIOD` | `20` | Janela da média móvel de volume |
| `VOLUME_MIN_RATIO` | `1.0` | Volume mínimo = média × ratio para permitir `BUY` |
| `PULLBACK_ENTRY_ENABLED` | `true` | Ativa entrada por pullback em tendência (além do crossover) |
| `PULLBACK_RSI_MIN` | `45` | RSI mínimo para entrada por pullback |
| `PULLBACK_MAX_DISTANCE_PCT` | `0.01` | Distância máxima entre a mínima do candle e a EMA lenta no pullback (1%) |

## Bollinger Bands e filtros aditivos (desligados por padrão)

| Variável | Default | Descrição |
|---|---|---|
| `BB_PERIOD` | `20` | Período das Bollinger Bands |
| `BB_STD` | `2.0` | Desvios padrão das Bollinger Bands |
| `REGIME_ADX_THRESHOLD` | `20` | ADX mínimo para classificar o regime como `trending` |
| `REGIME_FILTER_ENABLED` | `false` | Suspende novas entradas em regime `sideways`/`indefinido` |
| `HIGH_VOLATILITY_ATR_RATIO` | `0.05` | `ATR14/close` acima do qual o candle é "volatilidade elevada" |
| `HIGH_VOLATILITY_FILTER_ENABLED` | `false` | Bloqueia novas entradas em candles de volatilidade elevada |
| `ADAPTIVE_BOLLINGER_ENABLED` | `false` | Permite entrada acima da banda superior com tendência/volume fortes |
| `MTF_TIMEFRAME` | `1d` | Timeframe de confirmação de tendência (multi-timeframe) |
| `BREAKOUT_WINDOW` | `150` | Janela padrão da `BreakoutStrategy` (Donchian channel) |

Todos os três filtros aditivos (regime, volatilidade, Bollinger adaptativo) só afetam **novas entradas** — nunca bloqueiam a saída de uma posição já aberta. Ver [03 — Estratégia](03-estrategia.md).

## Ordens e execução

| Variável | Default | Descrição |
|---|---|---|
| `MAX_ORDER_SIZE_USDT` | `100.0` | Teto por ordem em USDT |
| `MAX_POSITIONS` | `5` | Máximo de posições abertas simultaneamente |
| `MAX_SPREAD_PCT_ENTRY` | `0.005` | Spread máximo do order book para permitir uma **entrada** |
| `MIN_ORDERBOOK_DEPTH_USDT` | `3 × MAX_ORDER_SIZE_USDT` | Profundidade mínima (lado ask) exigida para permitir entrada |
| `USE_LIMIT_ORDERS` | `false` | Quando `true`, entradas usam ordem limit em vez de mercado |
| `LIMIT_ORDER_TIMEOUT_CYCLES` | `3` | Ciclos até cancelar uma ordem limit não preenchida (ou assumir o parcial) |

## Gestão de risco

| Variável | Default | Descrição |
|---|---|---|
| `STOP_LOSS_PCT` | `0.015` | Stop loss fixo — fallback quando ATR indisponível (1.5%) |
| `TAKE_PROFIT_PCT` | `0.06` | Take profit fixo — fallback quando ATR indisponível (6%) |
| `ATR_SL_MULTIPLIER` | `1.5` | Multiplicador de ATR para stop loss |
| `ATR_TP_MULTIPLIER` | `3.0` | Multiplicador de ATR para take profit |
| `MAX_STOP_LOSS_PCT` | `0.08` | Teto de perda por trade quando o SL vem do ATR (protege pares de alta volatilidade) |

## Proteções operacionais

| Variável | Default | Descrição |
|---|---|---|
| `COOLDOWN_HOURS` | `4` | Horas de bloqueio de reentrada no par após stop loss / venda com prejuízo |
| `ENTRY_COOLDOWN_CYCLES` | `3` | Ciclos de bloqueio de entrada após determinados eventos internos |
| `DAILY_DRAWDOWN_LIMIT` | `0.05` | Limite de perda diária (5% do saldo de referência diário) |
| `WEEKLY_DRAWDOWN_LIMIT` | `0.10` | Limite de perda semanal (deve ser ≥ diário) |
| `MONTHLY_DRAWDOWN_LIMIT` | `0.20` | Limite de perda mensal (deve ser ≥ semanal) |
| `MAX_CONSECUTIVE_LOSSES` | `3` | Perdas seguidas até ativar o circuit breaker |
| `CIRCUIT_BREAKER_COOLDOWN_HOURS` | `4` | Horas até o circuit breaker se autodesativar mesmo sem lucro |
| `MAX_POSITION_CORRELATION` | `0.7` | Correlação de retornos acima da qual uma entrada é bloqueada por já haver posição correlacionada aberta |
| `CORRELATION_LOOKBACK` | `50` | Nº de candles usados no cálculo de correlação entre pares |

## Backtest e paper mode

| Variável | Default | Descrição |
|---|---|---|
| `BACKTEST_FEE_RATE` | `0.001` | Taxa da exchange sobre o valor nocional — usada no backtest **e** em paper mode |
| `BACKTEST_SLIPPAGE_PCT` | `0.0005` | Slippage aplicado ao preço de entrada/saída — usado no backtest **e** em paper mode |
| `EDGE_MIN_TRADES` | `10` | Amostra mínima de trades para o veredito de aprovação (`edge`/`scan`/`optimize`) ser conclusivo |

## Notificações

| Variável | Default | Descrição |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | — | Token do bot Telegram (opcional) |
| `TELEGRAM_CHAT_ID` | — | Chat ID Telegram (opcional) |
| `DAILY_REPORT_HOUR` | `0` | Hora (0–23) para enviar relatório diário via Telegram |

Sem `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` preenchidos, nenhum alerta chega — o bot funciona normalmente, só fica sem notificação fora do terminal/log.

## Validações cruzadas (`validate_config()`)

Algumas regras não são só "maior que zero" — vale saber delas de antemão:

- `EMA_FAST` precisa ser menor que `EMA_SLOW`
- `RSI_OVERSOLD < RSI_OVERBOUGHT`, ambos entre 0 e 100
- `PULLBACK_RSI_MIN < RSI_OVERBOUGHT`
- `WEEKLY_DRAWDOWN_LIMIT >= DAILY_DRAWDOWN_LIMIT`
- `MONTHLY_DRAWDOWN_LIMIT >= WEEKLY_DRAWDOWN_LIMIT`
- Em `TRADING_MODE=live`: `LIVE_TRADING_CONFIRMATION` deve ser exatamente `I_UNDERSTAND_LIVE_TRADING_RISK`, e `BINANCE_API_KEY`/`BINANCE_API_SECRET` são obrigatórios

## Próximo capítulo

[08 — Comandos CLI](08-comandos-cli.md) mostra como cada uma dessas variáveis se reflete no comportamento de cada comando `python main.py`.
