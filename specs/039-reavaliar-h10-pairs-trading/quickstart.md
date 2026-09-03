# Quickstart — validar a spec 039 (reavaliar H10)

## Pré-requisitos

- Ambiente configurado (`pip install -r requirements.txt`).
- Acesso de rede à Binance (candles).
- Testes/backtests longos: rodar na VPS (`vps-limulus`,
  `/root/nautilus-research`), não localmente.

## 1. Rodar a suite (sem rede, mockada)

```bash
pytest tests/test_pairs_trading.py -v
```

Cobre: split 70/30 por corte de tempo compartilhado entre pares; fatia de
validação inclui exatamente `formacao` candles de aquecimento antes do
início real reportado (`period_start` alinhado); `run_pairs_backtest`
chamado sem alteração de assinatura; `BacktestResult` de validação aceito
por `evaluate_approval()` sem erro.

## 2. Rodar a avaliação real

```bash
python main.py pairs
```

Espera-se:

- `total_trades` de validação **maior** que o teto de 0-7 já diagnosticado
  em `docs/research/registro-de-hipoteses.md` §4.11 (SC-001).
- Veredito (`evaluate_approval`) sobre a validação: aprovado/reprovado/inconclusivo.
- Treino e validação lado a lado, mesmos campos de qualquer outro
  resultado deste projeto.

## 3. Rodar a suite completa

```bash
pytest -q
```

Nenhuma regressão — `backtesting/engine.py`, `backtesting/approval.py`,
`backtesting/pairs_trading.py::run_pairs_backtest`/`selecionar_pares` não
são alterados.

## O que este quickstart não valida

Não decide se H10 deveria virar a estratégia operada pelo bot — o bot só
opera `strategy/ema_rsi.py` (regras), nunca pairs trading. O quickstart
valida a medição que estava pendente desde §4.11.
