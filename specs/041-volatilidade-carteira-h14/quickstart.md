# Quickstart — validar a spec 041 (dimensionamento por volatilidade na carteira de H14)

## Pré-requisitos

- Ambiente configurado (`pip install -r requirements.txt`).
- Acesso de rede à Binance (candles).
- Testes/backtests longos: rodar na VPS (`vps-limulus`,
  `/root/nautilus-research`), não localmente.

## 1. Rodar a suite (sem rede, mockada)

```bash
pytest tests/test_portfolio_h14.py -v
```

Cobre: `usar_dimensionamento_vol=False` (default) reproduz exatamente os
valores de referência já capturados para o caminho sem dimensionamento
(regressão); com `usar_dimensionamento_vol=True` e `atr_ratio` acima do
alvo, o tamanho da entrada é estritamente menor que sem o fator; com
`atr_ratio` ausente/inválido, o tamanho não muda (fator 1,0).

## 2. Rodar a avaliação real

```bash
python main.py carteira_vol
```

Espera-se:

- Curva de capital agregada sobre `UNIVERSO_H11` (12 pares) com
  dimensionamento por volatilidade ligado.
- `max_drawdown_pct` agregado, comparado diretamente contra o já
  publicado sem dimensionamento (28,66%, spec 037).
- Veredito (`evaluate_approval`): aprovado/reprovado/inconclusivo.

## 3. Rodar a suite completa

```bash
pytest -q
```

Nenhuma regressão — `backtesting/volatilidade.py`,
`backtesting/engine.py`, `backtesting/approval.py` não são alterados.

## O que este quickstart não valida

Não decide se H14 (com ou sem dimensionamento) deveria virar a
estratégia operada pelo bot. Também não prova que dimensionamento por
volatilidade "funciona" em geral — só testa se ele reduz o drawdown de
carteira específico que reprovou H14 duas vezes.
