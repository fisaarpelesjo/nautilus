---

description: "Task list for H11 — momentum em horizonte temporal superior"
---

# Tasks: H11 — Momentum em horizonte temporal superior

**Input**: Design documents from `/specs/024-horizonte-temporal-momentum/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: obrigatórios. A constituição do projeto (Princípio III — Test Before
Implement) exige critério de teste definido **antes** da implementação, e que
toda task nova estenda a suíte `pytest` existente em `tests/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos distintos, sem dependência)
- **[Story]**: US1, US2, US3 conforme a spec

## Path Conventions

Projeto único. Código em `backtesting/`, `main.py`; testes em `tests/`;
documentação em `docs/`. Caminhos conforme a Structure Decision do `plan.md`.

---

## Phase 1: Setup

**Purpose**: esqueleto do módulo, sem lógica.

- [ ] T001 Criar `backtesting/horizonte.py` com docstring de módulo explicando a tese de H11, a restrição de não alterar o horizonte de produção (FR-012) e por que o módulo delega inteiramente às peças existentes em vez de introduzir critério novo
- [ ] T002 Criar `tests/test_horizonte.py` com os imports do módulo e um teste de fumaça que apenas importa e instancia, garantindo que o arquivo entra na suíte desde o primeiro commit

**Checkpoint**: módulo importável, suíte verde, nada implementado.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: a medição de disponibilidade, da qual todo veredito depende. Sem
ela não há como distinguir `inconclusivo` de `reprovado`, que é a regra central
do `data-model.md`.

**⚠️ BLOQUEIA todas as histórias.**

- [ ] T003 [P] Escrever teste em `tests/test_horizonte.py` para `DisponibilidadeHistorico`: `utilizaveis` é `max(0, obtido − aquecimento)` e nunca negativo, inclusive quando o aquecimento excede o histórico
- [ ] T004 [P] Escrever teste em `tests/test_horizonte.py` verificando que combinação com `erro` preenchido não é avaliada, e não é avaliada com resultado zero
- [ ] T005 Implementar a dataclass `DisponibilidadeHistorico` em `backtesting/horizonte.py` conforme `data-model.md`, com os campos par, horizonte, solicitado, obtido, aquecimento, utilizaveis, dias_cobertos, historico_curto e erro
- [ ] T006 Implementar `medir_disponibilidade(pares, horizonte, solicitado)` em `backtesting/horizonte.py`, buscando via `data.fetcher.fetch_ohlcv` e devolvendo uma `DisponibilidadeHistorico` por par, sem interromper a varredura quando um par falha
- [ ] T007 Implementar `aquecimento_candles()` em `backtesting/horizonte.py` derivando o consumo de `EMA_TREND` de `config/settings.py`, e `aquecimento_dias(horizonte)` convertendo para dias — FR-010 exige as duas unidades porque 50 candles semanais são quase um ano

**Checkpoint**: disponibilidade medida e testada; histórias podem começar.

---

## Phase 3: User Story 1 — Responder se a escala explica as reprovações (P1) 🎯 MVP

**Goal**: produzir, para cada estratégia × horizonte × par, as métricas da
bateria e um veredito entre confirmado, só-na-busca, reprovado e inconclusivo.

**Independent Test**: `python main.py horizonte 1d` devolve uma tabela com
veredito por combinação, e nenhuma combinação com menos operações que o mínimo
aparece como reprovada.

### Tests for User Story 1 ⚠️

> Escrever primeiro e confirmar que falham antes de implementar.

- [ ] T008 [P] [US1] Teste em `tests/test_horizonte.py`: combinação com número de operações abaixo de `EDGE_MIN_TRADES` recebe status `inconclusivo`, nunca `reprovado` — FR-003, a regra que separou H10 de reprovação indevida
- [ ] T009 [P] [US1] Teste em `tests/test_horizonte.py`: combinação sem janela de validação válida (fatia abaixo de `MIN_WINDOW_CANDLES`) recebe `inconclusivo` com motivo declarando amostra insuficiente
- [ ] T010 [P] [US1] Teste em `tests/test_horizonte.py`: `n_janelas` é derivado como `min(5, utilizaveis // MIN_WINDOW_CANDLES)` e resulta em `inconclusivo` quando fica abaixo de 3 — conforme decisão D2 de `research.md`
- [ ] T011 [P] [US1] Teste em `tests/test_horizonte.py`: aprovação restrita à janela de descoberta produz `so_na_busca` e **não** `confirmado`

### Implementation for User Story 1

