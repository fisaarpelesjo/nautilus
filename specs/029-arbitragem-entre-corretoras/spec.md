# Feature Specification: H15 — Arbitragem entre corretoras

**Feature Branch**: `029-arbitragem-entre-corretoras`

**Created**: 2026-09-01

**Status**: Draft

**Input**: User description: H15 — Arbitragem entre corretoras. Décima sexta hipótese avaliada; primeira da família relativa e não-preditiva.

---

## Contexto e tese

**Tese.** O mesmo ativo é negociado simultaneamente em várias corretoras a
preços diferentes. Comprar onde está barato e vender onde está caro não exige
prever nada — o diferencial é **observável no instante da decisão**.

**Procedência.** H14 e H20 mediram, por caminhos independentes, que a componente
previsível do movimento é aproximadamente igual ao obstáculo econômico e muda
junto com ele. Isso esgotou as duas frentes direcionais que §6.3-b identificou.
H15 é a primeira hipótese da família **relativa e não-preditiva** — a única que
o registro ainda não testou.

---

## Esta hipótese não pode ser retrotestada

**É a diferença estrutural entre H15 e todas as quinze anteriores, e ela define
a spec.**

Corretoras não publicam histórico de livro de ofertas. As quinze hipóteses
anteriores foram avaliadas sobre candles históricos; aqui não existe equivalente.
O diferencial entre corretoras num instante passado é **irrecuperável**.

Consequência: H15 exige uma **campanha de amostragem** — observar o presente
repetidamente ao longo do tempo — e um veredito exige amostra que uma única
execução não produz. Uma spec que ignorasse isso entregaria um instantâneo
vestido de evidência.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir o diferencial líquido, não o aparente (Priority: P1)

O pesquisador obtém, por par e por combinação de corretoras, o diferencial entre
o melhor preço de compra numa e o melhor de venda noutra — **descontados os
custos de execução dos dois lados** e medido sobre profundidade real, não sobre
o topo do livro.

**Why this priority**: é a pergunta da hipótese. O diferencial bruto é sempre
positivo em algum par de corretoras a qualquer instante; o líquido é o que
existe ou não.

**Independent Test**: executar o comando e obter o diferencial bruto, o custo
total e o líquido, com o volume ao qual ele se aplica.

**Acceptance Scenarios**:

1. **Given** duas corretoras com o mesmo par, **When** a medição roda, **Then**
   reporta diferencial bruto, custo dos dois lados, diferencial líquido e o
   volume executável a esse preço.
2. **Given** um livro raso, **When** o volume pretendido excede a profundidade
   disponível, **Then** o diferencial reportado reflete o preço médio de
   execução, não o topo.
3. **Given** uma corretora indisponível, **When** as demais são consultadas,
   **Then** a medição continua e a combinação aparece com estado próprio.

---

### User Story 2 - Não comparar moedas de cotação diferentes (Priority: P1)

Comparações só ocorrem entre pares com a **mesma moeda de cotação**, e a
restrição aparece no relatório.

**Why this priority**: comparar `BTC/USDT` numa corretora com `BTC/USD` noutra
mistura o diferencial de arbitragem com o **desvio da paridade** USDT/USD. Uma
observação preliminar já mostrou o efeito: entre `BTC/USDT` da Binance e
`BTC/USD` da Coinbase o diferencial aparente foi de 0,104%, contra 0,037% entre
pares de mesma cotação. A maior parte do "diferencial" era a paridade.

**Why P1**: sem esta restrição, o número medido é maior e não é arbitragem —
exatamente o tipo de falso positivo que o registro documenta em M7, M10, M11 e
M13.

**Independent Test**: uma comparação entre cotações diferentes é recusada, com
motivo explícito.

**Acceptance Scenarios**:

1. **Given** dois pares com cotações diferentes, **When** a comparação é
   tentada, **Then** é recusada com motivo, nunca silenciosamente incluída.
2. **Given** o relatório, **When** gerado, **Then** declara quais moedas de
   cotação participaram.

---

### User Story 3 - Tratar latência como obstáculo de primeira ordem (Priority: P1)

O relatório apresenta o tempo entre a primeira e a última leitura de cada
comparação, e o diferencial é qualificado por esse tempo.

**Why this priority**: medição registrou latência **quente** de 272 a 1.082 ms
por consulta de livro, mediana **342 ms**. Uma arbitragem exige duas leituras e
duas ordens — cerca de **1,4 s** no melhor caso. Um diferencial de topo de livro
que persiste tanto tempo não é oportunidade; é sinal de que algo mais está
errado, como retirada suspensa ou liquidez fantasma.

> **Correção declarada.** A primeira redação desta spec citava 2,0 a 6,1
> segundos. Aquele número incluía `load_markets()` e conexão fria, e um processo
> de arbitragem mantém as conexões abertas. A correção enfraquece este argumento
> em uma ordem de grandeza; ele sobrevive, mas por menos. Ver `research.md`.

Reportar diferencial sem reportar o tempo em que ele foi observado descreveria
uma oportunidade que ninguém poderia executar.

**Independent Test**: toda comparação reporta o intervalo temporal entre as
leituras que a compõem.

**Acceptance Scenarios**:

1. **Given** uma comparação, **When** reportada, **Then** inclui o intervalo
   entre a primeira e a última leitura.
2. **Given** um intervalo acima de um teto declarado, **When** classificada,
   **Then** a comparação recebe estado próprio, distinto de oportunidade.

---

### User Story 4 - Acumular amostra ao longo do tempo (Priority: P2)

As medições são persistidas, de modo que execuções sucessivas construam a
amostra que um veredito exige.

