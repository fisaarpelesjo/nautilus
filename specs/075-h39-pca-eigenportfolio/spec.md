# Feature Specification: H39 — Arbitragem estatística via PCA/eigenportfolio (Avellaneda-Lee)

**Feature Branch**: `075-h39-pca-eigenportfolio`

**Created**: 2026-09-06

**Status**: Draft

**Input**: User description: decompõe o universo inteiro
(`UNIVERSO_AMPLO_HISTORICO_COMPLETO`, 22 pares, já usado por H10/H29) por
componentes principais (PCA) dos retornos padronizados, constrói
eigenportfolios, regride o retorno de cada ativo contra os fatores para
obter um resíduo, integra o resíduo e modela o processo integrado como
Ornstein-Uhlenbeck (Avellaneda-Lee 2008) — relação muitas-para-muitas, não
par-a-par como H10/H29. Sinal clássico: s-score = (X_t − média)/sigma do
processo OU; entra em s ≤ −1,25, sai em s ≥ −0,5 — limiares do paper
original. Literatura (SSRN, Jay Jung 2025) já reporta resultado
majoritariamente negativo em cripto. Sexta hipótese da leva H34-H40
(deepsearch 2026-09-06).

---

## Contexto e tese

**Por que isso é diferente de H10/H29.** H10 (cointegração) e H29 (cópula)
testam relação PAR-A-PAR entre dois ativos. H39 decompõe o universo
INTEIRO simultaneamente em fatores comuns (componentes principais dos
retornos) e testa se o resíduo de CADA ativo — o que sobra depois de
remover a exposição aos fatores comuns — reverte à média. É uma relação
muitas-para-muitas, matematicamente distinta, mesmo aplicada ao mesmo
universo de 22 pares.

**Limitação estrutural específica deste projeto, declarada antes de
medir.** O método original de Avellaneda-Lee negocia o RESÍDUO com hedge
contra os fatores — compra o ativo E vende os eigenportfolios
simultaneamente, posição dollar-neutral ao fator de mercado. O bot é
long-only (CLAUDE.md, sem infraestrutura de short). Esta implementação só
pode aproximar o sinal como uma aposta DIRECIONAL no ativo quando seu
resíduo está esticado para baixo — sem o hedge que tornaria a posição
neutra ao fator (tipicamente dominado por BTC em cripto). Isso muda o
risco real do trade (exposição ao fator permanece) e é reportado como
limitação, não escondido atrás do resultado.

**Obstáculo já medido na literatura.** O paper citado (SSRN, Jay Jung
2025) testa exatamente este método em cripto e reporta resultado
majoritariamente negativo — a estrutura de fatores cripto (fator BTC
dominante, correlações de altcoin instáveis) não produz resíduos
estáveis de reversão como em equities. Expectativa honesta declarada
baixa antes de medir, mesmo padrão de H26: a literatura já aponta o
resultado provável; medir aqui confirma com o critério e universo
próprios do projeto.

**Hipótese declarada antes de medir.** O resíduo (após remover a
exposição aos componentes principais, estimados só no treino) de pelo
menos alguns ativos do universo reverte à média de forma suficientemente
estável (meia-vida dentro da faixa já usada por H10) para que o sinal
s-score produza vantagem real na validação fora da amostra.

**Hipótese alternativa, com peso igual, e mais provável dado a
literatura.** O fator BTC dominante e a instabilidade das correlações de
altcoin fazem o resíduo se comportar como ruído ou passeio aleatório —
meia-vida fora da faixa negociável, ou dentro da faixa mas sem vantagem
que sobreviva à validação fora da amostra.

**Zero mecânica de trading nova.** Cada ativo é avaliado individualmente
pela bateria comum (E1-E6, já usada por H34/H36/H37) — não toca
`trading/`, `execution/`, `risk/` nem a estratégia em produção.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Veredito por ativo e agregado sobre o resíduo PCA/OU (Priority: P1)

O pesquisador obtém, numa única execução, para cada ativo do universo
declarado, se o sinal derivado do resíduo (após remover a exposição aos
fatores comuns, estimados só no treino) produz vantagem real na
validação fora da amostra, com o quadro completo das seis etapas da
bateria comum.

**Why this priority**: é a pergunta central da hipótese.

**Independent Test**: a decomposição PCA e a regressão de fatores podem
ser testadas isoladamente sobre uma matriz de retornos sintética com
estrutura de fator conhecida.

**Acceptance Scenarios**:

1. **Given** os retornos padronizados de todos os ativos do universo na
   fatia de treino, **When** decompostos por PCA, **Then** o número de
   componentes usados explica pelo menos 55% da variância total, até um
   teto de 10 componentes.
