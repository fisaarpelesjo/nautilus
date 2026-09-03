# Quickstart: H27 — meta-labeling, pré-condição sobre o sinal primário

## Pré-requisitos

- `.venv` com dependências do projeto instaladas.
- Acesso à Binance para `fetch_ohlcv` (mesmo requisito de `python main.py modelo`).

## Rodar

```bash
python main.py meta_labeling
```

Imprime, para `UNIVERSO_H11` e `ParametrosBarreira()` padrão: o baseline
(todos os candles rotuláveis) e a entrada primária (só onde o EMA/RSI de
produção sinalizaria BUY), cada um com n/alvo/stop/tempo/razão e se
supera o empate com 95% de confiança — e o veredito final de pré-condição
atendida ou não.

Resultado salvo em `reports/meta_labeling_<timestamp>.json`.

## Resultado esperado

Ver `research.md` D2. A entrada primária (razão 0,5011) fica muito mais
perto do empate (0,5000) que o baseline (0,4383, razão 0,5000 é o ponto
de empate) — mas não supera com confiança (n=740, 453 stops). Pré-condição
NÃO atendida — a spec se encerra aqui, sem treinar modelo secundário.

## Verificação

```bash
pytest tests/test_meta_labeling.py -q
```

6 testes: contagem por rótulo bruto, razão infinita sem stop,
pré-condição atendida com amostra grande e razão alta, pré-condição não
atendida espelhando o achado real medido, pares sem prep excluídos,
`ValueError` sem dado, pares passados respeitados.
