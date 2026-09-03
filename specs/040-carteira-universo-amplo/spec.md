# Feature Specification: Carteira de H14 sobre universo amplo

**Feature Branch**: `040-carteira-universo-amplo`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: Testar se ampliar o universo de pares do
motor de carteira de H14 (spec 037, 12 pares) reduz o drawdown de
carteira que reprovou H14 — hipótese derivada da observação de que a
estratégia comunitária mais usada do Freqtrade (NostalgiaForInfinity)
opera sobre 40-80 pares simultâneos em vez de um punhado, e da própria
seção 4.15 do registro, que já apontava correlação entre poucos pares
como o mecanismo provável do drawdown de 28,66% (5x o maior isolado por
par) — não coberto pela spec 037 de propósito (FR-007 excluiu
deliberadamente qualquer mudança de universo/correlação para isolar se o
problema era do sinal ou da pilha de risco).

---

## Contexto e tese

**Tese.** O drawdown de carteira de H14 (spec 037) veio de posições
simultâneas correlacionadas — cripto tem correlação mediana de 0,71 entre
pares (H7/H9), e com só 12 pares disponíveis, `MAX_POSITIONS` (5)
concorrentes tende a vir do mesmo grupo de altcoins que sobe e desce
junto. Ampliar o universo de pares candidatos, mantendo o mesmo teto de
posições simultâneas, dá ao modelo mais opções para as 5 posições saírem
de subconjuntos menos correlacionados entre si — **se** esse for de fato
o mecanismo, não um universo pequeno por si só.

**Por que isso não é "achar um sinal melhor".** Diversificação não cria
vantagem onde não há: se o sinal por decisão não tem expectativa positiva
(não é o caso de H14 — `supera_empate_com_confianca` continua `True`,
spec 036), mais pares só tornariam a perda mais previsível, não a
transformariam em lucro. Esta spec testa uma hipótese de **construção de
carteira**, não uma hipótese de sinal — reusa o modelo já treinado e
publicado de H14 sem alteração.

**Por que 34 pares, não 40-80 do Freqtrade.** Medido antes de qualquer
código (`research.md`, D1): usando os limiares de liquidez **já
declarados** do projeto (`MIN_VOLUME_USDT`, `MAX_SPREAD_PCT`,
`market/selector.py`), 39 pares USDT passam o piso de liquidez hoje;
descontando 5 que o filtro de stablecoins existente não pega (USD1,
RLUSD, EUR — moedas pareadas a fiat — e XAUT, PAXG — lastreadas em ouro,
sem o perfil de volatilidade de uma altcoin), sobram **34**. Não é um
número escolhido para bater 40 — é o que a régua de liquidez já usada
pelo projeto devolve, honestamente.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir drawdown de carteira sobre o universo amplo (Priority: P1)

O pesquisador obtém o drawdown agregado de carteira de H14 simulado sobre
34 pares em vez de 12 — mesmo modelo, mesmas barreiras, mesmo mecanismo
de saída, mesmo teto de posições simultâneas — e compara diretamente
contra o resultado já publicado (28,66%, spec 037).

**Why this priority**: é a pergunta da hipótese. Sem o comparativo direto
contra o número já publicado, não há como saber se a mudança ajudou.

**Independent Test**: rodar `simular_carteira` com o universo de 34 pares
sobre um conjunto sintético determinístico e confirmar que nunca há mais
de `MAX_POSITIONS` posições simultâneas, igual ao comportamento já
testado em spec 037.

**Acceptance Scenarios**:

1. **Given** o universo de 34 pares declarado (D1), **When** a carteira é
   simulada com o mesmo `MAX_POSITIONS` de produção, **Then** produz um
   `BacktestResult` único, reusando `_simular_carteira_core` (spec 037)
   sem alteração de mecânica.
2. **Given** o resultado de carteira sobre 34 pares, **When** comparado
   ao resultado já publicado sobre 12 pares, **Then** o relatório mostra
   os dois números lado a lado — nunca um substitui o outro no registro.

---

### Edge Cases

- **Par recém-listado sem 6.000 candles de histórico.** Vários dos 34
  pares (ex.: tokens listados nos últimos meses) não têm ~2,7 anos de
  histórico — tratamento já existente (`AvaliacaoH14` com `status="erro"`
  ou histórico curto, `run_modelo_scan` isola falha por par sem abortar a
  varredura, mesmo princípio de H11/H36).
- **Par com preço abaixo de `MIN_PRICE_USDT`.** Mesmo tratamento já
  existente.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST simular a carteira de H14 sobre o universo
  de 34 pares declarado em `research.md` (D1) — snapshot fixo, não
  recalculado a cada execução (mesma reprodutibilidade de `UNIVERSO_H11`).
- **FR-002**: O sistema MUST reusar `_simular_carteira_core`/
  `simular_carteira` (`backtesting/portfolio_h14.py`, spec 037) sem
  alteração de mecânica — mesmo dimensionamento, mesmo mecanismo de
  saída (D7 de spec 037), mesmo `MAX_POSITIONS`.
- **FR-003**: O sistema MUST manter `MAX_POSITIONS` no valor de produção
  — não aumentar o teto de posições simultâneas junto com o universo, o
  que confundiria "mais opções para escolher" com "mais exposição
  simultânea".
- **FR-004**: O sistema MUST reportar o drawdown agregado do universo
  amplo lado a lado com o já publicado sobre 12 pares (spec 037,
  28,66%) — nunca substituindo o registro anterior.
- **FR-005**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/`.

### Key Entities

- **Universo amplo (34 pares)**: lista fixa declarada em `research.md`
  (D1), medida via `market/selector.py::_filter_tickers` (piso de
  liquidez já existente) menos 5 pares pareados/lastreados que o filtro
  de stablecoins não cobre.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um `BacktestResult` de carteira sobre os 34 pares é
  produzido, com drawdown agregado comparável em unidade e período ao já
  publicado sobre 12 pares.
- **SC-002**: O veredito de `evaluate_approval()` sobre o resultado de 34
  pares é registrado, sem critério novo.
- **SC-003**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Universo**: 34 pares, snapshot de 2026-09-03 (D1, `research.md`) —
  medido com os limiares de liquidez já declarados do projeto, não
  escolhido para bater um número do Freqtrade.
- **MAX_POSITIONS, barreiras, mecanismo de saída, capital inicial**:
  todos já declarados em spec 037 (D1/D7), reusados sem alteração.
- Reprovação, aprovação ou resultado ainda inconclusivo desta spec não
  invalida o veredito já publicado de H14 (spec 037) — é uma pergunta
  diferente (construção de carteira sobre o mesmo sinal), mesmo princípio
  já aplicado a H10/H14 neste registro.
