# Quickstart: H25 — sazonalidade por sessão de negociação (hora do dia)

## Pré-requisitos

- `.venv` com dependências do projeto instaladas.
- Acesso à Binance para `fetch_ohlcv` (mesmo requisito de qualquer
  comando de backtest).

## Rodar

```bash
python main.py sazonalidade
```

Para cada uma das 3 janelas UTC (asiática 0-8h, europeia 8-16h,
americana 16-24h) × 12 pares de `UNIVERSO_H11` (36 combinações):
profit factor com e sem o filtro na janela de busca, e status de
confirmação fora da amostra (`confirmado`/`defensivo`/`só_na_busca`/
`reprovado`/`inconclusivo`/`erro`).

Resultado salvo em `reports/sazonalidade_<timestamp>.json`.

## Resultado esperado

Ver `research.md`, seção "Hipótese declarada antes de medir". Duas
leituras possíveis: ao menos uma combinação atinge `confirmado`
(evidência real de sazonalidade horária), ou nenhuma confirma (fecha a
família "filtro de tempo sobre H1", junto com H5).

## Verificação

```bash
pytest tests/test_sazonalidade.py -q
```

7 testes: filtro bloqueia BUY fora da janela, nunca toca SELL, preserva
HOLD original, janela ásia permite madrugada UTC, janelas cobrem as 24h
sem sobreposição, erro de busca não quebra a varredura, avaliação
continua após um par com erro.
