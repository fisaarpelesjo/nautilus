# Feature Specification: H14 — Aprendizado supervisionado com rotulagem de barreira tripla

**Feature Branch**: `027-aprendizado-barreira-tripla`

**Created**: 2026-09-01

**Status**: Draft

**Input**: User description: H14 — Aprendizado supervisionado com rotulagem de barreira tripla. Décima quarta hipótese da fila de `docs/research/registro-de-hipoteses.md`.

---

## Contexto e tese

**Tese.** Rotular cada evento por qual barreira o preço toca primeiro — alvo de
lucro, stop, ou limite de tempo — transforma a previsão de direção num problema
de classificação com rótulos **economicamente significativos**, em vez de "o
preço sobe no próximo candle?". Um classificador sobre os indicadores já
calculados poderia extrair estrutura que regras fixas de cruzamento não capturam.

**Procedência interna, e o ceticismo que a acompanha.** A seção 6.3-b do
registro documenta que **toda** hipótese exigindo previsão de direção falhou —
H1 a H7, H11, H13. As duas que mais se aproximaram de significar algo não eram
direcionais: H10 (cointegração, único profit factor de 1,58 em E2, reprovada por
poder estatístico do seletor) e H8 (efeito real, apenas pequeno demais: +3,21%
ao ano contra os 10–30% alegados na literatura popular).

H14 é direcional e entra sabendo disso. O valor de avaliá-la não está em esperar
aprovação, e sim em fechar a família: se um classificador com rótulos
economicamente significativos também falhar, a conclusão de que previsão de
direção nesta escala não produz vantagem passa a ter treze hipóteses de suporte
em vez de doze.

**O risco dominante já está quantificado pelo próprio registro.** H13 testou 96
combinações e produziu **uma** aprovação confirmada fora da amostra — abaixo do
que o acaso produziria. Um modelo com muitos graus de liberdade multiplica esse
problema. Daí a decisão de usar um classificador de **baixa capacidade** com
atributos declarados de antemão: é escolha metodológica, não limitação.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Descobrir se o classificador tem vantagem sobre as regras (Priority: P1)

O pesquisador roda um comando único que, para cada par do universo, rotula os
eventos por barreira tripla, treina o classificador sobre atributos declarados,
substitui o sinal da estratégia pelo do modelo, e apresenta o resultado ao lado
do resultado da estratégia de regras sobre a mesma série e o mesmo período.

**Why this priority**: é a pergunta da hipótese.

**Independent Test**: executar o comando e obter, por par, as métricas das duas
versões — regras e modelo — com as diferenças e o número de operações de cada.

**Acceptance Scenarios**:

1. **Given** um par com histórico suficiente, **When** o pesquisador roda a
   avaliação, **Then** obtém as métricas do modelo e das regras sobre o mesmo
   período, com o número de eventos rotulados e a distribuição das classes.
2. **Given** uma série em que a rotulagem não produz eventos suficientes,
   **When** a avaliação processa as demais, **Then** ela continua e o par
   aparece com estado próprio, sem abortar a execução.
3. **Given** qualquer par avaliado, **When** o relatório é gerado, **Then** o
   conjunto de atributos usado está declarado na saída.

---

### User Story 2 - Impedir que o modelo veja o futuro (Priority: P1)

O treino nunca usa amostras cujo horizonte de rótulo invada a janela de teste. A
separação entre treino e teste remove (purga) as amostras sobrepostas e insere
um intervalo morto (embargo) após a janela de teste.

**Why this priority**: rótulos de barreira tripla **se sobrepõem no tempo** — o
rótulo em `t` só é conhecido em `t + horizonte`. Um corte ingênuo entrega futuro
ao treino e produz o resultado mais convincente e mais falso possível. É o
análogo, em aprendizado supervisionado, do achado M2: um filtro que comparava
preço histórico contra indicador corrente, e que passou meses despercebido.

**Independent Test**: nenhuma amostra de treino tem horizonte de rótulo que
alcance qualquer instante da janela de teste ou do embargo.

**Acceptance Scenarios**:

1. **Given** uma divisão treino/teste, **When** a purga é aplicada, **Then**
   nenhuma amostra de treino tem horizonte de rótulo sobrepondo a janela de
   teste.
2. **Given** uma janela de teste, **When** o embargo é aplicado, **Then** as
   amostras imediatamente posteriores a ela ficam excluídas do treino.
3. **Given** purga e embargo aplicados, **When** a amostra útil de treino cai
   abaixo do mínimo, **Then** o resultado é inconclusivo por amostra, com o
   número declarado — nunca reprovação.

---

### User Story 3 - Distinguir sinal de ajuste a ruído (Priority: P1)

O mesmo modelo, com o mesmo conjunto de atributos e o mesmo procedimento de
validação, é treinado com os **rótulos embaralhados**, e avaliado pela mesma
bateria. O relatório apresenta os dois lado a lado.

