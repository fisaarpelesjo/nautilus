# Feature Specification: Paridade de Custos entre Paper e Backtest

**Feature Branch**: `010-paridade-custos-paper`

**Created**: 2026-08-16

**Status**: Concluída (US1-US2 implementadas, revisadas e commitadas; Polish completo)

**Input**: User description: "Paridade de custos entre paper mode live e backtest:
execution/order_manager.py `_paper_buy()`/`_paper_sell()` calculam custo/proceeds como `quantity *
price` puro, sem aplicar `BACKTEST_FEE_RATE` (0.001) nem `BACKTEST_SLIPPAGE_PCT` (0.0005) já
existentes em config/settings.py e já usados em todo o `backtesting/engine.py`. Isso cria uma
divergência sistemática: o bot em paper mode (rodando 24/7 numa VPS agora, coletando dados reais
pra validar a estratégia) registra PnL mais otimista que a realidade em ~0.3% por round-trip, o que
pode inverter o sinal de trades marginais. Escopo: aplicar os mesmos
`BACKTEST_FEE_RATE`/`BACKTEST_SLIPPAGE_PCT` em `_paper_buy()`/`_paper_sell()`, mantendo
`_live_buy()`/`_live_sell()` intocados. Validável inteiramente com testes unitários."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Slippage realista em entradas e saídas paper (Priority: P1)

Como operador validando a estratégia em paper mode, quero que o preço de entrada e saída simulado
reflita o mesmo slippage que o backtest já assume, para que uma posição não abra/feche num preço
melhor do que o mercado realmente ofereceria.

**Why this priority**: É metade da divergência de custo identificada — sem isso, o preço-base de
cada trade paper já está sistematicamente otimista antes mesmo de considerar taxa.

**Independent Test**: Abrir uma posição paper com preço de mercado conhecido e confirmar que o
preço de entrada registrado é `price * (1 + BACKTEST_SLIPPAGE_PCT)`; fechar e confirmar que o
preço de saída é `price * (1 - BACKTEST_SLIPPAGE_PCT)` — mesma fórmula usada em
`backtesting/engine.py`.

**Acceptance Scenarios**:

1. **Given** um sinal de compra em `TRADING_MODE=paper` com preço de mercado $100 e
   `BACKTEST_SLIPPAGE_PCT=0.0005`, **When** a posição abre, **Then** o preço de entrada registrado
   é $100.05, não $100.
2. **Given** uma posição paper aberta que atinge o alvo de saída (take profit, stop loss ou sinal
   de venda) a preço de mercado $110, **When** a posição fecha, **Then** o preço de saída
   registrado é $109.945 (`110 * (1 - 0.0005)`), não $110.
3. **Given** `TRADING_MODE=live`, **When** uma ordem real é executada, **Then** o preço vem
   integralmente da execução real da exchange, sem nenhum ajuste de slippage simulado adicional.

---

### User Story 2 - Taxa realista em entradas e saídas paper (Priority: P1)

Como operador validando a estratégia em paper mode, quero que o custo de entrada e o valor
recebido na saída considerem a taxa da exchange (`BACKTEST_FEE_RATE`), para que o PnL registrado em
`data/trades.csv` reflita o custo real de operar, não um cenário sem taxas.

**Why this priority**: É a outra metade da divergência de custo — mesma prioridade e mesmo motivo
de urgência que US1 (dados sendo coletados agora na VPS, quanto mais tempo sem corrigir, mais
histórico fica sob a distorção).

**Independent Test**: Abrir e fechar uma posição paper e confirmar que o saldo final e o PnL
registrado descontam a taxa de entrada e de saída, na mesma proporção (`BACKTEST_FEE_RATE`) usada
pelo backtest para o mesmo par de preços.

**Acceptance Scenarios**:

1. **Given** uma compra paper de $100 em valor nocional com `BACKTEST_FEE_RATE=0.001`, **When** a
   posição abre, **Then** o saldo paper é debitado em $100.10 (custo + taxa), não $100.
2. **Given** uma posição paper que fecha com valor nocional de saída $110 e
   `BACKTEST_FEE_RATE=0.001`, **When** a posição fecha, **Then** o saldo paper recebe $109.89
   (proceeds - taxa), e o PnL registrado em `data/trades.csv` reflete taxa de entrada + taxa de
   saída deduzidas, não o PnL bruto.
3. **Given** um trade paper fechado, **When** comparado a um backtest simulando exatamente os
   mesmos preços de entrada/saída de mercado, **Then** o PnL líquido registrado bate com o PnL que
   `simulate_backtest()` produziria para o mesmo par de preços (mesma fórmula de custo).

---

### Edge Cases

