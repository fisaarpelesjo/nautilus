# Feature Specification: Métricas de Risco Avançadas

**Feature Branch**: `004-advanced-risk-metrics`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Métricas de risco avançadas: medir qualidade do retorno, não apenas
retorno bruto. Escopo (ver `specs/BACKLOG.md` item 004, derivado do `ROADMAP.md` Fase 3): Sortino
Ratio e Calmar Ratio no relatório de backtest (hoje só tem Sharpe simplificado); retorno anualizado e
retorno por tempo exposto (a exposição já é calculada, falta anualizar); análise automática de
`data/decisions.csv` — resumir sinais, decisões finais, bloqueios e quais filtros mais impedem
entrada, já que hoje esse arquivo só é gravado, nunca lido de volta por nenhum comando."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Avaliar risco ajustado ao downside, não só volatilidade geral (Priority: P1)

Como operador do bot, eu quero ver o Sortino Ratio e o Calmar Ratio no relatório de backtest junto do
Sharpe já existente, para avaliar o retorno considerando especificamente quedas e o pior rebaixamento
sofrido, não uma medida de volatilidade que penaliza alta e queda igualmente.

**Why this priority**: É a métrica mais direta desta spec — uma extensão pura sobre o relatório de
backtest já existente (`backtesting/engine.py`), sem depender de nenhuma das outras duas capacidades.
Sharpe já é calculado hoje; Sortino e Calmar completam a visão sem exigir nova infraestrutura.

**Independent Test**: Pode ser testado isoladamente rodando qualquer backtest existente
(`python main.py backtest`) e conferindo que o relatório mostra Sortino e Calmar ao lado do Sharpe já
existente, com valores calculados a partir dos mesmos trades do backtest.

**Acceptance Scenarios**:

1. **Given** um backtest com trades de retornos mistos (positivos e negativos), **When** o relatório é
   gerado, **Then** o Sortino Ratio exibido usa só a volatilidade dos retornos negativos no
   denominador, não a volatilidade geral já usada pelo Sharpe.
2. **Given** o mesmo backtest, **When** o relatório é gerado, **Then** o Calmar Ratio exibido é o
   retorno anualizado dividido pelo drawdown máximo já calculado, não um novo cálculo de drawdown
   paralelo.
3. **Given** um backtest sem nenhum trade com prejuízo, **When** o Sortino é calculado, **Then** o
   relatório mostra um valor alto/infinito de forma explícita, não um erro de divisão por zero.

---

### User Story 2 - Julgar o retorno pela eficiência do capital exposto, não só o retorno bruto (Priority: P2)

Como operador do bot, eu quero ver o retorno anualizado e o retorno por tempo exposto ao lado da
exposição já calculada, para comparar de forma justa uma estratégia que fica pouco tempo comprada
contra buy-and-hold (que fica exposto o período inteiro).

**Why this priority**: Depende conceitualmente da mesma base de métricas da User Story 1 (extensão do
relatório de backtest), mas é uma dimensão de análise diferente (tempo/eficiência, não risco de
downside) — por isso vem em seguida, não junto.

**Independent Test**: Pode ser testado isoladamente rodando um backtest existente e conferindo que o
relatório mostra retorno anualizado e retorno por tempo exposto, calculados a partir do período e da
exposição (`exposure_pct`) já existentes.

**Acceptance Scenarios**:

1. **Given** um backtest sobre um período conhecido (ex: 1 ano de candles), **When** o relatório é
   gerado, **Then** o retorno anualizado exibido é consistente com o retorno total e a duração real do
   período testado.
2. **Given** uma estratégia que fica exposta só uma fração pequena do tempo total (baixo
   `exposure_pct`), **When** o retorno por tempo exposto é calculado, **Then** ele reflete a
   eficiência do capital enquanto exposto, não é diluído pelo tempo fora do mercado.
3. **Given** um backtest sem nenhum trade (exposição zero), **When** o retorno por tempo exposto é
   calculado, **Then** o relatório indica que a métrica não se aplica, em vez de um erro de divisão
   por zero.

---

### User Story 3 - Entender por que o bot não está entrando, sem vasculhar CSV manualmente (Priority: P3)

Como operador do bot, eu quero um resumo dos ciclos registrados em `data/decisions.csv` — quantos
sinais de cada tipo, quais bloqueios mais aparecem, indicadores médios por decisão — para diagnosticar
se o bot está parado por excesso de filtro, entrando em contexto ruim, ou bloqueando bons sinais por
uma regra específica, sem abrir a planilha manualmente.

**Why this priority**: É a capacidade mais independente das três (não estende o relatório de backtest,
opera sobre um arquivo de log operacional diferente) e depende de o bot já ter rodado por um tempo
para gerar dados reais — por isso vem por último.

**Independent Test**: Pode ser testado isoladamente rodando o novo comando de análise sobre um
`data/decisions.csv` de exemplo (real ou sintético) e conferindo que o resumo mostra contagem de
sinais, bloqueios mais frequentes e não quebra com um arquivo vazio ou inexistente.

**Acceptance Scenarios**:

1. **Given** um `data/decisions.csv` com histórico de ciclos, **When** o comando de análise roda,
   **Then** o resumo mostra quantos ciclos resultaram em cada sinal (BUY/SELL/HOLD) e quantos tiveram
   entrada efetivamente bloqueada.
2. **Given** o mesmo arquivo, **When** o resumo é calculado, **Then** os bloqueios (`blockers`) mais
   frequentes aparecem ranqueados, não uma lista não ordenada.
