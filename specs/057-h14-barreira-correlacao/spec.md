# Feature Specification: H14 — saída por barreira tripla + gate de correlação

**Feature Branch**: `057-h14-barreira-correlacao`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: Os dois melhores mecanismos medidos
isoladamente na linha de investigação de H14 — saída por barreira
tripla (melhor profit factor de toda a linha, 0,78, spec 056) e gate de
correlação (melhor drawdown isolado entre os mecanismos de risco,
20,74%, spec 042) — nunca foram testados juntos. Testar a combinação.

---

## Contexto e tese

**Por que esta combinação é diferente das anteriores.** Duas
combinações de dois mecanismos já foram medidas (spec 043:
dimensionamento+correlação; spec 046: correlação+limite diário), e nas
duas o gate de correlação dominou quase inteiramente — `total_trades`
do combinado ficou praticamente idêntico ao do gate sozinho, porque os
outros dois mecanismos só **ajustam ou filtram a mesma decisão de
entrada** que o gate já filtra (tamanho da posição, pausa temporal) —
nunca mudam **como uma posição já aberta sai**. Saída por barreira ataca
uma dimensão categoricamente diferente: não decide QUANDO/QUANTO abrir,
decide COMO fechar uma posição já aberta. As duas dominações anteriores
não são evidência de que esta combinação também vai colapsar num dos
dois — é evidência de um padrão específico (mecanismos que competem pela
mesma decisão de entrada) que não se aplica aqui.

**Hipótese declarada antes de medir.** Os dois efeitos são
**genuinamente aditivos** (ou próximos disso): o gate de correlação
reduz `total_trades` (menos entradas simultâneas correlacionadas), a
saída por barreira muda o resultado de CADA trade que abre (melhor
profit factor por trade). Como operam em pontos diferentes do ciclo de
vida da posição (entrada vs. saída), a expectativa é que o drawdown
combinado fique **abaixo** dos dois isolados (22,25% e 20,74%) — não
igual a um deles, como aconteceu nas duas combinações anteriores.

**Hipótese alternativa, com igual peso.** Se o profit factor observado
sob barreira (0,78) já reflete majoritariamente os trades que sobrariam
de qualquer forma sob o gate de correlação (sobreposição de amostra
entre os dois filtros), o resultado combinado fica perto de um dos dois
isolados, repetindo o padrão de dominância das specs 043/046 — refutando
a expectativa de aditividade.

**Zero mecânica nova.** Os dois parâmetros já existem
(`usar_saida_barreira`, spec 056; `usar_gate_correlacao`, spec 042),
já testados isoladamente. Esta spec só liga os dois ao mesmo tempo.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir o efeito combinado (Priority: P1)

O pesquisador obtém drawdown agregado, `total_trades` e profit factor
de carteira de H14 com saída por barreira e gate de correlação ligados
ao mesmo tempo, comparado contra os dois isolados e o baseline sem
overlay.

**Why this priority**: é a pergunta da hipótese — aditividade ou
dominância.

**Independent Test**: `_simular_carteira_core` com as duas flags `True`
sobre um cenário sintético com posição correlacionada não abre a
posição bloqueada, e a posição que abre respeita a mecânica de saída
por barreira (sem trailing) — os dois mecanismos coexistem sem um
sobrescrever o outro.

**Acceptance Scenarios**:

1. **Given** a carteira de H14 sobre `UNIVERSO_H11`, **When**
   `usar_saida_barreira=True` e `usar_gate_correlacao=True` ao mesmo
   tempo, **Then** produz um `BacktestResult` único, sem exceção,
   respeitando os dois mecanismos simultaneamente.
2. **Given** o resultado combinado, **When** comparado aos dois isolados
   e ao baseline, **Then** os quatro números aparecem lado a lado no
   registro — nunca um substitui o outro.
3. **Given** o resultado, **When** registrado, **Then** o registro
   documenta explicitamente se confirma aditividade ou dominância.

---

### Edge Cases

- Nenhum caso novo — os dois mecanismos têm seus próprios casos de
  borda cobertos nas specs 042/056.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST chamar `simular_carteira` com
  `usar_saida_barreira=True` e `usar_gate_correlacao=True`
  simultaneamente — nenhum parâmetro novo, nenhuma mecânica nova.
- **FR-002**: O sistema MUST usar `UNIVERSO_H11` (12 pares), mesmo
  universo de toda a linha de investigação de H14.
- **FR-003**: O sistema MUST reportar o resultado combinado ao lado dos
  já publicados (baseline, spec 056, spec 042) — nunca substituindo.
- **FR-004**: O sistema MUST registrar explicitamente se o resultado
  confirma aditividade (drawdown abaixo dos dois isolados) ou dominância
  (drawdown perto de um dos dois).
- **FR-005**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/`.

### Key Entities

- Nenhuma entidade nova.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `python main.py carteira_barreira_corr` produz um
  `BacktestResult` combinado, comparável aos já publicados.
- **SC-002**: O veredito de `evaluate_approval()` é registrado, sem
  critério novo.
- **SC-003**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Universo, capital, limiares de cada mecanismo**: já declarados em
  specs 037/042/056 — reusados sem alteração.
- Reprovação, aprovação ou inconclusivo desta spec não invalida os
  vereditos já publicados de H14.
- Se o resultado ainda reprovar (mais provável, dado o histórico de
  H14), fecha mais uma combinação, não a linha inteira — a barreira
  também nunca foi testada com dimensionamento nem limite diário.
