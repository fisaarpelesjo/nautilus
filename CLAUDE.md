# CLAUDE.md — Crypto Day Trader Bot

## Visão geral

Bot de trading algorítmico para cripto escrito em Python. Opera na Binance via `ccxt`. Suporta modo **paper** (simulado) e **live** (dinheiro real). Estratégia principal: EMA crossover (9/21) com filtro de tendência EMA50 e confirmação RSI.

---

## Estrutura do projeto

```
├── main.py                    # Ponto de entrada: python main.py [backtest|multibacktest|scan|bot|status]
├── bot.py                     # Wrapper de compatibilidade para trading/runner.py
├── config/
│   └── settings.py            # Todas as configs lidas do .env
├── data/
│   ├── fetcher.py             # Busca OHLCV da Binance com cache em memória
│   ├── paths.py               # Caminhos dos arquivos locais
│   ├── trade_store.py         # Trades fechados
│   ├── signal_store.py        # Mudanças de sinal
│   ├── decision_store.py      # Decisões por ciclo/par
│   ├── state_store.py         # Estado atual do bot
│   ├── ohlcv_store.py         # Candles acumulados
│   ├── trade_logger.py        # Compatibilidade com imports antigos
│   └── ohlcv/                 # Candles históricos acumulados (CSV por par/TF)
├── strategy/
│   ├── base.py                # Interface BaseStrategy + dataclasses Signal/TradeSignal
│   ├── diagnostics.py         # Checks e diagnóstico de sinais
│   └── ema_rsi.py             # Estratégia EMA9/21/50 + RSI14
├── trading/
│   ├── runner.py              # Loop principal do bot (poll a cada 60s)
│   ├── decision_logger.py     # Histórico analítico de decisões
│   └── position_lifecycle.py  # Entrada, saída, trailing e MTF
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

## Fluxo Incremental

Para qualquer mudança não trivial neste projeto, separe o trabalho em tópicos pequenos. Ao terminar cada tópico, rode os testes relevantes, faça commit com mensagem Conventional Commit concisa em português, envie para `origin/main` e só então continue para o próximo tópico. Não commite artefatos de runtime.

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
| `STOP_LOSS_PCT` | `0.015` | Stop loss fixo (fallback sem ATR) |
| `TAKE_PROFIT_PCT` | `0.06` | Take profit fixo (fallback sem ATR) |
| `ATR_SL_MULTIPLIER` | `1.5` | Multiplicador ATR para stop loss |
| `ATR_TP_MULTIPLIER` | `3.0` | Multiplicador ATR para take profit |
| `VOLUME_MA_PERIOD` | `20` | Janela da média de volume para filtro |
| `VOLUME_MIN_RATIO` | `1.2` | Volume mínimo = média × ratio para BUY |
| `MTF_TIMEFRAME` | `1d` | Timeframe de confirmação de tendência (multi-timeframe) |
| `COOLDOWN_HOURS` | `4` | Horas de bloqueio de reentrada após stop loss |
| `DAILY_DRAWDOWN_LIMIT` | `0.05` | Limite de perda diária (5% do saldo inicial = $50) |
| `DAILY_REPORT_HOUR` | `0` | Hora (0–23) para enviar relatório diário via Telegram |
| `BB_PERIOD` | `20` | Período das Bollinger Bands |
| `BB_STD` | `2.0` | Desvios padrão das Bollinger Bands |
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
- `atr` — ATR(14), usado pelo risk manager para SL/TP dinâmico
- `volume_ma` — média móvel simples do volume (período `VOLUME_MA_PERIOD`)
- `bb_upper`, `bb_middle`, `bb_lower` — Bollinger Bands(20, 2)

**Regras de entrada/saída:**

| Sinal | Condição |
|---|---|
| BUY | EMA9 cruza acima EMA21 **e** preço > EMA50 **e** RSI < 65 **e** volume > 1.2× média(20) **e** preço > EMA50 no timeframe diário (MTF) **e** preço ≤ BB superior (não sobreextendido) |
| SELL | EMA9 cruza abaixo EMA21 **e** RSI > 35 |
| HOLD | nenhuma das anteriores |

**Stop Loss / Trailing Stop / Take Profit** são gerenciados em `trading/position_lifecycle.py`, não na estratégia. A cada poll, se o preço fizer novo máximo, o stop loss sobe para `máximo - 1.5×ATR`, travando lucros. O TP fixo permanece como alvo máximo.

**Regras de gestão de ciclo (`trading/runner.py`):**
- `MAX_ENTRIES_PER_CYCLE = 1` — máximo de 1 nova posição aberta por ciclo de 60s, evitando entradas correlacionadas simultâneas
- Cooldown ativado após Stop Loss **e** após Sinal de Venda com prejuízo
- `log_signal` só grava quando o sinal muda (HOLD→BUY, BUY→SELL, etc.), não em todo poll

---

## Gestão de risco — risk/manager.py

- Tamanho da ordem: `min(MAX_ORDER_SIZE_USDT, saldo * 0.95)`
- **SL/TP dinâmico via ATR:** `SL = entrada - ATR_SL_MULTIPLIER × ATR14` / `TP = entrada + ATR_TP_MULTIPLIER × ATR14`
- Fallback (se ATR = 0): SL fixo em `STOP_LOSS_PCT` (1.5%), TP fixo em `TAKE_PROFIT_PCT` (6%)
- SL mínimo: nunca abaixo de 50% do preço de entrada
- Risk/reward ratio padrão com ATR: 1:2 (1.5× ATR de risco, 3× ATR de alvo)

---

## Persistência de dados

| Arquivo | Formato | Conteúdo |
|---|---|---|
| `data/decisions.csv` | CSV | Cada ciclo por par: sinal, decisão final, bloqueios, filtros e indicadores |
| `data/signals.csv` | CSV | Mudanças de sinal: timestamp, preço, indicadores, sinal |
| `data/trades.csv` | CSV | Cada trade fechado: entrada, saída, PnL, motivo |
| `data/ohlcv/BTCUSDT_4h.csv` | CSV | Candles históricos acumulados |
| `data/state.json` | JSON | Estado atual: saldo, posição aberta, contadores |
| `logs/YYYY-MM-DD.log` | texto | Log textual completo do dia |
| `logs/events-YYYY-MM-DD.jsonl` | JSONL | Eventos estruturados de ordens, erros e ciclo operacional |

O bot restaura o estado do `state.json` ao reiniciar — posição aberta e saldo paper são preservados.

---

## Cache de candles

`data/fetcher.py` mantém um cache em memória (`_cache` dict). Na primeira chamada busca `CANDLE_LIMIT=100` candles. Nas chamadas seguintes busca apenas os últimos 5 e faz merge, evitando latência repetida (~5s por chamada completa na Binance a partir do Brasil).

---

## Como adicionar uma nova estratégia

1. Criar `strategy/minha_estrategia.py` herdando `BaseStrategy`
2. Implementar `calculate_indicators(df)` e `generate_signal(df) -> TradeSignal`
3. Trocar a instância em `trading/runner.py` e `backtesting/engine.py`

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
