# Feature Specification: H11 — Momentum em horizonte temporal superior

**Feature Branch**: `024-horizonte-temporal-momentum`

**Created**: 2026-09-01

**Status**: Draft

**Input**: User description: "H11 — Avaliacao de momentum em horizonte temporal superior (diario e semanal). Liu & Tsyvinski (2021) documentam momentum de serie temporal em criptoativos em horizontes de uma a quatro semanas; o bot opera em 4h. Se o efeito existe nesse horizonte e nao no de 4h, as nove hipoteses direcionais reprovadas ate agora foram testadas na escala errada."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Responder se a escala temporal explica as reprovações (Priority: P1)

O operador conduz uma investigação sistemática registrada em
`docs/research/registro-de-hipoteses.md`. Dez hipóteses foram avaliadas: nove
reprovadas, uma inconclusiva. Todas as nove direcionais foram medidas em
timeframe de 4 horas.

A literatura que fundamenta momentum em criptoativos documenta o efeito em
horizontes de **uma a quatro semanas**. Se o efeito existe apenas nessa escala, a
investigação inteira mediu a escala errada, e as nove reprovações não dizem o que
parecem dizer.

O operador precisa de uma resposta com evidência: alguma das estratégias já
implementadas apresenta, em horizonte diário ou semanal, vantagem que sobreviva à
mesma bateria que reprovou as anteriores?

**Why this priority**: é a hipótese de maior consequência da fila. Um resultado
positivo reabre nove hipóteses fechadas; um resultado negativo elimina a
explicação mais plausível que restava para o conjunto de reprovações. Nos dois
casos, a fila muda de forma.

**Independent Test**: executar as estratégias existentes em 1d e 1w sobre o
universo de pares e submeter cada combinação às etapas E1–E6 da bateria,
produzindo um veredito por combinação. Entrega valor mesmo isolada: a resposta
não depende de nenhuma outra história desta spec.

**Acceptance Scenarios**:

1. **Given** as quatro estratégias implementadas e o universo de pares,
   **When** o operador solicita a avaliação em horizonte diário e semanal,
   **Then** o sistema produz, para cada combinação estratégia × timeframe ×
   par, as métricas da bateria e um veredito entre aprovado, reprovado,
   inconclusivo e só-na-busca.

2. **Given** uma combinação cujo número de operações fica abaixo do mínimo
   exigido pelo critério de aprovação, **When** o veredito é emitido,
   **Then** o resultado é **inconclusivo**, com o número de operações
   declarado — nunca reprovado por amostra insuficiente.

3. **Given** o resultado completo da avaliação, **When** a execução termina,
   **Then** o veredito de H11 é registrado em
   `docs/research/registro-de-hipoteses.md` com evidência e procedência,
   independentemente de ser favorável.

---

### User Story 2 — Distinguir vantagem preditiva de redução de custo (Priority: P2)

Horizontes maiores produzem menos operações. Menos operações significam menos
taxa e menos slippage pagos no total. Uma estratégia pode parecer superior em 1d
simplesmente por negociar menos, sem que sua capacidade preditiva tenha mudado.

O operador precisa que a avaliação separe explicitamente as duas causas, sob pena
de trocar o timeframe de produção por um ganho que é apenas economia de custo — e
que poderia ser obtido reduzindo a frequência de negociação em 4h.

**Why this priority**: sem essa separação, um resultado positivo em P1 é
ambíguo e não sustenta decisão. Depende de P1 ter produzido resultado.

**Independent Test**: reexecutar cada combinação com custo zerado e comparar a
diferença de retorno entre horizontes. Se a vantagem do horizonte maior
desaparece com custo zerado, ela era economia de custo.

**Acceptance Scenarios**:

1. **Given** uma combinação avaliada com custo real, **When** a mesma combinação
   é reexecutada sem taxa e sem slippage, **Then** o relatório apresenta os dois
   retornos lado a lado e o impacto do custo em pontos percentuais.

2. **Given** duas combinações da mesma estratégia em horizontes distintos,
   **When** ambas são comparadas, **Then** o relatório permite distinguir se a
   diferença de retorno persiste com custo zerado.

---

### User Story 3 — Declarar limitações de dado em vez de silenciá-las (Priority: P3)

Horizonte maior consome mais tempo por candle. Pares listados recentemente têm
histórico curto em escala diária e podem não ter nenhum em escala semanal. Além
disso, indicadores com janela longa consomem parte substancial do histórico antes
de emitir o primeiro sinal.

O operador precisa que o sistema declare essas limitações, porque um resultado
calculado sobre amostra silenciosamente menor é pior que nenhum resultado — foi
esse o mecanismo de dois defeitos de instrumentação já registrados no projeto.

**Why this priority**: não bloqueia a resposta principal, mas determina se ela é
confiável.

**Independent Test**: solicitar a avaliação incluindo um par de histórico
notoriamente curto e verificar que ele aparece marcado, não avaliado em silêncio.

**Acceptance Scenarios**:

1. **Given** um par cujo histórico disponível é menor que o solicitado,
   **When** a avaliação roda, **Then** o par é marcado como histórico
   insuficiente e a lacuna é quantificada no relatório.

2. **Given** um horizonte em que o aquecimento dos indicadores consome fração
   relevante do histórico, **When** a avaliação roda, **Then** o número de
   candles efetivamente utilizáveis para sinal é declarado.

3. **Given** uma divisão em janelas de walk-forward, **When** alguma janela não
   produz operação alguma, **Then** ela é reportada como vazia, e não
   contabilizada como resultado neutro.

