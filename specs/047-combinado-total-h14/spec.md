# Feature Specification: Combinação total (teto) dos mecanismos de risco não-degenerados na carteira de H14

**Feature Branch**: `047-combinado-total-h14`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: Combinar os três mecanismos de risco
não-degenerados já testados sobre a carteira de H14 —
dimensionamento por volatilidade (spec 041), gate de correlação
(spec 042) e limite de drawdown diário (spec 045) — ligados ao mesmo
tempo. Exclui o circuit breaker de perdas consecutivas (spec 044,
degenerado: colapsou a amostra para 6 trades). Duas combinações de
pares já foram medidas (spec 043: dimensionamento+correlação, quase
sem soma; spec 046: correlação+diário, quase sem soma, o gate domina
nos dois casos) — esta spec mede o teto: os três juntos, a melhor
combinação possível dentro desta família de mecanismos, para decidir se
vale a pena continuar testando permutações desta família ou se a fronteira já foi encontrada.

---

## Contexto e tese

**Por que testar o teto agora, em vez de mais pares.** Duas combinações
de dois mecanismos já foram medidas, e nas duas o gate de correlação
dominou quase inteiramente — o mecanismo adicional (dimensionamento em
spec 043, limite diário em spec 046) contribuiu uma redução marginal de
drawdown (~1,5-2% relativo) sobre o gate sozinho, nunca somando os
efeitos como se fossem independentes. O padrão já apareceu duas vezes
com dois mecanismos diferentes — a hipótese mais defensável agora não é
"talvez o TERCEIRO par funcione melhor", é "o teto desta família inteira
está próximo do que o gate de correlação sozinho já entrega". Medir os
três juntos testa essa hipótese diretamente: se o resultado também
ficar perto de 20-21% de drawdown, fecha a família com uma medição
decisiva (não mais uma suposição) em vez de continuar testando pares
adicionais que a evidência já sugere que vão repetir o mesmo padrão.

**Não é uma hipótese nova sobre o mecanismo — é uma medição de
fronteira.** Não introduz raciocínio novo sobre por que os três juntos
deveriam funcionar melhor; é o oposto — a expectativa declarada, com
base em spec 043 e spec 046, é que o resultado fique próximo do gate de
correlação sozinho (20,74% de drawdown), não uma melhora aditiva sobre
os três (o que somaria para muito abaixo de 20%, algo que a evidência
já tornou improvável).

**Zero mecânica nova.** Os três parâmetros já existem
(`usar_dimensionamento_vol`, `usar_gate_correlacao`,
`usar_limite_drawdown_diario`), já testados isoladamente e em pares.
Esta spec liga os três ao mesmo tempo — nenhuma linha de mecânica de
carteira nova.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir o teto dos três mecanismos ligados (Priority: P1)

O pesquisador obtém o drawdown agregado, `total_trades` e profit factor
de carteira de H14 com dimensionamento, correlação e limite diário
ligados ao mesmo tempo, comparado contra os sete resultados já
publicados.

**Why this priority**: é a pergunta da hipótese — confirma ou refuta se
o gate de correlação sozinho já representa o teto prático desta família
de mecanismos de risco.

**Independent Test**: rodar `_simular_carteira_core` com as três flags
`True` sobre um cenário sintético e confirmar que nenhuma entrada viola
nenhum dos três invariantes já testados isoladamente.

**Acceptance Scenarios**:

1. **Given** a carteira de H14 sobre `UNIVERSO_H11` (12 pares), **When**
   `usar_dimensionamento_vol=True`, `usar_gate_correlacao=True` e
   `usar_limite_drawdown_diario=True` ao mesmo tempo, **Then** produz um
   `BacktestResult` único, sem exceção, respeitando os três mecanismos
   simultaneamente.
2. **Given** o resultado combinado, **When** comparado aos sete já
   publicados, **Then** os oito números aparecem lado a lado no
   registro — nunca um substitui o outro.

---

### Edge Cases

- Nenhum caso novo — os três mecanismos já têm seus próprios casos de
  borda cobertos nas specs 041/042/045.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST chamar `simular_carteira` com
  `usar_dimensionamento_vol=True`, `usar_gate_correlacao=True` e
  `usar_limite_drawdown_diario=True` simultaneamente — nenhum parâmetro
  novo, nenhuma mecânica nova.
- **FR-002**: O sistema MUST usar `UNIVERSO_H11` (12 pares).
- **FR-003**: O sistema MUST reportar o resultado combinado ao lado dos
  sete já publicados — nunca substituindo nenhum deles no registro.
- **FR-004**: O sistema MUST registrar explicitamente se o resultado
  confirma ou refuta a expectativa declarada (próximo do gate de
  correlação sozinho, não uma soma aditiva dos três).
- **FR-005**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/`.

### Key Entities

- Nenhuma entidade nova.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um `BacktestResult` de carteira com os três mecanismos
  ligados é produzido, comparável aos sete já publicados.
- **SC-002**: O veredito de `evaluate_approval()` sobre o resultado
  combinado é registrado, sem critério novo.
- **SC-003**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Universo, capital, mecanismo de saída, limiares de cada mecanismo**:
  já declarados em specs 037/041/042/045 — reusados sem alteração.
- Reprovação, aprovação ou resultado ainda inconclusivo desta spec não
  invalida os vereditos já publicados de H14.
- Se o resultado confirmar a expectativa (próximo do gate sozinho), esta
  spec fecha a linha de investigação de overlays de risco sobre a mesma
  decisão de entrada — próximos passos, se houver, atacam outra parte
  do mecanismo (classificador de entrada ou saída), não mais
  combinações desta família.
