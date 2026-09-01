# Feature Specification: H13 — Barras dirigidas por informação

**Feature Branch**: `026-barras-por-informacao`

**Created**: 2026-09-01

**Status**: Draft

**Input**: User description: H13 — Barras dirigidas por informação (volume bars, dollar bars, CUSUM). Décima terceira hipótese da fila de `docs/research/registro-de-hipoteses.md`.

---

## Contexto e tese

Amostrar o mercado em intervalos de tempo fixos é uma escolha arbitrária, não
uma propriedade do mercado. Informação não chega uniformemente no tempo: chega
em rajadas. Uma barra de 4h numa madrugada parada e uma barra de 4h durante uma
liquidação em cascata carregam quantidades de informação radicalmente
diferentes, e o backtest as trata como observações equivalentes.

Barras dirigidas por informação fecham quando uma quantidade de **atividade** se
acumula — valor negociado, volume, ou desvio acumulado (CUSUM) — em vez de
quando o relógio marca.

**Procedência interna.** As doze hipóteses avaliadas rodaram **todas** sobre
candles de tempo fixo. Se o esquema de amostragem for o problema, cada hipótese
direcional reprovada mediu a *amostragem*, não a estratégia. H13 subiu de
prioridade média para alta por consequência direta do veredito de H12 (registro
§4.13): hipóteses de gestão são descendentes de hipóteses de sinal, e com taxa
de aprovação de sinal em zero, a fila prioriza sinal.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Descobrir se a amostragem por informação muda o resultado (Priority: P1)

O pesquisador roda um comando único que, para cada estratégia já implementada e
cada par do universo, executa a mesma estratégia sobre a série de tempo fixo e
sobre a série reamostrada por informação, **ancoradas no mesmo intervalo de
calendário**, e apresenta as duas lado a lado com as diferenças.

**Why this priority**: é a pergunta da hipótese. Sem a comparação pareada não há
resposta.

**Independent Test**: executar o comando e obter uma tabela onde cada linha traz
o número de barras, o retorno e o drawdown de cada versão, e o período de
calendário coberto por ambas.

**Acceptance Scenarios**:

1. **Given** um par com histórico suficiente, **When** o pesquisador roda a
   varredura, **Then** cada combinação reporta o resultado das duas versões e o
   número de observações de cada uma.
2. **Given** duas versões da mesma combinação, **When** o relatório é gerado,
   **Then** o intervalo de calendário coberto é idêntico entre elas e está
   declarado na saída.
3. **Given** uma combinação em que a reamostragem não pôde ser construída,
   **When** a varredura processa as demais, **Then** ela continua e a
   combinação aparece com estado próprio, sem abortar a execução.

---

### User Story 2 - Impedir que menos participação seja lida como vantagem (Priority: P1)

O relatório distingue melhora real de simples redução de participação. Barras
mais grossas produzem menos sinais, menos operações e menos exposição; num
mercado em queda isso sozinho melhora o retorno relativo sem nenhuma capacidade
de seleção.

**Why this priority**: o registro documenta **três** formas distintas do mesmo
erro — M7 (exposição em tempo), M10 (exposição em capital), M11 (sinal do
resultado base) — e a nota de M11 declara ser razoável supor que existam outras.
Uma mudança de amostragem altera o número de observações, que é uma dimensão
ainda não coberta por nenhuma das três guardas.

**Why P1 e não refinamento**: sem esta história, US1 produz uma tabela em que
amostragem mais grossa aparece como melhoria. Parar em US1 seria pior que não
implementar: geraria evidência enganosa que entraria no registro.

**Independent Test**: uma combinação cujo resultado melhora apenas na proporção
da menor participação recebe estado de ausência de vantagem, não de melhora.

**Acceptance Scenarios**:

1. **Given** uma combinação cuja versão reamostrada opera menos e cujo ganho
   descontada a exposição não sobe, **When** classificada, **Then** recebe
   estado de ausência de vantagem.
2. **Given** uma combinação cuja vantagem sobrevive ao desconto de exposição,
   **When** classificada, **Then** recebe estado de melhora.
3. **Given** qualquer combinação avaliada, **When** o relatório é gerado,
   **Then** a medida de exposição usada no desconto está declarada na saída.

---

### User Story 3 - Verificar que a construção da barra não usa futuro (Priority: P1)

A construção de uma barra dirigida por informação é verificável quanto a
causalidade: o fechamento de uma barra depende apenas de dados até aquele
instante, e nenhum campo da barra usa informação posterior ao seu fechamento.

**Why this priority**: é o modo de falha que produziria aprovação falsa mais
convincente. M2 documenta precisamente esta classe de defeito — um filtro que
comparava preço histórico contra indicador corrente — e ele passou despercebido
por meses. Uma barra construída com conhecimento do seu próprio total futuro
produziria resultados espetaculares e inteiramente falsos.