**Why this priority**: é a linha de base decisiva, e sem ela H14 não é
avaliável. Um classificador sempre encontra *alguma* estrutura; a pergunta é se
a estrutura existe nos dados ou apenas na capacidade do modelo. Se o desempenho
com rótulos embaralhados for indistinguível do desempenho com rótulos reais, o
que se mediu foi ajuste a ruído.

**Why P1 e não refinamento**: sem esta história, US1 produz uma tabela em que
qualquer desempenho aparece como descoberta. É o mesmo argumento que tornou US2
das specs 025 e 026 obrigatória para o MVP: parar antes produziria evidência
enganosa que entraria no registro.

**Independent Test**: uma execução com rótulos embaralhados produz métricas
comparáveis às do modelo real, e o veredito reflete a diferença entre as duas.

**Acceptance Scenarios**:

1. **Given** o modelo treinado com rótulos reais e o mesmo modelo com rótulos
   embaralhados, **When** ambos são avaliados, **Then** o relatório mostra as
   métricas das duas execuções.
2. **Given** desempenho do modelo real indistinguível do embaralhado, **When**
   classificado, **Then** o estado é de ausência de sinal, nunca de aprovação.
3. **Given** o embaralhamento, **When** ele é aplicado, **Then** preserva a
   distribuição das classes — embaralhar destrói a associação entre atributo e
   rótulo, não a proporção entre classes.

---

### User Story 4 - Separar vantagem de custo de giro (Priority: P2)

O relatório distingue o efeito do modelo do efeito do custo de execução que ele
provoca.

**Why this priority**: um classificador pode gerar muito mais sinais que as
regras, e cada operação paga taxa e slippage. Sem separar, uma diferença
negativa não distingue "o modelo não ajuda" de "o modelo ajuda e o giro come o
ganho". Mesmo tratamento dado em H12 e H13.

**Independent Test**: o relatório mostra operações de cada versão e a parcela do
resultado atribuível a custo.

**Acceptance Scenarios**:

1. **Given** um par avaliado, **When** o relatório é gerado, **Then** apresenta
   operações de cada versão e a diferença atribuível a custo.
2. **Given** uma reexecução com custo zerado, **When** comparada à execução com
   custo, **Then** o retorno é maior ou igual em ambas as versões.

---

### Edge Cases

- **Classe única.** Se todos os eventos rotulados caírem na mesma classe, não há
  o que classificar. Estado próprio, distinto de reprovação.
- **Classes severamente desbalanceadas.** Um classificador que sempre prevê a
  classe majoritária pode exibir acurácia alta e não operar nunca. A
  distribuição das classes precisa aparecer no relatório.
- **Modelo que não converge.** Estimação pode falhar por separação perfeita ou
  colinearidade entre atributos. Falha de convergência é estado explícito,
  nunca um modelo silenciosamente ruim.
- **Purga e embargo esvaziam o treino.** Resultado inconclusivo por amostra, com
  o número declarado.
- **Modelo não gera operação alguma.** Distinto de gerar operações ruins:
  inconclusivo por amostra, nunca `piora`.
- **Atributo constante na janela de treino.** Não contribui e pode impedir a
  estimação; precisa ser detectado, não produzir resultado silencioso.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST rotular cada evento pela barreira que o preço toca
  primeiro entre três: alvo superior, alvo inferior e limite de tempo.
- **FR-002**: As barreiras MUST ser derivadas da medida de volatilidade que o
  sistema já usa para calcular stop e alvo, sem introduzir parâmetro novo de
  risco.
- **FR-003**: O conjunto de atributos MUST ser declarado antes da avaliação e
  MUST permanecer único para toda ela. O sistema MUST NOT buscar atributos.
- **FR-004**: A rotulagem MUST ser causal: o rótulo de um evento MUST depender
  apenas de preços posteriores a ele, e nenhum atributo MUST usar informação
  posterior ao instante do evento.
- **FR-005**: O treino MUST excluir toda amostra cujo horizonte de rótulo se
  sobreponha à janela de teste (purga).
- **FR-006**: O treino MUST excluir as amostras situadas num intervalo declarado
  imediatamente após a janela de teste (embargo).
- **FR-007**: O sistema MUST treinar e avaliar o mesmo modelo com os rótulos
  embaralhados, preservando a distribuição das classes, e MUST reportar o
  resultado ao lado do modelo com rótulos reais.
- **FR-008**: Desempenho do modelo real que não se distinga do modelo com
  rótulos embaralhados MUST produzir estado de ausência de sinal, nunca
  aprovação.
- **FR-009**: O sistema MUST reportar a distribuição das classes e o número de
  eventos rotulados em toda avaliação.
- **FR-010**: O sistema MUST descontar exposição ao comparar as versões, e
  avaliação cuja versão de referência tenha resultado não positivo MUST receber
  estado próprio, distinto de melhora — a guarda contra ler menor participação
  como habilidade.
