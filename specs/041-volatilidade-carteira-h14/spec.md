# Feature Specification: Dimensionamento por volatilidade na carteira de H14

**Feature Branch**: `041-volatilidade-carteira-h14`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: Aplicar o dimensionamento por volatilidade
de H12 (`backtesting/volatilidade.py::fator_volatilidade`, já
implementado e declarado desde spec 025) ao motor de carteira de H14
(spec 037/040) — não uma repetição de H12 sobre as 4 estratégias de
regra, que o próprio registro já concluiu não ser testável (nenhuma
delas tem expectativa positiva, §4.13: "H12 não pode ser testada
enquanto nenhuma estratégia tiver expectativa positiva"). H14 é a única
avaliação deste registro com sinal estatisticamente positivo real
(`supera_empate_com_confianca`, spec 036) e foi reprovada duas vezes
especificamente por drawdown (28,66% e 35,08%, spec 037/040) — exatamente
o problema que dimensionamento por volatilidade existe para reduzir.

---

## Contexto e tese

**Por que H12 nunca foi um beco sem saída — só estava no par errado.**
`fator_volatilidade()` (spec 025) reduz o tamanho de uma posição em
proporção à volatilidade do candle de entrada, protegendo uma vantagem
real de trades desproporcionalmente grandes em momentos voláteis. Sobre
uma estratégia sem expectativa positiva, isso só encolhe a perda — sem
criar vantagem, e o registro corretamente concluiu isso como
inconclusiva por causa estrutural, não por defeito do mecanismo. H14 é a
primeira vantagem real disponível para testar o mecanismo como
originalmente concebido.

**Conexão direta com o mecanismo de falha já diagnosticado.** A
atualização de spec 040 (§4.15) já registrou a hipótese de que o
drawdown de carteira de H14 vem de posições correlacionadas quebrando
juntas — e que correlação entre ativos de risco tende a **subir**
durante quedas amplas de mercado, exatamente quando `atr_ratio` também
sobe (volatilidade e correlação de cauda costumam subir juntas). Reduzir
o tamanho de novas entradas quando `atr_ratio` está alto ataca esse
mecanismo diretamente — mesmo sem adicionar uma checagem de correlação
explícita.

**Reuso total, zero critério novo.** `fator_volatilidade(atr_ratio,
params)`, `ALVO_PADRAO=0,02` e `FATOR_MINIMO_PADRAO=0,20` já existem,
já testados, já com o alvo justificado (mediana medida de `atr_ratio`,
não ajustado a um resultado de desempenho — spec 025, D3). Esta spec só
aplica a função já pronta num novo ponto de chamada
(`_simular_carteira_core`, spec 037), como um parâmetro opt-in que
preserva o resultado já publicado byte a byte quando desligado.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir a carteira de H14 com dimensionamento por volatilidade (Priority: P1)

O pesquisador obtém o drawdown agregado de carteira de H14 com o
dimensionamento por volatilidade ligado, comparado diretamente contra o
já publicado sem ele (28,66%, spec 037, sobre os mesmos 12 pares).

**Why this priority**: é a pergunta da hipótese — sem o comparativo
pareado contra o número já publicado, não há como saber se o mecanismo
ajudou, prejudicou, ou foi neutro.

**Independent Test**: rodar `_simular_carteira_core` com
`usar_dimensionamento_vol=True` sobre um conjunto sintético
determinístico com `atr_ratio` variável e confirmar que o tamanho de
cada entrada nunca excede o que seria calculado sem o dimensionamento
(FR-003, o teto é a fórmula).

**Acceptance Scenarios**:

1. **Given** a carteira de H14 sobre `UNIVERSO_H11` (12 pares, mesmo
   universo do resultado já publicado — não o universo amplo de spec
   040, para isolar esta variável), **When**
   `usar_dimensionamento_vol=True`, **Then** cada nova entrada é
   dimensionada por `min(MAX_ORDER_SIZE_USDT, (caixa/slots_livres)*0,95)
   × fator_volatilidade(atr_ratio)` — nunca mais que sem o
   dimensionamento.
2. **Given** o mesmo cenário com `usar_dimensionamento_vol=False`
   (default), **When** a carteira é simulada, **Then** reproduz
   exatamente o resultado já publicado (28,66% de drawdown, spec 037) —
   regressão testada, não assumida.

---

### Edge Cases

- **`atr_ratio` ausente ou inválido no candle de entrada.** `fator_volatilidade`
  já trata isso (devolve 1,0 — mesmo tamanho de sem dimensionamento,
  política de falha do projeto: dado desconhecido nunca vira decisão
  silenciosa diferente do comportamento já vigente).
- **Volatilidade extrema.** `FATOR_MINIMO_PADRAO=0,20` já limita o quanto
  o fator pode encolher a posição — mesmo piso já declarado em spec 025.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST reusar `fator_volatilidade`/
  `ParametrosVolatilidade` (`backtesting/volatilidade.py`) sem
  alteração — mesmo alvo (0,02), mesmo piso (0,20), mesma fórmula.
- **FR-002**: O sistema MUST aplicar o fator **depois** do dimensionamento
  já existente (teto por ordem, reserva de caixa) — nunca antes, mesmo
  princípio já declarado em spec 025 ("compondo com as regras
  existentes em vez de substitui-las").
- **FR-003**: O fator MUST apenas poder reduzir o tamanho de uma entrada,
  nunca ampliá-lo — invariante herdado de `fator_volatilidade` (teto
  1,0), sem novo código de validação.
- **FR-004**: `usar_dimensionamento_vol` MUST ser opt-in
  (`False` por padrão) — o resultado já publicado de spec 037 (28,66% de
  drawdown) MUST continuar reproduzível byte a byte sem essa flag,
  testado por regressão.
- **FR-005**: O sistema MUST usar `UNIVERSO_H11` (12 pares, o mesmo do
  resultado já publicado) — não o universo amplo de spec 040, para
  isolar dimensionamento como a única variável em teste.
- **FR-006**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/`.

### Key Entities

- Nenhuma entidade nova — reusa `PosicaoCarteira`/`CarteiraH14`
  (spec 037) e `ParametrosVolatilidade`/`fator_volatilidade` (spec 025)
  sem alteração de forma.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um `BacktestResult` de carteira com dimensionamento por
  volatilidade é produzido, comparável em unidade e período ao já
  publicado sem ele (28,66% de drawdown, spec 037).
- **SC-002**: O veredito de `evaluate_approval()` sobre o resultado com
  dimensionamento é registrado, sem critério novo.
- **SC-003**: Com a flag desligada (default), o resultado é idêntico
  byte a byte ao já publicado — regressão testada antes de qualquer
  outra alteração.
- **SC-004**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Universo, capital, mecanismo de saída**: `UNIVERSO_H11` (12 pares),
  todos já declarados em spec 037 — reusados sem alteração.
- **Alvo e piso do fator**: 0,02 e 0,20, já declarados e medidos em spec
  025 (D3) — não redeclarados nem remedidos para esta spec.
- Reprovação, aprovação ou resultado ainda inconclusivo desta spec não
  invalida o veredito já publicado de H14 (spec 037/040) — é uma
  pergunta diferente (dimensionamento sobre o mesmo sinal), mesmo
  princípio já aplicado a H10/H14 (specs 037/040) neste registro.
