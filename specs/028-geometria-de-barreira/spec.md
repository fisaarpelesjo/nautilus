# Feature Specification: H20 — Geometria de barreira

**Feature Branch**: `028-geometria-de-barreira`

**Created**: 2026-09-01

**Status**: Draft

**Input**: User description: H20 — Geometria de barreira. Décima quinta hipótese avaliada, derivada diretamente do resultado de H14.

---

## Contexto e tese

**A hipótese nasceu de um resultado, não da literatura.** H14 mediu que um
classificador eleva a razão de chances alvo/stop de 0,3896 para 0,5134 no
subconjunto em que decide entrar — sinal robusto, `z = +5,21`, `p < 0,0001`. E
mediu que isso **não paga as barreiras**: o ponto de empate imposto pela
geometria `stop 1,5×ATR / alvo 3,0×ATR` é 0,500, e 0,5134 não se distingue dele
(`z = +0,50`, `p = 0,318`).

**Tese.** O ponto de empate é `stop / alvo` — uma razão **escolhida**, não dada
pelo mercado. Uma geometria com alvo mais distante em relação ao stop baixa o
ponto de empate, e pode caber dentro do sinal que H14 já demonstrou existir.

**E a razão pela qual isso pode não funcionar precisa estar dita desde já.**
Mudar a geometria muda os **rótulos**: um alvo mais distante é atingido menos
vezes, então a razão de chances observada **também cai**. Se ela cair mais
rápido que o ponto de empate, a margem piora em vez de melhorar. Não se trata de
substituir 0,500 por um número menor num resultado já obtido — é uma avaliação
inteiramente nova, e pode sair pior que H14.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir como a margem responde à geometria (Priority: P1)

O pesquisador obtém, para um conjunto de geometrias, a razão de chances **da
própria série** (sem modelo algum) contra o ponto de empate de cada uma — e
portanto a margem que cada geometria oferece antes de qualquer capacidade
preditiva.

**Why this priority**: é a medição que decide se a hipótese tem base. Se a razão
de chances cair tão rápido quanto o ponto de empate, a geometria não é uma
alavanca e H20 se encerra sem precisar treinar nada.

**Independent Test**: executar o comando e obter, por geometria, a razão de
chances observada, o ponto de empate e a margem entre os dois.

**Acceptance Scenarios**:

1. **Given** um conjunto de geometrias, **When** a medição roda, **Then** cada
   uma reporta razão de chances, ponto de empate, margem e número de eventos.
2. **Given** uma geometria em que a razão não pode ser calculada por ausência de
   stops, **When** o relatório é gerado, **Then** ela aparece com estado próprio,
   não com um número enganoso.

---

### User Story 2 - Escolher a geometria por regra declarada, não por resultado (Priority: P1)

A geometria levada à avaliação é escolhida por uma **regra escrita antes da
medição**, e a regra aparece no relatório junto do resultado.

**Why this priority**: sem isso, H20 é varredura. Testar geometrias até uma
passar é precisamente o problema de testes múltiplos que a metodologia contém —
e o registro já quantificou o risco em H13, onde 96 combinações produziram uma
aprovação, abaixo da expectativa do acaso.

**Why P1 e não refinamento**: a diferença entre esta spec e uma varredura
disfarçada é inteiramente esta história. Sem ela, o resultado não entra no
registro.

**Independent Test**: a geometria selecionada é reproduzível a partir da regra e
dos dados, sem consultar nenhum resultado de modelo.

**Acceptance Scenarios**:

1. **Given** a regra declarada e as medições, **When** a seleção roda, **Then**
   devolve uma única geometria, e a mesma geometria em execuções repetidas.
2. **Given** a seleção, **When** ela é feita, **Then** nenhuma métrica de
   desempenho de modelo participa — apenas propriedades da série e a elevação
   já medida em H14.
3. **Given** nenhuma geometria satisfazendo a regra, **When** a seleção roda,
   **Then** o resultado é que a hipótese não tem candidata — desfecho legítimo,
   não erro.

---

### User Story 3 - Avaliar a geometria escolhida com o mesmo rigor de H14 (Priority: P1)

A geometria selecionada passa pela avaliação de H14 sem alteração: rotulagem
causal, purga e embargo globais, modelo de rótulos embaralhados, desconto de
exposição, confirmação fora da amostra e banda de incerteza no limiar.

**Why this priority**: o valor de H20 depende inteiramente de a avaliação ser a
mesma. Uma geometria nova avaliada com régua nova não seria comparável a H14, e
o registro perderia a capacidade de dizer se algo mudou.

**Independent Test**: a avaliação produz os mesmos estados de H14 e a
comparação com o resultado de H14 é direta.

**Acceptance Scenarios**:

1. **Given** a geometria escolhida, **When** avaliada, **Then** o resultado usa
   os mesmos estados, guardas e limiares de H14.
2. **Given** o resultado, **When** comparado a H14, **Then** o relatório mostra
   as duas geometrias lado a lado, com a razão de chances e o ponto de empate de
   cada.
3. **Given** uma razão de chances acima do ponto de empate, **When**
   classificada, **Then** a superação exige a banda de incerteza, não a
   estimativa pontual.

---

### Edge Cases

- **A elevação medida em H14 não transfere.** O `+31,8%` foi medido numa
  geometria; noutra o modelo é retreinado sobre rótulos diferentes e a elevação
  pode ser outra. O relatório precisa mostrar a elevação **observada na nova
  geometria**, não a herdada.
