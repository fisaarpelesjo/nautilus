# Feature Specification: Histórico estendido para reavaliação de hipóteses

**Feature Branch**: `036-historico-estendido`

**Created**: 2026-09-02

**Status**: Draft

**Input**: User description: reavaliar H10, H11, H14 e H17 com mais
histórico — as três primeiras já estão registradas em
`docs/research/registro-de-hipoteses.md` como "inconclusiva, requer
reavaliação com histórico mais longo"/"limitação estrutural de
histórico"; H17 (spec 034, hoje) ficou inconclusiva porque a linha de
base de regras teve só 7 operações na janela de teste — o próprio
registro já anotou que reavaliar exigiria mais candles do que o teto
atual permite.

---

## Contexto

Todo o código da bateria de hipóteses (`backtesting/modelo.py`,
`backtesting/onchain_hipotese.py`, `backtesting/horizonte.py`, entre
outros) busca histórico via `data/fetcher.py::fetch_ohlcv(par, timeframe,
limit)`, e a maioria dos chamadores usa `limit=2000` — não porque seja o
máximo disponível, mas porque foi o valor original escolhido antes de
`data/fetcher.py` ganhar paginação (spec 011, rate limit hardening) para
superar o teto de ~1.000 candles por requisição da Binance. `fetch_ohlcv`
já pagina automaticamente para `limit` maior — o teto de 2.000 é uma
escolha de chamador nunca revisitada, não uma limitação do sistema.

**Medido antes desta spec** (2026-09-02): pedir 6.000 candles de 4h para
os 12 pares de `UNIVERSO_H11` devolve os 6.000 completos em todos,
cobrindo 2023-12-07 até hoje (~2,7 anos) — 3x o histórico que H10/H11/H14/
H17 usaram. BTC/USDT e ATOM/USDT chegam a ~15.000 candles (desde
2019-10-29) antes de esbarrar num teto real, mas isso não foi verificado
para os 12 pares — só 6.000 foi.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reavaliar H17 (on-chain) com amostra suficiente na linha de base (Priority: P1)

Com mais histórico, a linha de base de regras de H17 atinge o mínimo de
operações na janela de teste, permitindo um veredito além de
"inconclusivo".

**Why this priority**: é a hipótese mais recente e o motivo do bloqueio já
está diagnosticado com precisão (7 operações contra o mínimo de 10) — o
teste mais direto de que estender o histórico resolve o problema
específico que bloqueou um resultado hoje mesmo.

**Independent Test**: rodar `python main.py onchain` com o histórico
estendido e confirmar que a linha de base de regras atinge o mínimo de
operações — o veredito passa a ser aprovado/reprovado/sem_sinal/
insuficiente, não mais bloqueado por amostra da linha de base.

**Acceptance Scenarios**:

1. **Given** o histórico estendido (D1), **When** `avaliar_h17()` roda,
   **Then** a linha de base de regras tem pelo menos `EDGE_MIN_TRADES`
   operações na janela de teste.
2. **Given** o novo resultado, **When** comparado ao de hoje (7 operações,
   inconclusivo), **Then** o registro é atualizado com o veredito novo, ou
   com o motivo específico caso ainda seja inconclusivo por outra razão.

---

### User Story 2 - Reavaliar H14 com a mesma régua, histórico maior (Priority: P1)

H14 é reavaliada com o histórico estendido, mesma bateria (barreira
tripla, purga, embargo, três linhas de base), para confirmar se a
elevação de sinal (z=+5,21) e a insuficiência frente à barreira se mantêm
com mais amostra, ou mudam.

**Why this priority**: é o achado mais forte do registro — vale confirmar
com mais dado antes de tratá-lo como definitivo, e é a mesma
infraestrutura que H17 já reusa.

**Independent Test**: rodar `python main.py modelo` com o histórico
estendido e comparar `razao_chances_decidido`/`n_treino`/`n_teste` contra
os valores já publicados.

**Acceptance Scenarios**:

1. **Given** o histórico estendido, **When** `run_modelo_scan()` roda,
   **Then** `n_treino`/`n_teste` por par aumentam proporcionalmente ao
   histórico novo.

---

### User Story 3 - Reavaliar H11 (horizonte) nos timeframes afetados (Priority: P2)

H11 é reavaliada em 4h/1d com o histórico estendido — 1w fica fora, porque
`research.md`/comentários já existentes de `horizonte.py` documentam que
mais candles solicitados não aumentam o histórico semanal disponível
(a limitação ali é o listing date dos pares, não o `limit` pedido).

