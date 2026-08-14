# Feature Specification: Proteções Finais para Live

**Feature Branch**: `005-live-protections`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Proteções finais para live: continuação direta de US1/US2 da spec
001-hardening-incremental. Escopo (ver `specs/BACKLOG.md` item 005, derivado do `ROADMAP.md` Fase 6):
confirmação explícita e visível ao ligar `TRADING_MODE=live` (hoje só existe uma checagem silenciosa
de config, `LIVE_TRADING_CONFIRMATION`, sem mostrar pares/saldo/limites antes de operar); limites de
perda semanal e mensal, além do diário já existente e do circuit breaker de perdas consecutivas
(spec 001 US2); checagem de liquidez e spread do order book antes de enviar uma ordem; execução via
ordens limit/stop com rastreamento de preenchimento parcial, além das ordens a mercado já existentes.
Escopo completo, incluindo a parte de execução de ordens (mais complexa e mais difícil de validar sem
uma conta live de verdade) — decisão explícita do operador ao priorizar esta spec."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver claramente o que está em jogo antes de operar com dinheiro real (Priority: P1)

Como operador do bot, eu quero ver um resumo claro (pares, saldo real, tamanho máximo por ordem,
máximo de posições, limites de perda) antes do bot começar a operar em `TRADING_MODE=live`, para não
ligar live por engano ou com uma configuração que eu não revisei conscientemente.

**Why this priority**: É a primeira linha de defesa contra erro operacional — hoje existe só uma
checagem de configuração silenciosa (`LIVE_TRADING_CONFIRMATION` precisa bater com um texto exato em
`config/settings.py`), mas ela não mostra nada sobre o que vai efetivamente operar. Sem isso, as
demais proteções desta spec protegem contra riscos que o operador nem viu antes de começar. Também é
a mudança mais simples e com maior redução de risco por esforço — não depende de nenhuma das outras
três User Stories.

**Independent Test**: Pode ser testado isoladamente configurando `TRADING_MODE=live` (com
`LIVE_TRADING_CONFIRMATION` correto) e confirmando que, antes do loop principal do bot começar, um
resumo com pares, saldo real, `MAX_ORDER_SIZE_USDT`, `MAX_POSITIONS` e os limites de perda configurados
é exibido.

**Acceptance Scenarios**:

1. **Given** `TRADING_MODE=live` configurado corretamente, **When** `python main.py bot` inicia,
   **Then** um resumo é exibido antes de qualquer ordem poder ser enviada, mostrando pares ativos,
   saldo real da conta, tamanho máximo por ordem, máximo de posições simultâneas e os limites de
   perda (diário, semanal, mensal, perdas consecutivas) configurados.
2. **Given** o mesmo cenário, **When** o resumo é exibido, **Then** o bot só prossegue para o loop
   principal depois dessa exibição — não antes, não em paralelo.
3. **Given** `TRADING_MODE=paper`, **When** o bot inicia, **Then** esse resumo de confirmação não é
   exibido (comportamento atual preservado — a proteção é específica de live).

---

### User Story 2 - Bloquear entradas após degradação sustentada, não só num único dia ruim (Priority: P2)

Como operador do bot, eu quero que ele suspenda novas entradas quando a perda acumulada na semana ou
no mês ultrapassar um limite configurável, além do limite diário e do circuit breaker de perdas
consecutivas já existentes, para me proteger de uma degradação gradual da estratégia que nenhum dos
dois limites atuais capturaria sozinho.

**Why this priority**: Extensão direta e bem precedentada do circuit breaker já implementado na spec
001 (US2) — mesmo padrão (contador persistido, bloqueio de novas entradas, sem afetar posições já
abertas), só numa janela de tempo maior. Não depende de US3/US4.

**Independent Test**: Pode ser testado isoladamente em paper mode, simulando prejuízo acumulado ao
longo de uma semana/mês simulados e confirmando que o bot suspende novas entradas quando o limite é
ultrapassado, preservando a gestão de posições já abertas.

**Acceptance Scenarios**:

