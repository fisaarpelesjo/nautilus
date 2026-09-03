# Feature Specification: H20 — decompondo o custo de execução (taxa vs. slippage)

**Feature Branch**: `051-h20-decomposicao-custo`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: Spec 050 isolou o custo de execução como
mecanismo dominante da divergência entre o sinal de rótulo confirmado
(spec 048) e o backtest real reprovado (spec 049) — sem taxa nem
slippage, 8/12 pares ficam positivos. A pergunta natural seguinte é se
um método de execução mais barato (`USE_LIMIT_ORDERS`, já existente em
produção, `execution/order_manager.py`) resolveria isso. **Não é
diretamente testável**: `USE_LIMIT_ORDERS` depende de preenchimento
real contra o livro de ofertas, que não existe em histórico —
`REAL_SLIPPAGE_ENABLED` já é forçado `false` em `python main.py
replay` pela mesma razão (não existe order book do passado). O que É
testável, com o instrumento que já existe: decompor o custo já medido
em spec 050 (`fee_rate` e `slippage_pct` juntos, ambos zerados) nos
dois componentes independentes — `simulate_backtest` já aceita os dois
como parâmetros separados. Isola quanto de cada trava vem de taxa
(fixa por corretora, não muda com o tipo de ordem) contra slippage
(reduzido, mas não eliminado, por ordens limit — que na produção real
só se aplicam à ENTRADA, nunca à saída/stop, que precisa de execução
imediata).

---

## Contexto e tese

**O que isto decide, e o que não decide.** Não simula `USE_LIMIT_ORDERS`
literalmente — não há como, sem order book histórico. Decompõe o
número já medido (custo total consumido, spec 050) em duas fatias
independentes, e a partir daí formula, sem medir, o que seria
necessário para uma melhoria de execução resolver o problema: se a
taxa domina, nenhum tipo de ordem ajuda (taxa é da corretora, não do
tipo de ordem); se o slippage domina, há espaço real para melhoria
via execução mais cuidadosa — mas o limite superior otimista
(slippage=0 em toda a operação) ainda superestima o que ordens limit
entregariam de verdade, porque elas só afetam a entrada, nunca a
saída/stop, que continua a mercado por precisar de imediatismo.

**Zero mecânica nova, extensão simétrica do já existente.** O bloco
"E6 — custo de giro" (`backtesting/modelo.py::avaliar_par`) já chama
`_simular_com_sinais` com `fee_rate=0.0, slippage_pct=0.0` para
produzir `retorno_sem_custo_modelo` (spec 049/050). Esta spec adiciona
duas chamadas irmãs, mesma função, um parâmetro zerado de cada vez:
`retorno_sem_slippage_modelo` (`slippage_pct=0.0`, taxa real) e
`retorno_sem_taxa_modelo` (`fee_rate=0.0`, slippage real) — dois novos
campos em `AvaliacaoH14`, mesmo padrão do campo já existente.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Decompor o custo em taxa e slippage, por par (Priority: P1)

O pesquisador obtém, por par, três retornos: com custo real (já
publicado), sem slippage (taxa real), e sem taxa (slippage real) — ao
lado do já publicado sem custo algum (spec 050) — para saber qual
componente domina a divergência.

**Why this priority**: é a pergunta da hipótese — sem a decomposição,
"custo de execução" fica indiferenciado entre um componente
estruturalmente imutável (taxa) e um componente que um método de
execução melhor poderia, em parte, reduzir (slippage).

**Independent Test**: sobre um cenário sintético com trades e slippage/
taxa conhecidos, confirmar que `retorno_sem_slippage_modelo` e
`retorno_sem_taxa_modelo` refletem exatamente zerar um parâmetro de
cada vez, não os dois juntos.

**Acceptance Scenarios**:

1. **Given** a geometria `tp=2,0` já avaliada (specs 048-050), **When**
   `avaliar_par` roda o bloco E6 estendido, **Then** produz três
   variantes de retorno sem custo (nenhum, sem slippage, sem taxa) além
   do já existente com custo total.
2. **Given** os quatro números por par, **When** comparados, **Then**
   o registro declara qual componente domina a recuperação de retorno
   observada em spec 050, com a ressalva explícita de que "sem
   slippage" superestima o que ordens limit entregariam (que só
   afetam entrada, nunca saída).

---

### Edge Cases

- Par sem `a.modelo.convergiu`: os três campos permanecem `None` —
  mesmo tratamento já existente para `retorno_sem_custo_modelo`.
- `slippage_pct=0` e `fee_rate=0` simultaneamente (o caso já existente,
  `retorno_sem_custo_modelo`) continua inalterado — esta spec só
  adiciona, não modifica o campo já publicado.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST calcular `retorno_sem_slippage_modelo`
  (`slippage_pct=0.0`, `fee_rate` real) e `retorno_sem_taxa_modelo`
  (`fee_rate=0.0`, `slippage_pct` real) em `AvaliacaoH14`, mesmo
  padrão de `retorno_sem_custo_modelo` já existente.
- **FR-002**: O sistema MUST NOT alterar `retorno_sem_custo_modelo`
  nem nenhum resultado já publicado — extensão aditiva.
- **FR-003**: O sistema MUST reportar, por par, os três retornos sem
  custo (nenhum removido / sem slippage / sem taxa) ao lado do já
  publicado com custo total (spec 049).
- **FR-004**: O sistema MUST declarar explicitamente, no registro, que
  "sem slippage" é um teto otimista para o que ordens limit
  entregariam — a produção só usa `USE_LIMIT_ORDERS` na entrada, nunca
  na saída/stop, que precisa de execução imediata.
- **FR-005**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/`.

### Key Entities

- `AvaliacaoH14` ganha dois campos `Optional[float]` novos:
  `retorno_sem_slippage_modelo`, `retorno_sem_taxa_modelo`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Os três retornos sem custo (nenhum/sem slippage/sem
  taxa) são reportados por par, sem alterar nenhum número já publicado.
- **SC-002**: O registro declara qual componente (taxa ou slippage)
  domina a recuperação observada em spec 050.
- **SC-003**: A ressalva sobre o teto otimista de "sem slippage" está
  registrada explicitamente, não implícita.
- **SC-004**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Geometria avaliada**: `tp=2,0`, a mesma de specs 048-050 — nenhuma
  escolha nova.
- **`USE_LIMIT_ORDERS` não é simulável** com dados históricos — esta
  spec decompõe custo já medido, não simula ordens limit literalmente.
- Esta spec não decide se vale a pena habilitar `USE_LIMIT_ORDERS` em
  produção para H20 — mede só o teto de melhoria possível via redução
  de slippage, decisão operacional fica para depois, condicionada a
  este resultado.
