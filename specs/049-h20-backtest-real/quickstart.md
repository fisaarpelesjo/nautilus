# Quickstart — validar a spec 049 (H20 backtest real)

## Pré-requisitos

- Ambiente configurado (`pip install -r requirements.txt`).
- Acesso de rede à Binance (candles).
- Execução real: rodar na VPS (`vps-limulus`, `/root/nautilus-research`).

## 1. Rodar a suite (sem rede, mockada)

```bash
pytest tests/test_modelo.py tests/test_geometria.py -v
```

Cobre: `atr_tp_multiplier`/`atr_sl_multiplier` propagam de
`ParametrosBarreira` até `simulate_backtest`; `params=None` continua
reproduzindo H14 byte a byte
(`test_avaliar_par_sem_parametros_novos_reproduz_resultado_atual`, já
existente).

## 2. Rodar a avaliação real

```bash
python main.py geometria
```

Espera-se, além do já reportado por spec 048: backtest real por par
(retorno, drawdown, profit factor, trades) da geometria `tp=2,0`,
usando a mesma geometria para rotular e simular.

## 3. Rodar a suite completa

```bash
pytest -q
```

## O que este quickstart não valida

Não decide se H20 deveria virar motor de carteira (equivalente de spec
037) — isso é trabalho futuro, condicionado a este resultado.
