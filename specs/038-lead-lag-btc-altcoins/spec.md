# Feature Specification: H21 — Lead-lag BTC para altcoins

**Feature Branch**: `038-lead-lag-btc-altcoins`

**Created**: 2026-09-02

**Status**: Draft

**Input**: User description: H21 — o retorno do BTC no candle de 4h
anterior lidera o retorno da altcoin no candle seguinte. Medido antes
desta spec (2000 candles, 12 pares, dados reais): defasagem de 1 candle
prevendo o candle seguinte é a combinação mais forte e mais consistente —
correlação média 0,0445, positiva em 100% dos 11 pares (excluindo BTC).
Fundamentação: "Price Transmission from Bitcoin to Altcoins" (*Asia-Pacific
Financial Markets*, Springer 2026), causalidade de Granger unidirecional
BTC→altcoins.

---

## Contexto e tese

**Tese.** O BTC lidera o mercado cripto — seu retorno recente carrega
informação sobre o retorno futuro de altcoins de menor liquidez, que
reagem com atraso. Estruturalmente diferente de H7 (momentum do **próprio**
par, carteira) e do oposto de H10 (aposta em **reversão** de um spread,
não continuação). Comprar a altcoin quando o BTC acabou de subir aposta
que a alta "contagia" o par.

**Por que a defasagem foi medida antes do código.** Rodar
`fetch_ohlcv` sobre os 12 pares de `UNIVERSO_H11` (2000 candles de 4h,
dados reais) e cruzar o retorno defasado do BTC (`pct_change(N)`) contra o
retorno futuro de cada altcoin (`pct_change(M).shift(-M)`), para
N ∈ {1,2,3,4,6,8,12} e M ∈ {1,2,3}: a combinação N=1/M=1 tem a maior
correlação média (0,0445) **e** é positiva em 100% dos 11 pares — a única
combinação com esse grau de consistência. Fraca em magnitude (a defasagem
explica bem menos de 1% da variância do retorno futuro), mas o sinal do
efeito é robusto entre pares, o que justifica testar a hipótese formalmente
em vez de descartá-la ou de escolher a defasagem depois de ver o resultado
do backtest.

**Escolha do critério de entrada.** Sinal binário (BTC subiu ou não no
candle anterior), não um limiar de magnitude — o critério medido é sobre o
**sinal** da correlação, não sobre uma magnitude específica de retorno do
BTC. Introduzir um limiar de magnitude sem medição própria seria o mesmo
erro que o registro já corrigiu antes (M13: comparar estimativa pontual
sem evidência — aqui, ajustar um número sem testar se ele generaliza).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir o lead-lag com o motor de backtest já existente (Priority: P1)

O pesquisador obtém, para cada uma das 11 altcoins de `UNIVERSO_H11`
(excluindo BTC/USDT), o veredito (aprovado/reprovado/inconclusivo) de uma
estratégia cujo único sinal de entrada é "o BTC fechou em alta no candle
de 4h anterior" — usando o mesmo motor de métricas e o mesmo critério de
aprovação já usados por toda avaliação deste registro.

**Why this priority**: é a pergunta da hipótese. Reusar
`Trade`/`BacktestResult`/`evaluate_approval`/`edge_score` sem alteração é
o que torna o resultado comparável a H1-H20 — um critério novo só para
H21 reabriria a porta que este projeto já fechou (`compare`, `CLAUDE.md`:
"sem critério de comparação novo").

**Independent Test**: rodar a avaliação sobre um par com uma série de BTC
sintética determinística (retorno positivo/negativo alternado) e confirmar
que o sinal de compra dispara exatamente nos candles em que o retorno do
BTC do candle anterior é positivo, nunca nos demais.

**Acceptance Scenarios**:

1. **Given** o histórico de BTC/USDT e de uma altcoin do universo,
   **When** o retorno de fechamento-a-fechamento do BTC nesse mesmo
   candle (FR-001) é positivo, **Then** a estratégia emite BUY para a
   altcoin nesse candle, ao seu próprio fechamento — nunca quando o
   retorno do BTC é negativo ou zero.
2. **Given** uma posição aberta pela estratégia, **When** o preço toca o
   take-profit por ATR ou o stop trailing (mesmo mecanismo genérico já
   usado em toda avaliação do projeto, `simulate_backtest`), **Then** a
   posição fecha — a estratégia nunca emite sinal de venda próprio (mesmo
   padrão já usado pelos sinais do classificador de H14).
3. **Given** o `BacktestResult` produzido para um par, **When**
   `evaluate_approval()` roda sobre ele, **Then** aplica os mesmos
   limiares já usados por `compare`/`scan`/`grid`/`carteira` — sem
   parâmetro de aprovação novo.

---

### User Story 2 - Confirmar consistência entre pares (Priority: P2)

O pesquisador vê, junto ao veredito por par, quantos dos 11 pares
individualmente mostram vantagem na mesma direção — respondendo se o
efeito medido na correlação (positivo em 100% dos pares) se traduz em
vantagem de backtest de forma igualmente consistente, ou concentrada em
poucos pares.

**Why this priority**: a correlação medida na Fase 0 é fraca em magnitude;
saber se o resultado de backtest é amplamente consistente ou depende de 1-2
pares específicos muda a interpretação — mesmo princípio já usado em H11
("o achado real está na comparação entre janelas", não só no agregado).

**Independent Test**: contar, sobre o resultado real dos 11 pares, quantos
têm `total_return_pct` acima do respectivo `buy_hold_return_pct` e quantos
têm `profit_factor` acima de 1,0 — sem inventar um limiar de "consistência"
novo, só reportar a contagem já derivável do resultado de US1.

