# Feature Specification: Hardening Incremental do Bot de Daytrade

**Feature Branch**: `001-hardening-incremental`

**Created**: 2026-08-13

**Status**: Draft

**Input**: User description: "Refatorar o bot de daytrade Binance existente seguindo SDD: fechar os
gaps reais de seguranca operacional (idempotencia de ordens, reconciliacao com a exchange, circuit
breaker mais completo), qualidade (CI, lint, type-check) e validacao de estrategia (walk-forward),
preservando tudo que ja funciona (paper mode, backtest, testes existentes). Ver auditoria de codigo
real feita em 2026-08-13 documentada em `.specify/memory/constitution.md`."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ordens nunca duplicam nem ficam fora de sincronia (Priority: P1)

Como operador do bot (dono da conta Binance, opera sozinho, sem monitoramento 24/7), eu quero que
toda ordem enviada seja rastreável de forma única e que o estado local do bot nunca fique
divergente do estado real da minha conta, para que um retry de rede ou uma queda do bot não me
faça perder dinheiro por ordem duplicada ou por decisão tomada sobre um estado que não é mais real.

**Why this priority**: É o gap de maior risco financeiro direto confirmado na auditoria de código
(`execution/order_manager.py` hoje não usa `clientOrderId` nem reconcilia com a exchange) — P6 da
constitution do projeto. Sem isso, qualquer outra melhoria de estratégia é secundária.

**Independent Test**: Pode ser testado isoladamente rodando o bot em paper mode, forçando um retry
simulado de envio de ordem e um reinício do processo com uma posição aberta, e verificando que (a)
nenhuma ordem duplicada é criada e (b) o estado é reconciliado (ou a divergência é alertada) sem
intervenção manual.

**Acceptance Scenarios**:

1. **Given** o bot está prestes a enviar uma ordem de compra, **When** a chamada à exchange é
   repetida (ex: timeout seguido de retry), **Then** a exchange reconhece o `clientOrderId` já usado
   e não executa uma segunda ordem para o mesmo sinal.
2. **Given** o bot é reiniciado com uma posição registrada em `state.json`, **When** o bot inicializa,
   **Then** ele compara essa posição com o estado real da conta na Binance e, se houver divergência,
   grava um evento estruturado e envia um alerta — sem corrigir automaticamente o estado.
3. **Given** o bot está rodando em modo paper, **When** o ciclo de reconciliação periódica roda,
   **Then** nenhuma ordem/posição simulada é comparada contra a exchange real (reconciliação só se
   aplica a `TRADING_MODE=live`).

---

### User Story 2 - Circuit breaker além do limite diário de drawdown (Priority: P2)

Como operador do bot, eu quero que ele pare de abrir novas posições automaticamente depois de uma
sequência de perdas seguidas, e que eu tenha um jeito manual de suspender novas entradas a qualquer
momento, para que um problema de estratégia ou de mercado não continue consumindo capital antes que
eu perceba e intervenha.

**Why this priority**: Hoje o único circuit breaker automático é o limite de drawdown diário
(`DAILY_DRAWDOWN_LIMIT`); não há proteção contra uma sequência de perdas dentro do mesmo dia que
ainda não estourou esse limite, nem um jeito de parar o bot manualmente sem matar o processo.

**Independent Test**: Pode ser testado isoladamente em paper mode, simulando N stops consecutivos
com prejuízo e verificando que o bot suspende novas entradas; e testando o comando manual de
kill switch/resume de forma independente da lógica de perdas consecutivas.

**Acceptance Scenarios**:

1. **Given** o número de perdas consecutivas configurado (`MAX_CONSECUTIVE_LOSSES`) ainda não foi
   atingido, **When** um trade fecha com prejuízo, **Then** o contador de perdas consecutivas
   incrementa e o bot continua permitindo novas entradas.
2. **Given** o contador de perdas consecutivas atinge o limite configurado, **When** o próximo ciclo
   roda, **Then** o bot bloqueia novas entradas (mantendo gestão de posições já abertas) e registra o
   evento.
