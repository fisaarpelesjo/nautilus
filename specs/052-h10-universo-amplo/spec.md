# Feature Specification: H10 reavaliada com universo amplo de pares candidatos

**Feature Branch**: `052-h10-universo-amplo`

**Created**: 2026-09-03

**Status**: Draft

**Correção pós-T003 (2026-09-03).** A primeira execução real contra
`UNIVERSO_AMPLO` bruto (34 pares) devolveu 0 trades em treino E
validação — pior que o já publicado. Investigado antes de aceitar como
resultado: `UNIVERSO_AMPLO` inclui listagens recentes de histórico
curto (ex.: 504 candles), e `split_treino_validacao` usa a
**interseção** dos índices de tempo de todos os pares recebidos — o
mais curto do universo inteiro colapsa a janela comum de todo mundo.
Ver `research.md` D1. Todas as referências a `UNIVERSO_AMPLO` abaixo
(texto original, não reescrito para preservar procedência) passam a
significar `UNIVERSO_AMPLO_HISTORICO_COMPLETO` (22 pares, subconjunto
de histórico completo) — FR-001 e as referências a "34 pares" foram
as únicas partes atualizadas.

**Input**: User description: H10 (arbitragem estatística por
cointegração) segue **inconclusiva** desde spec 039 — o seletor foi
corrigido (poder de detecção 20%→60%, formação 250→500 candles), mas a
validação produziu só 6 trades, abaixo do mínimo de 10
(`EDGE_MIN_TRADES`). O treino chegou a passar profit factor (1,22) mas
a validação não tinha munição para confirmar nada. `selecionar_pares`
busca cointegração sobre `combinations(pares, 2)` — com os 12 pares de
`UNIVERSO_H11`, isso são 66 combinações candidatas por ciclo de
reseleção; `UNIVERSO_AMPLO` (34 pares, medido e validado em spec 040
para H14) dá 561 combinações, 8,5x mais chances de encontrar pares
cointegrados elegíveis a cada ciclo. Diferente de spec 040 (que
testou universo amplo para H14 e foi refutada — drawdown piorou por
puxar ativos mais voláteis/menos estabelecidos), aqui o objetivo não é
reduzir drawdown de carteira — é gerar amostra suficiente para o teste
resolver, não estrelar por fome de dados. `run_pairs_scan` já aceita
`pares` como parâmetro — nenhuma mecânica nova, só um universo
candidato diferente.

---

## Contexto e tese

**Por que isto não é repetir spec 040 com outro nome.** Spec 040
testou se um universo amplo reduz a CORRELAÇÃO/CONCENTRAÇÃO de risco
de carteira de H14 — e foi refutada, porque ampliar por liquidez pura
trouxe ativos mais novos e mais voláteis, piorando o drawdown. Esta
spec testa algo estruturalmente diferente: se um universo maior de
CANDIDATOS À COINTEGRAÇÃO produz pares elegíveis e trades suficientes
para o teste estatístico de H10 ter poder — uma pergunta sobre
TAMANHO DE AMOSTRA, não sobre concentração de risco. H10 não é uma
carteira com capital compartilhado (é `max_pares=3` simultâneos,
critério e capital já declarados em spec 039) — a métrica que falhou
não foi drawdown, foi `total_trades < EDGE_MIN_TRADES`.

**Zero mecânica nova.** `run_pairs_scan(pares=..., params=...)` já
aceita override de `pares` (mesmo padrão de `run_modelo_scan`,
`run_geometria_scan`). `UNIVERSO_AMPLO` já existe, já medido e validado
para liquidez em spec 040 (`backtesting/portfolio_h14.py`) — reusado
sem remedição. Regra de seleção de pares (`selecionar_pares`),
parâmetros de entrada/saída/stop (`PairsParams`), formação (500,
spec 039) e critério de aprovação (`evaluate_approval`) continuam
intocados — só o universo candidato muda.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reavaliar H10 com universo amplo de candidatos (Priority: P1)

