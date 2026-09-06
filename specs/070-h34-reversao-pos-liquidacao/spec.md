# Feature Specification: H34 — Reversão pós-liquidação (padrão de vela: pavio + pico de volume)

**Feature Branch**: `070-h34-reversao-pos-liquidacao`

**Created**: 2026-09-06

**Status**: Draft

**Input**: User description: cascatas de liquidação forçada (traders
alavancados liquidados em cadeia) deixam assinatura observável em candles —
pavio longo (preço ultrapassa e volta), pico de volume muito acima da
média, recuperação rápida. Mecanismo é liquidação forçada de terceiros, não
previsão de direção do preço — categoricamente diferente de H1-H7/H13 (que
leem o mesmo OHLCV como sinal técnico de tendência/reversão). Não há dado
de liquidação real disponível (Binance não publica histórico livre de
`forceOrder`); o teste usa pavio+volume como proxy da cascata. Primeira
hipótese da leva H34-H40 (deepsearch 2026-09-06, `docs/research/registro-de-hipoteses.md` §6.1).

---

## Contexto e tese

**Por que isso é diferente de H1-H7/H13/H20.** As hipóteses técnicas já
testadas (crossover, Donchian, Bollinger+RSI, squeeze breakout, geometria de
barreira) leem o mesmo OHLCV como sinal de tendência ou reversão estatística
do preço. H34 lê o mesmo dado como assinatura indireta de um evento
mecânico de terceiros — liquidação forçada em cascata — não como previsão
de direção. A distinção importa porque o mecanismo alegado (forçado,
não-informacional) é categoricamente diferente do mecanismo das hipóteses
técnicas (comportamental/informacional), mesmo que o dado de entrada seja
idêntico.

**O obstáculo é conhecido antes de medir.** Não existe dado de liquidação
real acessível (Binance não publica histórico livre de `forceOrder`), então
o teste necessariamente usa um PROXY (pavio + pico de volume) em vez da
cascata medida diretamente. Isso cria um risco real e declarado: reproduzir
H3 (reversão à média via Bollinger+RSI, já reprovada, win rate 20-31%) com
um filtro de entrada diferente sobre o mesmo fenômeno de ruído estatístico
comum, sem testar de fato o mecanismo de liquidação alegado. Por isso o
limiar de pavio/volume que define o proxy MUST ser declarado antes de medir
qualquer resultado (mesma disciplina de H5/H13/H20) — nunca ajustado depois
de ver o resultado para "passar".

**Hipótese declarada antes de medir.** Um candle com pavio (inferior, no
sentido de compra) acima de um limiar fixo do seu próprio range E volume
acima de um múltiplo fixo da média, seguido de fechamento de recuperação,
antecede retorno positivo acima do baseline — testado através da bateria
comum E1-E6.

**Hipótese alternativa, com peso igual.** O proxy captura o mesmo ruído já
testado (e reprovado) por H3, e qualquer resultado positivo aparente não
sobrevive à divisão treino/validação nem ao walk-forward — resultado tão
válido quanto o positivo, dado que o objetivo é decidir a família, não
confirmar a tese.

**Zero mecânica de trading nova.** É um sinal de entrada alternativo
avaliado pela infraestrutura de backtest já existente — não toca
`execution/`, `risk/manager.py` nem a estratégia em produção
(`strategy/ema_rsi.py`).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Veredito completo E1-E6 sobre o padrão pavio+volume (Priority: P1)

O pesquisador obtém, numa única execução, se comprar após um candle que
casa com o proxy de reversão pós-liquidação (pavio + pico de volume +
fechamento de recuperação) supera o baseline de mercado, com o quadro
completo das seis etapas da bateria (sanidade, janela única, busca +
confirmação fora da amostra, walk-forward, desconto de exposição,
sensibilidade a custo) — nunca um único número que esconda divergência
entre etapas.

**Why this priority**: é a pergunta central da hipótese; sem isso não há
veredito.

**Independent Test**: a função de detecção do padrão (pavio/volume/
fechamento) pode ser testada isoladamente sobre candles sintéticos com
resposta conhecida (candle construído para bater o padrão exatamente vs.
candle que erra por uma margem pequena em cada um dos três critérios).

**Acceptance Scenarios**:

1. **Given** um candle com pavio inferior acima do limiar declarado, volume
   acima do múltiplo declarado da média e fechamento de recuperação, **When**
   o motor avalia o sinal, **Then** um sinal de entrada (proxy de reversão
   pós-liquidação) é gerado.
