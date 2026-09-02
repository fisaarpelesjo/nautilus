# Fase 0 — Pesquisa: fonte de dados on-chain

**Data:** 2026-09-02

---

## D1 — API e formato

**Decisão:** `https://api.blockchain.info/charts/<nome>?timespan=<span>&format=json&sampled=false`.

**Medição** (2026-09-02, seis séries): todas `status: ok`, granularidade
diária, ~720-728 pontos em `timespan=2years`. Amostra da resposta:

```json
{"status":"ok","name":"Number Of Unique Addresses Used","unit":"Unique Addresses",
 "period":"day","values":[{"x":1785715200,"y":523906.0}, ...]}
```

`x` é timestamp Unix (segundos, UTC, meia-noite), `y` o valor do dia.
`sampled=false` evita que a API subamostre o período pedido (default da API
reduz a resolução em janelas longas) — sem isso, um pedido de 2 anos podia
devolver menos de um ponto por dia sem aviso.

**Rationale.** Único provedor gratuito e sem chave encontrado para métricas
de blockchain do Bitcoin. Sem custo, sem cadastro, formato estável (usado
publicamente desde 2014). `sampled=false` é o parâmetro que garante
granularidade diária real, não uma aproximação.

**Alternativas consideradas:**
- **Glassnode/CryptoQuant**: métricas mais ricas, mas exigem chave de API
  paga na maioria dos endpoints úteis — contradiz o padrão "sem chave" que
  H15 (spec 029) já estabeleceu para pesquisa, e adicionaria custo
  recorrente para uma hipótese com expectativa já registrada como baixa
  (§6.3 do registro).
- **Blockchair**: multi-chain, mas tier gratuito com limite de requisições
  mais agressivo e formato menos estável entre chains — não testado a
  fundo porque `blockchain.info` já resolve o caso de uso (BTC) sem
  nenhuma dessas desvantagens.

---

## D2 — Cliente HTTP

**Decisão:** `requests`, já dependência do projeto (`utils/notifier.py`),
`timeout=15` (mais generoso que os 5s do Telegram — resposta de série
histórica é maior que uma notificação).

**Rationale.** FR-005 proíbe dependência nova. `requests` já é usado com
exatamente esse padrão (`try/except` + `timeout`) em `utils/notifier.py`.

---

## D3 — Taxonomia de erro

**Decisão:** `fetch_onchain_series()` levanta `RuntimeError` (ou subclasse)
com o motivo, em três casos: falha de rede/timeout, HTTP não-200,
`status` no corpo diferente de `"ok"`. Série vazia (`values: []`) por
ausência real de dado **não** levanta — é um resultado válido (FR-004,
Edge Case "métrica válida sem dado no período").

**Rationale.** Mesmo princípio já em `data/sources/__init__.py::DataSource`
("MUST levantar exceção... nunca DataFrame vazio ou parcial silencioso")
e em `execution/liquidity.py` (custo desconhecido nunca vira zero) — dois
precedentes diretos no mesmo projeto, reusados aqui em vez de inventar um
terceiro critério.

---

## D4 — Módulo e assinatura

**Decisão:** `data/onchain.py` (novo, paralelo a `data/fetcher.py`, não
dentro de `data/sources/`).

```python
def fetch_onchain_series(metric: str, timespan: str = "3years") -> pd.DataFrame
```

Retorna `DataFrame` com `DatetimeIndex` (dia, UTC) crescente sem
duplicatas e uma coluna `value`.

**Rationale.** `data/sources/` implementa o protocolo `DataSource`
(`fetch_ohlcv(symbol, timeframe, limit)`) — forçar uma série de métrica
única (um valor por dia, sem symbol/timeframe/OHLC) nessa interface exigiria
campos falsos (open=high=low=close=value?) só para caber no contrato
errado. FR-006 já proíbe isso explicitamente. Módulo próprio, mesmo nível
de `data/fetcher.py`, é a opção que não força a abstração.

`timespan` como string (não `days: int`) porque é o formato nativo que a
API já aceita (`"2years"`, `"90days"`, `"all"`) — converter para dias e
reconverter de volta seria trabalho sem ganho.

---

## Resumo das decisões

| # | Decisão | Efeito |
|---|---|---|
| D1 | `api.blockchain.info/charts/<nome>`, `sampled=false` | Gratuito, sem chave, granularidade diária real medida |
| D2 | `requests`, `timeout=15` | Zero dependência nova (FR-005) |
| D3 | Exceção em falha/nome inválido/status não-ok; vazio-por-ausência não é erro | Mesmo princípio de `DataSource`/`check_liquidity` já no projeto |
| D4 | `data/onchain.py::fetch_onchain_series(metric, timespan)` | Módulo próprio — métrica on-chain não é OHLCV, protocolo `DataSource` não se aplica |

## Fontes

- Medição própria, 2026-09-02: `api.blockchain.info/charts/*`, seis séries.
- `data/sources/__init__.py` (protocolo `DataSource`, spec 023) — motivo de
  não reusar.
- `utils/notifier.py` — padrão de uso de `requests` já estabelecido.
