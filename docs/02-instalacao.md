# 02 — Instalação

[← Sumário](README.md)

## Pré-requisitos

- Python 3.11+
- Conta na Binance com API key (permissões **Leitura + Trading Spot** apenas — nunca habilite saque)
- Opcional: bot do Telegram, se quiser alertas (ver [seção Telegram](#telegram-opcional))

## Setup

```bash
# 1. Clonar
git clone https://github.com/fisaarpelesjo/nautilus.git
cd nautilus

# 2. Criar ambiente virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar credenciais
cp .env.example .env
# edite .env com suas API keys da Binance e os pares desejados
```

`config/settings.py` roda `validate_config()` na importação — se alguma variável do `.env` estiver fora do intervalo esperado (ex: `MAX_POSITIONS=0`, `DAILY_DRAWDOWN_LIMIT` fora de `0–1`), o processo falha imediatamente com a lista de erros, em vez de rodar com uma config inconsistente.

## Primeira execução (paper mode)

O padrão do `.env.example` já é `TRADING_MODE=paper` — nenhuma ordem real é enviada.

```bash
# Ver se a config e a conexão com a Binance estão OK
python main.py status

# Rodar um backtest rápido no par principal (PAIRS[0])
python main.py backtest

# Iniciar o bot (loop de 60s, multi-par)
python main.py bot
```

Na primeira chamada, `data/fetcher.py` busca `CANDLE_LIMIT=1000` candles por par — pode levar alguns segundos por par dependendo da latência até a Binance. Chamadas seguintes buscam só os candles novos e fazem merge com o cache em memória.

## Telegram (opcional)

Alertas (circuit breaker, ordens, erros) e relatório diário só funcionam se `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` estiverem preenchidos no `.env`. Sem eles, o bot funciona normalmente — só não notifica nada fora do terminal/log.

1. Fale com [@BotFather](https://t.me/BotFather) no Telegram, crie um bot, copie o token.
2. Envie uma mensagem qualquer pro bot recém-criado, depois acesse `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates` pra descobrir seu `chat_id`.
3. Preencha `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` no `.env`.

## Ambiente de desenvolvimento

```bash
# dependências extras (ruff, mypy, pytest, pre-commit)
pip install -r requirements-dev.txt

# hooks de lint/type-check/teste antes de cada commit
pre-commit install

# rodar manualmente
ruff check .
mypy risk/manager.py execution/order_manager.py
pytest
```

O repositório usa hooks locais (`.pre-commit-config.yaml`) que rodam `ruff`, `mypy` (restrito a `risk/manager.py` e `execution/order_manager.py`) e a suíte `pytest` inteira antes de cada commit — um commit só é aceito se os três passarem.

> Nota Windows: os hooks são `language: system`, ou seja, usam o `mypy`/`pytest` que estiver no `PATH` no momento do commit. Se você ativou a venv (`.venv\Scripts\activate`) no shell que vai rodar `git commit`, isso já resolve — os executáveis da venv entram no `PATH` automaticamente.

## Próximo passo

Com o ambiente rodando, veja [03 — Estratégia](03-estrategia.md) para entender as regras de entrada/saída, ou pule direto para [07 — Configuração](07-configuracao.md) se só quiser a referência de variáveis do `.env`.
