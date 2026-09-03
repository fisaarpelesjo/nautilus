# Quickstart: H26 — reversão contra funding extremo (crowding/liquidação)

## Pré-requisitos

- `.venv` com dependências do projeto instaladas.
- Acesso à Binance para `fetch_ohlcv` e `fetch_funding_rate_history`
  (endpoint público, sem credencial).

## Rodar

```bash
python main.py funding_extremo
```

Para cada par de `UNIVERSO_H11` com mercado perpétuo: calibra o limiar
de funding extremo (decil mais negativo) na fatia de treino (70% da
série), conta eventos extremos na fatia de validação (30%), rotula cada
evento pela barreira tripla de H14 e agrega alvo/stop entre pares.
Imprime a razão de chances pooled contra o ponto de empate e o veredito
de `supera_empate_com_confianca` (Wilson CI, 95%).

Resultado salvo em `reports/funding_extremo_<timestamp>.json`.

## Resultado esperado

Ver `research.md`, seção "Hipótese declarada antes de medir": REPROVADA
é o resultado mais provável, dado que 21 hipóteses direcionais
anteriores deste registro não sobreviveram a custo de execução e
confirmação fora da amostra. Um resultado positivo seria a exceção, não
a expectativa.

## Verificação

```bash
pytest tests/test_funding_reversao.py -q
```

Testes: calibração do limiar só no treino (não vaza validação),
alinhamento causal funding→candle (forward-fill), rotulagem de eventos
extremos, agregação pooled, delegação correta a
`supera_empate_com_confianca`.
