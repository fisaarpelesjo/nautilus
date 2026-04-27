# CLAUDE.md — Crypto Day Trader Bot

## Visão geral

Bot de trading algorítmico para cripto escrito em Python. Opera na Binance via `ccxt`. Suporta modo **paper** (simulado) e **live** (dinheiro real). Estratégia principal: EMA crossover (9/21) com filtro de tendência EMA50 e confirmação RSI.

---

## Estrutura do projeto

```
├── main.py                    # Ponto de entrada: python main.py [backtest|multibacktest|scan|bot|status]
├── bot.py                     # Loop principal do bot (poll a cada 60s)
├── config/
│   └── settings.py            # Todas as configs lidas do .env
├── data/
│   ├── fetcher.py             # Busca OHLCV da Binance com cache em memória
│   ├── trade_logger.py        # Persiste trades, sinais, OHLCV e state em disco
│   └── ohlcv/                 # Candles históricos acumulados (CSV por par/TF)
├── strategy/
│   ├── base.py                # Interface BaseStrategy + dataclasses Signal/TradeSignal
│   └── ema_rsi.py             # Estratégia EMA9/21/50 + RSI14
├── risk/
│   └── manager.py             # Calcula SL, TP, tamanho de posição
├── execution/
│   └── order_manager.py       # Abre/fecha ordens; persiste state; restaura ao reiniciar
├── backtesting/
│   ├── engine.py              # Simula estratégia em dados históricos
│   ├── multi.py               # Backtest em lista fixa de pares
│   └── scanner.py             # Busca top 30 pares por volume e faz backtest
└── utils/
    ├── display.py             # Display Rich: tabela multi-par, formatação de preços
    ├── logger.py              # Logger colorido no terminal + arquivo em logs/
    └── notifier.py            # Alertas via Telegram (opcional)
```

---

## Comandos

```bash
python main.py backtest         # backtest no par principal (PAIRS[0])
python main.py multibacktest    # backtest em lista fixa de pares
python main.py scan             # backtest nos top 30 pares por volume na Binance
python main.py bot              # inicia o bot multi-par
python main.py status           # preço atual e saldo
```

---

## Configuração (.env)

Todas as variáveis de ambiente ficam em `.env` (nunca commitar). O arquivo `.env.example` tem o template sem valores reais.

| Variável | Padrão | Descrição |
|---|---|---|
| `BINANCE_API_KEY` | — | API key da Binance |
| `BINANCE_API_SECRET` | — | Secret da Binance |
| `TRADING_MODE` | `paper` | `paper` ou `live` |
| `PAIRS` | `ENSO/USDT,...` | Lista de pares separados por vírgula; `SYMBOL` = `PAIRS[0]` |
| `TIMEFRAME` | `4h` | Timeframe dos candles |
| `MAX_ORDER_SIZE_USDT` | `100.0` | Teto por ordem em USDT |
| `MAX_POSITIONS` | `5` | Máximo de posições abertas simultaneamente |
| `STOP_LOSS_PCT` | `0.015` | Stop loss (1.5%) |
| `TAKE_PROFIT_PCT` | `0.06` | Take profit (6%) |
| `TELEGRAM_BOT_TOKEN` | — | Token do bot Telegram (opcional) |
| `TELEGRAM_CHAT_ID` | — | Chat ID Telegram (opcional) |

---

## Estratégia — EmaRsiStrategy

**Arquivo:** `strategy/ema_rsi.py`

**Indicadores calculados:**
- `ema_fast` — EMA(9)
- `ema_slow` — EMA(21)
- `ema_trend` — EMA(50), filtro de tendência
- `rsi` — RSI(14)
- `macd` — MACD diff (logado, não usado no sinal ainda)

**Regras de entrada/saída:**

| Sinal | Condição |
|---|---|
| BUY | EMA9 cruza acima EMA21 **e** preço > EMA50 **e** RSI < 65 |
| SELL | EMA9 cruza abaixo EMA21 **e** RSI > 35 |
| HOLD | nenhuma das anteriores |

**Stop Loss / Take Profit** são gerenciados no `bot.py`, não na estratégia. Isso permite trocar a estratégia sem mexer na gestão de risco.

---

## Gestão de risco — risk/manager.py

- Tamanho da ordem: `min(MAX_ORDER_SIZE_USDT, saldo * 0.95)`
- Stop loss: `entry_price * (1 - STOP_LOSS_PCT)` → 1.5% abaixo
- Take profit: `entry_price * (1 + TAKE_PROFIT_PCT)` → 6% acima
- Risk/reward ratio implícito: 1:4

---

## Persistência de dados

| Arquivo | Formato | Conteúdo |
|---|---|---|
| `data/signals.csv` | CSV | Cada checagem: timestamp, preço, indicadores, sinal |
| `data/trades.csv` | CSV | Cada trade fechado: entrada, saída, PnL, motivo |
| `data/ohlcv/BTCUSDT_4h.csv` | CSV | Candles históricos acumulados |
| `data/state.json` | JSON | Estado atual: saldo, posição aberta, contadores |
| `logs/YYYY-MM-DD.log` | texto | Log completo do dia |

O bot restaura o estado do `state.json` ao reiniciar — posição aberta e saldo paper são preservados.

---

## Cache de candles

`data/fetcher.py` mantém um cache em memória (`_cache` dict). Na primeira chamada busca `CANDLE_LIMIT=100` candles. Nas chamadas seguintes busca apenas os últimos 5 e faz merge, evitando latência repetida (~5s por chamada completa na Binance a partir do Brasil).

---

## Como adicionar uma nova estratégia

1. Criar `strategy/minha_estrategia.py` herdando `BaseStrategy`
2. Implementar `calculate_indicators(df)` e `generate_signal(df) -> TradeSignal`
3. Trocar a instância em `bot.py` e `backtesting/engine.py`

---

## Dependências principais

```
ccxt          # conexão com exchanges (Binance, etc.)
pandas        # manipulação de séries temporais
ta            # indicadores técnicos (EMA, RSI, MACD)
python-dotenv # leitura do .env
colorlog      # logs coloridos no terminal
requests      # notificações Telegram
```

---

## Avisos importantes

- **Nunca commitar o `.env`** — está no `.gitignore`
- **Nunca habilitar saque nas API keys da Binance** — permissões necessárias: Leitura + Trading Spot apenas
- Sempre validar no **modo paper por semanas** antes de ir para live
- O bot opera apenas posições **long** (compra). Short não está implementado.