- [ ] T012 [US1] Implementar a dataclass `CombinacaoAvaliada` em `backtesting/horizonte.py` conforme `data-model.md`, com os cinco estados de status
- [ ] T013 [US1] Implementar `_avaliar_combinacao(estrategia, horizonte, par, disponibilidade)` em `backtesting/horizonte.py`, delegando a `run_backtest` para E2, `split_train_validation` para E3 e `walk_forward` para E4, sem alterar nenhum limiar
- [ ] T014 [US1] Implementar a precedência de `inconclusivo` sobre `reprovado` em `backtesting/horizonte.py`: amostra insuficiente decide o status antes de qualquer avaliação de métrica
- [ ] T015 [US1] Implementar `run_horizonte_scan(estrategias, pares, horizontes)` em `backtesting/horizonte.py`, varrendo as combinações e capturando exceção por combinação sem abortar a varredura, como faz `backtesting/multimarket.py::run_scan`
- [ ] T016 [US1] Implementar a dataclass `RelatorioHorizonte` em `backtesting/horizonte.py` com as contagens agregadas de confirmadas e inconclusivas
- [ ] T017 [US1] Implementar `cmd_horizonte()` em `main.py` e registrar os aliases `horizonte` e `horizontes` no despacho de comandos, conforme `contracts/cli-horizonte.md`
- [ ] T018 [US1] Implementar a exibição em `main.py` com a contagem de avaliadas / confirmadas / inconclusivas **antes** da tabela, seguindo o padrão de `multimarket` — ler a tabela sem a contagem convida à leitura errada
- [ ] T019 [US1] Adicionar legenda na saída de `main.py` declarando que `so na busca` não é aprovação e que `inconclusivo` significa amostra insuficiente, não ausência de vantagem

**Checkpoint**: US1 funcional e testável isoladamente.

---

## Phase 4: User Story 2 — Separar vantagem preditiva de economia de custo (P2)

**Goal**: permitir verificar se a eventual superioridade de um horizonte
persiste com custo zerado.

**Independent Test**: `python main.py horizonte 4h 1d` apresenta, por combinação,
retorno com custo real, sem custo e o impacto em pontos percentuais.

### Tests for User Story 2 ⚠️

- [ ] T020 [P] [US2] Teste em `tests/test_horizonte.py`: reexecução com `fee_rate=0` e `slippage_pct=0` produz retorno maior ou igual ao com custo real, em qualquer combinação com ao menos uma operação
- [ ] T021 [P] [US2] Teste em `tests/test_horizonte.py`: o impacto do custo é reportado em pontos percentuais e corresponde à diferença entre os dois retornos

### Implementation for User Story 2

- [ ] T022 [US2] Adicionar `retorno_sem_custo_pct` a `CombinacaoAvaliada` e calculá-lo em `_avaliar_combinacao` em `backtesting/horizonte.py`, reexecutando o backtest com custo zerado
- [ ] T023 [US2] Exibir retorno líquido, retorno sem custo e impacto na tabela de `main.py`, para que a distinção seja legível sem cálculo mental
- [ ] T024 [US2] Adicionar ao quadro comparativo entre horizontes em `main.py` a diferença de impacto de custo entre escalas — horizonte maior negocia menos e paga menos taxa, e essa é a confusão que US2 existe para desfazer

**Checkpoint**: US1 e US2 funcionam de forma independente.

---

## Phase 5: User Story 3 — Declarar limitações de dado (P3)

**Goal**: garantir que limitação de amostra apareça no relatório em vez de ser
absorvida silenciosamente.

**Independent Test**: `python main.py horizonte 1w` marca AVAX, DOT e SOL como
histórico curto e não marca BTC nem ETH.

### Tests for User Story 3 ⚠️

- [ ] T025 [P] [US3] Teste em `tests/test_horizonte.py`: a marcação de histórico curto é relativa à **mediana do horizonte**, não ao valor solicitado — com candles semanais realistas, marca os pares de listagem recente e não marca os que definem o teto do horizonte
- [ ] T026 [P] [US3] Teste em `tests/test_horizonte.py`: universo em que todos os pares têm o mesmo tamanho não produz marcação alguma, provando que a marca não dispara por construção
- [ ] T027 [P] [US3] Teste em `tests/test_horizonte.py`: fold sem operação é marcado como vazio e **excluído** da contagem de janelas positivas e da média de ganho de timing — FR-006
- [ ] T028 [P] [US3] Teste em `tests/test_horizonte.py`: combinação cujo aquecimento excede a janela de teste recebe `inconclusivo` antes de qualquer simulação

