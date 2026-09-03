# Quickstart: H29 — pairs trading via cópula gaussiana

## Pré-requisitos

- `.venv` com dependências do projeto instaladas, incluindo
  `requirements-dev.txt` (`scipy`, pesquisa apenas).
- Acesso à Binance para `fetch_ohlcv` (mesmo requisito de
  `python main.py pairs_reselecao`).

## Rodar

```bash
python main.py pairs_copula
```

Roda a mesma seleção de pares de H10 (`UNIVERSO_AMPLO_HISTORICO_
COMPLETO`, 22 pares) com o sinal de entrada/saída trocado de z-score
linear para distribuição condicional da cópula gaussiana (h1|2).
Imprime treino/validação e compara contra o já publicado de H10 (spec
054: 10 trades, PF 0,15, drawdown 16,61%).

Resultado salvo em `reports/pairs_copula_<timestamp>.json`.

## Resultado esperado

Ver `research.md`, seção "Hipótese declarada antes da medição final".
Duas leituras possíveis: resultado materialmente diferente de H10
(confirma a hipótese principal), ou mesmo padrão de reprovação com
números parecidos (confirma a alternativa — o obstáculo não está no
sinal de entrada).

## Verificação

```bash
pytest tests/test_pairs_copula.py -q
```

8 testes: forma fechada de `h_condicional` (independência, ponto de
equilíbrio), `ajustar_copula_gaussiana` recupera correlação forte/fraca
construída, backtest opera par cointegrado sintético sem exceção,
histórico insuficiente não estoura, menos de dois símbolos devolve
resultado vazio, `run_pairs_copula_scan` aceita dados sem rede.
