# Feature Specification: Profundidade de liquidez próxima ao preço

**Feature Branch**: `030-liquidez-proxima-preco`

**Created**: 2026-09-02

**Status**: Draft

**Input**: User description: item 012 (metade pendente) do `specs/BACKLOG.md` —
`execution/liquidity.py::check_liquidity` soma o valor de todos os níveis (até
20) do lado ask do order book ao calcular a profundidade disponível, sem
considerar a distância de preço em relação ao melhor ask. Uma ordem pode ser
"aprovada" porque o book tem profundidade total suficiente, mesmo que grande
parte dela esteja em níveis de preço muito distantes do topo — liquidez que a
ordem nunca alcançaria a um preço aceitável.
`execution/liquidity.py::estimate_slippage_pct` (spec 018) já resolve esse
problema corretamente para o cálculo de slippage: caminha o book a partir do
melhor preço e mede o preço médio real de execução. O gate de profundidade
precisa do mesmo critério — profundidade útil é a que existe perto do preço
atual, não a soma bruta do book inteiro.

---

## Contexto

`execution/liquidity.py::check_liquidity` é chamado antes de toda entrada
real (`trading/position_lifecycle.py`) e bloqueia a ordem quando a
profundidade do lado ask é menor que `max(MIN_ORDERBOOK_DEPTH_USDT, 3 ×
MAX_ORDER_SIZE_USDT)`. Hoje essa profundidade é a soma bruta de até 20 níveis
do book, sem nenhum critério de proximidade de preço — um book fino perto do
preço com muita profundidade "fantasma" mais distante passa pelo gate hoje e
não deveria: a ordem, executada a mercado, nunca chegaria a esses níveis
distantes a um preço aceitável.

`estimate_slippage_pct` já resolve exatamente esse problema para outro
consumidor (medir o slippage esperado de uma ordem): caminha os níveis a
partir do melhor preço, acumula até preencher o volume pretendido, e mede o
preço médio real. Esta spec aplica o mesmo critério ao **gate**, que hoje usa
uma medição diferente (e mais otimista) da mesma grandeza.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bloquear profundidade fantasma distante do preço (Priority: P1)

O sistema recusa uma entrada quando a profundidade **perto do melhor preço**
é insuficiente, mesmo que a soma de todos os níveis do book pareça suficiente.

**Why this priority**: é o gap que esta spec existe para fechar — o cenário
que hoje passa pelo gate e não deveria.

**Independent Test**: montar um order book sintético com profundidade total
acima do requisito, mas concentrada em níveis de preço distantes do melhor
ask, e confirmar que `check_liquidity` recusa a entrada.

**Acceptance Scenarios**:

1. **Given** um order book cuja soma de todos os níveis excede o requisito de
   profundidade, mas cuja profundidade nos níveis próximos ao melhor preço
   fica abaixo dele, **When** `check_liquidity` roda, **Then** a entrada é
   recusada com motivo explícito.
2. **Given** o mesmo order book, **When** o motivo da recusa é reportado,
   **Then** ele distingue "profundidade insuficiente perto do preço" do
   motivo de spread já existente.

---

### User Story 2 - Não regredir os casos já aprovados (Priority: P1)

Um order book com profundidade suficiente **perto do preço** continua sendo
aprovado, exatamente como hoje.

**Why this priority**: sem isso, a mudança trocaria um falso positivo (gap
que esta spec fecha) por falsos negativos em massa (entradas legítimas
bloqueadas) — regressão pior que o problema original. Conforme
`specs/BACKLOG.md`, na maioria dos casos observados hoje (ordens de ~US$100)
a profundidade já é generosa perto do preço, então o comportamento deve
permanecer idêntico nesses casos.

**Independent Test**: rodar a suite de testes existente de
`execution/liquidity.py` (books gerados com profundidade concentrada perto do
topo) e confirmar que todos os casos que hoje aprovam continuam aprovando.

**Acceptance Scenarios**:

1. **Given** um order book com profundidade suficiente concentrada nos
   primeiros níveis, **When** `check_liquidity` roda, **Then** a entrada é
   aprovada, como no comportamento atual.
2. **Given** os testes existentes de `check_liquidity`, **When** a suite
   completa roda após a mudança, **Then** nenhum teste pré-existente quebra.

---

### User Story 3 - Um único critério de profundidade real no código (Priority: P2)

O gate de entrada e a estimativa de slippage usam o mesmo critério para
decidir até onde a profundidade do book é real.

**Why this priority**: os dois caminhos medem a mesma grandeza (quanto do
book é alcançável a partir do melhor preço) para propósitos diferentes. Dois
critérios divergentes para a mesma pergunta é o tipo de discordância entre
partes do sistema que specs anteriores já pagaram caro para descobrir tarde
(trailing stop no backtest, spec 019; MTF point-in-time no replay, spec 020).

**Why P2**: não é o requisito que fecha o gap (isso é US1) nem o que evita
regressão (US2) — é a garantia de que o gap não reabre por um caminho
paralelo divergir de novo no futuro.

