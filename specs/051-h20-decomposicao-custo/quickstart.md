# Quickstart — validar a spec 051 (H20 decomposição de custo)

## Pré-requisitos

- Ambiente configurado (`pip install -r requirements.txt`).
- Acesso de rede à Binance (candles).
- Execução real: rodar na VPS (`vps-limulus`, `/root/nautilus-research`).

## 1. Rodar a suite (sem rede, mockada)

```bash
pytest tests/test_modelo.py -v -k slippage or taxa
```

## 2. Rodar a avaliação real

```bash
python main.py geometria
```

Espera-se, além do já reportado por specs 048-050: por par, retorno
sem slippage (taxa real) e retorno sem taxa (slippage real), ao lado
do já publicado com custo total e sem custo algum.

## 3. Rodar a suite completa

```bash
pytest -q
```

## O que este quickstart não valida

Não simula `USE_LIMIT_ORDERS` — decompõe custo já medido, com a
ressalva de que "sem slippage" superestima o que ordens limit
entregariam de verdade (só afetam entrada, nunca saída/stop).