3. **Given** `data/decisions.csv` não existe ainda (bot nunca rodou), **When** o comando de análise
   roda, **Then** o sistema informa que não há dados para analisar, em vez de falhar com um erro não
   tratado.

---

### Edge Cases

- O que acontece quando um backtest não tem nenhum trade com prejuízo (User Story 1)? → Sortino
  exibido como valor alto/infinito explícito, mesma convenção já usada pelo profit factor existente
  quando não há perdas.
- O que acontece quando o drawdown máximo é zero (User Story 1, Calmar)? → Mesma convenção — valor
  alto/infinito explícito, não erro de divisão por zero.
- O que acontece quando a exposição é zero (User Story 2)? → Retorno por tempo exposto marcado como
  não aplicável, não um erro.
- O que acontece quando `data/decisions.csv` está vazio ou não existe (User Story 3)? → Mensagem clara
  de "sem dados para analisar", sem stack trace.
- O que acontece se `data/decisions.csv` tiver linhas de um schema antigo (colunas faltando de uma
  versão anterior do arquivo)? → Colunas ausentes tratadas como dado desconhecido nessa linha, sem
  interromper a análise das demais linhas.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST calcular e exibir o Sortino Ratio no relatório de backtest, usando só a
  volatilidade dos retornos negativos no denominador.
- **FR-002**: O sistema MUST calcular e exibir o Calmar Ratio no relatório de backtest, como retorno
  anualizado dividido pelo drawdown máximo já calculado.
- **FR-003**: O sistema MUST exibir um valor alto/infinito explícito (não um erro) quando o
  denominador de Sortino ou Calmar for zero (sem perdas, ou sem drawdown).
- **FR-004**: O sistema MUST calcular e exibir o retorno anualizado do backtest, derivado do retorno
  total e da duração real do período testado.
- **FR-005**: O sistema MUST calcular e exibir o retorno por tempo exposto, derivado do retorno total
  e da exposição (`exposure_pct`) já calculada.
- **FR-006**: O sistema MUST indicar que o retorno por tempo exposto não se aplica quando a exposição
  for zero, em vez de calcular uma divisão por zero.
- **FR-007**: O sistema MUST oferecer um comando que resuma `data/decisions.csv`: contagem de sinais
  por tipo, contagem de entradas bloqueadas, e os bloqueios mais frequentes ranqueados.
- **FR-008**: O sistema MUST informar claramente quando `data/decisions.csv` não existir ou estiver
  vazio, em vez de falhar com um erro não tratado.
- **FR-009**: O sistema MUST continuar funcionando com linhas de `data/decisions.csv` que tenham
  colunas ausentes (schema antigo), sem interromper a análise das demais linhas.
- **FR-010**: O sistema MUST manter compatibilidade com o comportamento atual dos comandos de backtest
  existentes — as métricas novas são exibidas a mais, não substituem nem alteram as já existentes.
- **FR-011**: O sistema MUST continuar operando apenas com acesso público de dados da Binance para as
  User Stories 1 e 2 (sem exigir credenciais); a User Story 3 opera só sobre um arquivo local, sem
  rede.

### Key Entities

- **Métricas de risco ajustado** (extensão do resultado de backtest já existente): Sortino Ratio,
  Calmar Ratio, retorno anualizado, retorno por tempo exposto — todas derivadas de dados já calculados
  pelo motor de backtest (trades, drawdown, exposição), sem introduzir uma nova fonte de dado.
- **Resumo de decisões**: agregação sobre `data/decisions.csv` — contagem de sinais por tipo, taxa de
  bloqueio, ranking de bloqueios mais frequentes, indicadores médios por tipo de decisão.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Rodando qualquer backtest existente, o operador vê Sortino, Calmar, retorno anualizado e
  retorno por tempo exposto no mesmo relatório, sem rodar comando adicional nem calcular manualmente.
- **SC-002**: Nenhuma das quatro métricas novas produz erro de divisão por zero em nenhum cenário de
  backtest testável (sem perdas, sem drawdown, sem exposição) — todas mostram um valor explícito
  nesses casos.
- **SC-003**: Rodando o novo comando de análise sobre um `data/decisions.csv` real ou sintético, o
  operador identifica o bloqueio mais frequente sem abrir o arquivo manualmente.
- **SC-004**: O comando de análise nunca falha com erro não tratado, mesmo com o arquivo ausente,
  vazio, ou com linhas de schema antigo.
- **SC-005**: Nenhuma das mudanças acima quebra o comportamento hoje coberto pela suíte de testes
  existente nem exige credenciais além do acesso público de dados da Binance (User Stories 1/2).

## Assumptions

- Sortino/Calmar/retorno anualizado/retorno por tempo exposto são adicionados ao mesmo
  `BacktestResult`/relatório já existente em `backtesting/engine.py` (mesmo padrão de extensão já
  usado nas specs 002/003), não um relatório separado.
- "Retorno anualizado" assume 365 dias/ano como base de anualização (convenção comum para cripto, que
  opera 24/7, diferente de mercados tradicionais com calendário de pregão) — decisão final documentada
  na fase de planejamento.
- A User Story 3 (análise de `decisions.csv`) é construída e testada com fixtures sintéticas nesta
  sessão de trabalho, já que este ambiente de desenvolvimento não tem um `data/decisions.csv` real
  (o bot nunca rodou continuamente aqui) — a validação com histórico operacional real fica pendente do
  operador rodar `python main.py bot` por um período e então o novo comando de análise.
- Novo comando de CLI para a User Story 3 (não uma flag de comando existente, já que opera sobre um
  arquivo diferente de qualquer backtest) — nome exato decidido na fase de planejamento.
