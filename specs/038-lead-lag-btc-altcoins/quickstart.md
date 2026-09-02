# Quickstart — validar a spec 038 (H21, lead-lag BTC → altcoins)

## Pré-requisitos

- Ambiente configurado (`pip install -r requirements.txt`).
- Acesso de rede à Binance (candles).
- Testes/backtests longos: rodar na VPS (`vps-limulus`,
  `/root/nautilus-research`), não localmente.

## 1. Rodar a suite (sem rede, mockada)

```bash
pytest tests/test_lead_lag.py -v
```

Cobre: sinal BUY dispara exatamente quando o retorno de BTC no mesmo
candle é positivo (D1/D2); candle sem retorno de BTC correspondente fica
sem sinal (FR-008); ausência de *lookahead* (o sinal na linha `t` depende
só de `close_btc[t]`/`close_btc[t-1]`, nunca de `close_btc[t+1]` em
diante); `BacktestResult` produzido aceito por `evaluate_approval()` sem
erro.

## 2. Rodar a avaliação real

```bash
python main.py leadlag
```

Espera-se, para cada um dos 11 pares:

- `total_trades`, `total_return_pct`, `buy_hold_return_pct`,
  `max_drawdown_pct`, `profit_factor` — mesmos campos de qualquer outro
  resultado deste projeto.
- Veredito (`evaluate_approval`): aprovado/reprovado/inconclusivo.
- Resumo (US2): quantos dos 11 pares superam o buy-hold, quantos têm
  profit factor acima de 1,0.

## 3. Confirmar ausência de *lookahead* manualmente

Sobre um trecho curto do histórico, verificar que alterar `close_btc` em
qualquer candle POSTERIOR ao candle `t` avaliado não muda o sinal
calculado em `t` — só candles em `t` e anteriores podem influenciá-lo.

## 4. Rodar a suite completa

```bash
pytest -q
```

Nenhuma regressão — `backtesting/engine.py`, `backtesting/approval.py`,
`backtesting/modelo.py` não são alterados.

## O que este quickstart não valida

Não decide se H21 deveria virar a estratégia operada pelo bot — o bot só
opera `strategy/ema_rsi.py` (regras), nunca este sinal. O quickstart
valida a medição.
