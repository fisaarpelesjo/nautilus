# Feature Specification: Evolução da Estratégia

**Feature Branch**: `006-evolucao-estrategia-novas`

**Created**: 2026-08-15

**Status**: Draft

**Input**: User description: "Evolução da estratégia: novas capacidades testáveis via backtest com
dados públicos, sem depender de operação paper em tempo real. Escopo (`specs/BACKLOG.md` item 006,
derivado do `ROADMAP.md` Fase 4 itens 2-6): filtro Bollinger adaptativo; regime detection via
ADX(14); detecção de volatilidade elevada via ATR_ratio; nova `strategy/breakout.py`; comando de
comparativo entre estratégias e presets. Fora de escopo: validar o preset operacional atual em paper
mode real (Fase 4 item 1) — depende do operador rodar o bot por um período, não é testável só com
backtest."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Não perder dinheiro repetidamente em mercado lateral (Priority: P1)

Como operador do bot, eu quero que a estratégia reconheça quando o mercado está sem tendência clara
(lateralizado) e reduza ou suspenda entradas nesse regime, para não acumular perdas pequenas e
repetidas em condições onde EMA crossover historicamente perde dinheiro.

**Why this priority**: É a fraqueza mais conhecida e documentada da estratégia atual (EMA crossover
gera sinais falsos em lateralização) — resolver isso primeiro tem o maior potencial de melhorar o
resultado líquido, e as demais capacidades desta spec (Bollinger adaptativo, volatilidade) se
beneficiam de já saber o regime de mercado corrente.

**Independent Test**: Backtest comparando o mesmo par/período com e sem o filtro de regime ativo,
confirmando que o regime é calculado e registrado por candle e que entradas são suspensas ou
endurecidas quando o regime é lateralizado.

**Acceptance Scenarios**:

1. **Given** um candle com ADX(14) acima de um limiar configurável, **When** os indicadores são
   calculados, **Then** o regime desse candle é classificado como "trending".
2. **Given** um candle com ADX(14) abaixo de um limiar configurável, **When** os indicadores são
   calculados, **Then** o regime é classificado como "sideways" e novas entradas são suspensas ou
   passam a exigir confirmação adicional.
3. **Given** um backtest rodado com o filtro de regime ativo, **When** o relatório é exibido,
   **Then** o regime de cada ciclo/candle relevante fica disponível para análise (mesmo destino de
   `data/decisions.csv` já usado para outros bloqueios).

---

### User Story 2 - Adaptar stops e alvos à volatilidade do momento, não a um valor fixo por regime (Priority: P2)

Como operador do bot, eu quero que a estratégia meça a volatilidade relativa atual (`ATR_ratio =
ATR14 / close`) e ajuste alvos/stops ou bloqueie entradas em candles extremos quando a volatilidade
estiver anormalmente alta, para não operar com o mesmo risco fixo num candle calmo e num candle em
explosão de preço.

**Why this priority**: Extensão direta e de baixo risco sobre o ATR já calculado e já usado pelo risk
manager (`risk/manager.py`) — não introduz um indicador novo, só uma nova leitura do que já existe.

**Independent Test**: Backtest comparando o mesmo par/período com e sem a detecção de volatilidade
elevada ativa, confirmando que candles com `ATR_ratio` acima do limiar configurado são tratados de
forma diferente (bloqueio de entrada ou ajuste de alvo/stop) dos candles normais.

**Acceptance Scenarios**:

1. **Given** um candle com `ATR_ratio` acima de um limiar configurável, **When** um sinal de compra
   ocorreria normalmente, **Then** a entrada é bloqueada ou os níveis de stop/take-profit são
   recalculados de forma mais conservadora, de modo auditável (motivo específico registrado).
2. **Given** um candle com `ATR_ratio` dentro do intervalo normal, **When** os indicadores são
   calculados, **Then** o comportamento de stop/take-profit permanece o já existente (ATR ×
   multiplicador fixo).

---

### User Story 3 - Permitir rompimentos fortes sem abrir mão do filtro contra compra esticada (Priority: P3)

Como operador do bot, eu quero que o filtro de Bollinger Bands permita uma entrada acima da banda
superior quando a tendência e o volume estiverem claramente fortes, em vez de bloquear toda entrada
acima da banda, para não perder rompimentos legítimos comuns em cripto.

**Why this priority**: Refinamento de um filtro já existente (`not_overextended` em
`strategy/ema_rsi.py`), mais específico e menos amplo em impacto que os regimes P1/P2 — vem depois
por afetar um único ponto da lógica de entrada, não a decisão de operar ou não.

**Independent Test**: Backtest comparando o mesmo par/período com o filtro Bollinger fixo atual
(bloqueia sempre acima da banda superior) contra o filtro adaptativo (permite quando tendência e
volume estão fortes), confirmando a diferença no número e na qualidade dos trades.

**Acceptance Scenarios**:

1. **Given** um candle com preço acima da banda superior de Bollinger **e** tendência/volume fortes
   (mesmos critérios já usados na estratégia, ex: `above_trend` e `volume_ok`), **When** as demais
   condições de compra forem atendidas, **Then** a entrada não é bloqueada só por estar acima da
   banda superior.
