# Feature Specification: Reavaliar H10 (pairs trading) com histórico estendido

**Feature Branch**: `039-reavaliar-h10-pairs-trading`

**Created**: 2026-09-02

**Status**: Draft

**Input**: User description: Reavaliar H10 (arbitragem estatística por
cointegração, variante long-only, `backtesting/pairs_trading.py`) com o
histórico estendido de 6.000 candles (spec 036) — a mesma classe de
correção que já mudou o veredito de H14. H10 nunca foi reprovada, ficou
**inconclusiva**: o registro (`docs/research/registro-de-hipoteses.md`
§4.11) já mediu que o seletor de pares tem só 20% de poder de detecção
com a janela de formação de 250 candles usada até aqui, subindo para 60%
em 500 candles, e já declarou explicitamente a reavaliação necessária:
"histórico mais longo que permita formação de 500+ candles com janelas
de teste que comportem ≥ 10 operações". `backtesting/pairs_trading.py`
nunca ganhou um comando CLI.

---

## Contexto e tese

**Por que reabrir, não redesenhar.** H10 já tem toda a tese, os critérios
de seleção (ADF + meia-vida) e os parâmetros de entrada/saída (z-score)
declarados e testados (bateria E1-E6, §4.11). O bloqueio identificado não
é "não há vantagem" — é que o instrumento de medição (seletor com 20% de
poder a 250 candles) não consegue detectar o próprio fenômeno que
tentaria medir, e as janelas de walk-forward tinham candles demais para a
formação e de menos para o teste (0 a 7 operações contra o mínimo de 10).
Esta spec aplica exatamente a correção já declarada — formação de 500
candles sobre os 6.000 já disponíveis (spec 036) — sem mudar critério de
seleção, entrada, saída ou aprovação.

**Precedente direto.** É a mesma classe de correção que já reverteu o
veredito de H14 (INSUFICIENTE → sinal confirmado, spec 036) — amostra
insuficiente lida como ausência de efeito, corrigida com mais histórico,
não com um critério novo.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Rodar H10 com formação de 500 candles sobre 6.000 de histórico (Priority: P1)

O pesquisador obtém um veredito (aprovado/reprovado/inconclusivo) para
H10 a partir de uma janela de treino e uma de validação **out-of-sample**
sobre os 12 pares já usados (`UNIVERSO_H11`), com a janela de formação do
seletor em 500 candles (já medida em 60% de poder de detecção,
§4.11) em vez dos 250 anteriores (20%).

**Why this priority**: é a correção que o próprio registro já declarou
necessária antes de qualquer veredito definitivo — sem ela, H10 permanece
inconclusiva por limitação de instrumento, não por medição completa.

**Independent Test**: rodar a avaliação sobre os 6.000 candles reais e
confirmar que a janela de validação produz `total_trades` suficiente para
`evaluate_approval()` decidir sem cair em "amostra insuficiente" pelo
mesmo motivo já diagnosticado.

**Acceptance Scenarios**:

1. **Given** os 12 pares com 6.000 candles de 4h, **When** a avaliação
   roda com `formacao=500`, **Then** produz um `BacktestResult` de treino
   e um de validação (split 70/30, mesma proporção já usada em
   H14/H17/H11), sem re-treinar a seleção de pares a cada candle
   (`reselecionar_a_cada=formacao`, mesma convenção já existente).
2. **Given** o `BacktestResult` de validação, **When**
   `evaluate_approval()` roda sobre ele, **Then** aplica os mesmos
   limiares já usados em toda avaliação do projeto — sem critério novo.

---

### Edge Cases

- **Par com preço abaixo de `MIN_PRICE_USDT`.** Mesmo tratamento já
  existente (`BacktestResult.below_min_price` → `evaluate_approval`
  devolve "inconclusivo", nunca "reprovado" por omissão).
- **Janela de validação sem candles de formação suficientes antes dela.**
  A validação recebe os `formacao` candles finais do treino como
  aquecimento (mesmo princípio de warmup causal já usado em `preparar()`,
  H14/H11) — nunca começa "fria".

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST usar `formacao=500` e
  `reselecionar_a_cada=500` (`PairsParams`) — já medido e declarado em
  §4.11, não um valor novo escolhido para esta spec.
- **FR-002**: O sistema MUST buscar 6.000 candles de 4h por par (D1, spec
  036) para os 12 pares de `UNIVERSO_H11` — mesmo teto já usado por
  H11/H14/H17/H37.
- **FR-003**: O sistema MUST dividir o histórico em treino (70%) e
  validação (30%) por corte de tempo compartilhado entre os 12 pares —
  nunca por linha independente por par, que desalinharia a seleção de
  pares entre os dois.
- **FR-004**: A janela de validação MUST incluir os `formacao` candles
  finais do treino como aquecimento do seletor, sem contá-los no
  resultado reportado (mesmo princípio de warmup causal já usado no
  projeto).
- **FR-005**: O sistema MUST NOT alterar critério de seleção de pares
  (ADF + meia-vida), z-scores de entrada/saída/stop, ou critério de
  `evaluate_approval()` — só a janela de formação e o histórico
  disponível mudam.
- **FR-006**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/`.

### Key Entities

- **`BacktestResult` de treino/validação** (reusados,
  `backtesting/pairs_trading.py::run_pairs_backtest`, sem alteração):
  produzidos separadamente sobre a fatia de treino e a de validação
  (com aquecimento, FR-004).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A janela de validação produz `total_trades` suficiente
  para `evaluate_approval()` decidir sem "amostra insuficiente" pelo
  mesmo motivo já diagnosticado em §4.11 (0 a 7 operações contra o
  mínimo de 10) — comparado explicitamente contra o valor anterior.
- **SC-002**: Um veredito final (aprovado/reprovado/inconclusivo) é
  registrado para H10, substituindo "inconclusiva, requer reavaliação"
  por um status definitivo ou por uma nova limitação especificamente
  identificada.
- **SC-003**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Formação e universo**: 500 candles, `UNIVERSO_H11` (12 pares), 6.000
  candles de histórico — todos já declarados em §4.11/spec 036, sem
  escolha nova para esta spec.
- **Split treino/validação**: 70/30, mesma proporção de
  `DEFAULT_VALIDATION_RATIO` (`backtesting/validation.py`) já usada em
  toda avaliação do projeto com split.
- Reprovação ou resultado ainda inconclusivo de H10 não invalida nenhuma
  hipótese anterior — é a mesma medição, com o instrumento corrigido.