1. **Given** o limite semanal de perda configurado, **When** a perda acumulada na semana corrente
   ultrapassa esse limite, **Then** o bot bloqueia novas entradas até a semana seguinte, mantendo a
   gestão de posições já abertas.
2. **Given** o limite mensal de perda configurado, **When** a perda acumulada no mês corrente
   ultrapassa esse limite, **Then** o bot bloqueia novas entradas até o mês seguinte, mesmo que o
   limite semanal ainda não tenha sido atingido.
3. **Given** o início de uma nova semana ou mês, **When** o ciclo vira, **Then** o contador
   correspondente reseta, independente do estado do outro (semanal e mensal contam separadamente,
   como o diário já faz).

---

### User Story 3 - Evitar slippage severo em pares com pouca liquidez (Priority: P3)

Como operador do bot, eu quero que ele valide a profundidade do order book e o spread antes de enviar
uma ordem, para não comprar num par onde o preço real de execução ficaria muito distante do preço
observado.

**Why this priority**: Protege contra um risco real (slippage em pares menores, citado no
`ROADMAP.md`), mas é uma capacidade adicional sobre o fluxo de entrada já existente — não é a causa
raiz de nenhum incidente já documentado neste projeto, ao contrário das User Stories 1/2.

**Independent Test**: Pode ser testado isoladamente simulando um order book com spread acima do
limite configurado (ou volume insuficiente) e confirmando que a entrada é bloqueada com um motivo
claro, sem exigir nenhuma das outras User Stories.

**Acceptance Scenarios**:

1. **Given** um par com spread acima do limite configurável, **When** um sinal de compra ocorre para
   esse par, **Then** a entrada é bloqueada com um motivo específico de liquidez/spread, distinto dos
   bloqueios já existentes (cooldown, sem slot, etc.).
2. **Given** um par com volume insuficiente no order book para o tamanho da ordem pretendida, **When**
   um sinal de compra ocorre, **Then** a entrada é bloqueada pelo mesmo motivo.
3. **Given** um par dentro dos limites de spread e liquidez, **When** um sinal de compra ocorre,
   **Then** a checagem não introduz bloqueio nem atraso perceptível no ciclo.

---

### User Story 4 - Reduzir slippage e rastrear preenchimento parcial em ordens reais (Priority: P4)

Como operador do bot, eu quero que ele possa usar ordens limit em vez de sempre ordem a mercado, e que
rastreie corretamente quando uma ordem é preenchida só parcialmente, para reduzir o custo de slippage
das ordens a mercado atuais e não perder o controle de posições que não fecharam por completo.

**Why this priority**: É a capacidade mais complexa desta spec e a mais dependente de comportamento
real de uma conta live/Testnet para validar por completo (paper mode simula preenchimento instantâneo
e completo, sem replicar preenchimento parcial real) — por isso vem por último, mesmo fazendo parte do
escopo desta spec por decisão explícita do operador.

**Independent Test**: Pode ser testado em paper mode para a lógica de rastreamento de estado
(idempotência, reconciliação de quantidade preenchida) com preenchimentos simulados, e validado de
forma mais completa em Binance Testnet antes de qualquer uso com dinheiro real — mesmo padrão de
validação em camadas já usado nas specs anteriores para mudanças em `execution/`.

**Acceptance Scenarios**:

1. **Given** o bot configurado para usar ordem limit numa entrada, **When** a ordem é enviada,
   **Then** o preço limite é calculado a partir dos dados já disponíveis (ex: melhor oferta do book),
   não um valor arbitrário.
2. **Given** uma ordem parcialmente preenchida, **When** o bot verifica o estado dela no próximo
   ciclo, **Then** a posição local reflete a quantidade realmente preenchida, não a quantidade
   originalmente solicitada.
3. **Given** uma ordem limit que não preenche dentro de um tempo/condição configurável, **When** esse
   limite é atingido, **Then** o bot tem um comportamento definido (cancelar e reverter para mercado,
   ou cancelar e desistir do sinal) — não fica com uma ordem pendente indefinidamente sem tratamento.
