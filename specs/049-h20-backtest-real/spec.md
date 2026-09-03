# Feature Specification: H20 — geometria propaga ao backtest real (não só ao rótulo)

**Feature Branch**: `049-h20-backtest-real`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: A reversão do veredito de H20 (spec 048:
sinal confirmado, razão pooled 0,8421 contra empate 0,750) mede só a
estatística de rótulo — se o preço, no futuro, tocaria o alvo de 2×ATR
antes do stop de 1,5×ATR dentro de 24 candles. Não mede se o backtest
real (`ResultadoModelo.backtest`, via `simulate_backtest`) usa essa
mesma geometria para decidir quando sair de uma posição. Auditoria do
código antes de qualquer medição nova encontrou uma lacuna real:
`avaliar_par` rotula e treina com `ParametrosBarreira.tp_mult`/
`sl_mult`, mas a chamada que produz `ResultadoModelo.backtest`
(`_resultado_modelo` → `_simular_com_sinais` → `simulate_backtest`)
nunca repassa esses multiplicadores — `simulate_backtest` roda com os
multiplicadores fixos de produção (`ATR_TP_MULTIPLIER=3.0`,
`ATR_SL_MULTIPLIER=1.5`) independente do `ParametrosBarreira` usado
para rotular. Para H14 (que sempre usou os multiplicadores default,
coincidentemente iguais aos de produção) essa lacuna é invisível — o
modelo é rotulado E simulado com a mesma geometria por acidente. Para
H20 (`tp_mult=2.0`), a lacuna é real: o modelo foi treinado para prever
"toca 2×ATR antes de 1,5×ATR", mas seu backtest simulado sai a 3×ATR —
uma estratégia diferente da que foi validada estatisticamente. Corrigir
propagando `atr_tp_multiplier`/`atr_sl_multiplier` (já parâmetros
existentes de `simulate_backtest`) a partir do `ParametrosBarreira`
usado em `avaliar_par`, e então medir o backtest real (retorno,
drawdown, profit factor, por par) da geometria `tp=2,0` já confirmada
estatisticamente em spec 048.

---

## Contexto e tese

**Por que isto importa antes de qualquer avaliação operacional de
H20.** O veredito revertido de spec 048 ("paga a geometria") é uma
afirmação sobre rótulos — eventos futuros de preço, não sobre dinheiro
simulado entrando e saindo de uma posição. Sem esta correção, qualquer
número de retorno/drawdown/profit factor que se tentasse citar para
H20 estaria medindo uma estratégia que sai a 3×ATR (produção), não a
estratégia de 2×ATR que o modelo foi treinado para prever — o mesmo
tipo de descompasso entre o que é medido e o que é operado que motivou
a correção de D7 em spec 037 (backtest usando as barreiras de
rotulagem em vez do motor real de saída — o problema espelhado: aqui
é o motor real de saída que ignora a geometria declarada).

**Por que isto não afetou nenhum resultado já publicado.**
`ParametrosBarreira()` tem `tp_mult: float = ATR_TP_MULTIPLIER` e
`sl_mult: float = ATR_SL_MULTIPLIER` como default — toda avaliação de
H14/H17 (specs 027, 034, 036, 037) usou o `ParametrosBarreira` default,
que já coincide com os multiplicadores de produção. A lacuna só se
manifesta quando alguém passa um `ParametrosBarreira` não-default — o
único caso no registro é H20. Nenhum resultado publicado de H14/H17
precisa de correção.

**Correção é aditiva e retrocompatível por construção.** Propagar
`p.tp_mult`/`p.sl_mult` como `atr_tp_multiplier`/`atr_sl_multiplier`
para `simulate_backtest` produz exatamente os multiplicadores de
produção quando `params=None` (o default), porque
`ParametrosBarreira()` já os herda — reproduz H14/H17 byte a byte,
testado como regressão explícita antes de qualquer medição de H20.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A geometria rotulada é a geometria simulada (Priority: P1)

O pesquisador confirma que `avaliar_par(params=ParametrosBarreira(tp_mult=2.0))`
produz um `ResultadoModelo.backtest` cujas saídas de take-profit
realmente disparam a 2×ATR, não a 3×ATR — e que o mesmo par com
`params=None` continua produzindo exatamente o resultado já publicado
de H14.

**Why this priority**: é o pré-requisito para qualquer número de
retorno/drawdown/profit factor de H20 ser válido — sem a correção,
qualquer medição estaria descrevendo uma estratégia diferente da
confirmada em spec 048.

