# Quickstart: H35 — Crowding via long/short ratio e open interest (Binance)

## Pré-requisitos

- `.venv` com dependências do projeto instaladas.
- Acesso à Binance Futures (mesmo requisito de `python main.py funding_extremo`).

## Rodar

```bash
python main.py crowding
```

Sobre `UNIVERSO_H11` (12 pares): para cada par, busca preço, long/short
ratio e open interest, corta em treino/validação dentro da janela real
disponível (retenção medida por par — tipicamente ~31 dias), calibra o
decil mais baixo de long/short ratio e a mediana de open interest só no
treino, rotula eventos de validação pela barreira tripla e agrega a
contagem alvo/stop entre pares. Imprime a retenção real medida, a
contagem pooled e o veredito de significância (Wilson CI).

Resultado salvo em `reports/crowding_<timestamp>.json`.

## Resultado esperado

Ver `research.md`, seção "Hipótese declarada antes de medir". Três
leituras possíveis: supera o ponto de equilíbrio com confiança (raro dado
o histórico deste registro — seria o primeiro caso positivo entre 23
hipóteses direcionais), reprova com amostra suficiente para a leitura ter
peso, ou fica inconclusiva por amostra insuficiente (esperado dado D6 —
retenção curta do endpoint).

## Verificação

```bash
pytest tests/test_crowding_extremo.py -q
```

Cobre: decil/mediana calibrados só no treino (não vazam validação),
alinhamento causal por forward-fill, descarte de candles anteriores ao
início real do histórico do endpoint (nunca ffill retroativo), evento
exige as duas confirmações (ratio no decil E open interest acima da
mediana), agregação pooled, par sem mercado perpétuo correspondente é
descartado sem abortar os demais.