**Independent Test**: reconstruir as barras usando apenas o prefixo da série
disponível em cada instante produz exatamente as mesmas barras que a construção
sobre a série completa.

**Acceptance Scenarios**:

1. **Given** uma série histórica, **When** as barras são construídas
   incrementalmente prefixo a prefixo, **Then** cada barra fechada é idêntica à
   correspondente construída sobre a série inteira.
2. **Given** uma barra em construção, **When** ela ainda não cruzou o limiar,
   **Then** ela não aparece na saída — barras incompletas nunca são avaliadas.

---

### User Story 4 - Separar vantagem de custo de giro (Priority: P2)

O relatório distingue o efeito da amostragem do efeito do custo adicional de
execução que ela provoca.

**Why this priority**: mais barras significa mais sinais e mais operações, cada
uma pagando taxa e slippage. Sem separar, uma diferença negativa não distingue
"a amostragem não ajuda" de "a amostragem ajuda e o giro come o ganho". Mesmo
tratamento dado em H12.

**Independent Test**: o relatório mostra, por combinação, o número de operações
de cada versão e quanto do resultado é atribuível a custo.

**Acceptance Scenarios**:

1. **Given** uma combinação avaliada, **When** o relatório é gerado, **Then**
   apresenta operações de cada versão e a diferença atribuível a custo.
2. **Given** uma reexecução com custo zerado, **When** comparada à execução com
   custo, **Then** o retorno é maior ou igual em ambas as versões.

---

### Edge Cases

- **Histórico insuficiente para o aquecimento.** O aquecimento de indicadores é
  contado em observações, mas 50 barras dirigidas cobrem uma quantidade de dias
  que varia com a atividade. Combinação cujo aquecimento não cabe no histórico é
  **inconclusiva**, nunca reprovada.
- **Reamostragem produz observações demais ou de menos.** Um limiar mal
  dimensionado pode gerar uma barra por candle (reamostragem inerte) ou três
  barras no período inteiro. Ambos são estados próprios, distintos de reprovação
   — a lição de `inerte` em H12.
- **Amostra de operações abaixo do mínimo em qualquer das versões.** Comparar 30
  operações contra 4 mede diferença de amostra, não amostragem. Resultado
  **inconclusivo**.
- **Série com volume ausente, zerado ou não confiável.** Barras por valor
  negociado dependem de volume. Volume ausente impede a construção e produz
  estado explícito, nunca uma barra silenciosamente errada.
- **Último período incompleto.** A última barra da série provavelmente não
  cruzou o limiar. Ela é descartada, não avaliada como se estivesse fechada.
- **Buy-and-hold divergente entre versões.** Se o retorno de referência calculado
  nas duas versões diferir além de tolerância numérica, a comparação está
  desancorada e a combinação é reportada como erro, não avaliada.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST converter uma série de candles de tempo fixo em uma
  série de barras dirigidas por informação, aplicando a conversão **antes** do
  cálculo de indicadores.
- **FR-002**: O sistema MUST oferecer pelo menos duas variantes de construção:
  por valor negociado acumulado e por evento de desvio acumulado (CUSUM).
- **FR-003**: A construção de barras MUST ser causal: o fechamento de cada barra
  MUST depender apenas de dados até aquele instante, e nenhum campo da barra
  MUST usar informação posterior ao seu fechamento.
- **FR-004**: Barras que não cruzaram o limiar MUST NOT aparecer na série de
  saída.
- **FR-005**: O sistema MUST executar cada estratégia nas duas versões sobre o
  **mesmo intervalo de calendário**, e MUST declarar esse intervalo na saída.
- **FR-006**: O sistema MUST reportar o número de observações de cada versão em
  toda combinação avaliada.
- **FR-007**: O sistema MUST calcular o retorno de referência (buy-and-hold)
  sobre o mesmo intervalo de calendário nas duas versões, e MUST tratar
  divergência além de tolerância numérica como erro da comparação.
- **FR-008**: O sistema MUST descontar exposição ao comparar as versões, e MUST
  declarar qual medida de exposição foi usada.
- **FR-009**: Combinação cujo resultado melhora sem que o ganho sobreviva ao
  desconto de exposição MUST receber estado de ausência de vantagem, distinto de
  melhora.
- **FR-010**: O aquecimento de indicadores MUST ser verificado em **dias de
  calendário**, não apenas em número de observações, e combinação cujo
  aquecimento não caiba no histórico MUST ser inconclusiva.
- **FR-011**: Combinação com menos operações que o mínimo estabelecido em
  **qualquer** das duas versões MUST ser inconclusiva, nunca reprovada.
- **FR-012**: Reamostragem que produza aproximadamente uma barra por candle de
  entrada MUST receber estado próprio de inércia, distinto de reprovação.
