# CLAUDE.md — Crypto Day Trader Bot

## Visão geral

Bot de trading algorítmico para cripto escrito em Python. Opera na Binance via `ccxt`. Suporta modo **paper** (simulado) e **live** (dinheiro real). Estratégia principal: EMA crossover (12/21) com filtro de tendência EMA50 e confirmação RSI.

---

## Estrutura do projeto

```
├── main.py                    # Ponto de entrada: python main.py [backtest|edge|multibacktest|scan|bot|status]
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
    ├── chart.py               # Gráfico interativo Dash/Plotly (candlestick, EMAs, RSI, posição aberta)
    ├── display.py             # Display Rich: tabela multi-par, formatação de preços
    ├── logger.py              # Logger colorido no terminal + arquivo em logs/
    └── notifier.py            # Alertas via Telegram (opcional)
```

---

## Comandos

```bash
python main.py backtest             # backtest no par principal (PAIRS[0])
python main.py backtest --validate  # backtest com split treino/validação out-of-sample + veredito
python main.py edge                 # relatório de vantagem contra buy-and-hold
python main.py multibacktest        # backtest em lista fixa de pares
python main.py scan                 # backtest nos top 30 pares por volume na Binance
python main.py compare              # compara multiplas estrategias/presets lado a lado
python main.py optimize             # grid search dos melhores parâmetros
python main.py analyze              # resumo do data/trades.csv
python main.py select               # ranqueia candidatos de pares dinâmicos
python main.py chart [PAR] [TF]     # gráfico interativo no browser (Dash/Plotly)
python main.py bot                  # inicia o bot multi-par
python main.py status               # patrimônio (caixa/posições/total), PnL, circuit breaker e kill switch
python main.py kill                 # suspende novas entradas (kill switch manual)
python main.py resume               # retoma novas entradas (kill switch manual)
python main.py painel               # patrimônio, posições, últimas operações/sinais e bloqueios recentes
python main.py debug [PAR]          # explica cada condição de entrada (EMA, RSI, MTF, regime, cooldown...)
python main.py performance          # curva de capital, drawdown e PnL por par (HTML no navegador)
```

---

## Fluxo Incremental

Para qualquer mudança não trivial neste projeto, separe o trabalho em tópicos pequenos. Ao terminar cada tópico, rode os testes relevantes, faça commit com mensagem Conventional Commit concisa em português, envie para `origin/main` e só então continue para o próximo tópico. Não commite artefatos de runtime.

## Padrão de commits

Todo commit requer título e corpo:

- **Título:** `tipo: descrição curta` (máx 72 chars) — ex: `feat: adicionar filtro de volatilidade`
- **Corpo:** uma ou mais linhas explicando *o que mudou e por quê* — listar mudanças principais, decisões e contexto relevante para leitura futura

Tipos: `feat:` nova funcionalidade, `fix:` correção, `docs:` documentação, `refactor:` reestruturação sem mudança de comportamento, `test:` testes, `chore:` tooling/config.

Exemplo:
```
feat: adicionar regime detection via ADX

Calcula ADX(14) em strategy/ema_rsi.py. ADX > 25 = trending (mantém
crossover), ADX < 20 = sideways (suspende entradas). Regime registrado
em data/decisions.csv para análise posterior.
```

## Sincronização CLAUDE.md ↔ AGENTS.md

