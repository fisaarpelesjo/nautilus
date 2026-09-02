# Feature Specification: Motor de carteira para aprovação de H14

**Feature Branch**: `037-motor-carteira-h14`

**Created**: 2026-09-02

**Status**: Draft

**Input**: User description: Motor de carteira para aprovação de H14
(aprendizado supervisionado, barreira tripla). A reavaliação de H14 em
`specs/036-historico-estendido/` (`docs/research/registro-de-hipoteses.md`
§4.15) mudou o veredito de INSUFICIENTE para "sinal confirmado" — o teste
que travava o resultado (razão de chances no subconjunto decidido supera o
empate, com confiança estatística) agora passa robustamente (z=+7,97, era
z=+0,50). A limitação que continua aberta: drawdown não pode ser agregado
entre os 12 pares porque cada avaliação roda isoladamente, cada uma com seu
próprio capital independente. Esta spec constrói um motor que simula os 12
pares simultaneamente, com capital compartilhado e concorrência real de
posições, para medir se o risco de carteira sustenta aprovação operacional.

---

## Contexto e tese

**O que já está resolvido.** H14 (`docs/research/registro-de-hipoteses.md`
§4.15) tem sinal estatisticamente robusto que paga as barreiras de custo —
isso nunca tinha acontecido em nenhuma hipótese direcional deste registro.
O modelo e o limiar de decisão já estão treinados e declarados; esta spec
não mexe neles. **Correção de leitura (2026-09-02, antes de qualquer
código desta spec):** as barreiras de alvo/stop/24-velas
(`strategy/barreira_tripla.py::rotular`) são usadas só para RÓTULO de
treino do classificador — o backtest publicado de H14
(`AvaliacaoH14.modelo.backtest`) mede desempenho através do motor genérico
já usado em todo o projeto (`backtesting/engine.py::simulate_backtest`),
que aplica take-profit por ATR e **stop trailing** (mesma fórmula de
produção, `trading/position_lifecycle.py::handle_open_position`), sem
limite de 24 velas. Ver D7, `research.md`.

**O que falta.** Cada avaliação de par em `backtesting/modelo.py::avaliar_par`
roda `_simular` (`backtesting/horizonte.py`) isoladamente, cada uma com seu
próprio capital inicial independente — como se fossem 12 contas separadas.
Nunca existiu um motor que simule os 12 pares com **um** caixa
compartilhado e concorrência real de posições, que é a única forma de medir
se o risco de carteira (não só o sinal estatístico por par) sustenta
aprovação de verdade. O próprio registro já explica por que somar ou
promediar 12 curvas de capital independentes não tem significado — a
resposta exige simular a carteira, não agregar depois.

**Por que agora.** É a última barra explícita que falta para H14
(`§4.15`, "Aprovação operacional... segue não avaliada"). Sem essa medição,
não é possível dizer se H14 é uma estratégia operável ou só um sinal
estatístico que desmorona sob concorrência real de capital.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Simular os 12 pares com capital compartilhado (Priority: P1)

O pesquisador obtém uma curva de capital única, resultado de simular os
sinais já treinados do modelo H14 sobre os 12 pares de `UNIVERSO_H11`
simultaneamente, avançando o tempo candle a candle na mesma linha do tempo,
com um único caixa disputado entre os pares — não 12 simulações
independentes somadas depois.

**Why this priority**: é a pergunta central da spec. Sem simulação
conjunta, qualquer número de drawdown produzido continuaria sendo drawdown
por par, exatamente a limitação já registrada em H14.

**Independent Test**: rodar a simulação sobre o histórico já usado por H14
(mesmo `UNIVERSO_H11`, mesmas 6.000 velas, spec 036) e obter uma curva de
capital com um único valor de caixa por candle, nunca 12 valores paralelos.

**Acceptance Scenarios**:

1. **Given** sinais de compra simultâneos em mais de um par no mesmo
   candle, **When** o caixa disponível não cobre todas as entradas no
   tamanho pleno, **Then** a simulação abre o que o caixa permite, na
   ordem de prioridade declarada (Assumptions), e não inventa capital.
