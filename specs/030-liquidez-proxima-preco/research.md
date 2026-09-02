# Fase 0 — Pesquisa: profundidade de liquidez próxima ao preço

**Data:** 2026-09-02

---

## D1 — Critério de "perto do preço"

**Decisão:** reusar `MAX_SPREAD_PCT_ENTRY` (default 0,5%) como o desvio de
preço máximo aceito ao somar a profundidade do lado ask — **nenhuma
constante nova**. Um nível de preço `> best_ask × (1 + MAX_SPREAD_PCT_ENTRY)`
não conta para `depth_usdt`.

**Rationale.** `MAX_SPREAD_PCT_ENTRY` já é, no gate de liquidez existente, a
resposta declarada para "quanto desvio de preço em relação ao topo do book
ainda é aceitável para esta entrada" — é usada exatamente para isso na
checagem de spread, alguns milissegundos antes da checagem de profundidade,
no mesmo `check_liquidity`. Introduzir uma segunda constante para a mesma
pergunta ("o que ainda é 'perto' do preço") duplicaria um conceito já
declarado, com risco real de as duas divergirem em edições futuras do
`.env`.

**Medição** (`data/fetcher.py::fetch_order_book`, 22 pares de `PAIRS`,
livro de 20 níveis, 2026-09-02):

| Grandeza medida | Resultado |
|---|---|
| Pares com profundidade @0,5% < profundidade total (20 níveis) | 9 de 22 — a diferença **existe** de verdade, não é hipotética |
| Menor razão profundidade@0,5% / profundidade total | ORCA/USDT: 3.117 / 29.843 = **10,4%** — quase 90% da "profundidade" somada hoje está fora do desvio aceito |
| Maior distância de preço do 20º nível ao melhor ask | ORCA/USDT: **+1,572%**, três vezes o `MAX_SPREAD_PCT_ENTRY` |

**Teste de divergência de decisão** — comparando a aprovação atual (soma dos
20 níveis) contra a proposta (soma limitada a 0,5%) em 4 tamanhos de ordem
(`$100` — config atual do bot — `$1.000`, `$5.000`, `$10.000`) × 22 pares =
88 combinações:

| Tamanho de ordem | Divergências | Pares afetados |
|---|---|---|
| **US$ 100** (config atual) | **0** | nenhum — SC-002 confirmado por medição, não por suposição |
| US$ 1.000 | 0 | nenhum |
| US$ 5.000 | 2 | ORCA/USDT, ROBO/USDT |
| US$ 10.000 | 2 | COW/USDT, HEMI/USDT |

Nas 4 divergências, a decisão **atual** aprova uma entrada que a **proposta**
recusa — nunca o contrário (o novo critério é estritamente mais conservador,
como esperado: ele nunca soma mais do que a soma bruta já somava).

**Leitura.** No tamanho de ordem que o bot roda hoje (`MAX_ORDER_SIZE_USDT =
100`), a mudança **não altera nenhuma decisão** — é exatamente o
comportamento que `specs/BACKLOG.md` já registrava ("a $100/ordem a
profundidade normalmente é generosa"). O gap é real, mas dorme até o
operador aumentar `MAX_ORDER_SIZE_USDT` — momento em que a checagem antiga
teria aprovado silenciosamente entradas com profundidade majoritariamente
inalcançável. Mesmo padrão de achado que a spec 018 (slippage) já registrou
para outro sintoma do mesmo book fino: o efeito aparece na escala, não no
tamanho de ordem atual.

**Alternativas consideradas:**
- **Nova constante dedicada** (ex. `LIQUIDITY_DEPTH_BAND_PCT`) — rejeitada:
  seria uma segunda resposta para a mesma pergunta que `MAX_SPREAD_PCT_ENTRY`
  já responde, com risco de as duas divergirem sem ninguém perceber.
- **Reusar o algoritmo de `estimate_slippage_pct`** (fixar volume, medir
  preço médio) em vez de fixar o desvio de preço e medir volume — rejeitada
  para o **gate**: o gate precisa responder "cabe uma ordem de até `3×
  order_size` aqui dentro de um desvio aceitável?", não "qual seria o
  slippage de uma ordem específica?". As duas perguntas são relacionadas
  (mesmo princípio: profundidade fantasma distante do preço não conta) mas
  não são a mesma conta — forçar o mesmo laço nas duas inverteria qual
  variável é fixada em cada uma. FR-004 é satisfeita pelo princípio
  compartilhado (nunca contar valor além de um desvio de preço aceito), não
  por uma função única — ver `plan.md`, Complexity Tracking.

---

## Resumo da decisão

| # | Decisão | Efeito |
|---|---|---|
| D1 | `depth_usdt` soma só níveis com `preço ≤ best_ask × (1 + MAX_SPREAD_PCT_ENTRY)`, reusando a constante existente | 0 divergências a $100 (config atual, medido); divergências reais a partir de ~$5.000 em pares de book mais fino |

## Fontes

- Medição própria, 2026-09-02: `data/fetcher.py::fetch_order_book`, 22 pares
  de `PAIRS` (`.env` local), livro de 20 níveis via Binance.
- `specs/BACKLOG.md`, itens 012 e 018 (018 implementado fora do fluxo formal
  de spec, sem pasta própria em `specs/`).
- `execution/liquidity.py::estimate_slippage_pct` — mesmo princípio de
  caminhar o book em vez de somar cegamente, aplicado antes para slippage.