`CLAUDE.md` (PT) e `AGENTS.md` (EN) devem ter sempre o mesmo conteúdo. Ao modificar qualquer seção em um arquivo, atualize o equivalente no outro no mesmo commit.

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
| `MAX_SPREAD_PCT_ENTRY` | `0.005` | Spread máximo do order book para permitir uma entrada (distinto de `MAX_SPREAD_PCT`, usado na seleção dinâmica de pares) |
| `MIN_ORDERBOOK_DEPTH_USDT` | `3 × MAX_ORDER_SIZE_USDT` | Profundidade mínima (lado ask) exigida para permitir uma entrada |
| `USE_LIMIT_ORDERS` | `false` | Quando `true`, entradas usam ordem limit em vez de mercado |
| `LIMIT_ORDER_TIMEOUT_CYCLES` | `3` | Ciclos (60s cada) antes de cancelar uma ordem limit não preenchida (ou assumir o preenchimento parcial já obtido) |
| `STOP_LOSS_PCT` | `0.015` | Stop loss fixo (fallback sem ATR) |
| `TAKE_PROFIT_PCT` | `0.06` | Take profit fixo (fallback sem ATR) |
| `ATR_SL_MULTIPLIER` | `1.5` | Multiplicador ATR para stop loss |
| `ATR_TP_MULTIPLIER` | `3.0` | Multiplicador ATR para take profit |
| `VOLUME_MA_PERIOD` | `20` | Janela da média de volume para filtro |
| `VOLUME_MIN_RATIO` | `1.2` | Volume mínimo = média × ratio para BUY |
| `MTF_TIMEFRAME` | `1d` | Timeframe de confirmação de tendência (multi-timeframe) |
| `COOLDOWN_HOURS` | `4` | Horas de bloqueio de reentrada após stop loss |
| `DAILY_DRAWDOWN_LIMIT` | `0.05` | Limite de perda diária (5% do saldo de referência diário) |
| `WEEKLY_DRAWDOWN_LIMIT` | `0.10` | Limite de perda semanal (10% do saldo de referência semanal); deve ser ≥ `DAILY_DRAWDOWN_LIMIT` |
| `MONTHLY_DRAWDOWN_LIMIT` | `0.20` | Limite de perda mensal (20% do saldo de referência mensal); deve ser ≥ `WEEKLY_DRAWDOWN_LIMIT` |
| `MAX_CONSECUTIVE_LOSSES` | `3` | Perdas seguidas (`pnl < 0`) até ativar o circuit breaker; reseta em trade com `pnl > 0` |
| `DAILY_REPORT_HOUR` | `0` | Hora (0–23) para enviar relatório diário via Telegram |
| `BB_PERIOD` | `20` | Período das Bollinger Bands |
| `BB_STD` | `2.0` | Desvios padrão das Bollinger Bands |
| `REGIME_ADX_THRESHOLD` | `20` | ADX mínimo para classificar o regime de mercado como `trending` |
| `REGIME_FILTER_ENABLED` | `false` | Quando `true`, suspende novas entradas em regime `sideways`/`indefinido` |
| `HIGH_VOLATILITY_ATR_RATIO` | `0.05` | `ATR_ratio` (ATR14/close) acima do qual o candle é considerado volatilidade elevada |
| `HIGH_VOLATILITY_FILTER_ENABLED` | `false` | Quando `true`, bloqueia novas entradas em candles de volatilidade elevada |
| `ADAPTIVE_BOLLINGER_ENABLED` | `false` | Quando `true`, permite entrada acima da banda superior com tendência/volume fortes |
| `BREAKOUT_WINDOW` | `150` | Janela padrão (períodos) de `strategy/breakout.py` |
| `TELEGRAM_BOT_TOKEN` | — | Token do bot Telegram (opcional) |
| `TELEGRAM_CHAT_ID` | — | Chat ID Telegram (opcional) |

---

## Estratégia — EmaRsiStrategy

**Arquivo:** `strategy/ema_rsi.py`

**Indicadores calculados:**
- `ema_fast` — EMA(12)
- `ema_slow` — EMA(21)
- `ema_trend` — EMA(50), filtro de tendência
- `rsi` — RSI(14)
- `macd` — MACD diff (logado, não usado no sinal ainda)
- `atr` — ATR(14), usado pelo risk manager para SL/TP dinâmico
- `atr_ratio` — ATR14 / close, indicador de volatilidade relativa
- `adx` — ADX(14), base do regime de mercado
- `regime` — `trending`/`sideways`/`indefinido`, derivado de `adx` vs `REGIME_ADX_THRESHOLD`
- `volume_ma` — média móvel simples do volume (período `VOLUME_MA_PERIOD`)
- `bb_upper`, `bb_middle`, `bb_lower` — Bollinger Bands(20, 2)

