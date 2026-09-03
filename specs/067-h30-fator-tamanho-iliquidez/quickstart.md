# Quickstart: H30 — fator de tamanho/iliquidez (cross-sectional, sem timing)

## Pré-requisitos

- `.venv` com dependências do projeto instaladas.
- Acesso à Binance para `fetch_ohlcv` (mesmo requisito de `python main.py carteira`).

## Rodar

```bash
python main.py fator_tamanho
```

Sobre `UNIVERSO_AMPLO_HISTORICO_COMPLETO` (22 pares): compara uma cesta
igualmente ponderada dos 7 pares de menor volume médio contra os 7 de
maior volume, rebalanceadas a cada 180 candles (~30 dias), em treino e
validação, sob 3 multiplicadores de slippage (1x/3x/5x). Imprime
retorno, drawdown e custo de giro de cada combinação, mais o excesso
ilíquida-líquida por fatia.

Resultado salvo em `reports/fator_tamanho_<timestamp>.json`.

## Resultado esperado

Ver `research.md`, seção "Hipótese declarada antes de medir". Duas
leituras possíveis: o excesso se sustenta em treino, validação e sob
slippage elevado (confirma o fator como tilt operável), ou desaparece
em algum desses três testes (refuta).

## Verificação

```bash
pytest tests/test_fator_tamanho.py -q
```

8 testes: seleção por menor/maior volume, capital intacto sem
movimento de preço, custo cobrado no rebalanceamento, valorização
capturada, multiplicador de slippage reduz capital, ausência de pares
válidos não quebra, `avaliar_fator_tamanho` aceita dados sem rede.