3. **Given** um trade fecha com lucro, **When** o resultado é processado, **Then** o contador de
   perdas consecutivas volta a zero.
4. **Given** o operador executa o comando de kill switch, **When** o próximo ciclo do bot roda,
   **Then** nenhuma nova entrada é aberta até o operador executar o comando de resume — mesmo que
   nenhum outro limite de risco tenha sido atingido.

---

### User Story 3 - Validação de estratégia fora da amostra usada para otimizar (Priority: P3)

Como operador do bot, eu quero que o relatório de backtest mostre separadamente o desempenho no
período usado para ajustar parâmetros e o desempenho em um período que a estratégia nunca viu, para
que eu não confie em um resultado bom que na verdade é só overfitting.

**Why this priority**: Já é uma lacuna reconhecida no `ROADMAP.md` do projeto (separação
treino/teste), mas de risco financeiro indireto (leva a uma decisão ruim de ativar `live`, não a uma
perda operacional imediata como US1/US2) — por isso vem depois.

**Independent Test**: Pode ser testado isoladamente rodando o backtest existente sobre um par/período
conhecido, com e sem o split, e comparando se o relatório passa a exibir métricas in-sample e
out-of-sample separadas, sem alterar o resultado do backtest atual (sem split) já coberto pelos
testes existentes.

**Acceptance Scenarios**:

1. **Given** um período histórico suficiente para pelo menos duas janelas, **When** o backtest roda
   com validação out-of-sample habilitada, **Then** o relatório mostra métricas (retorno, profit
   factor, drawdown) separadas para a janela de treino/otimização e para a janela de validação.
2. **Given** os critérios de aprovação automática (retorno > buy-and-hold, profit factor > 1.2,
   drawdown aceitável, nº mínimo de trades), **When** avaliados, **Then** são aplicados sobre a janela
   out-of-sample, não sobre a janela de treino.

---

### Edge Cases

- O que acontece se a reconciliação encontrar divergência mas o bot estiver em modo paper? → Não se
  aplica; reconciliação com a exchange real só roda em `TRADING_MODE=live` (paper não tem conta real
  para comparar).
- O que acontece se o kill switch for ativado enquanto há posições abertas? → As posições abertas
  continuam sendo geridas normalmente (SL/TP/trailing); só novas entradas são bloqueadas.
- O que acontece se `MAX_CONSECUTIVE_LOSSES` for atingido no mesmo ciclo em que
  `DAILY_DRAWDOWN_LIMIT` também é estourado? → Ambos os bloqueios são independentes e cumulativos;
  qualquer um dos dois já é suficiente para suspender novas entradas.
- O que acontece se não houver dados suficientes para uma janela out-of-sample? → O relatório indica
  que a validação out-of-sample não foi possível para aquele período, em vez de mostrar um número
  enganoso.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST gerar um identificador único (`clientOrderId`) para toda ordem enviada
  à exchange, tanto em modo paper quanto em modo live, e persistir esse identificador junto ao
  registro da ordem.
- **FR-002**: O sistema MUST comparar o estado local de posições/ordens com o estado real da conta
  Binance na inicialização do bot e periodicamente durante a execução, quando `TRADING_MODE=live`.
- **FR-003**: O sistema MUST registrar um evento estruturado e enviar um alerta quando uma
  divergência de reconciliação for detectada, e MUST NOT corrigir automaticamente o estado local sem
  intervenção do operador.
- **FR-004**: O sistema MUST contar perdas consecutivas (trades fechados com prejuízo) e resetar essa
  contagem a cada trade fechado com lucro.
- **FR-005**: O sistema MUST suspender a abertura de novas posições quando o número de perdas
  consecutivas atingir um limite configurável, mantendo a gestão de posições já abertas.
- **FR-006**: O sistema MUST oferecer um comando manual (kill switch) que suspende novas entradas
  imediatamente, independente de qualquer outro limite de risco, e um comando complementar para
  retomar (resume).
