# Feature Specification: H14 — saída por barreira tripla em vez de trailing stop

**Feature Branch**: `056-h14-saida-barreira`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: A linha de overlays de risco sobre a
carteira de H14 fechou (specs 040-047) e a de filtro de confiança
também (spec 055, refutada) apontando para o mecanismo de saída como a
última frente aberta. A carteira sempre saiu por take-profit ATR + stop
trailing (mecanismo real de produção, decisão deliberada D7 de spec
037), mas o classificador foi treinado e medido contra uma barreira
tripla fixa (mesmos níveis de preço em ATR, mas stop nunca sobe e fecha
em 24 velas se nenhum lado tocar). Testar se substituir o mecanismo de
saída pela mesma barreira do treino fecha esse descasamento e resolve o
profit factor por trade, que nunca passou de 0,75 em nenhuma
configuração de risco testada.

---

## Contexto e tese

**O descasamento nunca foi medido, só declarado.** Spec 037/D7 decidiu
deliberadamente usar o mecanismo real de produção (trailing) "para medir
H14 tal como foi publicado" — decisão correta para aquele objetivo, mas
deixou uma pergunta em aberto sem resposta: o classificador prevê
`P(toca alvo antes do stop, barreira fixa, 24 velas)`, e a razão de
chances desse subconjunto decidido é real (0,70, spec 036/055). Sob a
mesma barreira que definiu esse "alvo", a expectativa em unidades de
ATR é positiva (`0,3894×3 − 0,5543×1,5 ≈ +0,337 ATR` por trade, ignorando
timeout). Mas a carteira nunca opera sob essa barreira — opera sob
trailing, uma estrutura de payoff diferente. O profit factor observado
(0,68-0,75) pode ser, em parte, o resultado de avaliar a previsão do
classificador sob um mecanismo diferente daquele que ela prevê.

**Hipótese declarada antes de medir.** Se o descasamento for uma causa
real do profit factor baixo, a saída por barreira produz profit factor
mais próximo de — ou acima de — 1,0, mesmo que ainda não aprove H14
sozinha (drawdown de carteira é uma pergunta distinta, D7 já apontou
isso).

**Hipótese alternativa, com igual peso.** Se o profit factor continuar
baixo mesmo sob a barreira que o classificador foi medido contra, o
problema não é descasamento de mecanismo de saída — é que a previsão do
classificador, mesmo dentro da própria definição de sucesso que ela usa,
não se traduz em capital real quando executada como uma sequência de
trades reais (custos, ordem de execução, concorrência de capital) —
fechando também esta frente.

**Mede uma estratégia diferente de H14 como publicado — D7 já é
explícito sobre isso.** Não substitui nenhum resultado anterior; é uma
pergunta nova sobre o mesmo classificador.

**Escopo mínimo.** Reusa `_simular_carteira_core` (`backtesting/
portfolio_h14.py`), novo parâmetro opcional `usar_saida_barreira`
(default `False`, preserva os nove resultados já publicados byte a
byte) + `limite_velas` (default `LIMITE_VELAS_PADRAO`, já existente em
`strategy/barreira_tripla.py`). Zero mecânica de dimensionamento,
correlação, circuit breaker ou limite diário — testado isolado, mesmo
princípio de uma-variável-por-vez das specs 040-047.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir o profit factor sob saída por barreira (Priority: P1)

O pesquisador obtém drawdown agregado, `total_trades` e profit factor de
carteira de H14 com a saída por barreira tripla fixa, comparado contra
o resultado já publicado sem overlay (spec 037: 931 trades, drawdown
28,66%, PF 0,72).

**Why this priority**: é a pergunta da hipótese.

**Independent Test**: `_simular_carteira_core(usar_saida_barreira=True)`
sobre um cenário sintético fecha corretamente por (a) alvo fixo, (b)
stop fixo sem trailing, (c) limite de velas quando nenhum dos dois
toca — três invariantes testáveis sem dado real.

**Acceptance Scenarios**:

1. **Given** uma posição aberta sob `usar_saida_barreira=True`, **When**
   o preço sobe sem tocar o alvo, **Then** o stop **não** sobe (fica
   fixo no nível calculado na entrada) — diferente do trailing.
2. **Given** a mesma posição, **When** nenhuma barreira é tocada por
   `limite_velas` candles, **Then** a posição fecha a mercado com motivo
   próprio ("Limite de tempo (barreira)"), distinto de "Fim do período".
3. **Given** `usar_saida_barreira=False` (default), **When** a carteira
   roda, **Then** reproduz o comportamento trailing já publicado, byte a
   byte.

---

### Edge Cases

- **Alvo e stop tocados no mesmo candle**: mesma regra de precedência já
  usada em `rotular()` e no motor de trailing existente (stop primeiro,
  OHLC agregado não permite saber a ordem real).
- **Posição ainda aberta ao fim dos dados, sem ter atingido `limite_velas`**:
  fecha como "Fim do período", mesmo rótulo já usado pelo motor
  existente — não é um caso novo.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST aceitar `usar_saida_barreira: bool = False`
  em `_simular_carteira_core`/`simular_carteira` — `False` reproduz o
  resultado já publicado byte a byte.
- **FR-002**: Quando `usar_saida_barreira=True`, o stop MUST permanecer
  fixo no nível calculado na entrada — nenhuma atualização de trailing.
- **FR-003**: Quando `usar_saida_barreira=True` e nenhuma barreira for
  tocada em `limite_velas` candles, a posição MUST fechar a mercado com
  motivo distinto de qualquer outro já existente.
- **FR-004**: O sistema MUST reportar o resultado ao lado do já
  publicado sem overlay (spec 037) — nunca substituindo.
- **FR-005**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/`.

### Key Entities

- **PosicaoCarteira**: ganha `velas_decorridas: int = 0` — conta candles
  decorridos desde a entrada, só incrementado sob `usar_saida_barreira`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `python main.py carteira_barreira` produz um
  `BacktestResult` sob saída por barreira, comparável ao já publicado.
- **SC-002**: O veredito de `evaluate_approval()` é registrado, sem
  critério novo.
- **SC-003**: O registro documenta explicitamente se o profit factor
  melhora, piora ou fica igual sob a barreira — não só se aprova.
- **SC-004**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Universo, capital, custo**: `UNIVERSO_H11` (12 pares), mesmos
  defaults de todas as specs anteriores de H14.
- Resultado desta spec não substitui nenhum veredito já publicado de
  H14 (mede uma estratégia diferente, D7) — soma-se ao registro.
- Se o profit factor melhorar mas não aprovar sozinho, o passo natural
  seguinte é combinar com o gate de correlação (spec 042) — não coberto
  aqui, mesma disciplina de uma-variável-por-vez.