**Why this priority**: sem persistência, cada execução é um instantâneo e a
hipótese permanece permanentemente inconclusiva. Com ela, o veredito passa a ser
questão de tempo decorrido, não de método.

**Independent Test**: duas execuções sucessivas produzem um conjunto acumulado
maior que qualquer uma isolada.

**Acceptance Scenarios**:

1. **Given** execuções sucessivas, **When** a segunda roda, **Then** as
   observações da primeira permanecem.
2. **Given** o conjunto acumulado, **When** o relatório é gerado, **Then**
   declara o período coberto e o número de observações.

---

### Edge Cases

- **Livro raso.** Profundidade insuficiente para o volume pretendido: o preço
  médio de execução degrada e o diferencial líquido pode virar negativo.
- **Diferencial persistente e grande.** Suspeito, não promissor: normalmente
  indica retirada suspensa, par deslistado ou liquidez que não se realiza.
- **Corretora com taxa desconhecida.** Custo desconhecido nunca vira zero. A
  combinação é reportada com estado próprio.
- **Relógios dessincronizados.** O intervalo entre leituras é medido localmente,
  no mesmo relógio, para não depender do horário reportado por cada corretora.
- **Amostra de uma única execução.** Inconclusiva por construção.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST medir o diferencial entre corretoras usando o livro
  de ofertas, e MUST calcular o preço médio de execução para um volume
  declarado, nunca apenas o topo do livro.
- **FR-002**: O sistema MUST descontar os custos de execução dos **dois** lados
  ao reportar o diferencial líquido.
- **FR-003**: O sistema MUST NOT comparar pares com moedas de cotação
  diferentes, e MUST declarar quais participaram.
- **FR-004**: O sistema MUST reportar o intervalo temporal entre as leituras que
  compõem cada comparação.
- **FR-005**: Comparação cujo intervalo exceda um teto declarado MUST receber
  estado próprio, distinto de oportunidade.
- **FR-006**: Custo desconhecido para alguma corretora MUST produzir estado
  explícito, e MUST NOT ser tratado como zero.
- **FR-007**: Profundidade insuficiente para o volume declarado MUST ser
  reportada, e o diferencial MUST refletir a degradação.
- **FR-008**: O sistema MUST persistir as observações, de modo que execuções
  sucessivas acumulem amostra.
- **FR-009**: O relatório MUST declarar o período coberto e o número de
  observações acumuladas.
- **FR-010**: Amostra insuficiente MUST produzir resultado inconclusivo, com o
  número declarado — nunca reprovação.
- **FR-011**: Falha ao consultar uma corretora MUST NOT abortar a medição.
- **FR-012**: O sistema MUST NOT enviar ordem alguma. É medição, não execução.
- **FR-013**: O sistema MUST NOT exigir chave de API — apenas dados públicos.
- **FR-014**: O sistema MUST NOT alterar o comportamento do bot em produção.
- **FR-015**: O sistema MUST registrar, junto ao veredito, se uma eventual
  oportunidade seria executável pela infraestrutura atual, incluindo latência
  medida e a necessidade de capital pré-posicionado.

### Key Entities

- **Leitura de livro**: livro de ofertas de um par numa corretora num instante,
  com o momento local da leitura.
- **Comparação**: duas leituras do mesmo par em corretoras distintas, com
  diferencial bruto, custos dos dois lados, diferencial líquido, volume
  executável e intervalo entre as leituras.
- **Observação acumulada**: comparação persistida, para compor amostra ao longo
  do tempo.
- **Relatório**: comparações da execução mais o agregado histórico, com período
  coberto, número de observações e estado.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O pesquisador obtém o diferencial **líquido** por combinação de
  corretoras, com o volume ao qual ele se aplica.
- **SC-002**: Nenhuma comparação entre moedas de cotação diferentes entra no
  resultado.
- **SC-003**: Toda comparação reporta o intervalo temporal entre suas leituras.
- **SC-004**: Execuções sucessivas acumulam amostra, e o relatório declara o
  período coberto.
- **SC-005**: Amostra insuficiente é reportada como inconclusiva, com o número.
- **SC-006**: Nenhuma ordem é enviada e nenhuma chave de API é exigida.
- **SC-007**: O comportamento do bot em produção permanece idêntico.
- **SC-008**: O veredito é registrado com a declaração de executabilidade,
  incluindo latência medida.

---

## Assumptions

- **O veredito exigirá tempo decorrido, não mais método.** Uma execução isolada
  é inconclusiva por construção. Esta spec entrega o instrumento e a primeira
  medição; o veredito virá quando a amostra existir. Declarar isso agora evita
  que um instantâneo seja lido como evidência.
- **Arbitragem real exige capital pré-posicionado nas duas corretoras.**
  Transferir a cada operação leva minutos a horas, e nenhum diferencial
  sobrevive a isso. A avaliação assume capital em ambos os lados — hipótese
  favorável à hipótese, e declarada como tal.
- **Custos assumidos são os de taxa pública de tomador de liquidez**, sem
  descontos por volume. É o custo que este projeto de fato pagaria.
- **A observação preliminar é desfavorável e está registrada:** entre pares de
  mesma cotação e sobre seis corretoras, o maior diferencial **bruto** observado
  foi de **+0,0203%**, contra um custo mínimo possível de **0,200%** — uma ordem
  de grandeza de diferença. Um único instantâneo não é evidência, mas registrá-lo
  antes impede que o resultado seja apresentado como surpresa depois, e reformula
  o que a campanha precisa encontrar: não um diferencial ligeiramente acima do
  custo, mas um **dez vezes maior** que o observado.
- **O conjunto de corretoras é declarado e pequeno**, escolhido por acessibilidade
  pública e liquidez, não por diferencial observado.
