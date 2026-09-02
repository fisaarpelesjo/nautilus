---

description: "Task list for profundidade de liquidez proxima ao preco (spec 030)"
---

# Tasks: Profundidade de liquidez próxima ao preço

**Input**: Design documents from `/specs/030-liquidez-proxima-preco/`

**Prerequisites**: plan.md, spec.md, data-model.md, research.md, quickstart.md

**Tests**: obrigatórios — Princípio III da constitution ("Test Before
Implement"), estendendo `tests/test_liquidity.py` já existente. Sem arquivo
novo de teste (mudança é local a uma função já testada).

**Organization**: spec pequena (uma função, ~5 linhas), então US1 e US2 são
implementadas no mesmo tópico do Fluxo Incremental — são duas faces da
**mesma** mudança (bloquear o que deve bloquear, aprovar o que já aprovava).
US3 (P2, critério compartilhado com `estimate_slippage_pct`) é um tópico
separado, porque testa uma propriedade adicional, não a mudança em si.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

**Purpose**: nenhuma — sem dependência nova, sem arquivo novo a criar.
Direto para a implementação (Foundational e Setup colapsam nesta spec).

---

## Phase 2: User Story 1 + User Story 2 - Bloquear profundidade fantasma sem regredir os casos já aprovados (Priority: P1) 🎯 MVP

**Goal**: `depth_usdt` passa a somar só níveis com `preço ≤ best_ask × (1 +
MAX_SPREAD_PCT_ENTRY)` — bloqueia profundidade fantasma distante (US1),
preserva idêntica toda decisão que já era baseada em profundidade perto do
preço (US2).

**Independent Test**: um book sintético com profundidade concentrada perto
do topo continua aprovando; um book com profundidade total suficiente mas
majoritariamente distante do melhor preço passa a recusar.

### Tests for User Story 1 + 2

> **NOTE**: escrever estes testes primeiro, confirmar que
> `test_check_liquidity_blocks_on_phantom_depth_far_from_price` FALHA contra
> o código atual antes de implementar.

- [ ] T001 [P] [US2] Teste de não-regressão em `tests/test_liquidity.py`: book com profundidade concentrada nos primeiros níveis (padrão do `test_check_liquidity_approves_within_limits` já existente, replicado com níveis adicionais próximos ao topo) continua aprovando, com `depth_usdt` igual à soma dos níveis próximos
- [ ] T002 [P] [US1] Teste `test_check_liquidity_blocks_on_phantom_depth_far_from_price` em `tests/test_liquidity.py`: book com profundidade total acima do requisito, mas com a maior parte dos níveis a mais de `MAX_SPREAD_PCT_ENTRY` do melhor ask (replicando a proporção medida para ORCA/USDT em `research.md`: ~90% da soma bruta fora da banda) — `approved is False`, motivo distinto do motivo de spread (ex.: contém "perto do preço", não confundível com `"spread"`)

### Implementation for User Story 1 + 2

- [ ] T003 [US1][US2] Alterar `depth_usdt = sum(price * qty for price, qty in asks)` em `execution/liquidity.py::check_liquidity` para somar só os níveis com `price <= best_ask * (1 + MAX_SPREAD_PCT_ENTRY)` (D1, research.md) (depende de T001, T002)
- [ ] T004 [US1] Atualizar a mensagem de motivo de bloqueio por profundidade em `execution/liquidity.py::check_liquidity` para citar "perto do preço" explicitamente (FR-003), mantendo o valor de `depth_usdt` e `required_depth` já formatados na mensagem

**Checkpoint**: `pytest tests/test_liquidity.py -v` — todos os testes
(pré-existentes + T001 + T002) passam. MVP completo.

---

## Phase 3: User Story 3 - Critério compartilhado com `estimate_slippage_pct` (Priority: P2)

**Goal**: confirmar que `check_liquidity` e `estimate_slippage_pct` nunca
tratam profundidade distante do preço como "grátis" — mesmo princípio (FR-004),
não a mesma função (plan.md, Complexity Tracking: fixam variáveis diferentes,
compartilhar o laço seria abstração prematura para uma soma de uma linha).

**Independent Test**: com o mesmo book sintético, `check_liquidity` só conta
a profundidade perto do preço e `estimate_slippage_pct` reporta slippage alto
(ou preenchimento parcial) para um volume que só cabe usando os níveis
distantes — os dois concordam que aquela liquidez não é imediatamente
alcançável a preço aceitável.

### Tests for User Story 3

- [ ] T005 [US3] Teste `test_check_liquidity_and_slippage_agree_on_reachable_depth` em `tests/test_liquidity.py`: mesmo book sintético de T002 passado a `check_liquidity` (rejeita/`depth_usdt` reflete só a parte perto) e a `estimate_slippage_pct` (para um volume que só cabe usando os níveis distantes, retorna slippage acima de `MAX_SPREAD_PCT_ENTRY` ou preenchimento parcial) — nenhum dos dois trata a profundidade distante como imediatamente utilizável

### Implementation for User Story 3

Nenhuma — a propriedade já é consequência de T003 e do `estimate_slippage_pct`
existente (spec 018, não alterado nesta spec). T005 é só a prova.

**Checkpoint**: as três user stories passam juntas.

---

## Phase 4: Polish & Cross-Cutting Concerns

- [ ] T006 Rodar `pytest tests/test_liquidity.py tests/test_slippage_real.py -v` — confirma 0 regressão nos dois arquivos que tocam o mesmo módulo
- [ ] T007 Validar manualmente o passo 3 do `quickstart.md` contra dados reais (ORCA/USDT, COW/USDT, HEMI/USDT, ROBO/USDT — os quatro pares que `research.md` mediu com divergência a partir de US$ 5.000–10.000), comparando `order_size_usdt=100.0` (sem mudança esperada) contra `order_size_usdt=10000.0` (mudança esperada em pelo menos um dos quatro)
- [ ] T008 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão em `trading/position_lifecycle.py` e `execution/order_manager.py`, que consomem `check_liquidity` sem alteração de assinatura

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: N/A, sem tarefas
- **US1+US2 (Phase 2)**: sem dependência — é o único tópico que altera código
- **US3 (Phase 3)**: depende de T003 (Phase 2) já ter mudado `depth_usdt` — o teste de T005 verifica uma propriedade da implementação de T003, não pode rodar antes
- **Polish (Phase 4)**: depende de Phase 2 e Phase 3 completas

### Parallel Opportunities

- T001 e T002 (testes, mesmo arquivo mas funções independentes sem estado
  compartilhado) em paralelo
- T006 e T007 (verificações independentes) em paralelo

---

## Implementation Strategy

### MVP = Phase 2 (US1+US2)

Um único commit no Fluxo Incremental: T001+T002 (testes falhando) → T003+T004
(implementação, testes passam) → T006 (regressão) → commit → push. É a
mudança inteira — US3 é só a prova de uma propriedade que a mudança já tem.

### Incremental Delivery

1. Phase 2 (US1+US2) → MVP, fecha o gap e não regride
2. Phase 3 (US3) → prova formal de que o critério é consistente com
   `estimate_slippage_pct`
3. Phase 4 (Polish) → validação manual contra rede real + suite completa

Dado o tamanho da mudança (uma função, ~5 linhas), tudo cabe num único
commit/push seguindo o Fluxo Incremental do `CLAUDE.md` — não há tópicos
grandes o bastante para justificar mais de um.
