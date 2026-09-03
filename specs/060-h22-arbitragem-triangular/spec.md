# Feature Specification: H22 — arbitragem triangular intra-corretora

**Feature Branch**: `060-h22-arbitragem-triangular`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: H15 (arbitragem entre corretoras, spec 029)
mede diferencial entre DUAS corretoras diferentes e o obstáculo
dominante medido é latência de rede entre corretoras — 14 das 15
combinações nunca conseguiram uma leitura simultânea confiável mesmo
após paralelizar a leitura (spec 053). Arbitragem TRIANGULAR mede um
ciclo de TRÊS pernas dentro da MESMA corretora (ex.: `BTC/USDT` →
`ETH/BTC` → `ETH/USDT` → volta a `USDT`) — o obstáculo de latência entre
corretoras não se aplica, porque os três livros de ofertas estão no
mesmo lugar. Testar se isso revela uma vantagem que H15 não conseguiu
nem medir direito.

---

## Contexto e tese

**Por que triangular em vez de mais uma combinação de H15.** O
diagnóstico de H15 (M15, `specs/053-h15-leitura-paralela/`) identificou
que o obstáculo estrutural era a leitura sequencial entre corretoras
diferentes — corrigido com paralelismo, mas a limitação residual (`gate`
consistentemente mais lenta em termos absolutos) persiste porque é uma
característica real da rede entre servidores diferentes. Arbitragem
triangular elimina essa classe de obstáculo por construção: as três
pernas do ciclo estão na mesma corretora, lidas com o mesmo paralelismo
já validado em H15.

**Hipótese declarada antes de medir.** O diferencial bruto de um ciclo
triangular, líquido do custo de três pernas (0,30% — mesma taxa taker
spot em todas as três, verificada nesta sessão), fica **negativo ou
muito próximo de zero** na maioria das observações — mercados líquidos
de grandes exchanges são competidos por bots de arbitragem triangular há
anos, e a ausência de obstáculo de latência entre corretoras não
implica ausência de concorrência. **Não é a hipótese esperada como mais
provável de revelar oportunidade** — é a mais barata de medir depois de
H15/H8 antes de assumir que "sem obstáculo de latência" significa "sem
obstáculo".

**Hipótese alternativa, com igual peso.** A ausência do obstáculo de
latência entre corretoras (o que efetivamente inutilizou 14 das 15
combinações de H15) permite capturar desalinhamentos momentâneos entre
os três livros que existem por frações de segundo — mesmo que raros,
mensuráveis numa campanha de amostragem contínua.

**Zero execução real.** Mede apenas — nenhuma ordem é enviada, nenhuma
permissão de API muda, mesmo padrão de H15 (FR do original, spec 029).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir o diferencial líquido de um ciclo triangular (Priority: P1)

O pesquisador obtém, para um triângulo de moedas na Binance (padrão:
`BTC/USDT` × `ETH/BTC` × `ETH/USDT`), o diferencial bruto e líquido nas
duas direções possíveis do ciclo, qualificado por profundidade e
latência, persistido para acumular amostra entre execuções.

**Why this priority**: é a pergunta central da hipótese.

**Independent Test**: `medir_triangulo` sobre livros sintéticos
balanceados produz diferencial bruto ≈ 0 (estado `sem_oportunidade`
após custo); sobre livros artificialmente desbalanceados produz
diferencial positivo (estado `oportunidade`) — sem rede.

**Acceptance Scenarios**:

1. **Given** os três livros de ofertas do triângulo lidos com sucesso,
   **When** `medir_triangulo` roda, **Then** devolve os dois ciclos
   possíveis (direto e inverso), cada um com diferencial bruto, custo de
   3 pernas, diferencial líquido, profundidade suficiente e estado.
2. **Given** qualquer uma das três pernas indisponível, **When**
   medido, **Then** o ciclo inteiro é abortado (sem medição parcial) —
   diferente de H15, onde cada combinação de duas corretoras é
   independente.
3. **Given** o histórico acumulado, **When** agregado, **Then** reporta
   quantas observações existem por (triângulo, direção) e se a amostra
   é suficiente nas DUAS direções — nunca um veredito de
   aprovação/reprovação (mesmo princípio de H15).

---

### Edge Cases

- **Profundidade insuficiente numa perna intermediária** (ex.: `ETH/BTC`
  raso): a perna seguinte do ciclo nunca recebe mais do que a anterior
  realmente entregou — nunca extrapola além da profundidade real.
- **As duas direções do mesmo ciclo têm coberturas de amostra
  diferentes**: `estado_agregado` exige o mínimo na direção MENOS
  coberta, não na mais coberta (diferente de H15, que tem 15
  combinações independentes — aqui as duas direções sempre nascem
  juntas no mesmo ciclo).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST ler os três livros de ofertas do triângulo
  em paralelo (mesmo padrão de `ThreadPoolExecutor` de H15/spec 053).
- **FR-002**: O sistema MUST calcular as duas direções possíveis do
  ciclo (direto e inverso), caminhando a profundidade real de cada
  perna — nunca assumindo preenchimento total sem checar.
- **FR-003**: O sistema MUST usar a taxa taker spot real (0,10%,
  verificada nesta sessão) para as três pernas — custo total 0,30%.
- **FR-004**: O sistema MUST classificar cada ciclo em
  `profundidade_insuficiente` / `latencia_alta` / `oportunidade` /
  `sem_oportunidade`, nessa ordem de precedência.
- **FR-005**: O sistema MUST persistir cada ciclo medido (JSONL, por
  acréscimo) para acumular amostra entre execuções.
- **FR-006**: O sistema MUST NOT enviar ordem real nem exigir chave de
  API — só consulta pública de livro de ofertas.
- **FR-007**: O sistema MUST NOT produzir veredito de
  aprovação/reprovação — só estado descritivo de cobertura de amostra
  (mesmo princípio de H15, FR-010 original).
- **FR-008**: O sistema MUST declarar explicitamente por que é
  inexecutável em produção hoje (sem garantia de atomicidade entre a
  leitura do livro e a execução das três pernas).

### Key Entities

- **CicloTriangular**: triângulo, direção, volume, volume final,
  diferencial bruto, custo, diferencial líquido, profundidade
  suficiente, estado, intervalo de latência.
- **RelatorioH22**: ciclo atual, observações totais, observações por
  (triângulo, direção), estado agregado, executabilidade.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `python main.py triangular [INTERMEDIARIA] [BASE] [COTACAO]`
  mede um ciclo real e imprime as duas direções.
- **SC-002**: Uma campanha real (≥ 30 observações por direção) é
  registrada no repositório de pesquisa — instrumento de amostragem,
  não veredito único.
- **SC-003**: Nenhuma ordem real é enviada; nenhuma permissão de API
  muda; produção permanece idêntica.

---

## Assumptions

- **Triângulo padrão**: `BTC/USDT` × `ETH/BTC` × `ETH/USDT` — o par mais
  líquido e mais citado na literatura de arbitragem triangular em
  cripto, não escolhido por resultado prévio.
- **Volume de referência**: US$ 10.000 por ciclo, mesmo valor de H15,
  para comparabilidade entre as duas hipóteses de arbitragem deste
  registro.
- **Teto de latência**: reusa os 2.000ms de H15 por comparabilidade,
  mesmo sendo conservador para leitura intra-corretora (a latência real
  medida em smoke test local ficou em ~800ms, bem abaixo do teto).
- Resultado negativo (sem oportunidade líquida) não é falha do
  instrumento — é o resultado mais provável declarado antes de medir.
