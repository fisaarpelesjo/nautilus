# Feature Specification: H35 — Crowding via long/short ratio e open interest (Binance)

**Feature Branch**: `071-h35-crowding-long-short`

**Created**: 2026-09-06

**Status**: Draft

**Input**: User description: os endpoints públicos de long/short ratio e
open interest (Binance futures, sem chave) medem posicionamento bruto —
contas compradas vs. vendidas e capital comprometido — categoricamente
diferente de funding rate (H8/H26, mede o CUSTO da posição, não o
posicionamento). Extremos de long/short ratio são citados na literatura
como indicador contrário de crowding. Mecanismo contrário, long-only (mesma
família de H26): ratio no decil mais baixo do próprio par (crowded short) é
sinal contrário de squeeze — aposta LONG. Open interest confirma capital
real comprometido. Achado empírico crítico desta sessão (probe real via
ccxt, 2026-09-06): os dois endpoints retêm só ~31 dias de histórico (186
candles de 4h), independente do timeframe pedido — muito menor que os 2000
candles usados por H8/H14/H26 (funding rate tem retenção completa). Segunda
hipótese da leva H34-H40 (deepsearch 2026-09-06).

---

## Contexto e tese

**Por que isso é diferente de H8/H23/H24/H26.** Funding rate (H8/H23/H24)
mede o CUSTO de manter uma posição — o que o mercado cobra para ficar
posicionado. Long/short ratio e open interest medem o POSICIONAMENTO em si
— quantas contas estão de que lado e quanto capital está comprometido.
H26 (funding extremamente negativo → long contrário) e H35 usam a mesma
lógica de crowding contrário, mas sobre uma variável de mercado
categoricamente distinta — custo vs. posição — mesmo que ambas apontem para
o mesmo tipo de aposta (contrária, long-only).

**Achado empírico que redesenha o teste antes de medir qualquer resultado
de estratégia.** Um probe real contra os endpoints (`fetch_long_short_ratio_history`/
`fetch_open_interest_history` via `ccxt`, símbolo `BTC/USDT:USDT`,
timeframes 4h e 1d, `limit=500`) mediu retenção de exatamente ~31 dias
(186 candles de 4h) em ambos os endpoints — teto do próprio endpoint
público da Binance, não do parâmetro de paginação. Isso é
drasticamente menor que os 2000 candles (~333 dias) que H8/H14/H26 usam
com funding rate (retenção completa, sem teto). Com 186 candles por par,
um split treino/validação por par no padrão de `MIN_WINDOW_CANDLES=150`
usado pelo harness comum (`backtesting/bateria_hipotese.py`) é inviável
(186 < 2×150). O desenho segue, em vez disso, o mesmo padrão já usado por
H26 (`backtesting/funding_reversao.py`): eventos agrupados (pooled) entre
os pares do universo declarado, limiar calibrado só no treino (recorte
temporal dentro da própria janela curta), aplicado sem reajuste na
validação, significância via intervalo de confiança sobre a contagem
agregada — não um número pontual isolado por par.

**Hipótese declarada antes de medir.** Um evento de long/short ratio no
decil mais baixo do próprio par (crowded short), com open interest acima da
mediana da janela de treino do próprio par no mesmo instante, antecede
retorno positivo (barreira de alvo tocada antes da de stop) com frequência
acima do ponto de equilíbrio da relação risco/retorno do bot.

**Hipótese alternativa, com peso igual.** A mesma base rate que já reprovou
22 hipóteses direcionais consecutivas neste registro (H26 foi a mais
recente) se repete aqui — o dado subjacente é novo, mas o padrão de
resultado (nenhuma vantagem direcional sobrevive à confirmação fora da
amostra) não muda. Resultado esperado como mais provável, declarado antes
de medir; a medição decide, não a expectativa.

**Zero mecânica de trading nova.** Reusa a barreira tripla já usada por
H14/H20/H26 para rotular o resultado de cada evento — não toca
`trading/`, `execution/`, `risk/` nem a estratégia em produção.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Veredito pooled sobre crowding via posicionamento (Priority: P1)

O pesquisador obtém, numa única execução, se o evento "long/short ratio no
decil mais baixo do próprio par + open interest acima da mediana de treino"
antecede mais acertos (barreira de alvo) que erros (barreira de stop) na
contagem agregada entre pares, com o limiar calibrado apenas no treino e
aplicado sem reajuste na validação.

**Why this priority**: é a pergunta da hipótese.

**Independent Test**: a função de detecção de evento pode ser testada
isoladamente sobre uma série sintética de long/short ratio e open interest
com decil e mediana conhecidos.

**Acceptance Scenarios**:

1. **Given** o histórico real disponível de long/short ratio e open
   interest para um par (limitado pela retenção do endpoint), **When** o
   limiar do decil mais baixo é calibrado sobre a fatia de treino, **Then**
   esse mesmo limiar numérico é aplicado sem reajuste sobre a fatia de
   validação.
2. **Given** os eventos de validação agregados entre todos os pares do
   universo declarado, **When** a contagem de alvo vs. stop é comparada
   contra o ponto de equilíbrio da relação risco/retorno do bot, **Then** o
   veredito usa o limite inferior do intervalo de confiança da fração de
   alvos, não a razão pontual isolada.
