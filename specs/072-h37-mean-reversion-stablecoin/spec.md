# Feature Specification: H37 — Mean reversion em par de stablecoin (USDC/USDT)

**Feature Branch**: `072-h37-mean-reversion-stablecoin`

**Created**: 2026-09-06

**Status**: Draft

**Input**: User description: USDC/USDT é um símbolo negociável na Binance
hoje, nunca testado neste registro. Literatura documenta desvios de
US$0,003-0,010 do par revertendo em minutos por arbitragem de resgate —
instrumento categoricamente diferente de qualquer par já testado
(volatilidade quase nula, reversão determinística por design do emissor).
Obstáculo esperado: janelas de arbitragem duram segundos, dominadas por
bots MEV — mesmo padrão que já zerou H15/H22. Custo quase zero: roda o
motor de reversão à média já existente (H3, `strategy/mean_reversion.py`,
sem nenhuma mudança de código) sobre `USDC/USDT`, único par avaliado.
Terceira hipótese da leva H34-H40 (deepsearch 2026-09-06).

---

## Contexto e tese

**Por que isso é diferente de H3 nos outros pares.** H3 (Bollinger+RSI)
já foi testada e reprovada em BTC/SOL/ETH (pior desempenho do conjunto
original, win rate 20-31%) — mas nesses pares a reversão esperada é
comportamental (preço "esticado" volta à média por dinâmica de mercado).
Em `USDC/USDT`, a reversão alegada pela literatura é DETERMINÍSTICA — o
emissor da stablecoin garante resgate 1:1, então qualquer desvio do par
tem um mecanismo de arbitragem estrutural puxando de volta, não
comportamento de trader. É a mesma estratégia (H3, sem alteração), aplicada
a um instrumento com mecanismo de reversão categoricamente diferente —
por isso vale medir de novo, não é repetir H3.

**Obstáculo já declarado pela própria literatura.** As janelas de
arbitragem em stablecoins "duram segundos", dominadas por bots MEV —
mesma limitação estrutural que já zerou H15 e H22 (arbitragem pura já
testada e refutada por latência/competição). O motor de backtest deste
projeto opera em candles de 4h; se a reversão realmente dura segundos,
nenhum candle de 4h consegue capturar entrada e saída dentro da mesma
janela de reversão — a estratégia BB+RSI de H3 não foi desenhada para
esse horizonte, e a expectativa honesta é que ela não capture nada.

**Hipótese declarada antes de medir.** A estratégia de reversão à média já
existente (H3, inalterada) produz resultado positivo e consistente sobre
`USDC/USDT` quando avaliada pela bateria comum E1-E6.

**Hipótese alternativa, com peso igual.** A reversão real do par acontece
numa escala de tempo (segundos) que nenhum candle de 4h consegue capturar
— o resultado é indistinguível de ruído em torno de um preço
estruturalmente estável, sem sinal capturável no horizonte do bot.
Reprovação aqui teria valor de descartar a família com evidência própria,
não apenas citar a literatura de terceiros.

**Zero mecânica de trading nova.** Reusa `strategy/mean_reversion.py`
(H3) sem nenhuma alteração de código — apenas aplicada a um símbolo novo,
através do harness comum já usado por H34. Não toca `trading/`,
`execution/`, `risk/` nem a estratégia em produção
(`strategy/ema_rsi.py`).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Veredito completo E1-E6 sobre H3 aplicada a USDC/USDT (Priority: P1)

O pesquisador obtém, numa única execução, se a estratégia de reversão à
média já existente (sem alteração) produz vantagem real sobre
`USDC/USDT`, com o quadro completo das seis etapas da bateria (sanidade,
janela única, busca/confirmação fora da amostra, walk-forward, desconto
de exposição, sensibilidade a custo).

**Why this priority**: é a pergunta da hipótese; sem isso não há veredito.

**Independent Test**: a estratégia já é testada isoladamente em
`tests/test_mean_reversion.py` (existente, sem mudança) — este teste cobre
só a integração com o harness comum sobre o símbolo novo.

**Acceptance Scenarios**:

