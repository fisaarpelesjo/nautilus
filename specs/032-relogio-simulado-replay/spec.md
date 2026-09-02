# Feature Specification: Relógio simulado no replay

**Feature Branch**: `032-relogio-simulado-replay`

**Created**: 2026-09-02

**Status**: Draft

**Input**: User description: item 022 do `specs/BACKLOG.md` — cooldown,
drawdown (diário/semanal/mensal) e circuit breaker em
`execution/order_manager.py` usam `datetime.now()` (relógio real) em vez do
timestamp do candle simulado. Um replay de meses roda em segundos, então
esses períodos raramente viram durante a simulação, podendo estender
bloqueios além do que o bot real faria. Os timestamps de abertura/fechamento
dos trades do replay também são a hora real de execução do comando, não a
do candle. O próprio registro já observa que só vale a pena "se o replay
virar ferramenta central" — decisão do operador de puxar mesmo assim.

---

## Contexto

`trading/replay.py::run_replay()` roda o caminho de decisão real
(`handle_entry_candidate`/`handle_open_position`, spec 008) candle a candle
sobre histórico público, usando a mesma classe `OrderManager` da produção.
`execution/order_manager.py` chama `datetime.now()` diretamente em ~12
pontos: `set_cooldown`/`is_in_cooldown`, `_check_daily_reset`/
`_check_weekly_reset`/`_check_monthly_reset` (drawdown por período),
`_update_consecutive_losses`/`check_circuit_breaker_timeout` (circuit
breaker), e o valor default de `Position.opened_at` — todos com relógio
real, mesmo dentro de um replay que simula meses de histórico em segundos.

**Achado de auditoria adicional, além do que o item 022 já descrevia**:
`trading/replay.py::run_replay()` **nunca chama**
`manager.check_circuit_breaker_timeout()` — o loop de produção
(`trading/runner.py`) chama essa checagem a cada ciclo quando o breaker está
ativo; o replay não chama em nenhum ciclo. Consequência: hoje, uma vez que o
circuit breaker ativa durante um replay, ele **nunca** se autodesativa
dentro daquela execução, mesmo que o histórico simulado cubra várias vezes
`CIRCUIT_BREAKER_COOLDOWN_HOURS` — não é só "relógio errado", é "checagem
ausente". Isso entra no escopo desta spec (FR-004), porque corrigir só o
relógio sem adicionar a chamada deixaria o breaker preso do mesmo jeito.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cooldown e drawdown avançam com o tempo simulado (Priority: P1)

Cooldown após stop loss e os resets de drawdown diário/semanal/mensal usam o
timestamp do candle simulado em cada ciclo do replay, não a hora real de
execução do comando.

**Why this priority**: é o gap central que o item 022 descreve — sem isso,
um replay de meses (que roda em segundos de relógio real) nunca vê esses
períodos virarem, superestimando bloqueios em relação ao que o bot real
faria.

**Independent Test**: rodar um replay cujo histórico simulado atravesse
várias vezes `COOLDOWN_HOURS` e um dia/semana/mês calendário, e confirmar
que cooldowns vencem e os contadores de PnL por período resetam nas datas
simuladas corretas — não apenas uma vez (na execução real, que dura
segundos).

**Acceptance Scenarios**:

1. **Given** um cooldown ativado num candle simulado, **When** o replay
   avança candles cujo timestamp simulado ultrapassa `COOLDOWN_HOURS` depois
   daquele candle, **Then** o cooldown está vencido — mesmo que a execução
   real do comando tenha levado poucos segundos.
2. **Given** candles simulados que cruzam a virada de um dia calendário,
   **When** o replay processa o primeiro candle do novo dia, **Then**
   `daily_pnl`/`daily_reference_balance` resetam, na data simulada — não na
   data real de quando o comando roda.

---

### User Story 2 - Circuit breaker de fato destrava sozinho no replay (Priority: P1)

O replay chama a checagem de timeout do circuit breaker a cada ciclo
simulado, e essa checagem usa o tempo simulado.

**Why this priority**: achado de auditoria (Contexto) — hoje a checagem
nunca é chamada, então um breaker ativado trava a simulação inteira pelo
resto da execução, distorcendo qualquer replay que ative o breaker uma vez.
Igualmente crítico ao gap de relógio da US1: corrigir um sem o outro deixa o
comportamento errado do mesmo jeito.

**Independent Test**: forçar `MAX_CONSECUTIVE_LOSSES` perdas seguidas cedo
num replay cujo histórico restante cubra mais que
`CIRCUIT_BREAKER_COOLDOWN_HOURS`, e confirmar que o breaker desativa antes
do fim do replay.

**Acceptance Scenarios**:

1. **Given** o circuit breaker ativado num candle simulado, **When** candles
   subsequentes avançam o tempo simulado além de
   `CIRCUIT_BREAKER_COOLDOWN_HOURS`, **Then** o breaker se autodesativa,
   permitindo novas entradas nos candles seguintes.
2. **Given** o mesmo cenário, mas o histórico simulado restante é menor que
   `CIRCUIT_BREAKER_COOLDOWN_HOURS`, **When** o replay termina, **Then** o
   breaker continua ativo — comportamento correto (o bot real também não
   teria destravado ainda), não um bug.

---

### User Story 3 - Produção, paper e live continuam idênticos (Priority: P1)

Fora do ambiente isolado do replay, `execution/order_manager.py` continua
usando o relógio real exatamente como hoje.

**Why this priority**: `execution/order_manager.py` é código do caminho de
execução real (Constitution, Princípio I) — a mudança só é aceitável se for
comprovadamente um no-op fora do replay, não uma mudança de comportamento
"quase invisível" em produção.