3. **Given** um par sem mercado de futuros perpétuo correspondente, **When**
   avaliado, **Then** é descartado do universo sem abortar a avaliação dos
   demais pares.
4. **Given** candles anteriores ao início real do histórico disponível de
   long/short ratio ou open interest, **When** alinhados ao candle, **Then**
   são descartados — nunca preenchidos retroativamente a partir do primeiro
   valor disponível.

---

### Edge Cases

- **Endpoint devolve menos histórico que o esperado para um par específico**
  (retenção pode variar por símbolo): a fatia de treino ou validação fica
  pequena demais para aquele par — o par contribui menos eventos à
  contagem agregada, nunca quebra a avaliação dos demais.
- **Open interest ausente num instante em que o long/short ratio existe**
  (séries podem não estar perfeitamente alinhadas no tempo): o evento não
  conta como confirmado — a ausência de confirmação nunca é tratada como
  confirmação positiva por omissão.
- **Par sem eventos no decil mais baixo dentro da janela de treino**: par
  contribui zero eventos, sem erro.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST buscar long/short ratio e open interest via os
  endpoints públicos de futuros da Binance, sem exigir credencial.
- **FR-002**: O sistema MUST medir e declarar a retenção real de histórico
  de cada endpoint antes de dimensionar qualquer janela de avaliação —
  nunca presumir a mesma retenção de `funding rate` (H8/H26).
- **FR-003**: O sistema MUST descartar candles anteriores ao início real do
  histórico disponível de long/short ratio ou open interest — nunca
  preencher retroativamente (forward-fill) a partir do primeiro valor
  disponível.
- **FR-004**: O sistema MUST calibrar o limiar do decil mais baixo de
  long/short ratio somente sobre a fatia de treino de cada par, e aplicar
  esse mesmo valor sem reajuste sobre a fatia de validação.
- **FR-005**: O sistema MUST exigir, além do limiar de long/short ratio,
  que o open interest no instante do evento esteja acima da mediana da
  janela de treino do próprio par — evento sem essa confirmação não conta.
- **FR-006**: O sistema MUST rotular o resultado de cada evento pela mesma
  barreira tripla já usada por H14/H20/H26, e agregar (pooled) a contagem
  de alvo/stop entre todos os pares do universo antes de aplicar o
  critério de significância — nunca decidir por um único par isolado.
- **FR-007**: O sistema MUST usar o limite inferior do intervalo de
  confiança da fração de alvos (não a razão pontual) para decidir se supera
  o ponto de equilíbrio da relação risco/retorno do bot.
- **FR-008**: O sistema MUST descartar, sem abortar a avaliação dos demais
  pares, qualquer par sem mercado de futuros perpétuo correspondente ou sem
  histórico suficiente para dividir treino/validação.
- **FR-009**: O sistema MUST NOT enviar ordem real nem alterar `trading/`,
  `execution/`, `risk/` ou a estratégia em produção (`strategy/ema_rsi.py`).
- **FR-010**: O sistema MUST registrar o veredito final em
  `docs/research/registro-de-hipoteses.md`, incluindo a retenção real
  medida do histórico (FR-002) como parte do resultado reportado.

### Key Entities

- **EventoCrowding**: par, instante, long/short ratio, open interest,
  limiar de decil aplicado (calibrado no treino), rótulo do resultado
  (alvo/stop/sem toque dentro do horizonte).
- Reaproveita `ParametrosBarreira`/rótulo bruto já existentes — nenhuma
  entidade de rotulagem nova.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma execução única produz a contagem agregada de
  alvo/stop na validação, entre todos os pares do universo declarado, mais
  o veredito de significância.
- **SC-002**: O registro documenta a retenção real medida de histórico dos
  dois endpoints (FR-002) e como ela limitou o desenho do teste — nunca
  presumida ou omitida.
- **SC-003**: Nenhuma ordem real é enviada; o comportamento de produção
  permanece idêntico ao anterior a esta feature.

---

## Assumptions

- **Retenção do endpoint**: medida empiricamente nesta sessão em ~31 dias
  (186 candles de 4h) para o par testado — o plano técnico mede/confirma
  para cada par do universo antes de fixar o desenho final, mas o pedido de
  histórico já assume essa ordem de grandeza, não os 2000 candles/333 dias
  usados por hipóteses baseadas em funding rate.
- **Universo**: mesmo conjunto de 12 pares já usado por H26
  (`UNIVERSO_H11`) — família direcional já estabelecida neste registro, sem
  necessidade de declarar um universo novo ad hoc.
- **Decil e mediana como limiares**: percentual exato do decil (10%, mesmo
  valor de H26) e o uso da mediana de treino para o filtro de open interest
  são decisão técnica do `/speckit-plan`/`research.md` — esta especificação
  exige que sejam fixados e documentados antes de medir (FR-004), não fixa
  os números aqui.
- Resultado desta spec não substitui nenhum veredito já publicado — ataca
  um mecanismo (posicionamento bruto, não custo de posição) nunca testado
  antes neste registro.
