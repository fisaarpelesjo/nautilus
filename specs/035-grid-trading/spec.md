# Feature Specification: H18 — Grid trading com gestão de cauda

**Feature Branch**: `035-grid-trading`

**Created**: 2026-09-02

**Status**: Draft

**Input**: User description: H18 — grid trading
(`docs/research/registro-de-hipoteses.md` §6.3). Décima oitava hipótese do
registro, e a primeira das quatro de prioridade baixa (H16-H19) a ser
medida de verdade em vez de julgada só por raciocínio — a entrada atual do
registro ("carece de fundamentação preditiva; equivale a venda de
volatilidade sem gestão de cauda") nunca teve uma execução real por trás,
ao contrário de H1-H14/H17/H20.

---

## Contexto e tese

**Tese.** Grid trading não aposta em direção — lucra da oscilação de preço
dentro de uma faixa, comprando em quedas e vendendo em altas dentro dela.
Não precisa prever nada, só que o preço continue oscilando (mercado
"lateral"). É estruturalmente diferente de toda a família já testada (H1-14,
H20: previsão de direção) e de H15 (relativa entre corretoras).

**Por que nunca foi medida.** A objeção registrada — "venda de volatilidade
sem gestão de cauda" — é real e séria: sem controle, um grid mantém posições
abertas durante uma tendência forte contra ele, acumulando prejuízo sem
limite claro. Mas essa objeção descreve um grid **sem** gestão de cauda, não
um grid que a tenha. Este projeto já tem exatamente o instrumento que
faltava: um classificador de regime baseado em ADX
(`strategy/ema_rsi.py::_classify_regime`, já usado para outro propósito) que
distingue mercado lateral de mercado em tendência. Nunca foi combinado com
grid trading — esta spec faz essa combinação e mede.

**O que esta spec adiciona que a objeção original não tinha**: a gestão de
cauda é o próprio regime detector — a grade só opera em regime "sideways" e
**fecha tudo a mercado** assim que o regime muda para "trending". Isso
opera exatamente contra o mecanismo de falha que a objeção original
descreve.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir grid trading com o motor de métricas já existente (Priority: P1)

O pesquisador obtém, por par do universo já estabelecido, o veredito
(aprovado/reprovado/inconclusivo) de uma grade de negociação com gestão de
cauda, usando o mesmo motor de métricas e o mesmo critério de aprovação já
usados por todas as demais avaliações deste projeto.

**Why this priority**: é a pergunta da hipótese, e reusar o motor existente
(`Trade`/`BacktestResult`/`evaluate_approval`/`edge_score`) é o que torna o
resultado comparável a tudo que já foi medido — um critério novo só para
grid seria abrir uma porta que este projeto já fechou deliberadamente
(`compare`, CLAUDE.md: "sem critério de comparação novo").

**Independent Test**: rodar a avaliação sobre um par e obter um
`BacktestResult` válido, com `evaluate_approval()` produzindo um veredito
usando os mesmos limiares já estabelecidos (profit factor, drawdown,
mínimo de trades, buy-and-hold).

**Acceptance Scenarios**:

1. **Given** o histórico de um par do universo, **When** a grade é
   simulada, **Then** cada compra e venda completa num nível vira um
   `Trade`, e o resultado agregado usa `_calculate_advanced_metrics()` já
   existente — nenhuma métrica calculada em duplicata.
2. **Given** o `BacktestResult` produzido, **When** `evaluate_approval()`
   roda sobre ele, **Then** aplica os mesmos limiares já usados por
   `compare`/`scan`/`multibacktest` — sem parâmetro de aprovação novo.

---

### User Story 2 - Gestão de cauda: a grade fecha tudo quando o regime muda (Priority: P1)

A grade só abre em regime "sideways" (ADX abaixo do limiar já
estabelecido) e liquida todas as posições a mercado assim que o regime
muda para "trending" — nunca mantém posição aberta contra uma tendência
que se forma.

**Why this priority**: é a resposta direta à objeção registrada. Sem essa
regra, esta spec mediria exatamente o grid "sem gestão de cauda" que já foi
julgado reprovável por raciocínio — não acrescentaria nada ao registro.

**Independent Test**: forçar uma transição de regime de "sideways" para
"trending" com níveis ocupados, e confirmar que todos são liquidados no
mesmo candle, com motivo explícito.

**Acceptance Scenarios**:

1. **Given** uma grade ativa com posições em um ou mais níveis, **When** o
   regime do candle seguinte é "trending", **Then** todas as posições são
   liquidadas ao preço daquele candle, e a grade fica inativa.
2. **Given** regime "indefinido" (ADX insuficiente/NaN), **When** a grade
   está inativa, **Then** ela não abre — mesmo tratamento conservador já
   usado por `_classify_regime` (dado insuficiente nunca vira aprovação por
   omissão).
3. **Given** a grade inativa após uma liquidação forçada, **When** o
   regime volta a "sideways", **Then** uma nova grade pode abrir, com
   bandas recalculadas no candle atual (não as antigas).

---

### User Story 3 - Custo de execução aplicado a cada transação (Priority: P2)

Cada compra e venda de nível, e cada liquidação forçada, paga a mesma taxa
e slippage já usados pelo motor de backtest.

**Why this priority**: grid trading gera muito mais transações que a
estratégia de regras (um round-trip por nível tocado, não um por sinal de
tendência) — se o custo não for aplicado por transação, o resultado
superestimaria sistematicamente o grid, o mesmo erro que a spec 010
(paridade de custos) já corrigiu para paper mode.

**Independent Test**: comparar o retorno de uma grade com custo zerado
contra o retorno com custo padrão, sobre o mesmo histórico — a diferença
cresce com o número de níveis tocados, não é uma constante.

**Acceptance Scenarios**:

1. **Given** uma grade que completa N round-trips de nível, **When** o
   resultado é calculado, **Then** `BACKTEST_FEE_RATE`/
   `BACKTEST_SLIPPAGE_PCT` são aplicados em cada um dos N, não uma vez só.

---

### Edge Cases

- **Preço ultrapassa a banda superior sem o regime mudar.** O nível de
  venda mais alto é atingido normalmente; a grade continua operando dentro
  do que resta do range — não é gestão de cauda, é o range recalculado no
  próximo ciclo de abertura.
- **Liquidação forçada com múltiplos níveis ocupados no mesmo candle.**
  Todos liquidados ao mesmo preço de fechamento — nenhum tratado
  diferente por causa da ordem em que foram preenchidos.
- **Par com preço abaixo de `MIN_PRICE_USDT`.** Mesmo tratamento
  já existente (`BacktestResult.below_min_price` → `evaluate_approval`
  devolve "inconclusivo", nunca "reprovado").
- **Histórico começa em regime "trending" ou "indefinido".** Grade nunca
  abre até o primeiro candle "sideways" — resultado pode ter zero trades,
  tratado pelo mínimo de trades já existente em `evaluate_approval`.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST usar as Bollinger Bands já calculadas
  (`bb_upper`/`bb_lower`, `strategy/ema_rsi.py`) como limites da grade —
  sem parâmetro de banda novo.
- **FR-002**: A grade MUST abrir só quando o regime do candle (já
  calculado via ADX) for `"sideways"`.
- **FR-003**: A grade MUST liquidar todas as posições abertas a mercado,
  no mesmo candle, assim que o regime mudar para `"trending"` — a gestão
  de cauda desta hipótese, não uma opção configurável.
- **FR-004**: O número de níveis da grade MUST ser declarado antes de
  qualquer medição de desempenho (Fase 0), não ajustado a um resultado.
- **FR-005**: O sistema MUST aplicar `BACKTEST_FEE_RATE`/
  `BACKTEST_SLIPPAGE_PCT` a cada compra e venda de nível, e a cada
  liquidação forçada — mesmo modelo de custo já usado por
  `backtesting/engine.py`.
- **FR-006**: O sistema MUST produzir um `BacktestResult` compatível com o
  motor existente (`Trade`, `_calculate_advanced_metrics`), reusando
  `evaluate_approval`/`edge_score` sem critério de aprovação novo.
- **FR-007**: A avaliação MUST rodar sobre o universo já estabelecido
  (`UNIVERSO_H11`, 12 pares) — sem escolher pares por resultado.
- **FR-008**: Regime `"indefinido"` MUST bloquear a abertura da grade —
  mesmo tratamento conservador já usado pelo classificador de regime
  (dado insuficiente nunca aprova por omissão).
- **FR-009**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/`.

### Key Entities

- **Nível de grade**: preço fixo dentro da banda, com estado (ocupado ou
  vazio) e, se ocupado, o preço de entrada.
- **Episódio de grade**: do candle em que abre (regime vira "sideways")
  até o candle em que fecha (liquidação forçada por "trending", ou fim do
  histórico).
- **`Trade`** (reusado, `backtesting/engine.py`): cada round-trip de nível
  completo, e cada liquidação forçada, vira um `Trade` — sem estrutura
  nova.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cada par do universo produz um veredito
  (aprovado/reprovado/inconclusivo) via `evaluate_approval()`, sem
  critério novo.
- **SC-002**: Toda liquidação forçada por mudança de regime é registrada
  como `Trade` com motivo explícito, distinguível de um fechamento normal
  de nível.
- **SC-003**: O custo de execução está refletido no resultado — visível
  na diferença entre retorno com e sem custo (mesmo padrão de "E6, custo
  de giro" já usado por H13/H14).
- **SC-004**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Número de níveis**: declarado em `research.md` (Fase 0), com
  justificativa independente de desempenho — mesmo padrão de D1-D6 (spec
  029) e das demais decisões de engenharia já registradas nesta sessão.
- **Universo e período**: `UNIVERSO_H11` (12 pares), 2000 candles no
  `TIMEFRAME` de produção — mesmo teto já usado por H14/H17/H20, para não
  escolher amostra favorável.
- **Capital**: dividido igualmente entre os níveis de compra da grade,
  mesmo princípio de "sem escolha por resultado" — proporção declarada
  antes de medir.
- Reprovação ou resultado inconclusivo de H18 não invalida nenhuma
  hipótese anterior — é uma medição nova, independente.