**Independent Test**: rodar a suite de testes existente de
`execution/order_manager.py` (cooldown, drawdown, circuit breaker) sem
nenhuma alteração de resultado.

**Acceptance Scenarios**:

1. **Given** qualquer teste existente de cooldown/drawdown/circuit breaker
   que não passa pelo ambiente isolado do replay, **When** a suite roda após
   esta mudança, **Then** o resultado é idêntico ao anterior.
2. **Given** o bot rodando em paper ou live, **When** qualquer decisão de
   cooldown/drawdown/circuit breaker é tomada, **Then** ela usa
   `datetime.now()` real, sem diferença observável.

---

### User Story 4 - Timestamps de trade refletem a data simulada (Priority: P2)

Os campos de abertura e fechamento de um trade registrado pelo replay usam o
tempo simulado do candle, não a hora real de execução do comando.

**Why this priority**: menos crítico que US1/US2 (não afeta nenhuma decisão
de risco), mas é a outra metade do que o item 022 já descrevia — um relatório
de replay hoje mostra trades "abertos" e "fechados" na hora em que o comando
rodou, não no período histórico simulado, o que confunde qualquer leitura do
relatório por data.

**Independent Test**: rodar um replay sobre um histórico de meses atrás e
confirmar que `opened_at`/`closed_at` dos trades retornados caem dentro
desse período histórico, não na hora real de execução do comando.

**Acceptance Scenarios**:

1. **Given** um trade aberto e fechado durante o replay, **When** o
   resultado é inspecionado, **Then** `opened_at` e `closed_at` estão dentro
   do intervalo de datas do histórico simulado.

---

### Edge Cases

- **Circuit breaker ativado no último candle do replay.** Nunca destrava
  dentro daquela execução — comportamento correto (US2, Acceptance Scenario
  2), não uma falha desta spec.
- **Replay muito curto** (poucos candles, menos que `COOLDOWN_HOURS` de
  histórico). Cooldown não vence dentro da execução — também correto, é
  exatamente o que o bot real faria com esse histórico.
- **`_isolated_order_manager_environment` sai por exceção.** O relógio real
  MUST ser restaurado de qualquer forma — mesmo padrão `try/finally` já
  usado para os demais atributos isolados (`TRADING_MODE`, `load_state`,
  etc).
- **Outro código no mesmo processo usa `OrderManager` depois de um
  replay.** MUST ver relógio real, nunca o simulado vazando do replay
  anterior.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `execution/order_manager.py` MUST obter o instante atual
  (cooldown, drawdown por período, circuit breaker, timestamp de trade) por
  um único ponto de indireção, não chamadas diretas a `datetime.now()`
  espalhadas pelo arquivo.
- **FR-002**: Fora do ambiente isolado do replay, esse ponto de indireção
  MUST retornar exatamente `datetime.now()` — nenhuma diferença de
  comportamento em paper ou live.
- **FR-003**: O replay MUST avançar o relógio simulado para o timestamp do
  candle antes de avaliar cada ciclo.
- **FR-004**: O replay MUST chamar a checagem de timeout do circuit breaker
  a cada ciclo simulado — hoje essa chamada não existe no replay (achado de
  auditoria, Contexto).
- **FR-005**: O ambiente isolado do replay MUST restaurar o relógio real ao
  sair, inclusive em erro.
- **FR-006**: Timestamps de trade registrados pelo replay (abertura,
  fechamento) MUST refletir o tempo simulado, não a hora real de execução
  do comando.
- **FR-007**: A nota de "limitações conhecidas" em
  `trading/replay.py::compare_to_backtest()` sobre relógio real MUST ser
  atualizada quando esta spec for implementada — uma ressalva descrevendo um
  defeito que não existe mais desinformaria leitores futuros (mesmo
  princípio já aplicado na correção do MTF, spec 020).
- **FR-008**: O sistema MUST NOT alterar nenhum comportamento em
  `TRADING_MODE=paper` ou `TRADING_MODE=live`.

### Key Entities

- **Relógio simulado**: o timestamp do candle mais recente da janela em
  cada ciclo do replay — mesmo valor já usado pelo parâmetro `as_of` de
  `mtf_confirmed()` (spec 020), não um segundo conceito de "agora" simulado.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um cooldown ativado num candle simulado vence exatamente
  `COOLDOWN_HOURS` depois no tempo **simulado**, independente de quanto
  tempo real a execução do comando leva.
- **SC-002**: Um circuit breaker ativado durante o replay se autodesativa
  após `CIRCUIT_BREAKER_COOLDOWN_HOURS` de tempo simulado, quando o
  histórico restante cobre esse período.
- **SC-003**: Resets diário/semanal/mensal de drawdown ocorrem nas datas
  simuladas corretas.
- **SC-004**: `TRADING_MODE=paper` e `live` permanecem idênticos ao
  comportamento atual — verificado pela suite de testes existente sem
  alteração de resultado.
- **SC-005**: Timestamps de trade no relatório do replay caem dentro do
  período histórico simulado, nunca na data real de execução do comando.

---

## Assumptions

- O relógio simulado é o timestamp do último candle da janela em cada
  ciclo — mesmo valor já usado pelo `as_of` do MTF point-in-time (spec 020).
  Não introduz um segundo conceito de "agora" simulado no código.
- Esta spec não muda `check_pending_limit_orders()`/ordens limit no replay
  — usam contagem de ciclos (`cycles_waited`), não relógio, já corretas
  hoje.
- Esta spec não muda `execution/reconciliation.py` — no-op em paper, e o
  replay nunca chama reconciliação.
- Confirma o próprio texto do item 022 no backlog: não corrige
  comportamento em produção (paper/live já usam relógio real corretamente).
  É precisão de simulação — torna o replay mais fiel ao que o bot real
  faria, valor que só se realiza se o replay for usado com regularidade.
