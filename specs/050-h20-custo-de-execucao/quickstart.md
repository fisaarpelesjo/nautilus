# Quickstart — validar a spec 050 (H20 custo de execução)

## Pré-requisitos

- Ambiente configurado (`pip install -r requirements.txt`).
- Acesso de rede à Binance (candles).
- Execução real: rodar na VPS (`vps-limulus`, `/root/nautilus-research`).

## 1. Rodar a suite (sem rede, mockada)

```bash
pytest tests/test_modelo.py -v -k custo
```

## 2. Rodar a avaliação real

```bash
python main.py geometria
```

Espera-se, além do já reportado por specs 048/049: por par, retorno
com custo (já publicado) ao lado do retorno sem custo, e a fração da
vantagem bruta consumida pelo custo — mesma métrica de H10/H21.

## 3. Rodar a suite completa

```bash
pytest -q
```

## O que este quickstart não valida

Não isola os outros dois candidatos registrados em spec 049 (trailing
stop vs. barreira estática; amostra por par) — ficam em aberto.