O pesquisador obtém o resultado de treino e validação de H10 rodando
`selecionar_pares` sobre `UNIVERSO_AMPLO` (34 pares) em vez de
`UNIVERSO_H11` (12 pares), comparado explicitamente contra o já
publicado (6 trades na validação, spec 039).

**Why this priority**: é a pergunta da hipótese — sem o comparativo,
não há como saber se o universo amplo resolve a fome de amostra que
deixou H10 inconclusiva.

**Independent Test**: confirmar que `selecionar_pares` sobre um
cenário sintético com mais colunas de preço encontra, no mínimo, tantos
pares elegíveis quanto o mesmo cenário com menos colunas (nunca menos —
mais candidatos não pode reduzir o conjunto elegível, só mantê-lo ou
ampliá-lo).

**Acceptance Scenarios**:

1. **Given** os 34 pares de `UNIVERSO_AMPLO`, **When**
   `run_pairs_scan(pares=UNIVERSO_AMPLO)` roda com os mesmos
   `PairsParams` (formação 500) de spec 039, **Then** produz resultado
   de treino e validação comparável em estrutura ao já publicado.
2. **Given** o resultado amplo, **When** comparado ao já publicado (12
   pares, 6 trades na validação), **Then** os dois aparecem lado a
   lado no registro — nunca um substitui o outro.
3. **Given** `total_trades` da validação, **When** atinge
   `EDGE_MIN_TRADES` (10), **Then** o veredito de `evaluate_approval()`
   deixa de ser bloqueado por amostra insuficiente — resolve para
   aprovado ou reprovado de verdade, não mais inconclusivo por fome de
   dados.

---

### Edge Cases

- Se o universo amplo ainda não atingir `EDGE_MIN_TRADES`: resultado
  ainda inconclusivo, mas por um motivo diferente (universo já não é
  mais candidato a culpado) — reduz o espaço de hipóteses restantes
  para explicar a amostra pequena.
- Pares de `UNIVERSO_AMPLO` sem histórico suficiente (mesma checagem já
  existente de `fetch_ohlcv`/`requested_candles`): tratados como já
  previsto pelo código existente, sem mudança de comportamento.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST chamar
  `run_pairs_scan(pares=UNIVERSO_AMPLO_HISTORICO_COMPLETO)` — o
  subconjunto de `UNIVERSO_AMPLO` com histórico completo (D1,
  `research.md`) — nenhum parâmetro novo, nenhuma mecânica nova além
  do filtro mecânico já declarado.
- **FR-002**: O sistema MUST manter `PairsParams` (formação 500,
  `meia_vida_min`/`max`, `adf_alpha`, `max_pares`, `entrada_z`,
  `saida_z`, `stop_z`) idênticos aos já declarados em spec 039 — só o
  universo candidato muda.
- **FR-003**: O sistema MUST reportar o resultado ao lado do já
  publicado (12 pares, spec 039) — nunca substituindo.
- **FR-004**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/`.

### Key Entities

- Nenhuma entidade nova.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um resultado de treino/validação de H10 sobre
  `UNIVERSO_AMPLO` é produzido, comparável ao já publicado.
- **SC-002**: O veredito de `evaluate_approval()` é registrado — se
  resolve a inconclusão por amostra ou não.
- **SC-003**: Nenhuma ordem real é enviada; produção permanece
  idêntica.

---

## Assumptions

- **`UNIVERSO_AMPLO`**: já medido e validado (liquidez, spec 040) —
  reusado sem remedição.
- **Formação, parâmetros de entrada/saída/stop, critério de aprovação**:
  já declarados em spec 039 — reusados sem alteração.
- Reprovação, aprovação ou inconclusão por outro motivo desta spec não
  invalida o veredito já publicado de H10 (spec 039) — é a mesma
  pergunta, com um universo candidato maior.
