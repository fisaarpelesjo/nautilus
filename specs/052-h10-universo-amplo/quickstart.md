# Quickstart — validar a spec 052 (H10 universo amplo)

## Pré-requisitos

- Ambiente configurado (`pip install -r requirements.txt`).
- Acesso de rede à Binance (candles).
- Execução real: rodar na VPS (`vps-limulus`, `/root/nautilus-research`).

## 1. Rodar a suite (sem rede, mockada)

```bash
pytest tests/test_pairs_trading.py -v -k monoton
```

## 2. Rodar a avaliação real

```bash
python main.py pairs_amplo
```

Espera-se: resultado de treino/validação sobre `UNIVERSO_AMPLO` (34
pares), comparado contra o já publicado (12 pares, spec 039: 6 trades
na validação, inconclusiva). Foco em `total_trades` da validação —
atinge `EDGE_MIN_TRADES` (10)?

## 3. Rodar a suite completa

```bash
pytest -q
```

## O que este quickstart não valida

Não decide se H10 deveria virar a estratégia operada pelo bot. Também
não muda `PairsParams` (formação, z-scores, meia-vida) — só o universo
candidato.
