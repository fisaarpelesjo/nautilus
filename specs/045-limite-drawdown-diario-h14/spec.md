# Feature Specification: Limite de drawdown diário na carteira de H14

**Feature Branch**: `045-limite-drawdown-diario-h14`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: Aplicar o limite de drawdown diário já
existente e documentado em produção (`execution/order_manager.py`,
`DAILY_DRAWDOWN_LIMIT`, default 5%) à carteira de H14, pela primeira
vez. Sexto mecanismo de risco testado sobre a mesma carteira —
distinto do circuit breaker de perdas consecutivas (spec 044, drawdown
0,57% mas colapsou para 6 trades porque só reseta com um trade
lucrativo, raro numa base de profit factor abaixo de 1): este reseta
por **calendário** (novo dia), não por resultado — nunca fica preso
indefinidamente esperando um trade lucrativo que pode não vir.

---

## Contexto e tese

**Por que testar depois de um resultado degenerado.** O circuit breaker
de perdas consecutivas (spec 044) mostrou que qualquer mecanismo que
só destrava com um trade lucrativo, sobre uma estratégia de profit
factor abaixo de 1, tende a ficar preso — o drawdown cai porque quase
não há mais operação, não porque a qualidade das entradas melhorou
(documentado em `docs/research/registro-de-hipoteses.md` §4.15,
atualização spec 044). O limite de drawdown diário reresolve exatamente
essa falha estrutural por construção: o contador (saldo de referência)
reseta a cada novo dia de calendário, **independente de resultado** —
mesmo que o dia tenha fechado no limite de perda, o dia seguinte começa
destravado. Não pode ficar preso para sempre esperando sorte.

**Reuso de mecânica de produção já declarada.** `DAILY_DRAWDOWN_LIMIT`
(default 5%) e a semântica de saldo de referência resetado por período
já existem e rodam ao vivo (`execution/order_manager.py`,
`_reference_balance()`), documentados em `CLAUDE.md` ("Limites de
perda semanal e mensal"). Esta spec aplica só a via diária (a mais
simples das três — diária/semanal/mensal — e suficiente para testar se
a família "reset por calendário" evita a armadilha do reset por
resultado) dentro de `_simular_carteira_core`, via um novo parâmetro
opcional `usar_limite_drawdown_diario` (default `False`, preserva os
cinco resultados já publicados byte a byte).

**Escopo deliberadamente menor que o de produção**: só o limite diário,
não semanal/mensal — disciplina de uma-variável-por-vez. Se o diário
mostrar resultado não-degenerado (trades numa ordem de grandeza
comparável aos outros testes, não um colapso para poucas unidades),
semanal/mensal ficam como specs futuras. Se também colapsar, fecha a
família inteira de "reset por calendário" com dois casos confirmatórios
em vez de um.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir a carteira de H14 com o limite de drawdown diário ligado (Priority: P1)

O pesquisador obtém o drawdown agregado e o número de trades de
carteira de H14 com o limite de drawdown diário ligado, isolado (sem
dimensionamento, correlação ou circuit breaker), comparado contra os
cinco resultados já publicados (sem overlay: 28,66%/931 trades; só
volatilidade: 23,04%/763; só correlação: 20,74%/595; combinado
vol+correlação: 20,24%/595; circuit breaker: 0,57%/6).

**Why this priority**: é a pergunta da hipótese — sem o comparativo de
`total_trades`, não há como saber se este mecanismo reduz drawdown por
selecionar melhor os dias (reset por calendário, não colapsa a
amostra) ou repete a armadilha do circuit breaker (reset raro,
colapsa).

**Independent Test**: rodar `_simular_carteira_core` com
`usar_limite_drawdown_diario=True` sobre um cenário sintético com um
dia de perda que ultrapassa o limite e confirmar que (a) nenhuma
entrada nova abre pelo resto daquele dia de calendário, (b) uma entrada
volta a ser permitida no primeiro candle do dia seguinte, mesmo sem
nenhum trade lucrativo ter fechado.

**Acceptance Scenarios**:

1. **Given** a carteira de H14 sobre `UNIVERSO_H11` (12 pares, mesmo
   universo dos cinco resultados já publicados), **When**
   `usar_limite_drawdown_diario=True`, **Then** produz um
   `BacktestResult` único, sem exceção, bloqueando novas entradas
   quando o patrimônio do dia cai abaixo de `1 - DAILY_DRAWDOWN_LIMIT`
   vezes o saldo de referência do dia.
2. **Given** o limite diário ativo (patrimônio abaixo do saldo de
   referência do dia menos o limite), **When** o próximo candle
   pertence a um novo dia de calendário, **Then** o saldo de referência
   reseta para o patrimônio daquele instante e novas entradas voltam a
   ser permitidas, independente de ter havido trade lucrativo.
3. **Given** o resultado isolado do limite diário, **When** comparado
   aos cinco já publicados, **Then** os seis números aparecem lado a
   lado no registro — nunca um substitui o outro.

---

### Edge Cases

- Primeiro candle da série: sem dia de referência ainda — inicializa
  com o patrimônio inicial, nunca bloqueia no primeiro candle.
- Série inteira dentro do limite diário em todos os dias: comportamento
  idêntico ao default (nunca bloqueia).
- Timeframe de 4h: o "dia de calendário" é uma janela de 6 candles;
  suficiente para produzir vários resets ao longo de ~2,7 anos de
  histórico (não uma janela degenerada como a do circuit breaker).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST adicionar um parâmetro opcional
  `usar_limite_drawdown_diario` (default `False`) a
  `_simular_carteira_core` e `simular_carteira`, preservando os cinco
  resultados já publicados byte a byte quando `False`.
- **FR-002**: Quando `usar_limite_drawdown_diario=True`, o sistema MUST
  manter um saldo de referência diário, resetado ao patrimônio corrente
  no primeiro candle de cada novo dia de calendário (UTC) —
  independente de qualquer trade ter fechado.
- **FR-003**: Quando o patrimônio corrente (caixa + posições a
  mercado) cai abaixo de `saldo_referencia_diario × (1 -
  DAILY_DRAWDOWN_LIMIT)`, o sistema MUST bloquear qualquer nova
  entrada até o próximo reset diário — posições já abertas continuam
  geridas normalmente.
- **FR-004**: O sistema MUST usar `UNIVERSO_H11` (12 pares), o mesmo
  dos cinco resultados já publicados.
- **FR-005**: O sistema MUST testar o limite diário isolado (sem
  `usar_dimensionamento_vol`, `usar_gate_correlacao` nem
  `usar_circuit_breaker`), disciplina de uma-variável-por-vez.
- **FR-006**: O sistema MUST reportar o resultado ao lado dos cinco já
  publicados — nunca substituindo nenhum deles no registro.
- **FR-007**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/`.

### Key Entities

- Nenhuma entidade nova — saldo de referência diário e data do último
  reset são estado interno de `_simular_carteira_core`, não
  persistidos.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um `BacktestResult` de carteira com o limite diário
  isolado ligado é produzido, comparável em unidade e período aos
  cinco já publicados.
- **SC-002**: O veredito de `evaluate_approval()` sobre o resultado é
  registrado, sem critério novo.
- **SC-003**: Nenhuma ordem real é enviada; produção permanece
  idêntica.

---

## Assumptions

- **Universo, capital, mecanismo de saída**: já declarados em spec 037
  — reusados sem alteração.
- **`DAILY_DRAWDOWN_LIMIT`**: usa o valor já validado em
  `config/settings.py` (default 5%), o mesmo que produção usa.
- **Dia de calendário**: `pandas.Timestamp.date()` sobre o índice já
  em UTC (mesma convenção dos candles da Binance) — sem conversão de
  fuso horário nova.
- Reprovação, aprovação ou resultado ainda inconclusivo desta spec não
  invalida os vereditos já publicados de H14 — é a mesma pergunta
  (drawdown de carteira), com um mecanismo novo, isolado, medido pela
  primeira vez.
