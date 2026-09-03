# Feature Specification: Circuit breaker de perdas consecutivas na carteira de H14

**Feature Branch**: `044-circuit-breaker-carteira-h14`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: Aplicar o circuit breaker de perdas
consecutivas já existente e documentado em produção
(`execution/order_manager.py`, `MAX_CONSECUTIVE_LOSSES`, default 3) à
carteira de H14, pela primeira vez. Mecanismo temporal (reage a uma
sequência de resultados ruins ao longo do tempo), distinto dos dois já
testados sobre a mesma carteira — dimensionamento por volatilidade
(spec 041, reduz tamanho) e gate de correlação (spec 042, bloqueia por
sobreposição espacial entre pares no mesmo instante) — cuja combinação
(spec 043) não somou os efeitos: drawdown 20,24%, ainda reprovado,
`total_trades` idêntico ao do gate sozinho.

---

## Contexto e tese

**Por que este mecanismo é diferente dos dois já testados.**
Dimensionamento e correlação atacam o risco no **instante da entrada**:
quanto arriscar (tamanho) e se a posição nova se soma a um risco já
aberto (sobreposição entre pares). O circuit breaker ataca outra
dimensão — uma **sequência** de resultados ruins ao longo do tempo,
agnóstica a qual par ou a quanto risco correlacionado está envolvido.
Bloquear novas entradas depois de `N` trades fechados consecutivos com
prejuízo é a mesma lógica por trás de qualquer sistema de gestão de
risco que reconhece regimes ruins e reduz exposição a eles — já
implementada e rodando ao vivo (`execution/order_manager.py`), nunca
testada isoladamente sobre a carteira de H14.

**Não é mecânica nova, é reuso de uma mecânica de produção já
declarada.** `MAX_CONSECUTIVE_LOSSES` (default 3) e o reset em
`pnl > 0` já existem, documentados em `CLAUDE.md` ("Circuit breaker").
Esta spec aplica a mesma semântica — contador global de perdas
consecutivas, reset no primeiro trade lucrativo — dentro de
`_simular_carteira_core`, via um novo parâmetro opcional
`usar_circuit_breaker` (default `False`, preserva os quatro resultados
já publicados byte a byte).

**Escopo deliberadamente menor que o de produção**: sem o cooldown por
tempo (`CIRCUIT_BREAKER_COOLDOWN_HOURS`). Em produção esse cooldown
existe para destravar o bot quando não sobra nenhuma posição para gerar
o trade lucrativo que reseta o contador. Numa carteira simulada de 12
pares há sempre posições fechando ao longo da série — o reset primário
por trade lucrativo é suficiente; o cooldown por tempo nunca seria
exercitado. Documentado como decisão em `research.md`.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir a carteira de H14 com o circuit breaker de perdas consecutivas ligado (Priority: P1)

O pesquisador obtém o drawdown agregado de carteira de H14 com o
circuit breaker de perdas consecutivas ligado, isolado (sem
dimensionamento nem gate de correlação), comparado contra os quatro
resultados já publicados (sem overlay: 28,66%; só volatilidade: 23,04%;
só correlação: 20,74%; combinado vol+correlação: 20,24%).

**Why this priority**: é a pergunta da hipótese — sem o comparativo
contra os quatro números já publicados, não há como saber se este
mecanismo temporal, ortogonal aos dois já testados, reduz o drawdown
por um caminho que os outros não cobrem.

**Independent Test**: rodar `_simular_carteira_core` com
`usar_circuit_breaker=True` sobre um cenário sintético com uma sequência
controlada de trades perdedores seguida de posições candidatas e
confirmar que nenhuma entrada nova abre enquanto o contador de perdas
consecutivas está no limite, e que uma entrada volta a ser permitida
depois do primeiro trade fechado com lucro.

**Acceptance Scenarios**:

