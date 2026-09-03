# Feature Specification: H31 — viabilidade de dados alternativos (sentimento social/notícia)

**Feature Branch**: `068-h31-dados-alternativos-sentimento`

**Created**: 2026-09-03

**Status**: Concluída (viabilidade negativa)

**Input**: User description: H31 propõe sentimento agregado (Google
Trends via `pytrends`, ou atividade de desenvolvimento via API do
GitHub) como atributo de entrada, categoria de dado nunca tocada neste
registro. A entrada da fila exige explicitamente uma checagem de
viabilidade de fonte de dado ANTES de qualquer medição de hipótese —
mesmo princípio que já vetou H16/H19 por infraestrutura, aqui a
barreira é dado, não execução.

---

## Contexto e tese

**Esta spec não testa a hipótese H31 — testa se ela é testável.** A
pergunta de pesquisa não é "sentimento social prediz retorno", é
"existe uma fonte de dado gratuita, com histórico e granularidade
suficientes, para sequer tentar responder essa pergunta com o mesmo
rigor das outras 30 hipóteses deste registro". Uma resposta negativa
aqui é um resultado completo, não um bloqueio a contornar.

**Barra de viabilidade, declarada antes de testar:** para ser
utilizável no mesmo padrão de H14/H17 (colinearidade contra os 5
atributos existentes, pooled sobre `UNIVERSO_H11`), a fonte precisa
entregar (a) histórico comparável ao resto do registro (idealmente
próximo dos ~2,7 anos / 6.000 candles de 4h que H14/H17/H8 usam,
nunca menos que o piso mínimo de amostra que `avaliar_par` já exige),
(b) granularidade que não force um forward-fill grosseiro demais sobre
candles de 4h, e (c) confiabilidade suficiente para uma campanha real
de múltiplos pares sem infraestrutura paga.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Determinar se alguma fonte gratuita de sentimento é utilizável (Priority: P1)

O pesquisador testa, com chamadas reais (não suposição), as duas fontes
candidatas citadas na entrada da fila e decide se alguma passa a barra
de viabilidade declarada.

**Why this priority**: é a única pergunta desta spec.

**Independent Test**: cada fonte é testada com uma chamada real contra
a API pública, sem mock — o resultado (viável/não viável) é observável
diretamente na resposta obtida.

**Acceptance Scenarios**:

1. **Given** a API do GitHub (`stats/commit_activity`, sem autenticação),
   **When** consultada para um repositório real, **Then** o histórico e
   a granularidade retornados são comparados contra a barra declarada.
2. **Given** `pytrends` (Google Trends, não-oficial), **When** consultado
   com uma janela de tempo real, **Then** a confiabilidade entre
   chamadas sucessivas (simulando uma campanha de múltiplos pares) é
   medida diretamente, não presumida a partir da documentação do pacote.
3. **Given** o resultado das duas checagens, **When** nenhuma fonte
   passa a barra, **Then** a spec encerra com viabilidade negativa
   documentada — sem construir nenhum pipeline de medição.

---

### Edge Cases

- Nenhum caso de borda de execução — esta spec não chega a produzir
  código de produção/backtest, só o resultado da checagem de dado.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A investigação MUST testar a API do GitHub
  (`stats/commit_activity`) com uma chamada real, sem autenticação, e
  registrar histórico/granularidade/limite de taxa observados.
- **FR-002**: A investigação MUST testar `pytrends` com uma chamada
  real, incluindo pelo menos uma segunda chamada (simulando o padrão de
  campanha multi-par) para medir confiabilidade entre chamadas
  sucessivas — não apenas uma chamada isolada de melhor caso.
- **FR-003**: O sistema MUST NOT instalar nenhuma dependência nova no
  ambiente compartilhado do projeto (`.venv`) só para esta checagem —
  teste isolado, sem afetar outros agentes/desenvolvedores concorrentes.
- **FR-004**: O sistema MUST NOT criar nenhuma conta paga, chave de API
  paga, ou infraestrutura de contorno de rate limit (proxies, etc.)
  para viabilizar uma fonte que falhe sem isso.
- **FR-005**: O resultado (viável ou não) MUST ser registrado em
  `docs/research/registro-de-hipoteses.md` com evidência real, mesmo
  que negativo — mesma disciplina de qualquer outra hipótese do
  registro.

### Key Entities

- Nenhuma entidade de dado nova (a spec não chega a produzir um
  pipeline de dado de produção).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: As duas fontes candidatas são testadas com chamadas
  reais, com números concretos (não estimativas) documentados.
- **SC-002**: O registro documenta explicitamente se alguma fonte é
  viável — e, se não, exatamente por quê (histórico insuficiente,
  granularidade incompatível, ou confiabilidade insuficiente).
- **SC-003**: Nenhuma dependência nova entra no ambiente compartilhado
  do projeto; nenhuma conta ou chave paga é criada.

---

## Assumptions

- Barra de viabilidade (histórico ~2,7 anos, granularidade compatível
  com candles de 4h, confiabilidade para campanha multi-par sem
  infraestrutura paga) declarada a partir do padrão já estabelecido
  por H8/H14/H17 neste registro — não inventada para este teste
  específico.
- Se nenhuma fonte passar, H31 permanece na fila como "viabilidade
  negativa" — não é o mesmo status de uma hipótese REPROVADA (que foi
  medida e não teve efeito); é uma hipótese que não pôde ser medida
  com os recursos gratuitos disponíveis hoje. Pode ser reaberta se uma
  fonte gratuita nova aparecer no futuro.