2. **Given** uma posição aberta em um par, **When** o preço toca o
   take-profit por ATR ou o stop trailing (mesmo mecanismo já usado pelo
   backtest publicado de H14, D7), **Then** a posição fecha e o caixa
   liberado (mais/menos o resultado) volta a ficar disponível para
   qualquer par, não só o mesmo.

---

### User Story 2 - Decidir aprovação sobre o resultado agregado de carteira (Priority: P1)

O pesquisador obtém um veredito (aprovado/reprovado/inconclusivo) para H14
a partir do resultado de carteira, usando o mesmo `evaluate_approval()` já
usado por toda avaliação deste projeto — sem critério de aprovação novo
inventado para esta spec.

**Why this priority**: é a resposta que falta desde `§4.15`. Sem aplicar o
critério de aprovação já estabelecido sobre o resultado de carteira, a
spec produziria um número novo sem produzir uma decisão.

**Independent Test**: alimentar o resultado agregado em
`evaluate_approval()` e obter um veredito usando os mesmos limiares
(profit factor, drawdown, mínimo de trades, buy-and-hold) já aplicados em
`compare`/`scan`/`multibacktest`/H18.

**Acceptance Scenarios**:

1. **Given** o resultado de carteira agregado, **When** `evaluate_approval()`
   roda sobre ele, **Then** o veredito usa exatamente os limiares já
   declarados no projeto, sem parâmetro novo.

---

### User Story 3 - Comparar drawdown de carteira contra drawdown por par isolado (Priority: P2)

O pesquisador vê, lado a lado, o drawdown máximo agregado de carteira e o
maior drawdown entre os 12 resultados isolados por par já registrados em
H14 — expondo se concorrência real de capital piora, melhora ou pouco muda
o risco em relação à visão par a par.

**Why this priority**: é o que transforma o número novo em achado
interpretável — sem essa comparação explícita, o leitor do registro não
sabe se a concorrência de capital foi o fator decisivo ou não.

**Independent Test**: apresentar o drawdown agregado e o drawdown máximo
por par (já disponível nos relatórios de H14) na mesma unidade e mesmo
período, sem recálculo escondido.

**Acceptance Scenarios**:

1. **Given** o drawdown agregado de carteira e os drawdowns por par já
   registrados, **When** o resultado é reportado, **Then** os dois números
   aparecem juntos, explicitamente rotulados, sem um substituir o outro
   silenciosamente no registro.

---

### Edge Cases

- **Mais sinais de compra simultâneos que slots livres.** Resolvido pela
  ordem de prioridade declarada antes de medir (Assumptions) — nunca
  escolhida depois de ver o resultado.
- **Caixa insuficiente para o tamanho mínimo de ordem, mesmo com slot
  livre.** A simulação não abre a posição; é sinal perdido por falta de
  capital, registrado explicitamente — não erro silencioso nem posição
  fantasma.
- **Posição aberta quando o histórico termina.** Fechada a mercado no
  último candle disponível — mesma convenção já usada em H18
  (`backtesting/grid.py`, "Fim do período").
- **Par com preço abaixo de `MIN_PRICE_USDT`.** Mesmo tratamento já
  existente no motor de backtest (`BacktestResult.below_min_price` →
  `evaluate_approval` devolve "inconclusivo", nunca "reprovado" por
  omissão).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST simular os 12 pares de `UNIVERSO_H11`
  simultaneamente, avançando candle a candle na mesma linha do tempo — não
  par a par sequencial com resultados somados depois.
- **FR-002**: O sistema MUST usar as probabilidades já treinadas pelo
  modelo de H14 (`avaliar_par`, mesmos atributos, mesmo limiar de decisão)
  — sem retreinar nem promover atributo novo.
- **FR-003**: A saída de cada posição MUST usar exatamente o mecanismo já
  usado pelo backtest publicado de H14 — take-profit por ATR
  (`ATR_TP_MULTIPLIER`) e stop trailing (mesma fórmula de
  `simulate_backtest`/produção) — nunca as barreiras de rotulagem do
  treino (alvo/stop/24-velas, um mecanismo diferente, D7) nem um
  mecanismo de saída inventado para esta spec.
