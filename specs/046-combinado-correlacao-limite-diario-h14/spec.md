# Feature Specification: Combinação gate de correlação + limite de drawdown diário na carteira de H14

**Feature Branch**: `046-combinado-correlacao-limite-diario-h14`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: Combinar os dois mecanismos que
produziram melhora real e NÃO-DEGENERADA sobre a carteira de H14 — gate
de correlação (spec 042: 28,66% → 20,74%, maior redução isolada,
595 trades) e limite de drawdown diário (spec 045: 28,66% → 22,17%,
melhor profit factor isolado — 0,75, 762 trades). Diferente da
combinação já testada em spec 043 (dimensionamento + correlação, que
quase não somou porque o dimensionamento não muda quais trades abrem),
estes dois operam em dimensões ortogonais de verdade — o gate filtra
por **sobreposição espacial** entre pares no instante da entrada, o
limite diário pausa por **trajetória temporal** do patrimônio da
carteira inteira. Ambos já existem como parâmetros independentes de
`_simular_carteira_core`/`simular_carteira`
(`usar_gate_correlacao`, `usar_limite_drawdown_diario`); esta spec não
adiciona mecânica nova, só mede o efeito combinado e registra.

---

## Contexto e tese

**Por que esta combinação, e não outra.** Das cinco combinações
possíveis de overlay isolado medidas até aqui (dimensionamento,
correlação, circuit breaker, limite diário — spec 043 já testou
dimensionamento+correlação), só duas produziram melhora real
não-degenerada quando isoladas: correlação (maior redução de drawdown)
e limite diário (melhor profit factor, e o único que melhorou o PF em
vez de piorá-lo). O circuit breaker foi descartado desta combinação por
ser degenerado isolado (spec 044, colapsa a amostra) — combiná-lo só
pioraria o mesmo problema. O dimensionamento já foi testado com
correlação (spec 043) e mostrou sobreposição quase total de efeito —
testar de novo com o limite diário no lugar é a pergunta em aberto.

**Por que a sobreposição pode ser menor que em spec 043.** O
dimensionamento por volatilidade e o gate de correlação atacam a MESMA
decisão (que candidato abre, e com que tamanho) no MESMO instante —
por isso a sobreposição de efeito foi quase total. O limite diário
opera numa dimensão diferente: decide se a carteira inteira pode abrir
qualquer coisa NAQUELE DIA, independente de qual par ou de correlação
entre pares. Não há garantia de que os efeitos se somem linearmente,
mas a hipótese de sobreposição parcial (não quase-total, como em spec
043) é mais defensável aqui — mecanismos ortogonais tendem a somar
mais do que mecanismos que competem pela mesma decisão.

**Zero mecânica nova.** Os dois parâmetros já existem
(`usar_gate_correlacao` desde spec 042, `usar_limite_drawdown_diario`
desde spec 045), já testados isoladamente, já com regressão confirmando
que cada um não interfere no caminho default do outro. Esta spec liga
os dois ao mesmo tempo — nenhuma linha de mecânica de carteira nova.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir a carteira de H14 com os dois mecanismos ligados (Priority: P1)

O pesquisador obtém o drawdown agregado, `total_trades` e profit factor
de carteira de H14 com o gate de correlação E o limite de drawdown
diário ligados ao mesmo tempo, comparado contra os seis resultados já
publicados.

**Why this priority**: é a pergunta da hipótese — sem o comparativo,
não há como saber se a combinação supera o melhor resultado isolado
(correlação, 20,74% de drawdown) ou soma parcialmente os dois efeitos
(mais próximo do que spec 043 mostrou para dimensionamento+correlação).

**Independent Test**: rodar `_simular_carteira_core` com as duas flags
`True` sobre um cenário sintético e confirmar que nenhuma entrada viola
nenhum dos dois invariantes já testados isoladamente (nenhuma entrada
correlacionada com posição já aberta; nenhuma entrada durante um dia
com patrimônio abaixo do limite).

**Acceptance Scenarios**:

1. **Given** a carteira de H14 sobre `UNIVERSO_H11` (12 pares, mesmo
   universo dos seis resultados já publicados), **When**
   `usar_gate_correlacao=True` e `usar_limite_drawdown_diario=True` ao
   mesmo tempo, **Then** produz um `BacktestResult` único, sem exceção,
   respeitando os dois mecanismos simultaneamente.
2. **Given** o resultado combinado, **When** comparado aos seis já
   publicados, **Then** os sete números aparecem lado a lado no
   registro — nunca um substitui o outro.

---

### Edge Cases

- Nenhum caso novo — os dois mecanismos já têm seus próprios casos de
  borda cobertos (spec 042: sem posições abertas, amostra insuficiente;
  spec 045: primeiro candle da série, série inteira dentro do limite).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST chamar `simular_carteira` com
  `usar_gate_correlacao=True` e `usar_limite_drawdown_diario=True`
  simultaneamente — nenhum parâmetro novo, nenhuma mecânica nova.
- **FR-002**: O sistema MUST usar `UNIVERSO_H11` (12 pares), o mesmo
  dos seis resultados já publicados.
- **FR-003**: O sistema MUST reportar o resultado combinado ao lado dos
  seis já publicados — nunca substituindo nenhum deles no registro.
- **FR-004**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/`.

### Key Entities

- Nenhuma entidade nova.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um `BacktestResult` de carteira com os dois mecanismos
  ligados é produzido, comparável em unidade e período aos seis já
  publicados.
- **SC-002**: O veredito de `evaluate_approval()` sobre o resultado
  combinado é registrado, sem critério novo.
- **SC-003**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Universo, capital, mecanismo de saída, limiares de correlação,
  limite diário**: todos já declarados em specs 037/042/045 — reusados
  sem alteração.
- Reprovação, aprovação ou resultado ainda inconclusivo desta spec não
  invalida os vereditos já publicados de H14 — é a mesma pergunta
  (drawdown de carteira), com uma combinação nova de dois mecanismos já
  individualmente medidos.