---

### Edge Cases

- **Par sem histórico no horizonte solicitado.** Um par listado há poucos meses
  não tem candles semanais suficientes. Deve ser marcado, não avaliado.
- **Aquecimento maior que a janela de teste.** Uma média de tendência de 50
  períodos em escala semanal consome quase um ano. Se o aquecimento exceder a
  janela, a combinação é inconclusiva por construção.
- **Zero operações em uma combinação.** Uma estratégia pode não disparar sinal
  algum em escala semanal. Zero operações é resultado inconclusivo, não retorno
  de 0%.
- **Janela de walk-forward sem operação.** Reportada como vazia; não entra no
  cálculo de "janelas positivas".
- **Histórico disponível menor que o solicitado.** A lacuna entre o pedido e o
  recebido deve ser quantificada, não absorvida.
- **Universo enviesado por sobrevivência.** Pares escolhidos hoje por liquidez
  sobreviveram até hoje. Em cinco anos de histórico diário o viés pesa muito mais
  que em um ano de 4h; a limitação deve constar do registro.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST avaliar cada estratégia já implementada em cada
  horizonte temporal solicitado sobre cada par do universo, produzindo as
  métricas já usadas pelas avaliações anteriores.
- **FR-002**: O sistema MUST aplicar o critério de aprovação vigente sem
  alteração de limiar, para que o resultado seja comparável às hipóteses já
  registradas.
- **FR-003**: O sistema MUST emitir veredito **inconclusivo**, e não reprovado,
  quando o número de operações ficar abaixo do mínimo exigido, declarando o
  número observado.
- **FR-004**: O sistema MUST submeter cada combinação à confirmação em janela que
  não participou da descoberta, distinguindo aprovação confirmada de aprovação
  restrita à janela de busca.
- **FR-005**: O sistema MUST executar walk-forward em janelas contíguas e não
  sobrepostas, com o número de janelas ajustado ao histórico disponível.
- **FR-006**: O sistema MUST reportar janela de walk-forward sem operação como
  vazia, excluindo-a da contagem de janelas positivas.
- **FR-007**: O sistema MUST calcular o ganho de timing com desconto de
  exposição, para que exposição reduzida não seja lida como capacidade de
  seleção.
- **FR-008**: O sistema MUST reexecutar cada combinação sem custo de execução e
  apresentar o impacto do custo em pontos percentuais.
- **FR-009**: O sistema MUST declarar, por par e horizonte, quantos candles foram
  solicitados e quantos foram efetivamente obtidos.
- **FR-010**: O sistema MUST declarar quantos candles são consumidos pelo
  aquecimento dos indicadores antes do primeiro sinal possível.
- **FR-011**: O sistema MUST marcar como histórico insuficiente, sem avaliar,
  qualquer par cujo histórico não comporte aquecimento mais janela de teste.
- **FR-012**: O sistema MUST preservar o comportamento operacional vigente: a
  avaliação não altera o horizonte usado pelo bot em execução.
- **FR-013**: O resultado MUST ser registrado em
  `docs/research/registro-de-hipoteses.md` com veredito, evidência e
  procedência, qualquer que seja o desfecho.

### Key Entities

- **Combinação avaliada**: unidade de análise formada por estratégia, horizonte
  temporal e par. Carrega métricas, veredito e as limitações de dado observadas.
- **Relatório de horizonte**: agregação das combinações de um mesmo horizonte,
  permitindo comparar escalas entre si.
- **Registro de hipótese**: entrada em
  `docs/research/registro-de-hipoteses.md` contendo tese, evidência, veredito e
  procedência.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O operador obtém, numa única execução, o veredito de cada
  combinação de estratégia, horizonte e par, sem executar comandos separados por
  horizonte.
- **SC-002**: Nenhuma combinação recebe veredito de reprovação tendo produzido
  menos operações que o mínimo exigido pelo critério — casos assim aparecem como
  inconclusivos com a contagem declarada.
- **SC-003**: Para toda combinação avaliada, o relatório permite responder se a
  eventual diferença de retorno entre horizontes persiste com custo zerado.
- **SC-004**: Todo par com histórico insuficiente aparece marcado no relatório;
  nenhum é avaliado com amostra silenciosamente menor que a solicitada.
- **SC-005**: O registro de hipóteses passa a conter H11 com veredito e
  evidência, e a fila de hipóteses não testadas é reordenada em função do
  resultado.
- **SC-006**: O horizonte usado pelo bot em execução permanece inalterado ao fim
  da avaliação.

## Assumptions

- O universo de pares avaliado é o mesmo já usado nas avaliações anteriores, para
  que os resultados sejam comparáveis entre hipóteses.
- Os parâmetros de cada estratégia permanecem nos valores vigentes. Otimizar
  parâmetros por horizonte multiplicaria as combinações testadas e reintroduziria
  o problema de testes múltiplos que a confirmação fora da amostra existe para
  conter.
- Os horizontes avaliados são diário e semanal, além do horizonte atual mantido
  como linha de base para comparação.
- O custo de execução aplicado é o mesmo já usado nas demais avaliações,
  garantindo comparabilidade.
- A fonte de dados histórica atual é suficiente; a limitação de profundidade
  anteriormente existente foi removida, mas a disponibilidade real por par ainda
  precisa ser verificada em execução, não presumida.
- O viés de sobrevivência do universo não é corrigido nesta avaliação; é
  declarado como limitação no registro.