- **FR-004**: O sistema MUST manter um único caixa compartilhado entre os
  12 pares — nunca capital independente por par.
- **FR-005**: O dimensionamento de cada posição MUST reusar a fórmula já
  documentada (`CLAUDE.md`): `min(MAX_ORDER_SIZE_USDT, (caixa /
  slots_livres_restantes) * 0.95)`.
- **FR-006**: O sistema MUST respeitar `MAX_POSITIONS` como teto de
  posições simultâneas — mesmo parâmetro de produção, não um valor novo
  para esta spec.
- **FR-007**: O sistema MUST NOT incluir checagem de correlação entre
  posições, checagem de liquidez/order-book, trailing stop, circuit
  breaker, nem limites de drawdown diário/semanal/mensal — escopo
  deliberadamente estreito para isolar se o problema (se houver) é do
  sinal de H14 ou da pilha de risco operacional inteira.
- **FR-008**: O sistema MUST produzir uma única curva de capital agregada
  (nunca soma nem média de curvas independentes) e um drawdown máximo
  agregado calculado sobre essa curva única.
- **FR-009**: O sistema MUST aplicar `evaluate_approval()` (já existente)
  sobre o resultado agregado — sem critério de aprovação novo.
- **FR-010**: O sistema MUST NOT enviar ordem real nem alterar `trading/`,
  `execution/` ou `risk/`.
- **FR-011**: Quando sinais de compra simultâneos excederem o caixa
  disponível ou os slots livres, o sistema MUST resolver pela ordem de
  prioridade declarada em Assumptions — nunca por ordem arbitrária de
  iteração não declarada.

### Key Entities

- **Carteira simulada**: caixa único, posições abertas por par (até
  `MAX_POSITIONS`), e a curva de capital agregada candle a candle —
  substitui as 12 simulações independentes de `avaliar_par`/`_simular`
  para efeito de medir drawdown.
- **`Trade`**/**`BacktestResult`** (reusados, `backtesting/engine.py`):
  cada entrada/saída de posição vira um `Trade`; o resultado agregado usa
  `_calculate_advanced_metrics()` já existente — sem estrutura nova.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma curva de capital agregada única e um drawdown máximo
  agregado real são produzidos a partir da simulação conjunta dos 12
  pares.
- **SC-002**: `evaluate_approval()` decide aprovado/reprovado/inconclusivo
  sobre esse resultado agregado, usando os mesmos limiares já em uso em
  qualquer outra avaliação do projeto.
- **SC-003**: O drawdown agregado de carteira é reportado lado a lado com
  o maior drawdown por par isolado já registrado em H14, na mesma unidade
  e período — expõe se a concorrência de capital piora, melhora ou pouco
  muda o risco em relação à visão par a par.
- **SC-004**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Universo, mecanismo de saída e histórico**: `UNIVERSO_H11` (12 pares),
  mesmo mecanismo de saída já usado pelo backtest publicado de H14
  (take-profit por ATR + stop trailing, D7) e mesmas 6.000 velas (D1, spec
  036) — sem escolha nova de amostra que pudesse favorecer um resultado.
- **Capital inicial**: mesmo valor default já usado pelo motor de
  backtest existente (`backtesting/engine.py`) — declarado exatamente em
  `research.md`, Fase 0, antes de qualquer medição.
- **Ordem de prioridade quando sinais excedem capital/slots livres**:
  prioriza pela probabilidade prevista pelo modelo (mais alta primeiro) —
  critério derivado do próprio sinal já calculado, não arbitrário, e
  declarado antes de qualquer execução.
- **Modelo reusado tal como treinado por `avaliar_par`**: esta spec não
  retreina, não promove atributo novo, não muda limiar de decisão.
- **Reprovação ou resultado inconclusivo desta spec não invalida o achado
  estatístico já registrado em H14 (§4.15)** — é uma pergunta diferente
  (risco de carteira sob concorrência de capital vs sinal estatístico por
  par), mesmo princípio já aplicado a H17/H18 neste registro.
