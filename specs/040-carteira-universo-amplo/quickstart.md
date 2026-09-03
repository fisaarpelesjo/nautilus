# Quickstart — validar a spec 040 (carteira sobre universo amplo)

## Pré-requisitos

- Ambiente configurado (`pip install -r requirements.txt`).
- Acesso de rede à Binance (candles).
- Testes/backtests longos: rodar na VPS (`vps-limulus`,
  `/root/nautilus-research`), não localmente — 34 pares com treino de
  modelo pooled é mais pesado que a carteira de 12 pares.

## 1. Rodar a suite (sem rede, mockada)

```bash
pytest tests/test_portfolio_h14.py -v
```

Cobre: `UNIVERSO_AMPLO` tem 34 símbolos únicos, todos `/USDT`; nenhum dos
5 pares pareados/lastreados excluídos (D1) aparece na lista.

## 2. Rodar a avaliação real

```bash
python main.py carteira_ampla
```

Espera-se:

- Curva de capital agregada sobre 34 pares.
- `max_drawdown_pct` agregado, comparado diretamente contra o já
  publicado sobre 12 pares (28,66%, spec 037).
- Veredito (`evaluate_approval`): aprovado/reprovado/inconclusivo.

## 3. Rodar a suite completa

```bash
pytest -q
```

Nenhuma regressão — `backtesting/portfolio_h14.py::simular_carteira`/
`_simular_carteira_core` não são alterados, só chamados com um `pares`
diferente.

## O que este quickstart não valida

Não decide se H14 deveria virar a estratégia operada pelo bot. Também
não prova que diversificação por si só criaria vantagem onde o sinal não
tem — só testa se a construção de carteira (não o sinal) explica o
drawdown já medido em spec 037.