2. **Given** um candle com preço acima da banda superior **e** tendência ou volume fracos, **When**
   as demais condições de compra forem atendidas, **Then** a entrada continua bloqueada, mesmo
   comportamento de hoje.

---

### User Story 4 - Comparar EMA/RSI contra uma estratégia de rompimento nos mesmos dados (Priority: P4)

Como operador do bot, eu quero uma nova estratégia de rompimento de faixa (`strategy/breakout.py`)
testável com a mesma infraestrutura de backtest já existente, para avaliar com evidência se ela supera
a estratégia atual em algum par ou período, em vez de assumir que EMA/RSI é a única abordagem válida.

**Why this priority**: Maior escopo de implementação desta spec (uma estratégia inteira nova) e o
menos urgente — só tem valor real depois que o comparativo (User Story 5) puder colocá-la lado a lado
com a estratégia atual sob as mesmas condições.

**Independent Test**: Backtest rodando `strategy/breakout.py` isoladamente nos mesmos pares/custos/
timeframes já usados para `EmaRsiStrategy`, confirmando que produz sinais BUY/SELL/HOLD válidos e que
o motor de backtest (`backtesting/engine.py`) processa o resultado sem mudanças.

**Acceptance Scenarios**:

1. **Given** uma janela de rompimento configurável (50, 150 ou 200 períodos), **When** o preço rompe
   a máxima (ou mínima) da janela, **Then** a estratégia gera um sinal BUY (ou SELL) consistente com
   a interface `BaseStrategy`/`TradeSignal` já existente.
2. **Given** os mesmos dados históricos de um par já usado no backtest da estratégia atual, **When**
   `strategy/breakout.py` é testada com `backtesting/engine.py`, **Then** o relatório é gerado sem
   erros, com as mesmas métricas já calculadas para qualquer outra estratégia (edge_score, Sortino,
   Calmar, etc.).

---

### User Story 5 - Escolher a estratégia/preset vencedor com um único comando, não comparações manuais (Priority: P5)

Como operador do bot, eu quero um comando que rode múltiplas estratégias/presets sobre os mesmos
pares, custos e timeframes numa única execução e compare os resultados lado a lado, para não correr o
risco de comparar resultados gerados em condições diferentes e escolher a estratégia mais recente em
vez da mais robusta.

**Why this priority**: Depende de existir mais de uma estratégia real para comparar de forma útil
(User Story 4) — tem valor incremental menor sozinha, mas fecha o ciclo desta spec ao tornar as
demais capacidades (regime, volatilidade, Bollinger adaptativo, breakout) comparáveis entre si de
forma objetiva.

**Independent Test**: Rodar o novo comando com pelo menos duas estratégias/presets configurados,
confirmando que o relatório final usa as mesmas métricas, benchmark (buy-and-hold) e critérios de
aprovação (`evaluate_approval`/`edge_score`) já estabelecidos nas specs anteriores, sem duplicar essa
lógica.

**Acceptance Scenarios**:

1. **Given** duas ou mais estratégias/presets configurados para comparação, **When** o comando roda,
   **Then** cada uma é testada nos mesmos pares, período, custos e timeframe, e o relatório mostra as
   métricas de todas lado a lado.
2. **Given** o relatório de comparação gerado, **When** o operador o lê, **Then** o veredito de
   aprovação de cada estratégia/preset usa o mesmo critério já estabelecido (`evaluate_approval`), não
   um critério novo e paralelo.

---

### Edge Cases

- O que acontece se o histórico disponível for menor que a maior janela de rompimento configurada
  (ex: 200 períodos) para `strategy/breakout.py`? → Mesmo tratamento já usado em outras estratégias
  para dados insuficientes (`Signal.HOLD`, motivo explícito), não um erro não tratado.
- O que acontece se ADX ou `ATR_ratio` não puderem ser calculados (poucos candles, dados incompletos)?
  → Mesmo princípio de segurança já aplicado a outras checagens desta base de código: dado
  desconhecido não pode virar aprovação silenciosa — o regime desconhecido deve ser tratado de forma
  conservadora (ex: como se fosse "sideways"), não "trending".
- O que acontece se o comando de comparativo (User Story 5) for chamado com uma única
  estratégia/preset? → Deve funcionar normalmente (relatório com um item só), não exigir um mínimo
  arbitrário de itens para comparar.
- O que acontece com o filtro Bollinger adaptativo (User Story 3) e a detecção de volatilidade
  elevada (User Story 2) quando ambos indicam decisões conflitantes no mesmo candle (ex: rompimento
  forte mas volatilidade extrema)? → A checagem de volatilidade elevada (proteção de risco) tem
  precedência sobre a permissão de rompimento (ganho de oportunidade) — mesmo princípio já aplicado
  nesta base de código de proteções bloqueando antes de qualquer ganho de oportunidade ser avaliado.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST calcular ADX(14) como indicador e classificar cada candle em um regime
  (`trending`, `sideways`, ou `indefinido` quando não puder ser calculado), com o limiar configurável.
