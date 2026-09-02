---

description: "Task list for H15 -- arbitragem entre corretoras (spec 029)"
---

# Tasks: H15 — Arbitragem entre corretoras

**Input**: Design documents from `/specs/029-arbitragem-entre-corretoras/`

**Prerequisites**: plan.md, spec.md, data-model.md, contracts/cli-arbitragem.md, research.md, quickstart.md

**Tests**: obrigatórios, não opcionais — Princípio III da constitution ("Test
Before Implement") exige critério de teste definido antes de cada task de
implementação, estendendo a suite `pytest` existente em `tests/`. Um único
arquivo `tests/test_arbitragem.py` cresce ao longo das fases, mesmo padrão de
`tests/test_geometria.py`/`tests/test_modelo.py`.

**Organization**: tarefas agrupadas por user story de `spec.md` (US1–US4).
Cada fase de user story é um tópico do Fluxo Incremental do `CLAUDE.md`:
implementar → testar → commit → push → próxima fase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: paralelizável (arquivos diferentes, sem dependência de task incompleta)
- **[Story]**: US1/US2/US3/US4, conforme `spec.md`
- Caminho de arquivo exato em cada descrição

---

## Phase 1: Setup

**Purpose**: constantes e esqueleto de módulo, sem lógica ainda

- [X] T001 [P] Adicionar `ARBITRAGEM_FILE = "data/arbitragem.jsonl"` em `data/paths.py`
- [X] T002 [P] Criar `backtesting/arbitragem.py` com as constantes declaradas: `TAXA_TOMADOR` (dict corretora→taxa, D3: binance/bybit/kucoin 0.100%, okx 0.150%, gate 0.200%, kraken 0.400%), `CORRETORAS = ("binance", "bybit", "okx", "kucoin", "gate", "kraken")` (D1), `VOLUME_USDT_PADRAO = 10_000.0` (D2), `TETO_LATENCIA_MS = 2000` (D4)

**Checkpoint**: constantes existem e são importáveis; nenhuma função ainda.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: primitivas de aquisição de dados (leitura de livro normalizada)
que **todas** as user stories consomem. Nenhuma lógica de comparação, estado
ou CLI ainda — isso pertence às fases seguintes.

**⚠️ CRITICAL**: nenhuma user story começa antes desta fase.

- [X] T003 [P] Teste `normalizar_niveis()` com livro de 2 campos (preço, qtd) e de 3 campos (preço, qtd, instante — formato kraken/okx, achado de research.md D1) em `tests/test_arbitragem.py`
- [X] T004 Implementar `normalizar_niveis(raw: list) -> list[tuple[float, float]]` em `backtesting/arbitragem.py` (depende de T003 falhando antes)
- [X] T005 [P] Teste `LeituraLivro` (dataclass) e `ler_livro()`: sucesso com book mockado, falha de rede vira `LeituraLivro(erro=...)` sem levantar exceção, instância ccxt criada **sem** `apiKey`/`secret` (FR-013) em `tests/test_arbitragem.py`
- [X] T006 Implementar `LeituraLivro` (dataclass, campos de `data-model.md`) e `ler_livro(corretora: str, par: str) -> LeituraLivro` em `backtesting/arbitragem.py` — cache de instância ccxt pública por `corretora` (mesmo espírito de `data/fetcher.py::get_exchange`, mas por id de corretora, nunca autenticada); `instante` via `time.monotonic()`, nunca timestamp da corretora (edge case "relógios dessincronizados") (depende de T005, T004)

**Checkpoint**: `ler_livro("binance", "BTC/USDT")` retorna uma `LeituraLivro` normalizada ou com `erro` preenchido, nunca levanta exceção para o chamador.

---

## Phase 3: User Story 1 - Medir o diferencial líquido, não o aparente (Priority: P1)

**Goal**: dado duas leituras de livro, calcular diferencial bruto, custo dos
dois lados, diferencial líquido e o volume ao qual ele se aplica —
FR-001, FR-002, FR-006, FR-007.

**Independent Test**: `python main.py arbitragem` roda e imprime, para cada
combinação de corretoras disponível, diferencial bruto/custo/líquido/volume
preenchido.

### Tests for User Story 1

- [X] T007 [P] [US1] Teste `preco_medio_execucao()`: livro com profundidade suficiente (preço médio ≈ topo), livro raso que não preenche o volume pretendido (`volume_preenchido < volume_usdt`), livro vazio em `tests/test_arbitragem.py`
- [X] T008 [P] [US1] Teste `comparar()`: diferencial bruto/custo/líquido corretos com dois `TAXA_TOMADOR` conhecidos; estado `custo_desconhecido` quando uma corretora não está em `TAXA_TOMADOR` (**nunca** custo virando zero — FR-006); estado `profundidade_insuficiente` quando `volume_preenchido < volume_usdt` em qualquer perna, com o diferencial ainda calculado (degradado, não descartado — FR-007) em `tests/test_arbitragem.py`
- [X] T009 [P] [US1] Teste da **ordem dos estados**: um caso construído para disparar `custo_desconhecido` e `profundidade_insuficiente` simultaneamente MUST resultar em `custo_desconhecido` (checagem 1 precede checagem 2, `data-model.md`) em `tests/test_arbitragem.py`

### Implementation for User Story 1

- [X] T010 [US1] Implementar `preco_medio_execucao(niveis: list[tuple[float, float]], volume_usdt: float) -> tuple[float, float]` em `backtesting/arbitragem.py` (caminha os níveis a partir do melhor preço; depende de T007)
- [X] T011 [US1] Implementar `Comparacao` (dataclass completo de `data-model.md`, incluindo campos que as próximas fases ainda não preenchem: `intervalo_ms` default `0.0`) em `backtesting/arbitragem.py`
- [X] T012 [US1] Implementar `comparar(leitura_a: LeituraLivro, leitura_b: LeituraLivro, volume_usdt: float) -> Comparacao` com estados `custo_desconhecido` → `profundidade_insuficiente` → `oportunidade`/`sem_oportunidade` (ordem de `data-model.md`, sem `latencia_alta` ainda — US3) em `backtesting/arbitragem.py` (depende de T008, T009, T010, T011)
- [X] T013 [US1] Implementar `medir_ciclo(par: str, volume_usdt: float = VOLUME_USDT_PADRAO) -> tuple[list[Comparacao], list[str]]`: chama `ler_livro` para cada corretora em `CORRETORAS`, monta `Comparacao` para cada combinação C(6,2) cujas duas leituras tiveram sucesso, retorna também a lista de corretoras com `erro` (FR-011 — falha isolada não aborta o ciclo) em `backtesting/arbitragem.py`
- [X] T014 [US1] Criar `cmd_arbitragem()` em `main.py`: chama `medir_ciclo`, imprime tabela (corretora compra/venda, bruto, custo, líquido, volume preenchido, estado) e a lista de corretoras indisponíveis; registrar `"arbitragem": cmd_arbitragem` em `COMMANDS`
- [X] T015 [US1] Validar manualmente o passo 1 do `quickstart.md` (`python main.py arbitragem`) contra a rede real

**Checkpoint**: US1 completa e testável isoladamente — `python main.py
arbitragem` produz a tabela do ciclo com diferencial líquido correto.

---

## Phase 4: User Story 2 - Não comparar moedas de cotação diferentes (Priority: P1)

**Goal**: nenhuma `Comparacao` é criada entre pares de cotação diferente —
FR-003.

**Independent Test**: chamar a função de pareamento diretamente com duas
`LeituraLivro` de cotações diferentes (`BTC/USDT` vs `BTC/USD`) e confirmar
recusa com motivo, sem depender de rede.

### Tests for User Story 2

- [X] T016 [P] [US2] Teste `mesma_cotacao()` (ou equivalente): `BTC/USDT` vs `BTC/USDT` → compatível; `BTC/USDT` vs `BTC/USD` → incompatível, com motivo explícito em `tests/test_arbitragem.py`
- [X] T017 [P] [US2] Teste `medir_ciclo()` com leituras de cotações mistas (mock): a combinação incompatível não aparece em `comparacoes`, aparece em `pares_recusados` com motivo — nunca silenciosamente incluída (FR-003, Acceptance Scenario 1) em `tests/test_arbitragem.py`

### Implementation for User Story 2

- [X] T018 [US2] Implementar checagem de cotação (extrai `par.split("/")[1]` de cada `LeituraLivro`; recusa se diferente) em `backtesting/arbitragem.py` (depende de T016)
- [X] T019 [US2] Integrar a checagem em `medir_ciclo()`: aplicá-la antes de chamar `comparar()`; adicionar `pares_recusados: list[tuple[str, str, str]]` (corretora_a, corretora_b, motivo) ao retorno em `backtesting/arbitragem.py` (depende de T017, T018) — **ajusta a assinatura de `medir_ciclo` introduzida em T013**
- [X] T020 [US2] Atualizar `cmd_arbitragem()` em `main.py` para exibir "quais moedas de cotação participaram" e os pares recusados, quando houver (FR-003, Acceptance Scenario 2)

**Checkpoint**: US1 + US2 funcionam juntas — nenhuma comparação mistura cotação, e isso é visível na saída.

---

## Phase 5: User Story 3 - Tratar latência como obstáculo de primeira ordem (Priority: P1)

**Goal**: toda `Comparacao` reporta o intervalo entre suas duas leituras;
intervalo acima do teto vira estado próprio — FR-004, FR-005.

**Independent Test**: construir duas `LeituraLivro` com `instante` separados
por mais de `TETO_LATENCIA_MS` e confirmar que `comparar()` retorna estado
`latencia_alta`, não `oportunidade`/`sem_oportunidade`.

### Tests for User Story 3

- [X] T021 [P] [US3] Teste `comparar()` calcula `intervalo_ms = abs(instante_b - instante_a) * 1000` corretamente em `tests/test_arbitragem.py`
- [X] T022 [P] [US3] Teste de estado `latencia_alta`: intervalo acima de `TETO_LATENCIA_MS` produz esse estado mesmo quando o diferencial líquido seria positivo (a checagem de latência precede a classificação de oportunidade, `data-model.md`) em `tests/test_arbitragem.py`

### Implementation for User Story 3

- [X] T023 [US3] Estender `comparar()` em `backtesting/arbitragem.py`: calcular `intervalo_ms`; inserir a checagem `latencia_alta` entre `profundidade_insuficiente` e `oportunidade`/`sem_oportunidade` (ordem de `data-model.md`) (depende de T021, T022) — **modifica a função de T012**
- [X] T024 [US3] Atualizar `cmd_arbitragem()` em `main.py` para exibir a coluna `intervalo_ms` na tabela do ciclo (FR-004)

**Checkpoint**: US1 + US2 + US3 — toda linha da tabela mostra o intervalo, e um intervalo alto nunca aparece como oportunidade.

---

## Phase 6: User Story 4 - Acumular amostra ao longo do tempo (Priority: P2)

**Goal**: cada execução persiste suas observações; o relatório agrega **todo**
o histórico, não só o ciclo atual — FR-008, FR-009, FR-010, FR-015.

**Independent Test**: duas execuções sucessivas de `python main.py
arbitragem` produzem um `data/arbitragem.jsonl` com mais linhas após a
segunda, e o relatório da segunda execução declara período coberto e N maior
que o de uma execução isolada.

### Tests for User Story 4

- [X] T025 [P] [US4] Teste `data/arbitragem_store.py::registrar_observacoes()`: acrescenta linhas sem sobrescrever as existentes (modo `a`) em `tests/test_arbitragem.py`
- [X] T026 [P] [US4] Teste `data/arbitragem_store.py::carregar_observacoes()`: lê múltiplas linhas válidas; uma última linha corrompida/parcial é descartada sem abortar a leitura das demais (D5, cenário de execução interrompida) em `tests/test_arbitragem.py`
- [X] T027 [P] [US4] Teste `agregar()`: `periodo_coberto` = (primeira, última) observação de todo o histórico; `n_observacoes_total` e `n_observacoes_por_combinacao` corretos; `estado_agregado == "inconclusivo"` abaixo de `MIN_OBSERVACOES_AGREGACAO` (30) por combinação, `"amostra_suficiente"` quando a combinação mais medida atinge o mínimo — **nunca** `"reprovado"`/`"aprovado"` (FR-010, campo não existe em `RelatorioH15`) em `tests/test_arbitragem.py`

### Implementation for User Story 4

- [X] T028 [US4] Implementar `registrar_observacoes(comparacoes: list[Comparacao]) -> None` e `carregar_observacoes() -> list[dict]` em `data/arbitragem_store.py`, usando `ARBITRAGEM_FILE` de `data/paths.py` (depende de T025, T026)
- [X] T029 [US4] Implementar `MIN_OBSERVACOES_AGREGACAO = 30` e `agregar(observacoes: list[dict]) -> RelatorioH15` (incluindo `RelatorioH15` dataclass de `data-model.md`, com `executavel_em_producao=False` e o motivo de D6 sempre presente) em `backtesting/arbitragem.py` (depende de T027, T028)
- [X] T030 [US4] Integrar em `medir_ciclo()`: chamar `registrar_observacoes()` ao final do ciclo, com as `Comparacao` geradas (não os pares recusados) em `backtesting/arbitragem.py`
- [X] T031 [US4] Atualizar `cmd_arbitragem()` em `main.py`: chamar `carregar_observacoes()` + `agregar()` após o ciclo, imprimir seção "Agregado histórico" (período, N total, N por combinação, `estado_agregado`, quanto falta se `inconclusivo`) e seção "Executabilidade (D6)" sempre, e exportar via `export_report("arbitragem", ...)` (ciclo + agregado) — mesmo padrão de `barras`/`modelo`
- [X] T032 [US4] Validar manualmente os passos 2–4 do `quickstart.md` (persistência por acréscimo, agregado histórico, corretora indisponível não aborta)

**Checkpoint**: todas as 4 user stories funcionam juntas — o comando mede, classifica, persiste e agrega.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: garantias estruturais que não pertencem a nenhuma story
individual (FR-012, FR-013, FR-014) e sincronização de documentação.

- [X] T033 [P] Teste de guarda: `backtesting/arbitragem.py` e `data/arbitragem_store.py` **nunca** referenciam `create_order`/`createOrder` (FR-012) — grep/AST, mesmo espírito da guarda AST de `tests/test_geometria.py` contra `import modelo`, em `tests/test_arbitragem.py`
- [X] T034 [P] Teste de guarda: `ler_livro()` nunca passa `apiKey`/`secret` ao instanciar uma corretora ccxt (FR-013) em `tests/test_arbitragem.py`
- [X] T035 Atualizar a seção "Comandos" de `CLAUDE.md` **e** `AGENTS.md` no mesmo commit, adicionando `python main.py arbitragem [PAR]` — sincronização exigida pela constitution (Development Workflow)
- [X] T036 Rodar `pytest tests/test_arbitragem.py -v` completo e o passo 5–6 do `quickstart.md`
- [X] T037 Rodar a suite completa (`pytest`) para confirmar ausência de regressão em módulos existentes (`data/paths.py` ganhou uma constante nova; `main.py` ganhou um comando novo)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências
- **Foundational (Phase 2)**: depende de Setup — bloqueia todas as user stories
- **US1 (Phase 3)**: depende de Foundational; é a única com dependência real de infraestrutura (usa `ler_livro`/`normalizar_niveis`)
- **US2 (Phase 4)**: depende de US1 (`medir_ciclo`/`Comparacao` já existem) — a checagem de cotação em si (T016, T018) é testável sem US1, mas a integração (T019, T020) modifica código de US1
- **US3 (Phase 5)**: depende de US1 (modifica `comparar()` de T012) — mesma natureza de dependência que US2
- **US4 (Phase 6)**: depende de US1 (persiste `Comparacao` já formada); independente de US2/US3 no sentido de que persistência funciona mesmo sem os estados `cotacao_incompativel`/`latencia_alta`, mas a ordem de implementação sugerida é sequencial (P1 → P1 → P1 → P2, seguindo `spec.md`)
- **Polish (Phase 7)**: depende de todas as anteriores

**Nota sobre "independência" nesta spec**: diferente do caso geral de
Spec-Kit, US2 e US3 não são features aditivas independentes — são refinamentos
sucessivos da **mesma** função `comparar()`/`medir_ciclo()` que US1 cria,
porque a spec inteira descreve uma única medição com múltiplas qualificações
obrigatórias (cotação, latência, persistência). Cada fase ainda é testável
isoladamente (testes de função pura antes da integração), mas a integração é
sequencial, não paralela entre stories.

### Parallel Opportunities

- T001/T002 (Setup) em paralelo
- T003/T005 (testes foundational, arquivos/funções diferentes) em paralelo
- Dentro de cada fase de story, as tasks `[P]` de teste (ex.: T007/T008/T009) em paralelo entre si — todas escrevem em `tests/test_arbitragem.py`, mas como funções de teste independentes sem estado compartilhado
- T033/T034 (Polish, guardas independentes) em paralelo

---

## Implementation Strategy

### MVP First (User Story 1 apenas)

1. Setup + Foundational
2. US1 completa
3. **PARE e VALIDE**: `python main.py arbitragem` mede e classifica um ciclo
   corretamente, sem persistência nem checagem de cotação/latência ainda
4. US1 sozinha já corresponde ao que a medição preliminar de `research.md`
   fez manualmente — é o MVP real desta spec

### Incremental Delivery

1. Setup + Foundational → esqueleto de aquisição de dados
2. US1 → medição líquida correta (MVP)
3. US2 → nunca mistura cotação
4. US3 → latência qualifica cada leitura
5. US4 → amostra acumula entre execuções (o que a spec inteira existe para viabilizar)
6. Polish → guardas estruturais + docs sincronizados

Cada passo é um commit no Fluxo Incremental do `CLAUDE.md`: implementar →
`pytest tests/test_arbitragem.py` → commit (`feat(029): ...`) → push →
próximo tópico.
