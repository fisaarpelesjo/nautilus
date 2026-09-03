# Quickstart: H14 — saída por barreira tripla + gate de correlação

## Pré-requisitos

- `.venv` com dependências do projeto instaladas.
- Acesso à Binance para `fetch_ohlcv` (mesmo requisito de `python main.py carteira`).

## Rodar

```bash
python main.py carteira_barreira_corr
```

Roda a carteira de H14 (`UNIVERSO_H11`) com saída por barreira tripla
(spec 056) e gate de correlação (spec 042) ligados ao mesmo tempo.
Imprime capital final, retorno, buy&hold, trades, drawdown agregado,
profit factor e o veredito de `evaluate_approval()`, ao lado dos três
resultados já publicados (sem overlay: 28,66%/931/PF 0,72; só barreira:
22,25%/543/PF 0,78; só correlação: 20,74%/595/PF 0,68).

Resultado salvo em `reports/carteira_barreira_corr_<timestamp>.json`.

## Resultado esperado

Ver `research.md` D2-D3. Duas leituras possíveis: `total_trades`
significativamente diferente dos dois isolados com drawdown abaixo dos
dois (aditividade), ou `total_trades` perto de um dos dois isolados
(dominância, repetindo o padrão das specs 043/046).

## Verificação

```bash
pytest tests/test_portfolio_h14.py -q
```

Inclui os 2 testes novos da spec 057: as duas flags juntas não quebram
(gate ainda bloqueia candidato correlacionado), stop continua fixo sob
o modo combinado.
