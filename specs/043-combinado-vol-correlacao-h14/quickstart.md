# Quickstart — validar a spec 043 (combinação vol + correlação)

## Pré-requisitos

- Ambiente configurado (`pip install -r requirements.txt`).
- Acesso de rede à Binance (candles).
- Testes/backtests longos: rodar na VPS (`vps-limulus`,
  `/root/nautilus-research`), não localmente.

## 1. Rodar a suite (sem rede, mockada)

```bash
pytest tests/test_portfolio_h14.py -v
```

Cobre: as duas flags juntas não geram exceção e produzem um
`BacktestResult` válido sobre um cenário sintético.

## 2. Rodar a avaliação real

```bash
python main.py carteira_combo
```

Espera-se:

- Curva de capital agregada com os dois mecanismos ligados.
- `max_drawdown_pct` agregado, comparado contra os três já publicados
  (28,66% sem overlay; 23,04% só volatilidade; 20,74% só correlação).
- Veredito (`evaluate_approval`): aprovado/reprovado/inconclusivo.

## 3. Rodar a suite completa

```bash
pytest -q
```

Nenhuma regressão — `backtesting/portfolio_h14.py` não é alterado.

## O que este quickstart não valida

Não decide se H14 (com qualquer combinação de overlay) deveria virar a
estratégia operada pelo bot.
