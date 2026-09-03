# Quickstart — validar a spec 047 (combinação total / teto)

## Pré-requisitos

- Ambiente configurado (`pip install -r requirements.txt`).
- Acesso de rede à Binance (candles).
- Execução real: rodar na VPS (`vps-limulus`, `/root/nautilus-research`).

## 1. Rodar a suite (sem rede, mockada)

```bash
pytest tests/test_portfolio_h14.py -v
```

## 2. Rodar a avaliação real

```bash
python main.py carteira_teto
```

Espera-se: `max_drawdown_pct`, `total_trades` e profit factor
comparados contra os sete já publicados. Confirma/refuta se o resultado
fica perto do gate de correlação sozinho (20,74%/595).

## 3. Rodar a suite completa

```bash
pytest -q
```

## O que este quickstart não valida

Não decide se H14 deveria virar a estratégia operada pelo bot.
