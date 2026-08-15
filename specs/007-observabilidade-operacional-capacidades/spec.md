# Feature Specification: Observabilidade Operacional

**Feature Branch**: `007-observabilidade-operacional-capacidades`

**Created**: 2026-08-15

**Status**: Draft

**Input**: User description: "Observabilidade operacional: capacidades testáveis sem depender de
histórico real de paper mode rodando (specs/BACKLOG.md item 007, derivado do ROADMAP.md Fase 5 itens
2-3-5-6-7). Escopo: separar caixa livre/posições/patrimônio total no status; contexto explícito no
relatório de edge; painel local (`python main.py painel`); modo debug da estratégia; gráficos de
performance. Fora de escopo: forward test formal e comparação paper-vs-backtest do mesmo período
(Fase 5 itens 1 e 4) — exigem histórico real de paper mode rodando por um período."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Não confundir caixa livre com patrimônio total (Priority: P1)

Como operador do bot, eu quero ver separadamente caixa livre, valor em posições abertas, patrimônio
total, PnL realizado, PnL não realizado e PnL total em qualquer resumo operacional, para não
interpretar um saldo baixo como perda quando na verdade o capital está alocado numa posição aberta.

**Why this priority**: É a confusão mais direta e mais citada no `ROADMAP.md` — hoje `status` mostra
`paper_balance_usdt` (caixa livre) como se fosse "o saldo", sem separar do valor investido em posições
abertas. Afeta a leitura correta de qualquer outro resumo operacional, por isso vem primeiro.

**Independent Test**: Com uma posição aberta em paper mode, `python main.py status` mostra caixa
livre, valor da posição aberta ao preço atual, patrimônio total (caixa + posições) e os três PnLs
(realizado, não realizado, total) como valores distintos e corretos.

**Acceptance Scenarios**:

1. **Given** o bot com uma posição aberta e caixa livre, **When** `python main.py status` roda,
   **Then** caixa livre, valor em posições abertas e patrimônio total (caixa + posições) aparecem
   como três números distintos.
2. **Given** a mesma situação, **When** o status é exibido, **Then** PnL realizado (trades já
   fechados), PnL não realizado (posições abertas ao preço atual) e PnL total (soma dos dois)
   aparecem separadamente.
3. **Given** nenhuma posição aberta, **When** o status é exibido, **Then** patrimônio total é igual
   à caixa livre e PnL não realizado é zero — sem comportamento especial exigido para esse caso.

---

### User Story 2 - Não confundir o capital final do edge com o saldo real do bot (Priority: P2)

Como operador do bot, eu quero que `python main.py edge` deixe explícito que é uma simulação
histórica (par, timeframe, período testado, capital inicial simulado), para não achar que o
"capital final" ali reportado é o saldo atual do paper bot rodando.

**Why this priority**: Risco de interpretação errada direto (confundir simulação com estado real),
mas afeta só o comando `edge`, não todo resumo operacional como a User Story 1 — por isso prioridade
menor.

**Independent Test**: Rodar `python main.py edge` e confirmar que o relatório inclui um aviso
explícito de que é uma simulação histórica, junto com par, timeframe, período testado e capital
inicial simulado.

**Acceptance Scenarios**:

1. **Given** `python main.py edge` rodando para qualquer par, **When** o relatório é exibido,
   **Then** aparecem explicitamente: modo ("backtest simulado"), par, timeframe, período testado e
   capital inicial simulado.
2. **Given** o mesmo relatório, **When** o operador o lê, **Then** um aviso deixa claro que o
   resultado não reflete o estado real salvo em `data/state.json`.

---

### User Story 3 - Ver o estado operacional completo sem vasculhar múltiplos comandos (Priority: P3)

Como operador do bot, eu quero um painel único (`python main.py painel`) mostrando saldo, posições
abertas, PnL, últimas operações, últimos sinais, status dos pares e bloqueios recentes, para não
precisar rodar vários comandos ou abrir CSVs manualmente para saber se o bot está saudável.

**Why this priority**: Agrega informação que já existe em `status`/`data/trades.csv`/
`data/signals.csv`/`data/decisions.csv` — alto valor de conveniência, mas nenhuma informação nova
que já não estivesse acessível de outra forma, por isso vem depois das duas User Stories anteriores
(que corrigem informação hoje enganosa).

**Independent Test**: Rodar `python main.py painel` num ambiente com histórico de trades/sinais/
decisões (real ou sintético) e confirmar que todas as seções (saldo, posições, PnL, últimas
operações, últimos sinais, status dos pares, bloqueios recentes) aparecem sem erro.

