# Quickstart — validar a spec 046 (combinação correlação + limite diário)

## Pré-requisitos

- Ambiente configurado (`pip install -r requirements.txt`).
- Acesso de rede à Binance (candles).
- Execução real: rodar na VPS (`vps-limulus`, `/root/nautilus-research`),
  não localmente.

## 1. Rodar a suite (sem rede, mockada)

```bash
pytest tests/test_portfolio_h14.py -v
```

Cobre: as duas flags juntas não geram exceção e produzem um
`BacktestResult` válido sobre um cenário sintético.

## 2. Rodar a avaliação real

```bash
python main.py carteira_combo2
```

Espera-se:

- Curva de capital agregada com os dois mecanismos ligados.
- `max_drawdown_pct`, `total_trades` e profit factor, comparados contra
  os seis já publicados (28,66%/931; 23,04%/763; 20,74%/595; 20,24%/595;
  0,57%/6; 22,17%/762).
- Veredito (`evaluate_approval`): aprovado/reprovado/inconclusivo.

## 3. Rodar a suite completa

```bash
pytest -q
```

Nenhuma regressão — `backtesting/portfolio_h14.py` não é alterado.

## O que este quickstart não valida

Não decide se H14 (com qualquer combinação de overlay) deveria virar a
estratégia operada pelo bot.