### Implementation for User Story 3

- [ ] T029 [US3] Implementar `marcar_historico_curto(disponibilidades)` em `backtesting/horizonte.py` usando a mediana do próprio horizonte como referência, conforme decisão D3 de `research.md`
- [ ] T030 [US3] Implementar o guard de aquecimento em `_avaliar_combinacao` em `backtesting/horizonte.py`: se `aquecimento >= utilizaveis`, a combinação é inconclusiva sem simular
- [ ] T031 [US3] Ajustar a agregação de folds em `backtesting/horizonte.py` para excluir janelas vazias da contagem de positivas e da média de ganho de timing
- [ ] T032 [US3] Exibir o contexto de dado por horizonte em `main.py` — candles medianos, aquecimento em dias, pares marcados — antes da contagem e da tabela

**Checkpoint**: as três histórias funcionam de forma independente.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T033 [P] Exportar o resultado para `reports/horizonte_{timestamp}.{json,csv,md}` via `utils/report_export.py` em `main.py`, seguindo o padrão de `backtest`, `scan` e `optimize`
- [ ] T034 [P] Documentar o comando `horizonte` em `CLAUDE.md` e `AGENTS.md` **no mesmo commit** — a constituição exige que os dois permaneçam sincronizados
- [ ] T035 [P] Documentar o comando em `docs/08-comandos-cli.md`
- [ ] T036 Executar a varredura completa e registrar o veredito de H11 em `docs/research/registro-de-hipoteses.md`, com evidência, procedência e a expectativa registrada em `research.md` confrontada com o resultado observado
- [ ] T037 Reordenar a fila de hipóteses não testadas em `docs/research/registro-de-hipoteses.md` em função do resultado de H11
- [ ] T038 Executar os sete cenários de `quickstart.md` e confirmar que todos passam
- [ ] T039 Rodar a suíte completa e confirmar que a contagem total não diminuiu em relação ao commit anterior

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Fase 1)**: sem dependências
- **Foundational (Fase 2)**: depende da Fase 1 — **BLOQUEIA todas as histórias**
- **US1 (Fase 3)**: depende da Fase 2
- **US2 (Fase 4)**: depende da Fase 2; integra com US1 mas é testável isoladamente
- **US3 (Fase 5)**: depende da Fase 2; integra com US1 mas é testável isoladamente
- **Polish (Fase 6)**: depende das histórias desejadas estarem completas

### Dependência específica

T036 depende de T033: o veredito de H11 só pode ser registrado depois que a
varredura completa rodar e o relatório existir.

### Within Each User Story

- Testes escritos e **falhando** antes da implementação (Constituição III)
- Entidades antes dos serviços que as consomem
- Serviços antes da exibição em `main.py`
- História completa antes de passar à próxima prioridade

### Parallel Opportunities

- T003 e T004 em paralelo (testes, arquivos distintos de implementação)
- T008 a T011 em paralelo entre si (todos testes de US1)
- T020 e T021 em paralelo
- T025 a T028 em paralelo
- T033, T034 e T035 em paralelo (documentação e exportação, sem sobreposição)

**Restrição real:** T005–T007, T012–T019, T022–T024 e T029–T032 escrevem todos
em `backtesting/horizonte.py` ou `main.py` e **não** podem ser paralelizados
entre si, apesar de pertencerem a histórias diferentes.

---

## Implementation Strategy

### MVP primeiro (apenas US1)

1. Fase 1: Setup
2. Fase 2: Foundational — bloqueia tudo
3. Fase 3: US1
4. **PARAR e VALIDAR**: `python main.py horizonte 1d` produz veredito por
   combinação, e o cenário 2 do `quickstart.md` confirma que 1w é inconclusivo
5. Nesse ponto a pergunta central de H11 já está respondida

### Entrega incremental

Cada fase termina em commit próprio, com os testes daquela fase passando, e push
para `origin/main` antes da próxima — Fluxo Incremental do `CLAUDE.md` e
Princípio IV da constituição.

---

## Notes

- O resultado esperado, registrado em `research.md` antes da execução, é que 1d
  responda a hipótese e 1w fique inconclusivo por amostra. Se a implementação
  produzir 1w confirmado ou reprovado, o dimensionamento das janelas está errado
  — não é achado, é defeito.
- Nenhuma task altera `TIMEFRAME` de produção. T038 verifica isso explicitamente
  pelo cenário 6 do `quickstart.md`.
- Nenhuma task adiciona dependência.
