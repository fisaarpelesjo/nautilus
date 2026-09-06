# Quickstart: H39 — Arbitragem estatística via PCA/eigenportfolio (Avellaneda-Lee)

## Pré-requisitos

- `.venv` com dependências do projeto instaladas.
- Acesso à Binance para `fetch_ohlcv` (mesmo requisito de `python main.py pairs`).

## Rodar

```bash
python main.py pcaeigen
```

Sobre `UNIVERSO_AMPLO_HISTORICO_COMPLETO` (22 pares, 6.000 candles cada):
alinha o índice comum, corta treino/validação, decompõe os retornos
padronizados de treino por PCA, regride cada ativo contra os fatores,
integra o resíduo e ajusta um processo Ornstein-Uhlenbeck. Ativos com
meia-vida de resíduo fora de `[2, 120]` candles são excluídos; os demais
são avaliados individualmente pela bateria E1-E6. Imprime, por ativo, o
status de cada etapa, mais um resumo agregado e a limitação de não-hedge.

Resultado salvo em `reports/pca_eigenportfolio_<timestamp>.json`.

## Resultado esperado

Ver `research.md`, seção "Hipótese declarada antes de medir". A literatura
já aponta resultado majoritariamente negativo para cripto — a leitura
mais provável é a maioria dos ativos excluída pelo filtro de meia-vida ou
sem vantagem que sobreviva à validação, mas a medição decide, não a
expectativa.

## Verificação

```bash
pytest tests/test_pca_eigenportfolio.py -q
```

Cobre: PCA sobre matriz sintética com estrutura de fator conhecida
recupera o número esperado de componentes; ajuste OU recupera
média/sigma de uma série sintética com parâmetros conhecidos; filtro de
meia-vida exclui resíduo não-revertente sem abortar os demais;
`ResiduoStrategy`/`precompute_signals` geram BUY/SELL exatamente nos
cruzamentos declarados; `teste_sanidade` devolve zero trades sobre
s-score constante; `avaliar_universo` funciona com `fetch_ohlcv` mockado.