- O que acontece quando `BACKTEST_FEE_RATE`/`BACKTEST_SLIPPAGE_PCT` estão em `0.0` (desligados)?
  Deve se comportar exatamente como hoje (custo/proceeds sem ajuste) — não pode quebrar quem
  eventualmente zere essas variáveis no `.env`.
- O que acontece com o dado histórico já acumulado em `data/trades.csv` antes desta correção (ex:
  trades fechados durante os primeiros dias de operação da VPS, se algum já tiver fechado)? Fora de
  escopo corrigir retroativamente — a correção vale a partir do deploy desta spec; o operador deve
  estar ciente de que trades anteriores a essa data usam custo otimista.
- O saldo paper insuficiente para cobrir custo + taxa (hoje já bloqueia por saldo insuficiente
  sem taxa) — a checagem de saldo suficiente deve considerar o custo total (nocional + taxa), não
  só o nocional, senão uma compra pode ser aprovada e depois faltar saldo para a taxa.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST aplicar `BACKTEST_SLIPPAGE_PCT` ao preço de entrada em `_paper_buy()`
  (`entry_price = market_price * (1 + BACKTEST_SLIPPAGE_PCT)`), mesma fórmula de
  `backtesting/engine.py`.
- **FR-002**: O sistema MUST aplicar `BACKTEST_SLIPPAGE_PCT` ao preço de saída em `_paper_sell()`
  (`exit_price = market_price * (1 - BACKTEST_SLIPPAGE_PCT)`), mesma fórmula de
  `backtesting/engine.py`.
- **FR-003**: O sistema MUST aplicar `BACKTEST_FEE_RATE` sobre o valor nocional de entrada,
  debitando `custo + taxa` do saldo paper em vez de só `custo`.
- **FR-004**: O sistema MUST aplicar `BACKTEST_FEE_RATE` sobre o valor nocional de saída,
  creditando `proceeds - taxa` ao saldo paper em vez de só `proceeds`.
- **FR-005**: O PnL registrado em `data/trades.csv` para trades paper MUST refletir taxa de
  entrada e de saída deduzidas (PnL líquido), não o PnL bruto de preço.
- **FR-006**: O sistema MUST manter `_live_buy()`/`_live_sell()` sem nenhuma alteração — execução
  real já paga custo de mercado real, não deve ter ajuste simulado adicional.
- **FR-007**: A checagem de saldo suficiente para abrir uma posição paper MUST considerar o custo
  total (nocional + taxa), não só o nocional.
- **FR-008**: O sistema MUST continuar se comportando de forma idêntica ao atual quando
  `BACKTEST_FEE_RATE=0` e `BACKTEST_SLIPPAGE_PCT=0`.

### Key Entities

- **Custo de entrada paper**: nocional da posição (`quantity * entry_price` já com slippage) mais
  taxa (`nocional * BACKTEST_FEE_RATE`), debitado do saldo paper.
- **Proceeds de saída paper**: nocional da posição na saída (já com slippage) menos taxa, creditado
  ao saldo paper.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um trade paper fechado com preços de entrada/saída de mercado conhecidos produz o
  mesmo PnL líquido que `simulate_backtest()` produziria para o mesmo par de preços, com a mesma
  configuração de `BACKTEST_FEE_RATE`/`BACKTEST_SLIPPAGE_PCT` — diferença zero, não aproximada.
- **SC-002**: Toda a suíte de testes existente continua passando após a mudança (incluindo testes
  que hoje assumem custo exato sem taxa — esses são atualizados como parte da spec, não
  contornados).
- **SC-003**: Com `BACKTEST_FEE_RATE=0` e `BACKTEST_SLIPPAGE_PCT=0`, o comportamento é idêntico ao
  código anterior à spec (nenhuma regressão para quem desligar os dois).

## Assumptions

- `_paper_buy()`/`_paper_sell()` em `execution/order_manager.py` são o único caminho de execução
  simulada usado pelo loop de produção em `TRADING_MODE=paper` — não existe um segundo caminho
  paralelo de simulação a atualizar.
- As mesmas variáveis `BACKTEST_FEE_RATE`/`BACKTEST_SLIPPAGE_PCT` (já validadas em
  `validate_config()`) são reutilizadas sem criar uma segunda configuração paralela
  (`PAPER_FEE_RATE`, etc.) — reflete a intenção de que o paper mode deve simular a mesma realidade
  de custo que o backtest já modela, com o mesmo número.
- Trades paper já fechados antes desta correção (se houver, na janela entre o deploy da VPS em
  2026-08-16 e o merge desta spec) não são reprocessados — ficam registrados com o custo otimista
  anterior, e isso deve ser considerado ao analisar `data/trades.csv` posteriormente.
