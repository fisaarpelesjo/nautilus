# Quickstart — validar a spec 045 (limite de drawdown diário)

## Pré-requisitos

- Ambiente configurado (`pip install -r requirements.txt`).
- Acesso de rede à Binance (candles).
- Execução real: rodar na VPS (`vps-limulus`, `/root/nautilus-research`),
  não localmente.

## 1. Rodar a suite (sem rede, mockada)

```bash
pytest tests/test_portfolio_h14.py -v
```

Cobre: bloqueio de entrada abaixo do limite diário, reset do saldo de
referência no primeiro candle de um novo dia (mesmo sem trade
lucrativo), e regressão do caminho default
(`usar_limite_drawdown_diario=False` produz resultado idêntico ao já
publicado).

## 2. Rodar a avaliação real

```bash
python main.py carteira_dd_diario
```

Espera-se:

- Curva de capital agregada com o limite diário isolado ligado.
- `max_drawdown_pct` e `total_trades` agregados, comparados contra os
  cinco já publicados (28,66%/931; 23,04%/763; 20,74%/595; 20,24%/595;
  0,57%/6).
- Veredito (`evaluate_approval`): aprovado/reprovado/inconclusivo —
  atenção especial se `total_trades` cair abaixo do mínimo de 10 (M14),
  mesmo sinal de colapso amostral do circuit breaker.

## 3. Rodar a suite completa

```bash
pytest -q
```

Nenhuma regressão.

## O que este quickstart não valida

Não decide se H14 (com qualquer combinação de overlay) deveria virar a
estratégia operada pelo bot. Também não testa limite semanal/mensal nem
a combinação deste mecanismo com os outros quatro — specs futuras,
condicionadas a este resultado isolado não ser degenerado.
