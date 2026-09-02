# Feature Specification: Refresh periódico de pares dinâmicos

**Feature Branch**: `031-refresh-pares-dinamicos`

**Created**: 2026-09-02

**Status**: Draft

**Input**: User description: item 014 do `specs/BACKLOG.md` — com
`DYNAMIC_PAIRS_ENABLED=true`, `trading/runner.py::_load_active_pairs()` só é
chamada uma vez, no boot do bot. A lista de pares ativos nunca é re-varrida
enquanto o processo roda — um VPS de longa duração (padrão já comprovado
neste projeto) fica preso à seleção do dia em que foi ligado, mesmo que a
composição do mercado (volume, volatilidade, tendência) mude semanas depois.
Não é a configuração atual do bot (`PAIRS` fixo), mas é relevante para quando
`DYNAMIC_PAIRS_ENABLED` for ligado.

---

## Contexto

`market/selector.py::select_dynamic_pairs()` já existe e funciona (usado por
`python main.py select` para inspeção manual): busca tickers, filtra por
volume/spread/volatilidade/tendência, roda um backtest rápido por candidato e
ranqueia por score. `trading/runner.py::_load_active_pairs()` já chama essa
função — mas só na inicialização (`run()`, uma vez, antes do loop principal).

**Achado crítico de auditoria de código, antes de qualquer requisito ser
escrito**: o loop principal (`trading/runner.py::run()`) só chama a gestão de
posição aberta (`handle_open_position` — stop loss, trailing stop, take
profit, saída por sinal) para símbolos dentro de `active_pairs`, iterando
`for symbol in active_pairs`. Um refresh que **remova** um par com posição
aberta — porque o seletor não o escolheria mais — deixaria essa posição
**órfã**: nunca mais avaliada, nunca mais gerida, stop loss nunca mais
atualizado, até o processo ser reiniciado. Isso anularia toda proteção de
risco do bot (`MAX_STOP_LOSS_PCT`, trailing stop, take profit) para aquela
posição especificamente, silenciosamente. Este é o requisito central desta
spec, não um detalhe — ver FR-002.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Lista de pares se atualiza sem reiniciar o bot (Priority: P1)

Com `DYNAMIC_PAIRS_ENABLED=true`, a lista de pares ativos é re-selecionada
periodicamente enquanto o bot roda, sem exigir reinício do processo.

**Why this priority**: é o gap que esta spec existe para fechar — hoje a
seleção dinâmica só acontece uma vez, no boot.

**Independent Test**: rodar o bot com `DYNAMIC_PAIRS_ENABLED=true` por mais
de um intervalo de refresh configurado, e observar a lista de pares ativos
mudar sem reinício do processo.

**Acceptance Scenarios**:

1. **Given** o bot rodando com seleção dinâmica ativa, **When** o intervalo
   de refresh configurado é atingido, **Then** a lista de pares ativos é
   re-selecionada, sem interromper o ciclo em andamento.
2. **Given** o mesmo cenário, **When** os melhores candidatos não mudaram,
   **Then** a lista permanece a mesma (refresh é idempotente quando nada
   mudou).

---

### User Story 2 - Posição aberta nunca fica órfã (Priority: P1)

Um par com posição aberta continua recebendo gestão de risco completa (stop
loss, trailing stop, take profit, saída por sinal) mesmo depois de um refresh
que não o selecionaria mais.

**Why this priority**: é a condição de segurança sem a qual esta spec não
deveria existir — ver Contexto. Sem ela, o refresh trocaria um gap de
precisão (lista desatualizada) por um risco real (posição sem proteção).

**Independent Test**: forçar um refresh cujo resultado do seletor não inclua
um símbolo com posição aberta simulada, e confirmar que esse símbolo continua
na lista ativa e continua recebendo gestão de posição no próximo ciclo.

**Acceptance Scenarios**:

1. **Given** uma posição aberta num símbolo, **When** um refresh roda e o
   seletor não escolhe mais esse símbolo, **Then** o símbolo permanece na
   lista ativa até a posição fechar por conta própria (SL, TP, sinal ou
   trailing).
2. **Given** o mesmo símbolo, **When** a posição fecha, **Then** ele deixa de
   ser protegido contra remoção — o próximo refresh pode excluí-lo
   normalmente.
3. **Given** um símbolo com ordem limit pendente (não posição aberta ainda),
   **When** um refresh roda, **Then** o comportamento de
   `check_pending_limit_orders()` (já desacoplado de `active_pairs`) não
   muda — fora do escopo desta spec, mas verificado para não regredir.

---

### User Story 3 - Refresh é auditável (Priority: P2)

Todo refresh registra um evento estruturado dizendo quais pares entraram,
quais saíram, e quais foram mantidos apesar de não mais selecionados (por
terem posição aberta).

**Why this priority**: sem isso, uma mudança na lista de pares ativos —
que afeta diretamente onde o bot aloca capital — aconteceria silenciosamente,
sem rastro no mesmo pipeline de auditoria que já existe para outras decisões
de risco (constitution, Princípio V).

**Independent Test**: rodar um refresh e confirmar que um evento aparece em
`logs/events-*.jsonl` com os três conjuntos (entraram, saíram, mantidos por
posição).