**Independent Test**: inspecionar que `check_liquidity` e
`estimate_slippage_pct` compartilham a mesma lógica de caminhamento de níveis
do book, não duas implementações independentes.

**Acceptance Scenarios**:

1. **Given** o mesmo order book e o mesmo volume de referência, **When**
   `check_liquidity` mede profundidade e `estimate_slippage_pct` mede
   slippage, **Then** os dois concordam sobre até que nível do book é
   alcançável.

---

### Edge Cases

- **Book com profundidade real zero perto do preço, mas grande longe dele.**
  Caso central desta spec — deve recusar.
- **Book com profundidade concentrada exatamente nos primeiros níveis.**
  Comportamento atual, deve continuar aprovando (US2).
- **Falha ao buscar o order book.** Já tratado — continua "liquidez
  indisponível", sem mudança (fora de escopo).
- **`MIN_ORDERBOOK_DEPTH_USDT` configurado abaixo do padrão.** A margem sobre
  `3 × MAX_ORDER_SIZE_USDT` já existente continua se aplicando — esta spec
  muda como a profundidade é *medida*, não quanto é *exigido*.
- **Spread já acima do limite.** Checagem de spread já existente e
  independente — continua bloqueando antes de chegar à checagem de
  profundidade, sem mudança.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST medir a profundidade do lado ask usada no gate
  considerando apenas os níveis alcançáveis a partir do melhor preço até um
  critério de proximidade declarado — nunca a soma bruta de todos os níveis
  retornados pelo book, independente da distância de preço.
- **FR-002**: O sistema MUST manter o requisito de profundidade já existente
  (`max(MIN_ORDERBOOK_DEPTH_USDT, 3 × order_size_usdt)`) — esta spec muda
  como a profundidade disponível é medida, não quanto é exigido.
- **FR-003**: Profundidade perto do preço insuficiente MUST continuar
  bloqueando a entrada com motivo explícito, distinguível do motivo de
  spread.
- **FR-004**: O critério de proximidade de preço usado na medição MUST ser o
  mesmo, ou derivado do mesmo princípio, usado por
  `estimate_slippage_pct` para caminhar o book — não uma segunda lógica
  independente (US3).
- **FR-005**: O sistema MUST NOT alterar o comportamento da checagem de
  spread (`MAX_SPREAD_PCT_ENTRY`) já existente.
- **FR-006**: O sistema MUST continuar retornando "liquidez indisponível" —
  nunca aprovação por omissão — quando o book não puder ser lido.
- **FR-007**: O critério exato de proximidade de preço (o quanto conta como
  "perto") MUST ser medido e declarado antes da implementação (Fase 0 do
  plano), não ajustado a posteriori a um resultado observado.
- **FR-008**: O sistema MUST NOT alterar `execution/order_manager.py`,
  `risk/manager.py` ou o comportamento de ordens já enviadas — o escopo é
  só a decisão de aprovar/recusar a entrada.

### Key Entities

- **Nível de book**: par (preço, quantidade) do lado ask, como hoje
  retornado por `fetch_order_book`.
- **Profundidade próxima**: soma de valor (preço × quantidade) dos níveis
  alcançáveis a partir do melhor preço até o critério de proximidade
  declarado — a grandeza que substitui a soma bruta atual.
- **Decisão de liquidez**: `LiquidityCheck` já existente
  (`approved`, `reason`, `spread_pct`, `depth_usdt`, `best_ask`) — sem novo
  campo, `depth_usdt` passa a refletir a profundidade próxima em vez da soma
  bruta.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um book com profundidade total suficiente mas concentrada longe
  do melhor preço é recusado — cenário que hoje é aprovado incorretamente.
- **SC-002**: Um book com profundidade suficiente perto do preço continua
  aprovado, sem nenhuma mudança de resultado em relação ao comportamento
  atual (verificado pela suite de testes existente de
  `execution/liquidity.py`).
- **SC-003**: O motivo de bloqueio por profundidade permanece específico e
  distinguível do motivo de spread.
- **SC-004**: Nenhum outro caminho do bot (execução real, risco, backtest)
  muda de comportamento.

---

## Assumptions

- `MAX_ORDER_SIZE_USDT` e `MIN_ORDERBOOK_DEPTH_USDT` permanecem como estão —
  só a medição de profundidade disponível muda, não o requisito.
- O critério de proximidade de preço (quanto conta como "perto" do melhor
  preço) é uma decisão de engenharia com restrição declarada, medida em
  research.md antes da implementação — mesmo padrão de D1-D6 na spec 029,
  não uma ambiguidade de requisito de negócio.
- O efeito esperado é pequeno na maioria dos casos observados hoje — a
  ~US$100/ordem a profundidade já é generosa perto do preço, segundo medição
  registrada em `specs/BACKLOG.md` (item 012) — mas fecha um gap real em
  pares ou momentos de book fino, e em ordens maiores.
- Esta spec fecha a metade pendente do item 012 do backlog; a outra metade
  (MTF fail-closed) já foi corrigida em 2026-08-18, fora do fluxo formal de
  spec.