**Independent Test**: sobre uma série sintética com preço tocando
exatamente 2×ATR (não 3×ATR) acima da entrada, `avaliar_par` com
`tp_mult=2.0` MUST produzir um trade fechado por "Take Profit" naquele
nível; o mesmo cenário com `params=None` (produção, 3×ATR) MUST manter
a posição aberta (preço não alcança o alvo de produção).

**Acceptance Scenarios**:

1. **Given** `ParametrosBarreira(tp_mult=2.0, sl_mult=1.5)`, **When**
   `avaliar_par` roda sobre uma série onde o preço toca 2×ATR acima da
   entrada mas não 3×ATR, **Then** `ResultadoModelo.backtest` registra
   uma saída por "Take Profit" naquele nível — não mantém a posição
   aberta esperando 3×ATR.
2. **Given** `params=None` (default, produção), **When** `avaliar_par`
   roda sobre os mesmos 12 pares já publicados de H14, **Then**
   `ResultadoModelo.backtest` é byte a byte idêntico ao já publicado —
   regressão explícita, testada antes de qualquer medição de H20.
3. **Given** a geometria `tp=2,0` já confirmada estatisticamente (spec
   048), **When** o backtest real roda com a correção aplicada,
   **Then** retorno, drawdown e profit factor por par são reportados,
   comparáveis (mas não idênticos, geometria diferente) aos números
   por-par já publicados de H14 (`tp=3,0`).

---

### Edge Cases

- `params=None`: comportamento idêntico ao já publicado — nenhum
  multiplicador novo é introduzido, só o já existente é propagado.
- Par sem eventos suficientes para treinar (`n_treino < MIN_TREINO`):
  comportamento inalterado — a correção só afeta o caminho que já
  produzia um `ResultadoModelo.backtest`, não os caminhos de erro/
  amostra insuficiente já existentes.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST propagar `params.tp_mult`/`params.sl_mult`
  (de `ParametrosBarreira`) como `atr_tp_multiplier`/`atr_sl_multiplier`
  para `simulate_backtest`, via `_resultado_modelo`/`_simular_com_sinais`
  — parâmetros já existentes de `simulate_backtest`, nenhum novo.
- **FR-002**: O sistema MUST preservar byte a byte todo resultado já
  publicado de H14/H17 quando `params=None` ou `params=ParametrosBarreira()`
  (default) — regressão obrigatória antes de qualquer medição nova.
- **FR-003**: O sistema MUST medir o backtest real (retorno, drawdown,
  profit factor, trades) por par, sobre `UNIVERSO_H11`, com a geometria
  `tp=2,0` já selecionada e confirmada em spec 048 — não uma geometria
  nova, não uma escolha de parâmetro nova.
- **FR-004**: O sistema MUST reportar o resultado ao lado dos números
  por-par já publicados de H14 (`tp=3,0`) — nunca substituindo.
- **FR-005**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/`.
- **FR-006**: O sistema MUST NOT decidir aprovação operacional nesta
  spec — mede o backtest por par, não constrói motor de carteira
  (trabalho futuro, condicionado a este resultado, mesmo padrão de
  spec 037 vir depois de spec 036 para H14).

### Key Entities

- Nenhuma entidade nova — `ResultadoModelo.backtest` já existe
  (`BacktestResult`, `backtesting/engine.py`), só passa a refletir a
  geometria correta.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Teste demonstra que a geometria rotulada e a geometria
  simulada coincidem — take-profit dispara no nível declarado por
  `ParametrosBarreira`, não no default de produção, quando diferem.
- **SC-002**: Toda avaliação já publicada de H14/H17 permanece
  idêntica byte a byte (regressão explícita).
- **SC-003**: Backtest real por par da geometria `tp=2,0` é medido e
  registrado, sem decidir aprovação operacional.
- **SC-004**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Geometria avaliada**: `tp=2,0`, `sl=1,5`, a mesma já selecionada
  pela regra declarada de H20 (spec 028) e confirmada estatisticamente
  (spec 048) — nenhuma escolha nova.
- **Universo, capital inicial, custo de execução**: já declarados em
  specs anteriores (037) — reusados sem alteração.
- Esta spec não decide se H20 deveria virar motor de carteira
  (equivalente de spec 037 para H14) — isso é trabalho futuro,
  condicionado ao resultado do backtest real medido aqui.