**Acceptance Scenarios**:

1. **Given** um refresh que muda a composição da lista, **When** ele
   completa, **Then** um evento estruturado é gravado com os pares
   adicionados, removidos e mantidos por posição aberta.
2. **Given** um refresh que não muda nada, **When** ele completa, **Then**
   o evento ainda é gravado (declara explicitamente "sem mudança"), para o
   histórico mostrar que o refresh rodou, não só quando ele muda algo.

---

### Edge Cases

- **Seleção dinâmica falha durante um refresh** (rede indisponível, erro do
  seletor). A lista ativa atual é preservada — mesmo princípio de fail-safe
  já usado em `_load_active_pairs()` no boot (`except Exception: return
  PAIRS`), adaptado para "mantém a lista atual" em vez de "volta para
  `PAIRS`".
- **Todos os pares com posição aberta continuam sendo os melhores
  candidatos.** Nenhuma mudança visível, mas o evento de auditoria (US3)
  ainda registra que o refresh rodou.
- **`MAX_POSITIONS` já atingido quando pares novos entram.** Nenhuma
  posição é aberta além do limite — comportamento de dimensionamento já
  existente (`risk/manager.py`, `trading/position_lifecycle.py`) não é
  alterado por esta spec; pares novos só passam a ser **avaliados**.
- **`DYNAMIC_PAIRS_ENABLED=false` (default, config atual do bot).** Nenhum
  comportamento muda — sem refresh, sem evento, `PAIRS` fixo como hoje.
- **Todos os pares selecionados coincidem com `PAIRS` original.** Caso
  trivial, mesmo tratamento dos demais.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST re-selecionar periodicamente a lista de pares
  ativos quando `DYNAMIC_PAIRS_ENABLED=true`, sem exigir reinício do
  processo.
- **FR-002**: O sistema MUST NOT remover da lista ativa nenhum símbolo com
  posição aberta, independente do resultado da seleção dinâmica — a posição
  continua sendo gerida (SL, trailing, TP, saída por sinal) até fechar por
  conta própria.
- **FR-003**: O intervalo entre refreshes MUST ser configurável, com um
  padrão declarado e justificado antes da implementação (Fase 0 — custo da
  seleção dinâmica: busca de tickers + backtest por candidato).
- **FR-004**: Falha durante a seleção dinâmica de um refresh MUST preservar
  a lista ativa vigente — nunca esvaziar nem abortar o ciclo do bot.
- **FR-005**: Todo refresh MUST gerar um evento estruturado no mesmo
  pipeline de eventos já existente (`logs/events-*.jsonl`), com os pares
  adicionados, removidos e mantidos apesar de não mais selecionados.
- **FR-006**: O sistema MUST NOT alterar nenhum comportamento quando
  `DYNAMIC_PAIRS_ENABLED=false` (default).
- **FR-007**: O sistema MUST NOT abrir posição além de `MAX_POSITIONS` nem
  alterar o dimensionamento de ordem existente só porque novos pares
  entraram na lista ativa.
- **FR-008**: Um par removido (sem posição aberta) MUST parar de ser
  avaliado para nova entrada a partir do próximo ciclo.

### Key Entities

- **Lista de pares ativos** (`active_pairs`, já existente): símbolos
  avaliados a cada ciclo. Passa a poder mudar em runtime, não só no boot.
- **Resultado de refresh**: pares adicionados, pares removidos, pares
  mantidos apesar de não mais selecionados (por posição aberta) — o
  conteúdo do evento de auditoria (US3).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com `DYNAMIC_PAIRS_ENABLED=true`, a lista de pares ativos muda
  em runtime, sem reinício do processo, após o intervalo configurado.
- **SC-002**: Um par com posição aberta continua recebendo gestão completa
  de risco mesmo após um refresh que não o selecionaria mais — nenhuma
  posição fica sem stop loss/trailing/take profit gerido.
- **SC-003**: Falha de rede durante um refresh não interrompe o bot nem
  esvazia a lista ativa.
- **SC-004**: Todo refresh (mude algo ou não) produz um evento auditável.
- **SC-005**: Com `DYNAMIC_PAIRS_ENABLED=false`, o comportamento é idêntico
  ao atual — sem exceção.

---

## Assumptions

- O custo de `select_dynamic_pairs()` (busca de tickers + até
  `DYNAMIC_PAIRS_CANDIDATES` backtests) é real e não deve rodar a cada ciclo
  de 60s — o intervalo de refresh (FR-003) é medido e declarado em
  research.md, mesmo padrão de D1-D6/D1 nas specs 029/030.
- Esta spec não muda `market/selector.py` — reusa `select_dynamic_pairs()` e
  `selected_symbols()` já existentes e testados.
- Esta spec não muda `risk/manager.py` nem o dimensionamento de ordem —
  apenas quais símbolos são avaliados a cada ciclo.
- `DYNAMIC_PAIRS_ENABLED` continua `false` por padrão — não é a configuração
  atual do bot (`.env` local usa `PAIRS` fixo), então esta spec não muda
  comportamento observável em produção até o operador ligar a flag.
