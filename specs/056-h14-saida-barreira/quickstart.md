# Quickstart: H14 — saída por barreira tripla em vez de trailing stop

## Pré-requisitos

- `.venv` com dependências do projeto instaladas.
- Acesso à Binance para `fetch_ohlcv` (mesmo requisito de `python main.py carteira`).

## Rodar

```bash
python main.py carteira_barreira
```

Roda a carteira de H14 (`UNIVERSO_H11`, sem nenhum outro overlay de
risco) com saída por barreira tripla fixa (stop nunca sobe, fecha em 24
velas se nenhum lado tocar) em vez do trailing stop real de produção.
Imprime capital final, retorno, buy&hold, trades, drawdown agregado,
profit factor e o veredito de `evaluate_approval()`, ao lado do já
publicado sem overlay (spec 037: 931 trades, 28,66% drawdown, PF 0,72).

Resultado salvo em `reports/carteira_barreira_<timestamp>.json`.

## Resultado esperado

Ver `research.md` D2-D3. Duas leituras possíveis, ambas informativas:
profit factor sobe de forma clara (confirma que o descasamento de saída
era parte do problema) ou continua baixo (refuta — a previsão não se
traduz em capital real mesmo sob sua própria definição de sucesso).

## Verificação

```bash
pytest tests/test_portfolio_h14.py -q
```

Inclui os 4 testes novos da spec 056: fecha no limite de velas sem
tocar barreira, stop não sobe sob o novo modo, barreiras fixas ainda
disparam antes do limite, default `False` reproduz o trailing existente.