2. **Given** a bateria completa (`backtesting/bateria_hipotese.py::rodar_bateria`)
   rodando sobre o universo padrão de pesquisa, **When** a execução termina,
   **Then** cada uma das seis etapas (E1-E6) é reportada individualmente, com
   status explícito por etapa.
3. **Given** um teste de sanidade E1 com série sintética construída para
   nunca produzir pavio nem pico de volume, **When** a bateria roda sobre
   essa série, **Then** zero entradas ocorrem — o motor não pode confundir
   ruído comum com o padrão declarado.
4. **Given** o veredito final da bateria, **When** registrado, **Then** o
   registro compara explicitamente o resultado com H3 (mesma família de
   reversão à média) — nunca apresentado como achado isolado sem essa
   comparação.

---

### Edge Cases

- **Candle no período de warmup** (histórico insuficiente para calcular a
  média de volume): o sinal não dispara — nunca calcula sobre uma média
  incompleta.
- **Pavio e pico de volume presentes, mas o candle fecha em queda** (não há
  recuperação): não conta como sinal — o mecanismo alegado exige a
  recuperação, não só o pavio e o volume isolados.
- **Vários candles seguidos batendo o padrão** (cascata prolongada): cada
  candle é avaliado independentemente pelas mesmas regras de entrada já
  existentes (cooldown, `MAX_ENTRIES_PER_CYCLE`), sem lógica nova de
  agregação de sinais consecutivos.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST declarar, antes de qualquer medição, o limiar
  de pavio (proporção do range do candle) e o limiar de pico de volume
  (múltiplo da média) que definem o proxy — documentado no registro antes de
  rodar, nunca ajustado depois de ver o resultado.
- **FR-002**: O sistema MUST detectar o padrão exclusivamente a partir de
  OHLCV já coletado (pavio inferior, volume acima da média, fechamento de
  recuperação) — sem depender de nenhum dado de liquidação real (indisponível).
- **FR-003**: O sistema MUST orquestrar a avaliação pela bateria comum
  (`backtesting/bateria_hipotese.py::rodar_bateria`, E1-E6), sem reimplementar
  a orquestração por conta própria.
- **FR-004**: O sistema MUST incluir um teste de sanidade (E1) com dado
  sintético em que o padrão nunca ocorre, verificando zero trades — descarta
  falso positivo do motor antes de ler qualquer resultado como evidência.
- **FR-005**: O sistema MUST comparar o veredito final explicitamente com o
  de H3 (reversão à média via Bollinger+RSI, já reprovada) no registro, para
  não confundir reprodução do fenômeno já testado com achado novo.
- **FR-006**: O sistema MUST NOT enviar ordem real nem alterar `trading/`,
  `execution/`, `risk/` ou a estratégia em produção (`strategy/ema_rsi.py`).
- **FR-007**: O sistema MUST registrar o veredito final (conforme os status
  já padronizados por `evaluate_approval`/`classify`) em
  `docs/research/registro-de-hipoteses.md`.

### Key Entities

- Reaproveita `BacktestResult` e `RelatorioBateria` (já existentes em
  `backtesting/engine.py` e `backtesting/bateria_hipotese.py`) — nenhuma
  entidade de dado nova é necessária para este teste.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma execução única produz o `RelatorioBateria` completo
  (E1-E6) sobre o universo padrão de pesquisa.
- **SC-002**: O registro documenta explicitamente se o padrão pavio+volume
  sobrevive às seis etapas ou em qual delas reprova, e se o resultado
  diverge do de H3 ou o reproduz — nunca implícito.
- **SC-003**: Nenhuma ordem real é enviada; o comportamento de produção
  permanece idêntico ao anterior a esta feature.

---

## Assumptions

- **Limiares exatos de pavio/volume**: os valores numéricos específicos
  (ex.: pavio ≥ X% do range, volume ≥ Yx a média) são decisão técnica do
  `/speckit-plan`/`research.md` — esta especificação só exige que sejam
  fixados e documentados antes de qualquer medição (FR-001), não fixa os
  números.
- **Universo e timeframe**: reusa a infraestrutura de coleta e o universo de
  pares já usados pelas hipóteses recentes da bateria (`data/fetcher.py`,
  sem infraestrutura de dado nova) — escolha exata do universo/timeframe
  cabe ao plano.
- **Nenhuma infraestrutura de dado nova é necessária**: OHLCV já coletado
  via `ccxt`/`data/fetcher.py` cobre pavio, volume e fechamento — não requer
  fetcher novo (diferente de H35, que precisa de um endpoint novo).
- Resultado desta spec não substitui nenhum veredito já publicado — ataca um
  mecanismo (proxy de liquidação forçada) nunca testado antes neste registro.