**Acceptance Scenarios**:

1. **Given** o bot com histórico de operações, **When** `python main.py painel` roda, **Then** o
   painel mostra patrimônio (reusando a User Story 1), posições abertas, últimas operações
   (`data/trades.csv`), últimos sinais (`data/signals.csv`) e bloqueios recentes
   (`data/decisions.csv`).
2. **Given** o bot sem nenhum histórico (instalação nova), **When** o painel roda, **Then** cada
   seção mostra um estado vazio claro ("nenhuma operação ainda"), não um erro.

---

### User Story 4 - Entender por que um par não está entrando sem ler código (Priority: P4)

Como operador do bot, eu quero um modo de diagnóstico que explique por que cada par está em `BUY`,
`SELL` ou `HOLD` — incluindo EMA, RSI, volume, MTF, Bollinger, regime e cooldown — para não precisar
adivinhar qual filtro está bloqueando uma entrada esperada.

**Why this priority**: Ferramenta de diagnóstico usada sob demanda (quando algo parece errado), não
informação que o operador precisa ver toda vez — prioridade menor que os itens anteriores, que afetam
a leitura padrão do estado do bot.

**Independent Test**: Rodar o modo debug para um par específico e confirmar que a saída explica o
valor de cada filtro relevante (EMA fast/slow/trend, RSI, volume vs média, MTF, Bollinger, regime,
cooldown) e por que o sinal final é `BUY`/`SELL`/`HOLD`.

**Acceptance Scenarios**:

1. **Given** um par com sinal `HOLD`, **When** o modo debug roda para esse par, **Then** a saída
   mostra o valor de cada condição de entrada (EMA, RSI, volume, MTF, Bollinger, regime,
   volatilidade) e identifica qual(is) delas está bloqueando o `BUY`.
2. **Given** um par em cooldown, **When** o modo debug roda, **Then** o cooldown aparece
   explicitamente como o motivo, não escondido atrás de "condições normais não bateram".

---

### User Story 5 - Ver visualmente o que os números não mostram claramente (Priority: P5)

Como operador do bot, eu quero gráficos de curva de capital, drawdown e PnL por par, além dos
candles com marcações de entrada/saída, para identificar padrões (lucro concentrado em poucos
trades, drawdown longo, entradas antes de reversões) que são mais difíceis de ver só em números.

**Why this priority**: Maior esforço de implementação desta spec (visualização, não só leitura de
dados já existentes) e o valor mais complementar às demais — vem por último.

**Independent Test**: Gerar os gráficos (curva de capital, drawdown, PnL por par) a partir de um
histórico de trades (real ou sintético) e confirmar que são produzidos sem erro, com marcações de
entrada/saída no gráfico de candles já existente (`python main.py chart`).

**Acceptance Scenarios**:

1. **Given** um histórico de trades fechados, **When** os gráficos de performance são gerados,
   **Then** curva de capital, drawdown ao longo do tempo e PnL por par aparecem corretamente.
2. **Given** o gráfico de candles já existente (`python main.py chart`), **When** há trades
   fechados no período exibido, **Then** marcações de entrada/saída aparecem sobre os candles.

---

### Edge Cases

- O que acontece se `python main.py painel`/modo debug/gráficos de performance rodarem sem nenhum
  histórico (`data/trades.csv`/`data/signals.csv`/`data/decisions.csv` inexistentes ou vazios)? →
  Estado vazio claro em cada seção, não erro — mesmo princípio já aplicado em
  `data/decisions_analysis.py` (spec 004) para CSV ausente/vazio.
- O que acontece se o preço atual de uma posição aberta não puder ser buscado (falha de rede) ao
  calcular PnL não realizado? → Mesmo princípio já usado em `trading/position_lifecycle.py`
  `_current_balance`: não pode virar `0.0`/aprovação silenciosa — PnL não realizado daquela posição
  MUST ser exibido como indisponível, não escondido nem calculado incorretamente como zero.
- O que acontece com o modo debug para um par com dados insuficientes (poucos candles)? → Mesmo
  tratamento já usado pelas estratégias para dados insuficientes — explicar isso como o motivo, não
  travar ou mostrar um erro não tratado.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST exibir caixa livre, valor em posições abertas (ao preço atual) e
  patrimônio total (soma dos dois) como valores distintos em `python main.py status`.