4. **Given** `TRADING_MODE=paper`, **When** uma ordem é simulada, **Then** o comportamento de
   preenchimento (completo ou parcial simulado) é claramente marcado como simulação, não confundido
   com um preenchimento real reportado pela exchange.

---

### Edge Cases

- O que acontece se o operador iniciar `TRADING_MODE=live` sem terminal interativo (ex: rodando como
  serviço/cron)? → O resumo da User Story 1 ainda é exibido (via log, não só terminal), mas o bot MUST
  NOT bloquear esperando uma confirmação interativa adicional além do `LIVE_TRADING_CONFIRMATION` já
  existente em `.env` — não pode travar um processo não-interativo indefinidamente.
- O que acontece se os limites semanal e mensal (US2) forem configurados de forma inconsistente (ex:
  limite semanal maior que o mensal)? → Validado na configuração (mesmo padrão de `validate_config()`
  já existente), com erro claro antes do bot iniciar, não uma inconsistência silenciosa em runtime.
- O que acontece se a checagem de liquidez/spread (US3) falhar por erro de rede ao buscar o order
  book? → Tratado como bloqueio conservador (não compra), não como liquidez aprovada por omissão —
  mesmo princípio já usado em decisões de saldo desconhecido na spec 001.
- O que acontece com uma ordem limit (US4) durante uma reconciliação (spec 001 US1)? → A reconciliação
  já existente continua sendo a rede de segurança final; uma ordem limit pendente não reconciliada
  deve aparecer como divergência real, não ser ignorada pela lógica de reconciliação atual.
- O que acontece se o preenchimento parcial deixar uma posição menor que o mínimo negociável do par
  (LOT_SIZE/MIN_NOTIONAL da Binance)? → Tratado explicitamente (ex: liquidar o residual ou registrar
  como posição presa com alerta), não deixado para uma falha silenciosa numa tentativa futura de
  fechar.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST exibir um resumo (pares, saldo real, `MAX_ORDER_SIZE_USDT`,
  `MAX_POSITIONS`, limites de perda diário/semanal/mensal/perdas-consecutivas) antes do bot iniciar o
  loop principal quando `TRADING_MODE=live`.
- **FR-002**: O sistema MUST NOT exibir esse resumo (nem alterar o comportamento de inicialização)
  quando `TRADING_MODE=paper`.
- **FR-003**: O sistema MUST NOT bloquear a inicialização esperando confirmação interativa adicional
  além da já existente (`LIVE_TRADING_CONFIRMATION` em `.env`) — o resumo é informativo, não um novo
  prompt bloqueante.
- **FR-004**: O sistema MUST contar perda acumulada por semana e por mês, cada um com seu próprio
  limite configurável, independente do limite diário e do circuit breaker de perdas consecutivas já
  existentes.
- **FR-005**: O sistema MUST suspender novas entradas quando o limite semanal OU o mensal for
  ultrapassado, mantendo a gestão de posições já abertas — mesmo comportamento já estabelecido para o
  circuit breaker (spec 001 US2).
- **FR-006**: O sistema MUST resetar cada contador (semanal, mensal) de forma independente, na
  virada do respectivo período.
- **FR-007**: O sistema MUST validar spread e profundidade de liquidez do order book antes de uma
  ordem de compra, bloqueando a entrada com motivo específico quando fora dos limites configuráveis.
- **FR-008**: O sistema MUST tratar falha ao buscar dados de liquidez/spread como bloqueio
  conservador, não como aprovação por omissão.
- **FR-009**: O sistema MUST oferecer a opção de enviar ordens limit (além das ordens a mercado já
  existentes), com preço limite derivado de dado de mercado real disponível no momento do envio.
- **FR-010**: O sistema MUST rastrear e refletir corretamente na posição local quando uma ordem for
  preenchida apenas parcialmente, não assumir preenchimento completo.
- **FR-011**: O sistema MUST ter um comportamento definido e testado para ordens limit que não
  preenchem dentro de um critério configurável (tempo ou condição), sem deixar ordens pendentes sem
  tratamento.
