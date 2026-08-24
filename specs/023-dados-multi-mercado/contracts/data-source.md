# Contrato: Fonte de dados (DataSource)

**Feature**: 023-dados-multi-mercado

Contrato que toda fonte MUST cumprir para ser plugável atrás de `data/fetcher.py::fetch_ohlcv()`. O objetivo é que os ~10 consumidores existentes (backtest, compare, scan, optimize, validation, replay, runner, chart, selector, diagnostics) **não saibam** qual fonte respondeu.

---

## Operação obrigatória

```
fetch_ohlcv(symbol: str, timeframe: str, limit: int) -> DataFrame
```

### Entrada

| Parâmetro | Contrato |
|---|---|
| `symbol` | Identificador cru, como o operador escreveu. A fonte MUST aceitar a convenção do seu próprio mercado |
| `timeframe` | String de intervalo (`4h`, `1h`, `1d`). A fonte MUST recusar explicitamente um intervalo que não suporta |
| `limit` | Número **máximo** de candles desejado. A fonte pode devolver menos se não tiver histórico |

### Saída

DataFrame com:

- **Índice**: `DatetimeIndex`, crescente, sem duplicatas
- **Colunas** (exatamente estas, minúsculas): `open`, `high`, `low`, `close`, `volume`
- **Ordenação**: do mais antigo para o mais recente

A normalização de nome de coluna é responsabilidade da **fonte**, não do consumidor — `yfinance` devolve `Open/High/Low/Close/Volume` capitalizado e MUST converter internamente.

---

## Política de falha

Segue a política de todo o projeto: **dado desconhecido nunca vira valor aproveitável**.

| Situação | Comportamento obrigatório |
|---|---|
| Símbolo inexistente | Levantar exceção com mensagem identificando o símbolo |
| Timeframe não suportado pela fonte | Levantar exceção nomeando o intervalo recusado |
| Falha de rede | Levantar exceção (após a política de retry da própria fonte, se houver) |
| Zero candles retornados | Levantar exceção — MUST NOT devolver DataFrame vazio |
| Menos candles que `limit` | **Devolver o que tem**, e registrar a lacuna de forma detectável |

A última linha é o risco técnico nº 3 de `research.md`: pedir 2.000 candles e receber 993 é o comportamento normal de uma fonte com teto de histórico, mas se passar silencioso, uma comparação cripto × ações fica desbalanceada sem ninguém perceber.

---

## Restrições de escopo

Operações que **MUST permanecer exclusivas de cripto** e MUST NOT fazer parte deste contrato:

- `fetch_ticker` / `fetch_tickers` — usadas pela seleção dinâmica de pares
- `fetch_balance` — usada pela execução e reconciliação
- `fetch_order_book` — usada pela checagem de liquidez e pelo slippage medido

Nenhuma delas é necessária para pesquisa, e todas pertencem ao caminho de execução, que esta feature não toca.

---

## Contrato de não-regressão

A fonte cripto MUST produzir resultado **idêntico** ao do fetcher atual para a mesma entrada. Isso inclui:

- A política de cache incremental (primeira chamada busca `limit` candles; seguintes buscam 5 e fazem merge)
- O singleton de instância por modo e o retry com backoff em erro de rate limit
- O formato e a ordenação do DataFrame

Este contrato existe porque a abstração é, por natureza, uma oportunidade de introduzir mudança de comportamento sem querer — e este projeto já perdeu tempo duas vezes com dois pontos do sistema discordando silenciosamente sobre a mesma coisa (simulação sem trailing stop; confirmação de tendência olhando o futuro). Um teste MUST fixar essa equivalência.
