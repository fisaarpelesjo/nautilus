# Feature Specification: Gate de correlação na carteira de H14

**Feature Branch**: `042-gate-correlacao-carteira-h14`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: Testar o gate de correlação de produção
(`risk/correlation.py::check_correlated_exposure`) na carteira de H14 —
mecanismo real, já em produção, nunca testado nesta linha de
investigação. Terceira variável isolada sobre o drawdown de carteira que
reprovou H14 (spec 037: 28,66%; spec 040, universo amplo: refutado,
35,08%; spec 041, dimensionamento por volatilidade: 23,04%, primeira
melhora real). Motivação declarada desde spec 040: "a produção já tem
exatamente o mecanismo ativo que faltou aqui... bloqueia uma entrada
nova especificamente por já haver posição aberta correlacionada, não por
escassez de opções... testar esse gate seria a hipótese natural
seguinte."

---

## Contexto e tese

**Diferente das duas tentativas anteriores.** Universo amplo (spec 040)
tentou reduzir correlação **indiretamente** (mais opções de pares) e
piorou o resultado. Dimensionamento por volatilidade (spec 041) reduziu
exposição em momentos de alta volatilidade, sem medir correlação
diretamente — e ajudou parcialmente. Esta spec ataca o mecanismo de
frente: bloqueia uma entrada nova especificamente quando ela está
correlacionada com uma posição **já aberta**, o mesmo texto que já
existe em produção para exatamente este propósito.

**Por que não é possível chamar `check_correlated_exposure` direto.**
Essa função busca dados **ao vivo** (`fetch_ohlcv(symbol, timeframe)`
sem argumento de histórico, pegando os candles mais recentes disponíveis
no momento da chamada) — correta para o loop de produção, mas duas
propriedades a tornam incompatível com um backtest sem modificação:

1. **Vazamento de futuro.** Chamada num candle histórico `t` do
   backtest, ela buscaria os candles de HOJE, não os disponíveis em
   `t` — o oposto de point-in-time.
2. **Custo de rede.** Uma chamada de API por par candidato por candle
   tornaria a varredura de milhares de candles inviável.

Esta spec implementa uma função **irmã**, com a mesma semântica e os
mesmos limiares (`MAX_POSITION_CORRELATION`, `CORRELATION_LOOKBACK`) do
`risk/correlation.py`, mas operando sobre os dados já carregados em
memória pela carteira, fatiados até o instante `t` (causal, mesmo
princípio já usado por todo o resto do backtest deste projeto).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir a carteira de H14 com o gate de correlação (Priority: P1)

O pesquisador obtém o drawdown agregado de carteira de H14 com o gate de
correlação ligado — bloqueando uma nova entrada quando correlacionada
(retornos ≥ `MAX_POSITION_CORRELATION` na janela `CORRELATION_LOOKBACK`)
com uma posição já aberta — comparado diretamente contra o já publicado
sem ele (28,66%, spec 037).

**Why this priority**: é a pergunta da hipótese — sem o comparativo
pareado, não há como saber se o mecanismo real de produção, nunca antes
testado nesta linha, ajuda.

**Independent Test**: cenário sintético com dois pares de retornos
quase idênticos (correlação > 0,7) e um terceiro descorrelacionado;
confirmar que uma segunda entrada no par correlacionado é bloqueada
enquanto a primeira está aberta, mas o terceiro par nunca é bloqueado.

**Acceptance Scenarios**:

1. **Given** uma posição já aberta num par, **When** um candidato de
   entrada tem retorno correlacionado (≥ 0,7) com esse par na janela de
   50 candles, **Then** a entrada é bloqueada — o candidato é ignorado
   nesse candle, não substitui a checagem de slots/caixa já existente.
2. **Given** o mesmo cenário, **When** o candidato NÃO está
   correlacionado com nenhuma posição aberta, **Then** a entrada procede
   normalmente, mesma mecânica já existente (slots, caixa,
   dimensionamento).
3. **Given** o `BacktestResult` produzido, **When** comparado ao já
   publicado sem o gate (spec 037), **Then** os números aparecem lado a
   lado — nunca um substitui o outro no registro.

---

### Edge Cases

- **Menos de `CORRELATION_LOOKBACK // 2` candles disponíveis para um dos
  dois pares no instante `t`.** Mesma política de
  `check_correlated_exposure`: não bloqueia por dado insuficiente (falha
  aberta, comparação individual — um par com histórico curto não trava
  a checagem contra os demais).
- **Nenhuma posição aberta no momento da checagem.** Nunca bloqueia —
  não há com o que comparar (mesmo comportamento do `others` vazio na
  função original).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST implementar uma checagem de correlação
  ponto-no-tempo, usando os mesmos limiares já declarados em produção
  (`MAX_POSITION_CORRELATION=0,7`, `CORRELATION_LOOKBACK=50`,
  `config/settings.py`) — sem novo limiar.
- **FR-002**: A checagem MUST usar apenas dados até o instante `t` já
  carregados em memória (`preparados[par]`) — nunca buscar dado novo,
  nunca olhar candle futuro.
- **FR-003**: Uma entrada candidata MUST ser bloqueada quando
  correlacionada (≥ limiar) com **qualquer** posição já aberta no mesmo
  instante — mesma semântica de "qualquer uma basta" já existente em
  `check_correlated_exposure`.
- **FR-004**: Falha por dado insuficiente MUST falhar aberta por
  comparação individual — não bloquear a entrada inteira só porque um
  par específico já aberto tem histórico curto (mesmo princípio já
  declarado para o mecanismo de produção).
- **FR-005**: `usar_gate_correlacao` MUST ser opt-in (`False` por
  padrão) — o resultado já publicado de spec 037 (28,66% de drawdown)
  MUST continuar reproduzível byte a byte sem essa flag, testado por
  regressão.
- **FR-006**: O sistema MUST usar `UNIVERSO_H11` (12 pares, o mesmo do
  resultado já publicado) — mesma disciplina de isolar uma variável por
  vez já usada em spec 040/041.
- **FR-007**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/` — a checagem ponto-no-tempo desta
  spec é código de pesquisa novo, não uma alteração do gate de produção.

### Key Entities

- Nenhuma entidade nova — reusa `PosicaoCarteira`/`CarteiraH14`
  (spec 037) sem alteração de forma. A checagem de correlação é uma
  função pura sobre dados já existentes.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um `BacktestResult` de carteira com o gate de correlação é
  produzido, comparável em unidade e período ao já publicado sem ele
  (28,66% de drawdown, spec 037).
- **SC-002**: O veredito de `evaluate_approval()` sobre o resultado com
  o gate é registrado, sem critério novo.
- **SC-003**: Com a flag desligada (default), o resultado é idêntico
  byte a byte ao já publicado — regressão testada.
- **SC-004**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Limiares de correlação**: `MAX_POSITION_CORRELATION` (0,7) e
  `CORRELATION_LOOKBACK` (50), já declarados e em uso em produção — não
  redeclarados nem remedidos para esta spec.
- **Universo, capital, mecanismo de saída**: `UNIVERSO_H11` (12 pares),
  todos já declarados em spec 037 — reusados sem alteração.
- Reprovação, aprovação ou resultado ainda inconclusivo desta spec não
  invalida o veredito já publicado de H14 — é uma pergunta diferente
  (gate de correlação sobre o mesmo sinal), mesmo princípio já aplicado
  a H10/H14 neste registro.