**Regras de entrada/saída:**

| Sinal | Condição |
|---|---|
| BUY | EMA12 cruza acima EMA21 **e** preço > EMA50 **e** RSI < 60 **e** volume > 1.2× média(20) **e** preço > EMA50 no timeframe diário (MTF) **e** preço ≤ BB superior (não sobreextendido, ou `ADAPTIVE_BOLLINGER_ENABLED` com tendência/volume fortes) |
| SELL | EMA12 cruza abaixo EMA21 **e** RSI > 35 |
| HOLD | nenhuma das anteriores, **ou** bloqueado por `REGIME_FILTER_ENABLED`/`HIGH_VOLATILITY_FILTER_ENABLED` (só para novas entradas — sinal de venda de uma posição já aberta nunca é bloqueado por esses filtros) |

**Filtros opcionais** (todos desligados por padrão, aditivos — ver `specs/006-evolucao-estrategia-novas/`): regime de mercado via ADX (`REGIME_FILTER_ENABLED`), volatilidade elevada via `ATR_ratio` (`HIGH_VOLATILITY_FILTER_ENABLED`) e filtro Bollinger adaptativo (`ADAPTIVE_BOLLINGER_ENABLED`). Aplicados tanto no caminho por candle (`generate_signal`) quanto no vetorizado (`precompute_signals`, usado por `optimize`/`backtest --validate`/`optimize --walk-forward`) — os dois caminhos precisam ficar sincronizados sempre que um filtro novo for adicionado.

**Stop Loss / Trailing Stop / Take Profit** são gerenciados em `trading/position_lifecycle.py`, não na estratégia. A cada poll, se o preço fizer novo máximo, o stop loss sobe para `máximo - 1.5×ATR`, travando lucros. O TP fixo permanece como alvo máximo.

**Estratégia de rompimento** (`strategy/breakout.py`, `BreakoutStrategy`): Donchian channel — compra quando o preço rompe a máxima das últimas `BREAKOUT_WINDOW` velas (padrão `150`, testável em 50/150/200), vende quando rompe a mínima. Roda pela mesma infraestrutura de backtest via `run_backtest(..., strategy=BreakoutStrategy(window=N))`.

**Comparativo de estratégias/presets**: `python main.py compare` (alias `comparar`) roda múltiplas estratégias/presets nos mesmos pares/timeframe numa única execução, reusando `evaluate_approval`/`edge_score` já estabelecidos — sem critério de comparação novo.

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

## Proteções operacionais — reconciliação, circuit breaker e kill switch

- **Reconciliação** (`execution/reconciliation.py`): em `TRADING_MODE=live`, compara `state.json`
  com o saldo real via `fetch_balance()` na inicialização e a cada ~30min
  (`RECONCILIATION_INTERVAL_CYCLES=30` ciclos). Divergência gera evento
  `reconciliation_mismatch`/`reconciliation_error` (JSONL) e alerta Telegram — nunca corrige
  automaticamente. Resultado visível em `python main.py status`. No-op em `paper` (sem conta real
  para comparar).
- **Circuit breaker** (`execution/order_manager.py`): contador global `consecutive_losses` de trades
  fechados com `pnl < 0`, reseta só em `pnl > 0`. Ao atingir `MAX_CONSECUTIVE_LOSSES`,
  `circuit_breaker_active=true` bloqueia novas entradas (posições abertas continuam geridas
  normalmente). Independente e cumulativo com `DAILY_DRAWDOWN_LIMIT`.
- **Kill switch** (`data/killswitch_store.py`): flag manual em `data/killswitch.json` — arquivo
  próprio, não em `state.json`, para que uma escrita normal do bot em execução não sobrescreva uma
  ativação externa via `python main.py kill`. Ativa/desativa via `kill`/`resume`; o bot lê o arquivo
  do disco uma vez por ciclo.
