# Quickstart — validar a spec 044 (circuit breaker de perdas consecutivas)

## Pré-requisitos

- Ambiente configurado (`pip install -r requirements.txt`).
- Acesso de rede à Binance (candles).
- Execução real: rodar na VPS (`vps-limulus`, `/root/nautilus-research`),
  não localmente.

## 1. Rodar a suite (sem rede, mockada)

```bash
pytest tests/test_portfolio_h14.py -v
```

Cobre: bloqueio de entrada ao atingir `MAX_CONSECUTIVE_LOSSES`, reset do
contador no primeiro trade lucrativo, e regressão do caminho default
(`usar_circuit_breaker=False` produz resultado idêntico ao já
publicado).

## 2. Rodar a avaliação real

```bash
python main.py carteira_breaker
```

Espera-se:

- Curva de capital agregada com o circuit breaker isolado ligado.
- `max_drawdown_pct` agregado, comparado contra os quatro já publicados
  (28,66% sem overlay; 23,04% só volatilidade; 20,74% só correlação;
  20,24% combinado vol+correlação).
- Veredito (`evaluate_approval`): aprovado/reprovado/inconclusivo.

## 3. Rodar a suite completa

```bash
pytest -q
```

Nenhuma regressão.

## O que este quickstart não valida

Não decide se H14 (com qualquer combinação de overlay) deveria virar a
estratégia operada pelo bot. Também não testa a combinação do circuit
breaker com os outros dois mecanismos — isso é uma spec futura, só se
o resultado isolado aqui mostrar melhora.
