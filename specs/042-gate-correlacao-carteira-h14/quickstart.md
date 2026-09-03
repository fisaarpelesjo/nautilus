# Quickstart — validar a spec 042 (gate de correlação na carteira de H14)

## Pré-requisitos

- Ambiente configurado (`pip install -r requirements.txt`).
- Acesso de rede à Binance (candles).
- Testes/backtests longos: rodar na VPS (`vps-limulus`,
  `/root/nautilus-research`), não localmente.

## 1. Rodar a suite (sem rede, mockada)

```bash
pytest tests/test_portfolio_h14.py -v
```

Cobre: candidato com retornos quase idênticos a uma posição já aberta é
bloqueado (correlação ≥ 0,7); candidato descorrelacionado nunca é
bloqueado; sem posições abertas, nunca bloqueia; amostra insuficiente
falha aberta; `usar_gate_correlacao=False` (default) reproduz os valores
de referência já capturados.

## 2. Rodar a avaliação real

```bash
python main.py carteira_corr
```

Espera-se:

- Curva de capital agregada sobre `UNIVERSO_H11` (12 pares) com o gate
  de correlação ligado.
- `max_drawdown_pct` agregado, comparado diretamente contra o já
  publicado sem o gate (28,66%, spec 037).
- Veredito (`evaluate_approval`): aprovado/reprovado/inconclusivo.

## 3. Rodar a suite completa

```bash
pytest -q
```

Nenhuma regressão — `risk/correlation.py`, `backtesting/engine.py`,
`backtesting/approval.py` não são alterados.

## O que este quickstart não valida

Não decide se H14 (com ou sem o gate) deveria virar a estratégia operada
pelo bot. Também não testa o gate de correlação de produção em si — só
uma versão ponto-no-tempo com a mesma semântica, aplicada à carteira de
pesquisa.
