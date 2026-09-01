# Feature Specification: H12 — Dimensionamento de posição por volatilidade

**Feature Branch**: `025-dimensionamento-por-volatilidade`

**Created**: 2026-09-01

**Status**: Draft

**Input**: User description: "H12 — Dimensionamento de posição por volatilidade (volatility targeting). Redimensionar a posição inversamente à volatilidade realizada é o mecanismo padrão de controle de drawdown em gestão sistemática. H7 foi reprovada com drawdown de 11,76% contra teto de 10,0%, com todos os demais critérios passando — a única hipótese da investigação a falhar exclusivamente no limite de risco."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Descobrir se o drawdown era problema de dimensionamento (Priority: P1)

Onze hipóteses foram avaliadas e registradas em
`docs/research/registro-de-hipoteses.md`. Nenhuma aprovada. Uma delas, porém,
falhou de forma diferente das outras: o momentum transversal atingiu profit
factor, número de operações e retorno acima do buy-and-hold, e reprovou **apenas
pelo limite de risco** — drawdown de 11,76% contra o teto de 10,0%.

Nenhuma outra hipótese chegou tão perto. Se o excesso de drawdown for
consequência de alocar valor nocional constante em ativos de volatilidade
variável, então dimensionar a posição pela volatilidade recente pode trazê-lo
para dentro do teto — e a hipótese volta a ser testável. Se reduzir drawdown e
retorno na mesma proporção, a questão está encerrada: o drawdown não era
problema de dimensionamento.

O operador precisa dessa resposta com evidência, porque ela decide se vale
revisitar a hipótese que chegou mais perto de passar.

**Why this priority**: é a única pergunta que H12 existe para responder. Um
resultado favorável reabre uma hipótese; um desfavorável fecha uma linha inteira
de investigação.

**Independent Test**: avaliar cada estratégia com e sem dimensionamento, nos
mesmos pares e escala temporal, e comparar drawdown e retorno lado a lado.
Entrega valor isolada: a resposta não depende de nenhuma outra história.

**Acceptance Scenarios**:

1. **Given** uma estratégia e um conjunto de pares, **When** o operador solicita
   a avaliação com dimensionamento por volatilidade, **Then** o sistema produz,
   para cada combinação, as métricas da bateria nas duas versões — com e sem
   dimensionamento — permitindo compará-las diretamente.

2. **Given** uma combinação cujo drawdown cai com o dimensionamento, **When** o
   resultado é apresentado, **Then** a variação de retorno é apresentada junto,
   de modo que redução proporcional dos dois seja imediatamente visível.

3. **Given** o resultado completo, **When** a execução termina, **Then** o
   veredito de H12 é registrado em `docs/research/registro-de-hipoteses.md` com
   evidência e procedência, favorável ou não.

---

### User Story 2 — Impedir que redução de exposição seja lida como habilidade (Priority: P1)

Dimensionar pela volatilidade reduz a exposição média — é o que a técnica faz.
Uma carteira menos exposta durante uma queda apresenta retorno superior ao
buy-and-hold sem possuir qualquer capacidade de seleção.

Esse é o risco dominante desta hipótese, e não é hipotético: o registro já
documenta um caso em que a variante de melhor retorno bruto tinha praticamente
nenhum ganho atribuível à escolha de ativos. Sem descontar exposição, H12 passa
trivialmente e a aprovação não significa nada.

**Why this priority**: também P1 porque, sem ela, a resposta de US1 é
inutilizável. As duas juntas formam o MVP.

**Independent Test**: para uma combinação em que o dimensionamento melhora o
retorno, verificar se a melhora persiste após descontar a redução de exposição.

**Acceptance Scenarios**:

1. **Given** uma combinação avaliada nas duas versões, **When** o relatório é
   apresentado, **Then** ele informa o ganho atribuível à escolha de ativos,
   já descontada a variação de exposição.

2. **Given** uma combinação cujo retorno melhora apenas na proporção da redução
   de exposição, **When** o veredito é emitido, **Then** ela é reportada como
   **sem vantagem**, não como melhoria.

---

### User Story 3 — Separar vantagem de custo de giro (Priority: P2)

Ajustar o tamanho da posição conforme a volatilidade muda implica operações
adicionais. Cada ajuste paga taxa e escorregamento de preço. Uma versão
dimensionada pode apresentar resultado pior apenas por girar mais, sem que o
mecanismo em si seja ruim — ou apresentar resultado melhor por girar menos.

O operador precisa distinguir as duas causas antes de concluir qualquer coisa
sobre o mecanismo.

**Why this priority**: não bloqueia a resposta principal, mas determina se ela é
atribuível ao dimensionamento ou ao custo.

**Independent Test**: reexecutar as duas versões sem custo de execução e
verificar se a diferença entre elas persiste.

**Acceptance Scenarios**:

1. **Given** as duas versões de uma combinação, **When** ambas são reexecutadas
   sem custo, **Then** o relatório apresenta a diferença de resultado com e sem
   custo, e o número de operações de cada versão.

2. **Given** uma versão dimensionada que executa mais operações que a original,
   **When** o resultado é apresentado, **Then** o custo adicional decorrente do
   giro extra é quantificado separadamente.

---

### Edge Cases

- **Volatilidade estimada igual a zero.** Um ativo sem variação na janela de
  estimativa levaria a divisão por zero. O dimensionamento deve recair no
  tamanho que o sistema já calcularia, nunca produzir posição infinita.