1. **Given** a carteira de H14 sobre `UNIVERSO_H11` (12 pares, mesmo
   universo dos quatro resultados já publicados), **When**
   `usar_circuit_breaker=True`, **Then** produz um `BacktestResult`
   único, sem exceção, bloqueando novas entradas depois de
   `MAX_CONSECUTIVE_LOSSES` trades fechados consecutivos com prejuízo.
2. **Given** o circuit breaker ativo (contador no limite), **When** o
   próximo trade fechado tem `pnl > 0`, **Then** o contador reseta e
   novas entradas voltam a ser permitidas no próximo candidato elegível.
3. **Given** o resultado isolado do circuit breaker, **When** comparado
   aos quatro já publicados, **Then** os cinco números aparecem lado a
   lado no registro — nunca um substitui o outro.

---

### Edge Cases

- Carteira sem nenhum trade perdedor ainda (início da série): contador
  em zero, circuit breaker nunca bloqueia — comportamento idêntico ao
  default.
- Todas as posições fechadas com prejuízo até o fim da série: circuit
  breaker permanece ativo até o fim, sem nenhum trade lucrativo para
  resetar — resultado válido (menos trades, não exceção).
- `MAX_CONSECUTIVE_LOSSES` não definido/zero: tratado como o valor já
  validado por `config/settings.py` (nunca chega zero em produção,
  mesma garantia aqui).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST adicionar um parâmetro opcional
  `usar_circuit_breaker` (default `False`) a `_simular_carteira_core` e
  `simular_carteira`, preservando os quatro resultados já publicados
  byte a byte quando `False`.
- **FR-002**: Quando `usar_circuit_breaker=True`, o sistema MUST manter
  um contador global (carteira inteira, não por par) de trades fechados
  consecutivos com `pnl < 0`, incrementado a cada fechamento com
  prejuízo e resetado a zero no primeiro fechamento com `pnl > 0` —
  mesma semântica de `execution/order_manager.py`.
- **FR-003**: Quando o contador atinge `MAX_CONSECUTIVE_LOSSES`
  (`config/settings.py`), o sistema MUST bloquear qualquer nova entrada
  até o contador resetar — posições já abertas continuam geridas
  normalmente (mesmo padrão de produção: o breaker bloqueia entradas,
  nunca gestão de posição aberta).
- **FR-004**: O sistema MUST usar `UNIVERSO_H11` (12 pares), o mesmo dos
  quatro resultados já publicados — sem escolha nova de universo.
- **FR-005**: O sistema MUST testar o circuit breaker isolado (sem
  `usar_dimensionamento_vol` nem `usar_gate_correlacao`), seguindo a
  disciplina de uma-variável-por-vez já usada nas specs 040-043.
- **FR-006**: O sistema MUST reportar o resultado ao lado dos quatro já
  publicados (sem overlay, só volatilidade, só correlação, combinado) —
  nunca substituindo nenhum deles no registro.
- **FR-007**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/`.

### Key Entities

- Nenhuma entidade nova — contador de perdas consecutivas é estado
  interno de `_simular_carteira_core`, não persistido.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um `BacktestResult` de carteira com o circuit breaker
  isolado ligado é produzido, comparável em unidade e período aos
  quatro já publicados.
- **SC-002**: O veredito de `evaluate_approval()` sobre o resultado é
  registrado, sem critério novo.
- **SC-003**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Universo, capital, mecanismo de saída**: já declarados em spec 037 —
  reusados sem alteração.
- **`MAX_CONSECUTIVE_LOSSES`**: usa o valor já validado em
  `config/settings.py` (default 3), o mesmo que produção usa — não é
  parâmetro novo de pesquisa, é reuso de configuração existente.
- Reprovação, aprovação ou resultado ainda inconclusivo desta spec não
  invalida os vereditos já publicados de H14 — é a mesma pergunta
  (drawdown de carteira), com um mecanismo novo, isolado, medido pela
  primeira vez.