- **FR-012**: O sistema MUST manter compatibilidade com o comportamento atual (ordens a mercado,
  limites hoje existentes) para quem não habilitar as novas capacidades de US3/US4 — mudanças
  aditivas via configuração, não substituições forçadas do comportamento hoje validado.
- **FR-013**: Nenhuma tarefa desta spec MUST habilitar `TRADING_MODE=live` automaticamente nem
  remover/contornar o guard-rail de `LIVE_TRADING_CONFIRMATION` já existente (Constitution, princípio
  I).

### Key Entities

- **Resumo de confirmação live**: snapshot exibido na inicialização em modo live — pares, saldo real,
  limites de tamanho/posições/perda configurados no momento.
- **Contadores de perda por período**: perda acumulada na semana e no mês correntes, cada um com
  limite e data de reset próprios — extensão do padrão já usado pelo `daily_pnl`/circuit breaker.
- **Checagem de liquidez**: resultado (aprovado/bloqueado + motivo) da validação de spread/profundidade
  do order book para um par antes de uma ordem.
- **Ordem limit rastreada**: ordem enviada com preço limite, quantidade solicitada, quantidade
  efetivamente preenchida (pode ser parcial), e o critério de expiração/cancelamento aplicado.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Ao iniciar `python main.py bot` em `TRADING_MODE=live`, o operador vê pares, saldo real
  e todos os limites de perda configurados antes de qualquer ordem poder ser enviada, sem precisar
  consultar `.env`/código para saber o que está configurado.
- **SC-002**: Uma sequência de perdas que não atinge o limite diário nem o circuit breaker de perdas
  consecutivas, mas ultrapassa o limite semanal ou mensal configurado, ainda assim suspende novas
  entradas — verificável em teste automatizado simulando esse cenário.
- **SC-003**: Uma tentativa de compra num par com spread/liquidez fora dos limites configurados é
  bloqueada antes de qualquer ordem ser enviada à exchange, com um motivo específico registrado.
- **SC-004**: Uma ordem limit com preenchimento parcial simulado resulta numa posição local com a
  quantidade correta (não a quantidade original solicitada), verificável em teste automatizado.
- **SC-005**: Nenhuma das mudanças acima altera o comportamento de `TRADING_MODE=paper` nem exige
  `TRADING_MODE=live` para ser testada — toda a lógica é validável em paper mode ou com dados
  simulados, exceto a confirmação final de comportamento real de preenchimento parcial (User Story 4),
  que depende de Testnet/live conforme o processo de validação em camadas já estabelecido no projeto.
- **SC-006**: Nenhuma das mudanças acima quebra o comportamento hoje coberto pela suíte de testes
  existente.

## Assumptions

- "Perda semanal/mensal" segue o mesmo padrão já usado por `daily_pnl` (spec existente,
  `execution/order_manager.py`): contador persistido em `state.json`, resetado na virada do período
  (semana: segunda-feira; mês: dia 1 — a decidir exatamente na fase de planejamento), não uma janela
  deslizante de N dias.
- A checagem de liquidez/spread (US3) usa `fetch_order_book`/`fetch_ticker` via `ccxt`, já em uso pelo
  projeto para outras chamadas de mercado — sem nova dependência externa.
- Ordens limit (US4) são uma capacidade adicional configurável, não uma substituição obrigatória das
  ordens a mercado já existentes e validadas — o comportamento default continua sendo ordem a mercado,
  a menos que explicitamente configurado o contrário, preservando o comportamento já testado em paper
  mode por semanas.
- O critério exato de "spread aceitável"/"profundidade mínima" (US3) e o "critério de
  expiração"/estratégia de fallback de ordens limit não preenchidas (US4) ficam definidos com valores
  default razoáveis na fase de planejamento, configuráveis via `.env` como todo o resto do projeto.
- Esta spec, como todas as anteriores, MUST NOT habilitar uso em dinheiro real por conta própria — todo
  trabalho é implementado e validado em paper mode (e Testnet quando aplicável para US4), com a decisão
  de ativar live permanecendo manual e exclusiva do operador, conforme checklist de go-live já
  registrado em `specs/001-hardening-incremental/tasks.md` (T037).