- **FR-002**: O sistema MUST permitir suspender ou endurecer novas entradas quando o regime for
  `sideways`, mantendo o comportamento atual quando o regime for `trending`.
- **FR-003**: O sistema MUST registrar o regime de mercado em `data/decisions.csv` (ou destino
  equivalente já usado para diagnóstico de decisão por ciclo), para análise posterior.
- **FR-004**: O sistema MUST calcular `ATR_ratio = ATR14 / close` como indicador.
- **FR-005**: O sistema MUST bloquear a entrada ou ajustar os níveis de stop/take-profit de forma
  configurável quando `ATR_ratio` exceder um limiar configurável, com o motivo específico registrado.
- **FR-006**: O sistema MUST permitir uma entrada acima da banda superior de Bollinger quando
  tendência e volume estiverem fortes (mesmos critérios já usados na estratégia atual), mantendo o
  bloqueio quando não estiverem.
- **FR-007**: O sistema MUST implementar `strategy/breakout.py` herdando `BaseStrategy`, com janela de
  rompimento configurável (padrão testável em 50, 150 e 200 períodos), retornando `TradeSignal`
  compatível com a interface já existente.
- **FR-008**: O sistema MUST permitir rodar `strategy/breakout.py` através da mesma infraestrutura de
  backtest já existente (`backtesting/engine.py`), sem exigir mudanças no motor de backtest.
- **FR-009**: O sistema MUST oferecer um comando que rode múltiplas estratégias/presets sobre os
  mesmos pares, custos e timeframe numa única execução e compare os resultados usando as métricas e
  critérios de aprovação já estabelecidos (`evaluate_approval`/`edge_score`), sem duplicar essa
  lógica.
- **FR-010**: O sistema MUST manter compatibilidade com o comportamento atual de `EmaRsiStrategy` para
  quem não habilitar as novas capacidades (regime, volatilidade elevada, Bollinger adaptativo) — mudanças
  aditivas via configuração, não substituições forçadas do comportamento hoje validado.
- **FR-011**: Nenhuma tarefa desta spec MUST exigir dados privados, credenciais ou execução em
  `TRADING_MODE=live` para ser validada — toda validação funcional é feita via backtest com dados
  públicos da Binance.

### Key Entities

- **Regime de mercado**: classificação por candle (`trending`/`sideways`/`indefinido`), derivada de
  ADX(14) e um limiar configurável.
- **Indicador de volatilidade relativa**: `ATR_ratio`, derivado do ATR já calculado e do preço de
  fechamento.
- **Estratégia de rompimento**: `strategy/breakout.py`, nova implementação de `BaseStrategy` baseada
  em janelas de máxima/mínima configuráveis.
- **Relatório de comparação**: agregação de resultados de múltiplas estratégias/presets sob as mesmas
  condições, reutilizando as métricas e o veredito de aprovação já existentes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: É possível rodar um backtest do mesmo par/período com e sem cada uma das novas
  capacidades (regime, volatilidade elevada, Bollinger adaptativo) ativas e comparar o resultado, sem
  editar código manualmente entre uma execução e outra — só configuração.
- **SC-002**: `strategy/breakout.py` produz um relatório de backtest completo (mesmas métricas de
  qualquer outra estratégia) para pelo menos um par com histórico suficiente para a maior janela
  testada (200 períodos).
- **SC-003**: O comando de comparação de estratégias/presets produz um único relatório legível
  contendo o veredito de aprovação de cada item comparado, sem exigir que o operador rode backtests
  separados e compare manualmente.
- **SC-004**: A suíte de testes existente continua passando sem alteração de comportamento para quem
  não habilitar nenhuma das novas capacidades desta spec.

## Assumptions

- O limiar de ADX que separa `trending` de `sideways` (tipicamente citado como 20-25 em literatura de
  análise técnica) e o limiar de `ATR_ratio` considerado "elevado" não têm um valor único
  universalmente correto — ficam configuráveis via `.env`, com um default razoável documentado e
  sujeito a ajuste posterior via backtest/otimização (já suportado desde a spec 003).
- "Registrar regime em `data/decisions.csv`" reusa o padrão já estabelecido nessa spec anterior
  (colunas adicionais, não um arquivo novo) — mesma decisão de design já validada para `blockers` na
  spec 005.
- O comando de comparação (User Story 5) reutiliza `evaluate_approval`/`edge_score`
  (`backtesting/approval.py`, spec 002) como critério de veredito — não inventa uma métrica de
  comparação nova, para manter consistência com `edge`/`multibacktest`/`scan` já existentes.
- "Estratégia de rompimento" (User Story 4) usa a definição clássica de breakout de faixa (compra
  quando o preço rompe a máxima das últimas N velas, venda quando rompe a mínima ou por outro
  critério de saída já compatível com `position_lifecycle.py`) — não uma variante mais sofisticada
  (ex: com filtro de volume ou confirmação de fechamento), que fica como possível evolução futura se
  o backtest inicial mostrar potencial.
