# Feature Specification: Combinação dimensionamento por volatilidade + gate de correlação na carteira de H14

**Feature Branch**: `043-combinado-vol-correlacao-h14`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: Combinar os dois mecanismos que já
mostraram melhora real e isolada sobre o drawdown de carteira de H14—
dimensionamento por volatilidade (spec 041: 28,66% → 23,04%) e gate de
correlação (spec 042: 28,66% → 20,74%, a maior redução medida) — ligados
ao mesmo tempo. Ambos já existem como parâmetros independentes de
`_simular_carteira_core`/`simular_carteira`
(`usar_dimensionamento_vol`, `usar_gate_correlacao`); esta spec não
adiciona mecânica nova, só mede o efeito combinado e registra.

---

## Contexto e tese

**Por que combinar, não só somar os números.** Os dois mecanismos atacam
o mesmo problema (drawdown por posições correlacionadas quebrando
juntas) por ângulos diferentes — um reduz o TAMANHO de entradas
arriscadas, o outro BLOQUEIA entradas correlacionadas inteiramente. Não
há garantia de que os efeitos se somem linearmente: o gate de correlação
já impede várias das entradas que o dimensionamento por volatilidade
apenas encolheria, então parte do benefício pode se sobrepor, não somar.
Medir é a única forma de saber.

**Zero mecânica nova.** Os dois parâmetros já existem
(`usar_dimensionamento_vol` desde spec 041, `usar_gate_correlacao`
desde spec 042), já testados isoladamente, já com regressão confirmando
que cada um não interfere no caminho default do outro. Esta spec liga os
dois ao mesmo tempo — nenhuma linha de mecânica de carteira nova.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir a carteira de H14 com os dois mecanismos ligados (Priority: P1)

O pesquisador obtém o drawdown agregado de carteira de H14 com
dimensionamento por volatilidade E gate de correlação ligados ao mesmo
tempo, comparado contra os três resultados já publicados (sem overlay:
28,66%; só volatilidade: 23,04%; só correlação: 20,74%).

**Why this priority**: é a pergunta da hipótese — sem o comparativo
contra os três números já publicados, não há como saber se a combinação
supera o melhor resultado isolado (gate de correlação) ou se os efeitos
se sobrepõem sem ganho adicional.

**Independent Test**: rodar `_simular_carteira_core` com as duas flags
`True` sobre um cenário sintético e confirmar que nenhuma entrada viola
nenhum dos dois invariantes já testados isoladamente (tamanho nunca
maior que sem dimensionamento; nenhuma entrada correlacionada com
posição já aberta).

**Acceptance Scenarios**:

1. **Given** a carteira de H14 sobre `UNIVERSO_H11` (12 pares, mesmo
   universo dos três resultados já publicados), **When**
   `usar_dimensionamento_vol=True` e `usar_gate_correlacao=True` ao
   mesmo tempo, **Then** produz um `BacktestResult` único, sem exceção,
   respeitando os dois mecanismos simultaneamente.
2. **Given** o resultado combinado, **When** comparado aos três já
   publicados, **Then** os quatro números aparecem lado a lado no
   registro — nunca um substitui o outro.

---

### Edge Cases

- Nenhum caso novo — os dois mecanismos já têm seus próprios casos de
  borda cobertos (spec 041: `atr_ratio` ausente/extremo; spec 042: sem
  posições abertas, amostra insuficiente).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST chamar `simular_carteira` com
  `usar_dimensionamento_vol=True` e `usar_gate_correlacao=True`
  simultaneamente — nenhum parâmetro novo, nenhuma mecânica nova.
- **FR-002**: O sistema MUST usar `UNIVERSO_H11` (12 pares), o mesmo dos
  três resultados já publicados — sem escolha nova de universo.
- **FR-003**: O sistema MUST reportar o resultado combinado ao lado dos
  três já publicados (sem overlay, só volatilidade, só correlação) —
  nunca substituindo nenhum deles no registro.
- **FR-004**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/`.

### Key Entities

- Nenhuma entidade nova.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um `BacktestResult` de carteira com os dois mecanismos
  ligados é produzido, comparável em unidade e período aos três já
  publicados.
- **SC-002**: O veredito de `evaluate_approval()` sobre o resultado
  combinado é registrado, sem critério novo.
- **SC-003**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Universo, capital, mecanismo de saída, alvo/piso de volatilidade,
  limiares de correlação**: todos já declarados em spec 037/041/042 —
  reusados sem alteração.
- Reprovação, aprovação ou resultado ainda inconclusivo desta spec não
  invalida os vereditos já publicados de H14 — é a mesma pergunta
  (drawdown de carteira), com uma combinação nova de mecanismos já
  individualmente medidos.