- **FR-013**: O sistema MUST reportar, por combinação, o número de operações de
  cada versão e a parcela do resultado atribuível a custo de execução.
- **FR-014**: O limiar de construção de cada variante MUST ser declarado e
  justificado por medição prévia, e MUST permanecer único para toda a avaliação.
  O sistema MUST NOT varrer limiares em busca de um que produza aprovação.
- **FR-015**: O sistema MUST NOT alterar o comportamento do bot em produção. O
  `TIMEFRAME` operacional e o ciclo de decisão permanecem inalterados enquanto
  nenhuma hipótese for aprovada.
- **FR-016**: Falha ao processar uma combinação MUST NOT abortar a varredura; a
  combinação MUST aparecer com estado de erro e as demais MUST prosseguir.
- **FR-017**: O sistema MUST registrar, junto ao veredito, se uma eventual
  aprovação seria **executável** pela infraestrutura operacional atual.
- **FR-018**: A avaliação MUST usar os critérios de aprovação já vigentes no
  projeto, sem introduzir limiar novo.

### Key Entities

- **Série reamostrada**: sequência de barras derivada de candles de tempo fixo,
  cada barra com preços de abertura, máxima, mínima e fechamento, volume
  acumulado, instante de fechamento e quantidade de candles de origem que a
  compõem.
- **Parâmetros de amostragem**: variante de construção e o limiar declarado que
  a governa.
- **Comparação pareada**: uma estratégia sobre um par, nas duas versões, com o
  intervalo de calendário comum, o número de observações de cada lado, as
  métricas de cada versão, as diferenças derivadas, o estado e o motivo.
- **Relatório de varredura**: conjunto de comparações com contagem por estado e
  os parâmetros declarados da execução.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O pesquisador obtém, numa única execução, a resposta sobre se
  amostrar por informação altera o resultado, para cada estratégia e par do
  universo já usado nas avaliações anteriores.
- **SC-002**: Toda combinação avaliada apresenta o número de observações das
  duas versões e o intervalo de calendário comum, permitindo verificar que a
  comparação não é entre tamanhos de amostra diferentes.
- **SC-003**: Nenhuma combinação recebe estado de melhora sem que a vantagem
  sobreviva ao desconto de exposição.
- **SC-004**: A causalidade da construção de barras é demonstrada por
  reconstrução incremental, com igualdade exata entre a construção prefixo a
  prefixo e a construção sobre a série completa.
- **SC-005**: Combinação com amostra insuficiente em qualquer das versões, ou
  com aquecimento que não cabe no histórico, é reportada como inconclusiva e
  nunca como reprovada.
- **SC-006**: O comportamento do bot em produção permanece idêntico ao anterior
  à feature, verificável por ausência de alteração nos caminhos de decisão e
  execução.
- **SC-007**: O veredito de H13 é registrado com evidência, procedência e
  declaração explícita de executabilidade operacional, favorável ou não.
- **SC-008**: Se a limitação de granularidade impedir construção defensável, o
  veredito registrado é inconclusivo por limitação de dado, com declaração do
  que seria necessário para tornar a hipótese testável.

---

## Assumptions

- **Granularidade é o risco dominante e é específico desta hipótese.** Barras
  dirigidas por informação canônicas se constroem a partir de dados de
  negociação individuais. O projeto consome candles agregados. Agrupar candles
  inteiros produz barras sempre **mais grossas** que a série de origem, nunca
  mais finas — o que pode inverter o efeito que a hipótese prevê. A escolha da
  granularidade de base e a declaração honesta do que se perde em relação a
  dados de negociação individuais ficam para a fase de pesquisa. Se a
  aproximação não for defensável, o veredito correto é inconclusivo por
  limitação de dado, e isso é resultado legítimo, não falha.
- **Universo e estratégias são os mesmos das avaliações anteriores**, para que o
  resultado seja comparável, e não são parametrizáveis pela interface — expô-los
  convidaria a varrer combinações até achar uma que passe.
- **A medida de exposição correta para uma mudança de amostragem pode não ser
  nenhuma das já existentes.** M7 usa tempo, M10 usa capital, M11 usa o sinal do
  resultado base. Se a amostragem exigir uma quarta medida, ela é o achado
  principal desta spec e deve ser registrada como tal.
- **Uma aprovação pode ser inexecutável.** O bot decide sobre candles obtidos
  periodicamente da corretora; construir barras dirigidas ao vivo exigiria
  acompanhar atividade de forma contínua. Se o veredito for favorável mas
  inexecutável, isso é parte do resultado — aprovar algo inexecutável é pior que
  reprovar.
- **A hipótese mede amostragem, não sinal.** Nenhuma estratégia nova é
  implementada. As estratégias existentes são executadas sem alteração.
- **Custos de execução seguem o modelo já usado no projeto**, sem introduzir
  parâmetro novo de custo.
