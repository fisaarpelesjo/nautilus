# Quickstart — validar a spec 054 (H10 reseleção frequente)

## Pré-requisitos

- Ambiente configurado (`pip install -r requirements.txt`).
- Acesso de rede à Binance (candles).
- Execução real: rodar na VPS (`vps-limulus`, `/root/nautilus-research`).

## 1. Rodar a suite (sem rede, mockada)

```bash
pytest tests/test_pairs_trading.py -v -k reselecao
```

Cobre: `reselecionar_a_cada=None` reproduz o resultado já publicado
(regressão); `reselecionar_a_cada` explícito muda de fato quantas
vezes `selecionar_pares` é chamado dentro de `run_pairs_backtest`.

## 2. Rodar a avaliação real

```bash
python main.py pairs_reselecao
```

Espera-se: resultado de treino/validação com `reselecionar_a_cada=120`
(era 500, amarrado à formação), comparado contra os dois já publicados
(6 trades, specs 039/052). Foco em `total_trades` da validação —
atinge `EDGE_MIN_TRADES` (10)?

## 3. Rodar a suite completa

```bash
pytest -q
```

## O que este quickstart não valida

Não decide se H10 deveria virar a estratégia operada pelo bot. Também
não testa outros valores de `reselecionar_a_cada` — `120` é o único
testado, ancorado em `meia_vida_max` (D3 de `research.md`).