**Acceptance Scenarios**:

1. **Given** os 11 resultados por par, **When** o resumo é reportado,
   **Then** mostra quantos pares individualmente superam o respectivo
   buy-and-hold e quantos têm profit factor acima de 1,0 — números
   descritivos, não um veredito agregado novo.

---

### Edge Cases

- **Retorno do BTC exatamente zero no candle anterior.** Não dispara BUY
  (a condição é estritamente `> 0`, não `>= 0`) — consistente com o sinal
  medido (positivo vs. não-positivo), sem caso especial.
- **BTC e a altcoin com candles em timestamps diferentes** (gap de
  listagem, manutenção da exchange). O candle da altcoin sem retorno de
  BTC correspondente não recebe sinal (tratado como dado ausente, nunca
  como retorno zero) — mesmo princípio de "dado ausente nunca aprova por
  omissão" já usado no projeto.
- **Par com preço abaixo de `MIN_PRICE_USDT`.** Mesmo tratamento já
  existente (`BacktestResult.below_min_price` → `evaluate_approval`
  devolve "inconclusivo", nunca "reprovado" por omissão).
- **Histórico do BTC mais curto que o da altcoin (não deveria ocorrer,
  mas verificado).** A interseção de índices define a janela avaliável —
  nunca estender o sinal do BTC além do que foi de fato medido.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST calcular o retorno de fechamento-a-fechamento
  do BTC/USDT no **mesmo candle** que está sendo avaliado para a altcoin
  (`close_btc[t] / close_btc[t-1] - 1`, D1) — o retorno mais recente do
  BTC conhecido no exato instante em que a altcoin fecha esse candle (os
  dois fecham simultaneamente na mesma grade de 4h da exchange), usado
  para decidir a entrada na altcoin **usando o fechamento desse mesmo
  candle**, apostando no candle seguinte da altcoin. Não é *lookahead*:
  nenhuma informação de um candle futuro é usada, só o retorno de um
  candle que acabou de fechar — mesma convenção de "negociar no
  fechamento" já usada por `simulate_backtest` em todo o projeto.
- **FR-002**: A estratégia MUST emitir BUY quando esse retorno for
  estritamente positivo, e HOLD em qualquer outro caso (incluindo zero) —
  nunca SELL.
- **FR-003**: A saída de cada posição MUST usar exatamente o mecanismo
  genérico já usado por todo o projeto — take-profit por ATR e stop
  trailing (`simulate_backtest`) — sem mecanismo de saída novo.
- **FR-004**: O sistema MUST avaliar os 11 pares de `UNIVERSO_H11`
  excluindo BTC/USDT — o par-sinal não é alvo de operação nesta hipótese.
- **FR-005**: O sistema MUST usar 6.000 candles de 4h (mesma infra da
  spec 036) para a avaliação real — a amostra de 2.000 candles usada na
  Fase 0 serviu só para escolher a defasagem, não para o veredito final.
- **FR-006**: O sistema MUST produzir um `BacktestResult` compatível com
  o motor existente (`Trade`, `_calculate_advanced_metrics`), reusando
  `evaluate_approval`/`edge_score` sem critério de aprovação novo.
- **FR-007**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/`.
- **FR-008**: Candle de altcoin sem retorno de BTC correspondente
  (interseção de índices) MUST ficar sem sinal (nunca BUY por omissão de
  dado).

### Key Entities

- **Retorno defasado do BTC**: série derivada de BTC/USDT (`close`),
  alinhada ao índice de candles de cada altcoin por interseção de
  timestamps (D1, mesma classe de alinhamento já usada no motor de
  carteira de H14, spec 037, D3) — nunca reamostrada ou interpolada.
- **`Trade`**/**`BacktestResult`** (reusados, `backtesting/engine.py`):
  cada entrada/saída via `simulate_backtest(precomputed_signals=...)`, o
  mesmo caminho já usado por H14 (`_simular_com_sinais`).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cada um dos 11 pares produz um veredito
  (aprovado/reprovado/inconclusivo) via `evaluate_approval()`, sem
  critério novo.
- **SC-002**: O resumo reporta quantos dos 11 pares superam o respectivo
  buy-and-hold e quantos têm profit factor acima de 1,0 (US2) — números
  descritivos derivados do resultado, sem veredito agregado inventado.
- **SC-003**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Defasagem e direção do sinal**: N=1 candle de 4h, sinal binário
  (`retorno > 0`), declarados em `research.md` (Fase 0) a partir de
  medição real sobre 2000 candles — não ajustados a um resultado de
  backtest.
- **Universo e histórico**: `UNIVERSO_H11` menos BTC/USDT (11 pares),
  6.000 candles de 4h (D1, spec 036) — mesmo teto já usado por
  H11/H14/H17/H37, para não escolher amostra favorável.
- **Sem filtros adicionais** (RSI, volume, tendência MTF): a hipótese
  testa o mecanismo de lead-lag isolado, mesmo princípio de H2/H3/H4
  (uma mecânica por spec, sem empilhar filtros novos sobre um resultado
  ainda não medido). Um filtro adicional, se justificado por um resultado
  ruidoso aqui, seria uma hipótese nova, não um ajuste desta.
- Reprovação ou resultado inconclusivo de H21 não invalida nenhuma
  hipótese anterior — é uma medição nova, independente, mesmo princípio já
  aplicado a H17/H18/H37 neste registro.
