# Crypto Day Trader Bot

Bot de trading algorítmico para cripto em Python. Conecta na Binance via API, calcula indicadores técnicos e opera automaticamente com gestão de risco embutida.

---

## Funcionalidades

- Estratégia EMA crossover (9/21) com filtro de tendência EMA50 + RSI
- Stop Loss e Take Profit automáticos
- Modo **paper trading** (simulado) e **live trading**
- Backtest em dados históricos
- Persistência completa: trades, sinais, candles e estado salvos em disco
- Recuperação automática de posição após restart
- Alertas opcionais via Telegram
- Relatório diário automático via Telegram (PnL, trades, win rate, saldo)

---

## Instalação

```bash
# 1. Clonar o repositório
git clone <repo-url>
cd crypto-trader

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar credenciais
cp .env.example .env
# edite o .env com suas API keys da Binance
```

---

## Configuração do .env

```env
BINANCE_API_KEY=sua_api_key
BINANCE_API_SECRET=seu_api_secret

TRADING_MODE=paper        # paper (simulado) ou live (real)
LIVE_TRADING_CONFIRMATION= # obrigatório para live: I_UNDERSTAND_LIVE_TRADING_RISK
PAIRS=BTC/USDT,ETH/USDT,SOL/USDT   # lista de pares; primeiro é usado no backtest simples
TIMEFRAME=4h
DYNAMIC_PAIRS_ENABLED=false # true para selecionar pares automaticamente ao iniciar o bot
DYNAMIC_PAIRS_TOP_N=5
DYNAMIC_PAIRS_CANDIDATES=20
MIN_VOLUME_USDT=10000000
MAX_SPREAD_PCT=0.003
MIN_VOLATILITY_PCT=1.0

MAX_ORDER_SIZE_USDT=100.0
MAX_POSITIONS=5           # máximo de posições abertas simultaneamente
STOP_LOSS_PCT=0.015       # fallback se ATR indisponível
TAKE_PROFIT_PCT=0.06      # fallback se ATR indisponível
ATR_SL_MULTIPLIER=1.5     # SL = entrada - 1.5 × ATR14
ATR_TP_MULTIPLIER=3.0     # TP = entrada + 3.0 × ATR14
VOLUME_MA_PERIOD=20       # janela da média de volume
VOLUME_MIN_RATIO=1.2      # volume mínimo para BUY = média × 1.2
MTF_TIMEFRAME=1d          # timeframe de confirmação de tendência
COOLDOWN_HOURS=4          # horas bloqueado após stop loss no par
DAILY_DRAWDOWN_LIMIT=0.05 # para de abrir posições se perder 5% no dia
DAILY_REPORT_HOUR=0       # hora (0–23) para envio do relatório diário via Telegram

# Opcional — alertas Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

> **Permissões necessárias na Binance:** Leitura + Trading Spot. **Nunca habilite saques.**

---

## Uso

```bash
# Backtest no par principal (PAIRS[0])
python main.py backtest

# Backtest em lista fixa de pares
python main.py multibacktest

# Backtest nos top 30 pares por volume na Binance
python main.py scan

# Analisar trades salvos em data/trades.csv
python main.py analisar

# Otimizar parametros da estrategia no par principal
python main.py otimizar

# Selecionar pares dinamicamente por liquidez, spread, volatilidade, tendencia e backtest
python main.py selecionar

# Iniciar o bot multi-par
python main.py bot

# Ver preço atual e saldo
python main.py status
```

---

## Estratégia

**EMA Crossover + RSI com filtro de tendência**

| Sinal | Condição |
|---|---|
| **COMPRA** | EMA9 cruza acima EMA21 + preço > EMA50 + RSI < 65 + volume > 1.2× média(20) + preço > EMA50 no diário + preço ≤ Banda Superior BB(20,2) |
| **VENDA** | EMA9 cruza abaixo EMA21 + RSI > 35 |
| **Stop Loss** | `entrada - 1.5 × ATR14` (inicial) |
| **Trailing Stop** | sobe para `máximo - 1.5 × ATR14` a cada novo topo |
| **Take Profit** | `entrada + 3.0 × ATR14` (alvo máximo) |

Risk/reward ratio: **1:2** (adaptado à volatilidade de cada par via ATR14)

---

## Dados coletados

Tudo salvo automaticamente em disco enquanto o bot roda:

| Arquivo | Conteúdo |
|---|---|
| `data/signals.csv` | Cada checagem: preço, EMA9/21/50, RSI, MACD, sinal |
| `data/trades.csv` | Cada trade: entrada, saída, PnL, motivo |
| `data/ohlcv/BTCUSDT_4h.csv` | Candles históricos acumulados |
| `data/state.json` | Estado atual (saldo, posição aberta) |
| `logs/YYYY-MM-DD.log` | Log completo do dia |

O bot **restaura o estado automaticamente** ao reiniciar.

---

## Estrutura do projeto

```
├── main.py                 # Ponto de entrada
├── bot.py                  # Loop principal do bot
├── config/settings.py      # Configurações via .env
├── data/
│   ├── fetcher.py          # Busca candles com cache
│   ├── trade_logger.py     # Persistência em disco
│   └── ohlcv/              # Candles históricos
├── strategy/
│   ├── base.py             # Interface de estratégia
│   └── ema_rsi.py          # EMA9/21/50 + RSI14
├── risk/manager.py         # Cálculo de SL/TP/posição
├── execution/
│   └── order_manager.py    # Ordens paper e live
├── backtesting/
│   ├── engine.py           # Motor de backtest
│   ├── multi.py            # Backtest em múltiplos pares
│   └── scanner.py          # Scan top 30 pares por volume
└── utils/
    ├── display.py          # Tabela multi-par e formatação Rich
    ├── logger.py           # Logs coloridos + arquivo
    └── notifier.py         # Alertas Telegram
```

---

## Resultado do backtest (BTC/USDT 4h)

| Métrica | Valor |
|---|---|
| Período | ~400 dias |
| Total de trades | 13 |
| Win rate | 53.8% |
| Retorno | +1.46% |
| Max drawdown | 0% |

> Backtest inclui período de queda do BTC em março/abril 2026. Resultados passados não garantem resultados futuros.

---

## Rodar em servidor (produção)

```bash
# Manter o bot rodando após fechar o terminal
nohup python main.py bot > /dev/null 2>&1 &

# Ver se está rodando
ps aux | grep main.py

# Parar
kill <PID>
```

Para produção, recomenda-se uma VPS (Oracle Cloud gratuito, DigitalOcean ~$4/mês).

---

## Aviso de risco

> Trading algorítmico envolve risco de perda de capital. Use `TRADING_MODE=paper` para validar a estratégia antes de operar com dinheiro real. Nunca invista mais do que pode perder.