- **Confirmação de sessão live** (`trading/runner.py`): antes do loop principal, em
  `TRADING_MODE=live`, exibe um resumo (pares, saldo real, `MAX_ORDER_SIZE_USDT`, `MAX_POSITIONS`,
  limites diário/semanal/mensal/perdas-consecutivas) e grava o evento `live_session_started`. Não
  bloqueia a inicialização esperando confirmação interativa — só informativo, além do
  `LIVE_TRADING_CONFIRMATION` já exigido. Não aparece em `paper`.
- **Limites de perda semanal e mensal** (`execution/order_manager.py`): mesmo padrão do diário, cada
  um com seu próprio saldo de referência real (`daily_reference_balance`/`weekly_reference_balance`/
  `monthly_reference_balance`, capturado a cada reset de período via `_reference_balance()`) e reset
  independente (dia calendário / semana ISO / mês calendário). `WEEKLY_DRAWDOWN_LIMIT` deve ser
  ≥ `DAILY_DRAWDOWN_LIMIT`; `MONTHLY_DRAWDOWN_LIMIT` deve ser ≥ `WEEKLY_DRAWDOWN_LIMIT` (validado em
  `validate_config()`). Saldo de referência desconhecido bloqueia conservador em vez de usar um
  limite de $0.
- **Checagem de liquidez** (`execution/liquidity.py`): antes de cada entrada, `check_liquidity`
  consulta o order book real e bloqueia com motivo específico (`"liquidez: ..."`) quando o spread
  excede `MAX_SPREAD_PCT_ENTRY` ou a profundidade do lado ask fica abaixo de
  `MIN_ORDERBOOK_DEPTH_USDT`. Falha ao buscar o order book também bloqueia (`"liquidez
  indisponivel"`) — nunca aprovação por omissão.
- **Ordens limit com preenchimento parcial** (`execution/order_manager.py`): opcional via
  `USE_LIMIT_ORDERS` (default `false`, preserva o comportamento a mercado). Quando ligado, a entrada
  usa o melhor preço de venda do order book (já obtido pela checagem de liquidez) como preço limite;
  a ordem fica em `pending_limit_orders` até `check_pending_limit_orders()` (chamado uma vez por
  ciclo) confirmar o preenchimento — total abre a posição, parcial após `LIMIT_ORDER_TIMEOUT_CYCLES`
  cancela o restante e abre só com a quantidade preenchida, zero após o timeout cancela e descarta.

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

## Observabilidade operacional

- **Patrimônio operacional** (`trading/portfolio.py` `compute_portfolio_snapshot()`): calcula caixa
  livre, valor em posições (ao preço atual), patrimônio total, PnL realizado, PnL não realizado e
  PnL total — reusado por `status` e `painel`. Preço indisponível para uma posição propaga `None`
  em todos os campos agregados (nunca `0.0` silencioso).
- **`python main.py painel`** (`trading/panel.py`): agrega patrimônio, posições abertas, últimas
  operações (`data/trades.csv`), últimos sinais (`data/signals.csv`) e bloqueios recentes
  (`analyze_decisions()`, já existente). Histórico ausente/vazio vira estado explícito em cada
  seção, nunca erro.
- **`python main.py debug <PAR>`** (`strategy/diagnostics.py` `full_diagnosis()`): estende
  `signal_checks()` já existente com MTF, regime, volatilidade e cooldown — mostra o valor de cada
  condição de entrada para diagnosticar por que um par está em `BUY`/`SELL`/`HOLD`.
- **`python main.py performance`/`desempenho`** (`backtesting/performance_charts.py`): curva de
  capital, drawdown e PnL por par a partir de `data/trades.csv`, HTML combinado aberto no
  navegador. `python main.py chart` ganha uma camada de marcadores de trades reais (distinta dos
  marcadores teóricos de sinal já existentes).

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
plotly        # gráficos interativos
dash          # servidor web local para o chart interativo
```

---

## Avisos importantes

- **Nunca commitar o `.env`** — está no `.gitignore`
- **Nunca habilitar saque nas API keys da Binance** — permissões necessárias: Leitura + Trading Spot apenas
- Sempre validar no **modo paper por semanas** antes de ir para live
- O bot opera apenas posições **long** (compra). Short não está implementado.
