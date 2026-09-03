# Quickstart: H14 — calibração do classificador de entrada

## Pré-requisitos

- `.venv` com dependências do projeto instaladas.
- Acesso à Binance para `fetch_ohlcv` (mesmo requisito de `python main.py modelo`).

## Rodar

```bash
python main.py calibracao
```

Imprime, para `UNIVERSO_H11` e `ParametrosBarreira()` padrão:

- Limiar real de decisão e ponto de empate.
- Uma linha por corte de probabilidade testado — `n`, `alvo`, `stop`,
  `tempo`, razão de chances, e se supera o empate com 95% de confiança
  (`supera_empate_com_confianca`, Wilson CI).

Resultado salvo em `reports/calibracao_<timestamp>.json`.

## Resultado esperado

Ver tabela completa em `research.md` D3. Resumo: o corte real (0,3333)
e o corte seguinte (0,35) têm razão praticamente igual (~0,69-0,70,
ambos significativos); cortes acima de 0,40 colapsam em amostra antes
de mostrar qualquer tendência de melhora — refutando a ideia de um
filtro de confiança mais estrito.

## Verificação

```bash
pytest tests/test_calibracao_h14.py -q
```

7 testes: contagem por rótulo bruto, sentinela do corte 0 (resolve para
o limiar real), razão infinita sem stop, significância com amostra
grande vs. pequena (mesma razão, veredito oposto), `avaliar_calibracao`
sem previsões e com pares/params customizados.