1. **Given** o histórico de `USDC/USDT` disponível na Binance, **When** a
   bateria completa (E1-E6) roda sobre ele com a estratégia de reversão à
   média inalterada, **Then** cada uma das seis etapas é reportada
   individualmente, com status explícito por etapa.
2. **Given** um teste de sanidade E1 com série sintética construída para
   nunca tocar a banda inferior em sobrevenda (preço constante, sem
   volatilidade), **When** a bateria roda sobre essa série, **Then** zero
   entradas ocorrem.
3. **Given** o veredito final da bateria, **When** registrado, **Then** o
   registro compara explicitamente com o resultado original de H3 nos
   outros pares (BTC/SOL/ETH) — nunca apresentado como achado isolado sem
   essa comparação.

---

### Edge Cases

- **Histórico de `USDC/USDT` insuficiente para dividir treino/validação**
  (par pode ter menos histórico que pares mais antigos): resultado
  reportado como inconclusivo por amostra — nunca aprovado por omissão de
  dado.
- **Preço efetivamente constante por longos períodos** (característica
  esperada de uma stablecoin bem administrada): Bollinger Bands podem
  colapsar para uma faixa extremamente estreita — o motor de backtest já
  existente lida com isso sem mudança (mesmo cálculo de indicador de
  qualquer outro par).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST avaliar `strategy/mean_reversion.py::MeanReversionStrategy`
  sobre `USDC/USDT` sem nenhuma alteração de código na estratégia.
- **FR-002**: O sistema MUST orquestrar a avaliação pela bateria comum
  (`backtesting/bateria_hipotese.py::rodar_bateria`, E1-E6), sem
  reimplementar a orquestração por conta própria.
- **FR-003**: O sistema MUST incluir um teste de sanidade (E1) com série
  sintética de preço constante/sem volatilidade, verificando zero trades.
- **FR-004**: O sistema MUST comparar o veredito final explicitamente com
  o resultado original de H3 (seção 4.4 do registro, BTC/SOL/ETH) no
  registro, para deixar claro que o instrumento — não a estratégia — é o
  que muda nesta hipótese.
- **FR-005**: O sistema MUST NOT enviar ordem real nem alterar `trading/`,
  `execution/`, `risk/` ou a estratégia em produção (`strategy/ema_rsi.py`).
- **FR-006**: O sistema MUST registrar o veredito final (conforme os
  status já padronizados por `evaluate_approval`/`classify`) em
  `docs/research/registro-de-hipoteses.md`.

### Key Entities

- Reaproveita `BacktestResult` e `RelatorioBateria` (já existentes) —
  nenhuma entidade de dado nova é necessária.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma execução única produz o `RelatorioBateria` completo
  (E1-E6) sobre `USDC/USDT`.
- **SC-002**: O registro documenta explicitamente se a reversão à média
  se sustenta em `USDC/USDT` ou não, e como isso se compara ao resultado
  original de H3 nos outros pares — nunca implícito.
- **SC-003**: Nenhuma ordem real é enviada; o comportamento de produção
  permanece idêntico ao anterior a esta feature.

---

## Assumptions

- **Sem universo multi-par**: diferente de H34/H35, esta hipótese é sobre
  um símbolo específico (`USDC/USDT`), não uma família de pares — um único
  par é avaliado, por desenho.
- **Parâmetros da estratégia**: os defaults já existentes de
  `MeanReversionStrategy` (RSI 14/30/70, Bollinger 20/2.0, sem filtro ADX)
  são reusados sem reajuste — reajustar parâmetros especificamente para
  este par seria otimizar até passar, o problema que a metodologia deste
  registro existe para impedir.
- **Timeframe e histórico**: mesmo `TIMEFRAME` padrão do projeto e mesma
  infraestrutura de coleta já usada por outras hipóteses da bateria
  (`data/fetcher.py`) — sem infraestrutura de dado nova.
- Resultado desta spec não substitui o veredito já publicado de H3 nos
  outros pares — ataca a pergunta "o mecanismo de reversão muda com um
  instrumento estruturalmente diferente", não repete a pergunta original.