- **Alvo muito distante esvazia a classe positiva.** Se quase nenhum evento
  atinge o alvo, a estimação perde a classe e o resultado é `classe_unica`.
- **Alvo muito distante estoura o limite de tempo.** Mais eventos terminam por
  tempo, o que não é alvo nem stop — a razão de chances passa a descrever uma
  fração menor dos eventos, e isso precisa aparecer.
- **Stop muito próximo aumenta o giro.** Mais operações, mais custo. E6 precisa
  separar.
- **Nenhuma geometria satisfaz a regra.** Desfecho legítimo: a hipótese não tem
  candidata e se encerra sem avaliação de modelo.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST medir, para cada geometria de um conjunto
  declarado, a razão de chances observada na série, o ponto de empate imposto
  pela geometria, e a margem entre os dois.
- **FR-002**: A medição de FR-001 MUST usar apenas a rotulagem, sem treinar
  modelo algum.
- **FR-003**: O sistema MUST selecionar a geometria levada à avaliação por uma
  **regra declarada antes da medição**, e MUST exibir a regra no relatório.
- **FR-004**: A regra de seleção MUST NOT consultar qualquer métrica de
  desempenho de modelo.
- **FR-005**: A seleção MUST ser determinística: as mesmas entradas produzem a
  mesma geometria.
- **FR-006**: Se nenhuma geometria satisfizer a regra, o sistema MUST reportar
  ausência de candidata como desfecho, e MUST NOT relaxar a regra.
- **FR-007**: A avaliação da geometria selecionada MUST reusar, sem alteração, a
  rotulagem causal, a purga e o embargo globais, o modelo de rótulos
  embaralhados, o desconto de exposição, a confirmação fora da amostra e a banda
  de incerteza no limiar.
- **FR-008**: O sistema MUST reportar a elevação da razão de chances **observada
  na geometria avaliada**, e MUST NOT reutilizar a elevação medida noutra.
- **FR-009**: O sistema MUST reportar a fração de eventos que termina por limite
  de tempo, por geometria — a razão de chances descreve apenas os eventos que
  tocam alvo ou stop.
- **FR-010**: O relatório MUST apresentar a geometria avaliada e a geometria de
  referência lado a lado.
- **FR-011**: Avaliação com amostra abaixo do mínimo, classe única ou falha de
  convergência MUST produzir estado próprio, nunca reprovação.
- **FR-012**: O sistema MUST NOT alterar o comportamento do bot em produção.
- **FR-013**: O sistema MUST NOT adicionar dependência.
- **FR-014**: O sistema MUST NOT avaliar mais de uma geometria com modelo. A
  medição sem modelo cobre o conjunto; a avaliação cobre **uma**.

### Key Entities

- **Geometria**: um par de distâncias — stop e alvo, em múltiplos da medida de
  volatilidade — mais o limite de tempo. Determina os rótulos e o ponto de
  empate.
- **Perfil de geometria**: o resultado da medição sem modelo para uma geometria:
  razão de chances observada, ponto de empate, margem, distribuição das três
  classes e número de eventos.
- **Regra de seleção**: critério declarado que mapeia o conjunto de perfis a uma
  única geometria, ou a nenhuma.
- **Comparação de geometrias**: a geometria avaliada e a de referência, com
  razão de chances, ponto de empate, elevação observada e estado de cada uma.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O pesquisador obtém, numa única execução, como a margem entre
  razão de chances e ponto de empate responde à geometria, sem treinar modelo.
- **SC-002**: A geometria avaliada é reproduzível a partir da regra declarada e
  dos dados, sem consultar resultado de modelo.
- **SC-003**: Exatamente uma geometria é submetida à avaliação com modelo.
- **SC-004**: A avaliação usa as mesmas guardas e limiares de H14, permitindo
  comparação direta.
- **SC-005**: A elevação reportada é a observada na geometria avaliada.
- **SC-006**: Nenhuma geometria satisfazendo a regra é reportado como desfecho,
  não como falha.
- **SC-007**: O comportamento do bot em produção permanece idêntico.
- **SC-008**: Nenhuma dependência nova é adicionada.
- **SC-009**: O veredito de H20 é registrado com evidência e com a comparação
  explícita contra H14.

---

## Assumptions

- **A regra de seleção é o cerne desta spec, e sua formulação fica para a fase
  de pesquisa** — com a restrição, declarada aqui, de que ela só pode usar
  propriedades da série e a elevação já medida em H14, nunca desempenho de um
  modelo treinado na geometria candidata.
- **A elevação de H14 pode não transferir.** Ela é usada apenas para *formular*
  a regra de seleção; a elevação que conta no veredito é a medida na geometria
  avaliada.
- **O conjunto de geometrias candidatas é declarado e pequeno**, e existe apenas
  para a medição sem modelo. Ampliá-lo não muda o risco de testes múltiplos na
  avaliação, porque só uma geometria é avaliada com modelo.
- **Universo, período e estratégia de referência são os mesmos de H14**, para
  comparabilidade.
- **A medida de volatilidade continua a mesma** que o sistema já usa para stop e
  alvo. Introduzir outra criaria duas definições concorrentes.
- **Uma aprovação herdaria as ressalvas de H14**: ausência de mecanismo de
  retreino e de detecção de degradação.