- **Volatilidade extremamente baixa.** Mesmo diferente de zero, uma volatilidade
  muito pequena ampliaria a posição além do capital. O dimensionamento só pode
  **reduzir** em relação ao tamanho vigente, jamais ampliá-lo.
- **Histórico insuficiente para estimar volatilidade.** No início da série não há
  janela completa. Enquanto não houver, o dimensionamento não se aplica.
- **Combinação com poucas operações.** Vale a regra já estabelecida: amostra
  abaixo do mínimo resulta em **inconclusivo**, nunca em reprovado.
- **Dimensionamento reduz a posição abaixo do mínimo operacional.** Se o tamanho
  calculado ficar abaixo do que a corretora aceita, a entrada não acontece — e
  isso precisa aparecer como entrada não realizada, não como perda.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST calcular o tamanho da posição em função da
  volatilidade realizada recente do ativo, de modo que ativos mais voláteis
  recebam alocação menor.
- **FR-002**: O dimensionamento MUST decidir apenas **quanto** alocar, nunca
  **se** entrar ou sair — o sinal da estratégia permanece inalterado.
- **FR-003**: O dimensionamento MUST apenas reduzir o tamanho em relação ao que o
  sistema já alocaria, nunca ampliá-lo, e MUST NOT introduzir alavancagem.
- **FR-004**: O sistema MUST compor com as regras de dimensionamento já
  existentes — teto por ordem e reserva proporcional aos slots livres — em vez
  de substituí-las.
- **FR-005**: O sistema MUST avaliar cada estratégia nas duas versões, com e sem
  dimensionamento, sobre os mesmos pares e a mesma escala temporal.
- **FR-006**: O sistema MUST apresentar, por combinação, a variação de drawdown
  **e** a variação de retorno entre as duas versões.
- **FR-007**: O sistema MUST informar o ganho atribuível à escolha de ativos com
  a variação de exposição descontada.
- **FR-008**: O sistema MUST reportar como **sem vantagem** a combinação cuja
  melhora de retorno não sobreviva ao desconto de exposição.
- **FR-009**: O sistema MUST informar o número de operações de cada versão e o
  custo de execução de cada uma, permitindo isolar o efeito do giro adicional.
- **FR-010**: O sistema MUST aplicar o critério de aprovação vigente sem
  alteração de limiar, para que o resultado seja comparável às hipóteses já
  registradas.
- **FR-011**: O sistema MUST emitir veredito **inconclusivo**, e não reprovado,
  quando a amostra ficar abaixo do mínimo exigido.
- **FR-012**: O sistema MUST recair no tamanho vigente quando a volatilidade não
  puder ser estimada ou for nula.
- **FR-013**: O sistema MUST preservar o comportamento operacional: o cálculo de
  tamanho usado pelo bot em execução permanece inalterado.
- **FR-014**: O resultado MUST ser registrado em
  `docs/research/registro-de-hipoteses.md` com veredito, evidência e
  procedência, qualquer que seja o desfecho.

### Key Entities

- **Posição dimensionada**: tamanho resultante da aplicação do fator de
  volatilidade sobre o tamanho que o sistema calcularia, com o fator e o tamanho
  original preservados para auditoria.
- **Comparação pareada**: as duas versões de uma mesma combinação — com e sem
  dimensionamento — com métricas, exposição, número de operações e custo de
  cada uma.
- **Registro de hipótese**: entrada em `docs/research/registro-de-hipoteses.md`
  contendo tese, evidência, veredito e procedência.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O operador obtém, numa única execução, a comparação pareada de
  cada estratégia com e sem dimensionamento, sem executar comandos separados.
- **SC-002**: Para toda combinação, o relatório permite responder se a variação
  de drawdown veio acompanhada de variação proporcional de retorno.
- **SC-003**: Nenhuma combinação é reportada como melhoria quando o ganho
  desaparece ao descontar a variação de exposição.
- **SC-004**: Para toda combinação, o relatório permite distinguir efeito do
  mecanismo de efeito do custo de giro adicional.
- **SC-005**: Nenhuma combinação recebe veredito de reprovação tendo produzido
  amostra abaixo do mínimo — casos assim aparecem como inconclusivos.
- **SC-006**: O cálculo de tamanho usado pelo bot em execução permanece
  inalterado ao fim da avaliação.
- **SC-007**: O registro de hipóteses passa a conter H12 com veredito e
  evidência, e a fila é reordenada em função do resultado.

## Assumptions

- A janela de estimativa da volatilidade é fixa e declarada, não varrida.
  Otimizá-la por par ou estratégia multiplicaria as combinações testadas e
  reintroduziria o problema de descoberta por acaso que a confirmação fora da
  amostra existe para conter.
- O alvo de volatilidade também é fixo e único para toda a avaliação, pela mesma
  razão.
- O universo de pares e a escala temporal são os mesmos usados nas avaliações
  anteriores, para que os resultados sejam comparáveis entre hipóteses.
- As estratégias avaliadas são as já implementadas, sem alteração de parâmetros.
- O custo de execução aplicado é o mesmo das demais avaliações.
- A medida de volatilidade usada é a variação típica dos retornos recentes do
  ativo; a definição exata é decisão de implementação, desde que declarada.