2. **Given** os pesos de fator e os parâmetros do processo OU estimados
   só na fatia de treino, **When** aplicados à fatia de validação sem
   reajuste, **Then** o s-score da validação usa exatamente os mesmos
   parâmetros do treino.
3. **Given** a meia-vida do resíduo integrado de um ativo, **When** fora
   da faixa negociável já usada por H10, **Then** esse ativo é excluído
   da avaliação de estratégia, sem abortar os demais.
4. **Given** o s-score de um ativo, **When** cruza os limiares
   declarados (entrada ≤ −1,25, saída ≥ −0,5), **Then** um sinal de
   entrada ou saída é gerado, avaliado pela bateria comum E1-E6.
5. **Given** o veredito final por ativo, **When** registrado, **Then** o
   registro relata a limitação de não-hedge declarada e compara o padrão
   agregado com o resultado já reportado na literatura para cripto.

---

### Edge Cases

- **Ativo cuja meia-vida do resíduo é infinita ou negativa** (resíduo não
  reverte, passeio aleatório): excluído da avaliação de estratégia,
  reportado explicitamente como "sem reversão detectável", não como erro.
- **Matriz de retornos com histórico desalinhado entre ativos** (mesmo
  problema já catalogado por H10, spec 052): usa a mesma correção de
  interseção de índice já aplicada ao universo de histórico completo.
- **Poucos componentes principais explicam quase toda a variância**
  (fator BTC muito dominante, cenário esperado pela literatura): o
  critério de 55%/teto 10 ainda se aplica sem alteração — um resultado
  qualitativo esperado, não um caso a tratar diferente.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST decompor os retornos padronizados do
  universo declarado em componentes principais, usando componentes
  suficientes para explicar pelo menos 55% da variância total, até um
  teto de 10 componentes.
- **FR-002**: O sistema MUST estimar os pesos de fator e os parâmetros do
  processo Ornstein-Uhlenbeck do resíduo integrado somente sobre a fatia
  de treino, e aplicá-los sem reajuste à fatia de validação.
- **FR-003**: O sistema MUST filtrar ativos cuja meia-vida do resíduo
  integrado, estimada no treino, esteja fora da faixa já usada por H10
  (`backtesting/pairs_trading.py::PairsParams.meia_vida_min/meia_vida_max`)
  — reusando a função de estimativa de meia-vida já existente, sem
  reimplementar o estimador.
- **FR-004**: O sistema MUST gerar sinal de entrada quando o s-score
  cruza ≤ −1,25 e sinal de saída quando cruza ≥ −0,5 — limiares fixados
  antes de medir, não ajustados.
- **FR-005**: O sistema MUST avaliar cada ativo individualmente pela
  bateria comum (`backtesting/bateria_hipotese.py::rodar_bateria`,
  E1-E6), sem reimplementar a orquestração por conta própria.
- **FR-006**: O sistema MUST relatar explicitamente, no resultado e no
  registro final, que a implementação é uma aposta direcional sem hedge
  contra os fatores — diferente do método original dollar-neutral.
- **FR-007**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/`, `risk/` ou a estratégia em produção.
- **FR-008**: O sistema MUST registrar o veredito final, por ativo e
  agregado, em `docs/research/registro-de-hipoteses.md`, comparando o
  padrão observado com o resultado já reportado na literatura para
  cripto.

### Key Entities

- Reaproveita `BacktestResult`/`RelatorioBateria` (já existentes) para o
  veredito por ativo — nenhuma entidade de rotulagem nova.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma execução única produz o `RelatorioBateria` completo
  (E1-E6) para cada ativo do universo cuja meia-vida de resíduo caia na
  faixa negociável.
- **SC-002**: O registro documenta, por ativo e agregado, se o sinal
  sobrevive às seis etapas — e relata explicitamente a limitação de
  não-hedge (FR-006) e a comparação com a literatura (FR-008).
- **SC-003**: Nenhuma ordem real é enviada; o comportamento de produção
  permanece idêntico ao anterior a esta feature.

---

## Assumptions

- **Universo**: `UNIVERSO_AMPLO_HISTORICO_COMPLETO` (22 pares, mesmo de
  H10/H29) — sem universo novo.
- **Número de componentes, limiares de entrada/saída e faixa de
  meia-vida**: valores clássicos do paper original e da disciplina já
  estabelecida por H10, reusados sem reajuste — decisão técnica de como
  exatamente implementar a estimação (OLS, AR(1)) cabe ao
  `/speckit-plan`.
- **Sem hedge dos fatores**: decisão de escopo já declarada na
  fundamentação (limitação estrutural do bot long-only), não uma escolha
  aberta ao plano técnico.
- Resultado desta spec não substitui nenhum veredito já publicado — ataca
  um mecanismo (decomposição de fator muitas-para-muitas) nunca testado
  antes neste registro.