- **FR-007**: O sistema MUST persistir o estado do kill switch entre reinícios do bot.
- **FR-008**: O sistema MUST permitir rodar o backtest existente com uma divisão configurável entre
  janela de treino/otimização e janela de validação out-of-sample, reportando as métricas de cada
  janela separadamente.
- **FR-009**: O sistema MUST manter compatibilidade total com o comportamento atual quando as novas
  capacidades acima não estiverem habilitadas ou não se aplicarem (ex: modo paper para reconciliação,
  backtest sem split para o modo de validação).
- **FR-010**: O sistema MUST ter cobertura de teste automatizada para cada uma das capacidades acima
  antes de qualquer uma delas ser considerada pronta para `TRADING_MODE=live`.

### Key Entities

- **Ordem rastreável (clientOrderId)**: identificador único gerado pelo bot para cada ordem enviada;
  associado ao registro de trade/ordem já existente em `data/trade_store.py` e `state.json`.
- **Relatório de reconciliação**: comparação pontual entre o estado local (`state.json`) e o estado
  real da conta Binance; resultado é "ok" ou "divergência" com detalhes do que diverge.
- **Contador de perdas consecutivas**: contador persistido por par (ou global, a definir na fase de
  planejamento) que soma stops com prejuízo em sequência e zera em qualquer trade positivo.
- **Kill switch**: flag booleana persistida indicando se novas entradas estão manualmente suspensas.
- **Janela de validação out-of-sample**: partição temporal de um backtest em período de
  treino/otimização e período de validação, cada uma com seu próprio conjunto de métricas.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma ordem reenviada por retry de rede nunca resulta em posição duplicada — verificável
  em 100% das execuções de teste simulando retry.
- **SC-002**: Toda divergência entre `state.json` e a conta real da Binance gera um alerta em até um
  ciclo de reconciliação (inicialização ou próximo ciclo periódico), nunca passando despercebida
  silenciosamente.
- **SC-003**: O bot suspende novas entradas em até um ciclo depois de atingir o limite de perdas
  consecutivas configurado, sem exigir reinício manual.
- **SC-004**: O operador consegue suspender novas entradas manualmente em menos de 1 minuto (tempo de
  rodar o comando + próximo ciclo de 60s) a qualquer momento, sem precisar derrubar o processo do
  bot.
- **SC-005**: Um relatório de backtest com validação out-of-sample habilitada mostra claramente se a
  estratégia se sustenta fora da amostra usada para otimizar parâmetros, permitindo decidir
  "aprovado", "reprovado" ou "inconclusivo" sem julgamento subjetivo.
- **SC-006**: Nenhuma das mudanças acima quebra o comportamento hoje coberto pela suíte de testes
  existente (32 testes, baseline registrado em `ROADMAP.md`).

## Assumptions

- Uso é pessoal, conta única na Binance (não multi-conta/multi-usuário) — confirmado por leitura do
  `CLAUDE.md` e ausência de qualquer indicação de multi-tenant no código.
- O bot continua operando somente Binance Spot, sem alavancagem (`max_leverage = 1`) — restrição já
  declarada no `CLAUDE.md` ("bot opera apenas posições long").
- O bot continua rodando localmente (não em VPS/cloud) por enquanto; isso não bloqueia nenhuma das
  User Stories acima, que são independentes de onde o processo roda.
- Persistência continua em CSV/JSON; nenhuma das User Stories acima exige um banco de dados.
- "Reconciliação periódica" roda dentro do loop existente de 60s do `trading/runner.py`, não como um
  processo separado — evita introduzir infraestrutura nova para uma necessidade que o loop atual já
  cobre.
- O limite de perdas consecutivas (`MAX_CONSECUTIVE_LOSSES`) é uma nova variável de ambiente com
  default a validar durante o planejamento técnico (sugestão inicial: 3), não um valor fixo no
  código.
