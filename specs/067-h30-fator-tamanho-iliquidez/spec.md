# Feature Specification: H30 — fator de tamanho/iliquidez (cross-sectional, sem timing)

**Feature Branch**: `067-h30-fator-tamanho-iliquidez`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: literatura de factor investing em cripto
(Liu-Tsyvinski-Wu, já citada nas referências do registro) documenta
tamanho e iliquidez como os fatores com maior retorno cumulativo no
cross-section cripto — diferente de H7 (momentum transversal, já
testado e reprovado) e de H9 (prêmio de rebalanceamento, bloqueado por
correlação alta). Mecanismo: manter sistematicamente uma cesta de
tokens menores/menos líquidos (rebalanceada periodicamente), sem
qualquer componente de timing ou previsão — um TILT estrutural, não uma
estratégia ativa.

---

## Contexto e tese

**Por que isso é diferente de H7 e H9.** H7 (momentum transversal)
seleciona ativos por retorno passado — um componente de PREVISÃO
(aposta que o vencedor recente continua vencendo). H9 (prêmio de
rebalanceamento) exige correlação baixa/negativa entre ativos — medido
e refutado (correlação mediana 0,71 no universo disponível). H30 não
prevê nada e não depende de correlação baixa: mantém uma cesta
igualmente ponderada dos tokens de MENOR volume, rebalanceada num
intervalo fixo, testando se o tamanho/iliquidez em si carrega prêmio —
um tilt estrutural passivo, mais próximo de "qual universo segurar" do
que "quando comprar/vender".

**Hipótese declarada antes de medir.** A cesta ilíquida supera a cesta
líquida (mesma construção, mesmo universo, só o critério de seleção
inverte) em excesso de retorno, e esse excesso sobrevive tanto ao corte
de treino quanto ao de validação.

**Hipótese alternativa, com igual peso.** O próprio enunciado da
hipótese já assume o risco: iliquidez maior implica custo de execução
maior, e o "prêmio" pode ser inteiramente consumido por esse custo —
testado diretamente via sensibilidade a multiplicadores de slippage
(1x/3x/5x), não assumido.

**Zero mecânica de trading nova.** Não é uma estratégia de entrada/saída
— é construção de carteira (seleção + rebalanceamento periódico), sem
tocar em `strategy/`, `risk/`, `execution/` ou `trading/`.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Comparar cesta ilíquida vs. líquida em treino e validação (Priority: P1)

O pesquisador obtém retorno, drawdown e custo de giro de duas cestas
igualmente ponderadas (menor volume vs. maior volume) rebalanceadas
periodicamente, em treino e validação, sob três multiplicadores de
custo de slippage.

**Why this priority**: é a pergunta da hipótese.

**Independent Test**: `simular_cesta` sobre preços sintéticos com
valorização conhecida produz o retorno esperado; `selecionar_cesta`
ordena corretamente por volume médio.

**Acceptance Scenarios**:

1. **Given** o universo de 22 pares com histórico completo, **When**
   `avaliar_fator_tamanho` roda, **Then** devolve retorno/drawdown/custo
   para as duas cestas, em treino e validação, sob 3 multiplicadores de
   slippage — 12 resultados no total.
2. **Given** os dois cortes (treino/validação), **When** comparados,
   **Then** o excesso ilíquida-líquida é reportado separadamente para
   cada um — nunca um único número que esconda divergência entre eles.
3. **Given** preços constantes (sem movimento), **When** simulado,
   **Then** o capital final reflete só o custo de giro pago nos
   rebalanceamentos, nunca um ganho artificial.

---

### Edge Cases

- **Par sem dado num instante de rebalanceamento**: pulado nesse
  rebalanceamento específico, não aborta a simulação inteira.
- **Caixa insuficiente para completar uma compra**: a compra é limitada
  ao caixa disponível (parcial), nunca caixa negativo.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST selecionar a cesta por volume médio em
  USDT (`close × volume`) sobre a própria fatia de dados avaliada —
  nunca um ranking fixo calculado sobre o futuro.
- **FR-002**: O sistema MUST rebalancear a pesos iguais num intervalo
  fixo de candles, declarado antes de medir (`REBALANCE_A_CADA`).
- **FR-003**: O sistema MUST cobrar custo (taxa + slippage) sobre o
  GIRO de cada rebalanceamento, nunca sobre o nocional inteiro reaberto
  do zero.
- **FR-004**: O sistema MUST medir sob pelo menos três multiplicadores
  de slippage distintos — nenhum número único de custo é reportado como
  definitivo, dado que o backtest não tem acesso a order book histórico
  real.
- **FR-005**: O sistema MUST comparar a cesta ilíquida contra a mesma
  construção sobre a cesta líquida (baseline simétrico) — nunca contra
  buy-and-hold puro isoladamente.
- **FR-006**: O sistema MUST reportar treino e validação separadamente,
  usando o mesmo corte compartilhado de tempo já usado por H10
  (`split_treino_validacao`).
- **FR-007**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/`, `risk/` ou `strategy/`.

### Key Entities

- **ResultadoCesta**: critério, pares, nº de rebalanceamentos, capital
  inicial/final, retorno %, drawdown máximo %, custo total de giro,
  multiplicador de slippage aplicado.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `python main.py fator_tamanho` produz os 12 resultados
  (2 fatias × 2 critérios × 3 multiplicadores) numa tabela.
- **SC-002**: O registro documenta se o excesso ilíquida-líquida é
  positivo e consistente entre treino e validação, ou não — explícito,
  não implícito.
- **SC-003**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Universo**: `UNIVERSO_AMPLO_HISTORICO_COMPLETO` (22 pares,
  `backtesting/pairs_trading.py`) — já existente, já confirmado com
  histórico completo de 6.000 candles, evita o bug de colapso de índice
  comum já catalogado (H10, spec 052).
- **N=7, rebalance a cada 180 candles (30 dias)**: declarados antes de
  medir, não ajustados depois de ver o resultado.
- Resultado desta spec não substitui nenhum veredito já publicado —
  ataca um mecanismo (tilt estrutural por tamanho) nunca testado antes.