- **FR-002**: O sistema MUST exibir PnL realizado, PnL não realizado (das posições abertas) e PnL
  total (soma dos dois) separadamente em `python main.py status`.
- **FR-003**: O sistema MUST exibir no relatório de `python main.py edge`: modo ("backtest
  simulado"), par, timeframe, período testado e capital inicial simulado, com aviso explícito de que
  não reflete o estado real do bot.
- **FR-004**: O sistema MUST oferecer um comando (`python main.py painel`) que agregue saldo/
  patrimônio (reusando FR-001/FR-002), posições abertas, últimas operações, últimos sinais, status
  dos pares e bloqueios recentes numa única execução.
- **FR-005**: O sistema MUST tratar histórico ausente ou vazio em qualquer seção do painel como
  estado vazio explícito, não como erro.
- **FR-006**: O sistema MUST oferecer um modo de diagnóstico que explique, para um par específico,
  o valor de cada condição de entrada relevante (EMA, RSI, volume, MTF, Bollinger, regime,
  volatilidade, cooldown) e identifique qual delas está bloqueando um sinal `BUY` quando aplicável.
- **FR-007**: O sistema MUST gerar gráficos de curva de capital, drawdown ao longo do tempo e PnL
  por par a partir de um histórico de trades.
- **FR-008**: O sistema MUST exibir marcações de entrada/saída de trades sobre o gráfico de candles
  já existente (`python main.py chart`) quando houver trades fechados no período exibido.
- **FR-009**: O sistema MUST tratar falha ao buscar o preço atual de uma posição aberta (para PnL
  não realizado) como indisponível, nunca como zero silencioso.
- **FR-010**: Nenhuma tarefa desta spec MUST exigir histórico real de operação paper para ser
  validada — toda validação funcional usa dados públicos de backtest ou fixtures sintéticas
  (mesmo padrão já usado em `data/decisions_analysis.py`, spec 004).

### Key Entities

- **Patrimônio operacional**: caixa livre, valor em posições abertas, patrimônio total, PnL
  realizado, PnL não realizado, PnL total — cálculo compartilhado entre `status` e `painel`.
- **Contexto de simulação**: metadados do relatório de edge (modo, par, timeframe, período, capital
  inicial simulado).
- **Painel operacional**: agregação read-only de patrimônio, posições, últimas operações, últimos
  sinais, status dos pares e bloqueios recentes.
- **Diagnóstico de sinal**: explicação estruturada de cada condição de entrada avaliada para um par,
  reusando `strategy/diagnostics.py` (já existente) como base.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com uma posição aberta em paper mode, `python main.py status` mostra caixa livre,
  valor em posições e patrimônio total como três números que somam corretamente
  (patrimônio = caixa + posições), sem exigir cálculo manual pelo operador.
- **SC-002**: `python main.py edge` deixa inequívoco, sem o operador precisar ler o código-fonte,
  que o resultado é uma simulação histórica e não o estado atual do bot.
- **SC-003**: `python main.py painel` funciona (sem erro) tanto com histórico completo quanto com
  histórico vazio/ausente.
- **SC-004**: O modo de diagnóstico identifica corretamente, para um par com sinal `HOLD`, qual
  condição específica está impedindo o `BUY`, verificável comparando contra o motivo já registrado
  em `data/decisions.csv` para o mesmo ciclo.
- **SC-005**: Os gráficos de performance e as marcações de entrada/saída são gerados sem erro a
  partir de um histórico de trades sintético.

## Assumptions

- "Painel local" (User Story 3) é um comando de terminal (mesmo padrão Rich já usado em
  `status`/`multibacktest`), não uma interface web nova — `utils/chart.py` já cobre visualização web
  via Dash/Plotly para o gráfico de candles; um painel textual é suficiente para agregar os dados
  operacionais desta spec.
- "Modo debug da estratégia" (User Story 4) reusa `strategy/diagnostics.py` (`signal_checks`,
  `hold_diagnosis`, já existentes desde antes desta spec) como base, estendendo-o para cobrir os
  novos indicadores de regime/volatilidade adicionados na spec 006, em vez de duplicar essa lógica.
- "Gráficos de performance" (User Story 5) usa a mesma stack já em uso (`plotly`/`dash`, via
  `utils/chart.py`) — não introduz uma biblioteca de gráficos nova.
- PnL não realizado (User Story 1) é calculado ao preço atual de mercado (`fetch_ticker`), mesmo
  padrão já usado em `cmd_status` hoje para mostrar o P&L% de cada posição aberta.