**Why this priority**: menor prioridade que US1/US2 porque o próprio
código já indica que a correção não atinge a limitação real de 1w — só
vale confirmar 4h/1d.

**Independent Test**: rodar `python main.py horizonte 4h 1d` com o
histórico estendido e comparar contra o resultado já publicado.

**Acceptance Scenarios**:

1. **Given** o histórico estendido, **When** `run_horizonte_scan()` roda
   para `4h`/`1d`, **Then** os candles obtidos por par aumentam
   proporcionalmente.

---

### Edge Cases

- **Par com histórico real menor que 6.000 candles** (listagem recente).
  `fetch_ohlcv` já devolve o que existir, sem erro — mesmo comportamento
  documentado em `horizonte.py` ("pedir 2000 e receber 400 é normal").
- **H10 (cointegração)**: `backtesting/pairs_trading.py::run_pairs_backtest`
  não tem comando CLI nem chamador permanente hoje — foi avaliada por
  script ad-hoc. Reavaliar exigiria criar esse comando primeiro. **Fora do
  escopo desta spec** (Assumptions) — é trabalho de tamanho comparável a
  uma spec própria, não um ajuste de constante.
- **Custo de rede maior**: mais candles por par significa mais tempo de
  busca. Medido (Contexto): ~35s para os 12 pares a 6.000 candles cada,
  aceitável para uma reavaliação pontual, não um comando de ciclo de
  produção.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST usar um teto de histórico maior que 2.000
  candles nos chamadores de `fetch_ohlcv` de `backtesting/modelo.py`
  (H14/H17) e `backtesting/onchain_hipotese.py` (H17).
- **FR-002**: O novo teto MUST ser um valor medido e declarado (Fase 0),
  não o máximo teórico não verificado para todo o universo.
- **FR-003**: `backtesting/horizonte.py` MUST poder rodar com o teto
  maior para os timeframes `4h`/`1d` — `1w` MUST continuar como está
  (edge case, sem mudança).
- **FR-004**: O sistema MUST NOT alterar `execution/order_manager.py`,
  `trading/`, nem o comportamento de produção — mudança restrita à
  bateria de pesquisa.
- **FR-005**: O sistema MUST NOT alterar `run_backtest()`
  (`backtesting/engine.py`) nem qualquer comando que sirva usuários fora
  da bateria de hipóteses (`backtest`, `edge`, `compare`, `scan`,
  `optimize`) — escopo restrito aos módulos de H10/H11/H14/H17.
- **FR-006**: Cada reavaliação (H14, H17, H11 em 4h/1d) MUST ter seu
  resultado novo registrado em
  `docs/research/registro-de-hipoteses.md`, comparado explicitamente
  contra o valor já publicado — nunca substituindo silenciosamente um
  número sem declarar o que mudou e por quê.
- **FR-007**: H10 MUST ficar fora do escopo desta spec — documentado como
  trabalho futuro (Assumptions), não implementado aqui.

### Key Entities

- **Teto de histórico**: constante nova, declarada e medida (Fase 0),
  usada pelos chamadores dentro do escopo (FR-001).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: H17 sai do bloqueio específico de amostra da linha de base
  (7 < 10 operações) com o histórico estendido.
- **SC-002**: H14 e H17 são reavaliadas com `n_treino`/`n_teste` maiores
  que os valores publicados hoje.
- **SC-003**: H11 é reavaliada em 4h/1d; 1w permanece sem mudança
  (declarado, não uma falha).
- **SC-004**: Nenhuma mudança de comportamento em produção
  (`trading/`, `execution/`, `risk/`) nem nos comandos de uso geral
  (`backtest`, `edge`, `compare`, `scan`, `optimize`).
- **SC-005**: Cada resultado novo é comparado explicitamente contra o
  publicado no registro-mestre.

---

## Assumptions

- Teto novo declarado e medido em `research.md` (Fase 0) — mesmo padrão
  D1-D6 já usado em toda a sessão, não um valor arbitrário.
- **H10 fica fora do escopo**: `run_pairs_backtest` não tem comando CLI
  nem chamador permanente — criar isso é trabalho do tamanho de uma spec
  própria (comando novo, decisões de universo/período), não um ajuste de
  constante como H11/H14/H17. Registrado aqui para não ser esquecido, não
  para ser resolvido nesta spec.
- Resultado de uma reavaliação pode confirmar, enfraquecer ou fortalecer
  o veredito já publicado — nenhum dos três é o objetivo; o objetivo é
  medir com a amostra que já deveria ter sido usada.