- **FR-011**: Avaliação com menos operações que o mínimo estabelecido em
  **qualquer** das versões MUST ser inconclusiva, nunca reprovada.
- **FR-012**: Falha de convergência da estimação, classe única, ou atributo
  constante MUST produzir estado explícito e MUST NOT resultar em métricas
  silenciosamente inválidas.
- **FR-013**: O sistema MUST reportar o número de operações de cada versão e a
  parcela do resultado atribuível a custo de execução.
- **FR-014**: Falha ao processar um par MUST NOT abortar a avaliação; o par MUST
  aparecer com estado de erro e os demais MUST prosseguir.
- **FR-015**: O sistema MUST NOT alterar o comportamento do bot em produção.
- **FR-016**: O sistema MUST NOT adicionar dependência ao projeto.
- **FR-017**: O sistema MUST registrar, junto ao veredito, se uma eventual
  aprovação seria executável pela infraestrutura operacional atual, incluindo o
  que a ausência de mecanismo de retreino implicaria.
- **FR-018**: A avaliação MUST usar os critérios de aprovação já vigentes no
  projeto, sem introduzir limiar novo.
- **FR-019**: O sistema MUST NOT varrer hiperparâmetros, arquiteturas ou
  conjuntos de atributos.

### Key Entities

- **Evento rotulado**: um instante da série com o rótulo da barreira tocada
  primeiro, o instante em que essa barreira foi tocada (o fim do horizonte do
  rótulo) e os valores dos atributos no instante do evento.
- **Conjunto de atributos**: lista declarada de grandezas derivadas dos
  indicadores já calculados, fixa para toda a avaliação.
- **Divisão purgada**: par de janelas treino/teste em que o treino teve removidas
  as amostras sobrepostas ao teste e as situadas no embargo.
- **Avaliação pareada**: um par, com o resultado do modelo, o resultado das
  regras, o resultado do modelo de rótulos embaralhados, a distribuição das
  classes, as diferenças derivadas, o estado e o motivo.
- **Relatório**: conjunto de avaliações com contagem por estado, atributos
  declarados e a declaração de executabilidade operacional.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O pesquisador obtém, numa única execução, a resposta sobre se o
  classificador supera a estratégia de regras, para cada par do universo já
  usado nas avaliações anteriores.
- **SC-002**: Toda avaliação apresenta o resultado do modelo com rótulos reais e
  do mesmo modelo com rótulos embaralhados, permitindo verificar se o desempenho
  se distingue de ajuste a ruído.
- **SC-003**: Nenhuma avaliação recebe estado de aprovação sem se distinguir do
  modelo de rótulos embaralhados **e** sem que a vantagem sobreviva ao desconto
  de exposição.
- **SC-004**: A ausência de vazamento por sobreposição de rótulos é demonstrada
  por verificação explícita: nenhuma amostra de treino tem horizonte alcançando
  a janela de teste ou o embargo.
- **SC-005**: Avaliação com amostra insuficiente, classe única, ou falha de
  convergência é reportada com estado próprio e nunca como reprovação.
- **SC-006**: O comportamento do bot em produção permanece idêntico ao anterior
  à feature, verificável por ausência de alteração nos caminhos de decisão e
  execução.
- **SC-007**: Nenhuma dependência nova é adicionada ao projeto.
- **SC-008**: O veredito de H14 é registrado com evidência, procedência e
  declaração explícita de executabilidade operacional, favorável ou não.

---

## Assumptions

- **Classificador de baixa capacidade é escolha metodológica.** O risco dominante
  é sobreajuste, e o registro já o quantificou: H13 obteve uma aprovação em 96
  testes, abaixo da expectativa do acaso. Um modelo com poucos parâmetros e
  atributos declarados minimiza graus de liberdade. A escolha específica do
  estimador fica para a fase de pesquisa, com a restrição de não adicionar
  dependência.
- **Universo e período são os mesmos das avaliações anteriores**, para
  comparabilidade, e não são parametrizáveis pela interface — expô-los
  convidaria a varrer combinações até achar uma que passe.
- **As barreiras reusam a medida de volatilidade já existente** no cálculo de
  stop e alvo. Introduzir uma medida nova criaria duas definições concorrentes
  do mesmo conceito no mesmo sistema.
- **A comparação relevante tem três linhas de base**: a estratégia de regras
  sobre a mesma série, o buy-and-hold do período, e o modelo de rótulos
  embaralhados. Superar as duas primeiras sem superar a terceira **não** é
  vantagem.
- **Uma aprovação pode ser inexecutável.** O bot decide a cada ciclo sobre
  candles obtidos periodicamente; avaliar um modelo a cada ciclo é viável, mas
  um modelo treinado sobre histórico se degrada conforme o regime muda, e não
  existe mecanismo de retreino. Se o veredito for favorável mas inexecutável,
  isso é parte do resultado.
- **A hipótese mede capacidade preditiva, não gestão.** Dimensionamento, stop e
  alvo permanecem como o sistema já os calcula.
