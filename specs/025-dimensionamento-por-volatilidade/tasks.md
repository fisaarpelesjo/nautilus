---

description: "Task list for H12 — dimensionamento de posição por volatilidade"
---

# Tasks: H12 — Dimensionamento de posição por volatilidade

**Input**: Design documents from `/specs/025-dimensionamento-por-volatilidade/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: obrigatórios. Constituição, Princípio III — critério de teste definido
**antes** da implementação, estendendo a suíte `pytest` existente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos distintos, sem dependência)
- **[Story]**: US1, US2, US3 conforme a spec

## Path Conventions

Projeto único. Código em `backtesting/`, `main.py`; testes em `tests/`;
documentação em `docs/`.

---

## Phase 1: Setup

- [X] T001 Criar `backtesting/volatilidade.py` com docstring de módulo declarando a tese de H12, o teto do fator como invariante de código, e por que `risk/manager.py` não é tocado
- [X] T002 Criar `tests/test_volatilidade.py` com teste de fumaça que importa o módulo e verifica a API pública

**Checkpoint**: módulo importável, suíte verde.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: o fator de dimensionamento e sua integração no motor. Tudo depende
disso.

**⚠️ BLOQUEIA todas as histórias.**

- [X] T003 [P] Teste em `tests/test_volatilidade.py`: `fator_volatilidade` nunca excede 1,0, incluindo alvo absurdamente alto (0,5) e volatilidade próxima de zero — FR-003, invariante que sustenta a proibição de alavancagem
- [X] T004 [P] Teste em `tests/test_volatilidade.py`: `atr_ratio` nulo, ausente, negativo ou não finito devolve fator 1,0, sem divisão por zero — FR-012
- [X] T005 [P] Teste em `tests/test_volatilidade.py`: fator é monotonicamente decrescente na volatilidade — dobrar `atr_ratio` reduz o fator
- [X] T006 [P] Teste em `tests/test_volatilidade.py`: fator respeita `fator_minimo`, nunca produzindo posição arbitrariamente pequena
- [X] T007 Implementar `ParametrosVolatilidade` e `fator_volatilidade(atr_ratio, params)` em `backtesting/volatilidade.py` conforme `data-model.md`, com o `min(1.0, ...)` explícito na fórmula
- [X] T008 Adicionar parâmetro opcional de dimensionamento a `simulate_backtest` em `backtesting/engine.py`, com default que preserva o comportamento atual
- [X] T009 Teste de regressão em `tests/test_volatilidade.py`: `simulate_backtest` sem o parâmetro produz resultado idêntico ao de antes desta feature, campo a campo — a garantia de que o default não muda nada
- [X] T010 Teste em `tests/test_volatilidade.py`: `risk/manager.py` não é importado nem referenciado por `backtesting/volatilidade.py` — FR-013, guarda contra regressão de escopo

**Checkpoint**: fator testado, motor aceita dimensionamento, produção intacta.

---

## Phase 3: User Story 1 — Descobrir se o drawdown era problema de dimensionamento (P1) 🎯 MVP

**Goal**: produzir, por combinação, as métricas nas duas versões com os deltas.

**Independent Test**: `python main.py volatilidade` devolve tabela pareada com
drawdown e retorno de cada versão.

### Tests for User Story 1 ⚠️

- [ ] T011 [P] [US1] Teste em `tests/test_volatilidade.py`: `ComparacaoPareada` calcula `delta_drawdown` e `delta_retorno` como dimensionado menos base
- [ ] T012 [P] [US1] Teste em `tests/test_volatilidade.py`: amostra abaixo do mínimo em **qualquer** das duas versões produz `inconclusivo`, nunca `piora` — FR-011; comparar 30 operações contra 4 mede diferença de amostra, não dimensionamento
- [ ] T013 [P] [US1] Teste em `tests/test_volatilidade.py`: falha ao simular uma das versões produz `erro`, distinto de `piora`

### Implementation for User Story 1

- [ ] T014 [US1] Implementar `ComparacaoPareada` em `backtesting/volatilidade.py` com as seis grandezas derivadas de `data-model.md`
- [ ] T015 [US1] Implementar `comparar_combinacao(estrategia, par, horizonte, params)` em `backtesting/volatilidade.py`, rodando a bateria nas duas versões e reusando `preparar()` de `horizonte.py` para calcular indicadores uma vez
- [ ] T016 [US1] Implementar `run_volatilidade_scan(estrategias, pares, params)` em `backtesting/volatilidade.py`, sem abortar a varredura quando uma combinação falha
- [ ] T017 [US1] Implementar `cmd_volatilidade()` em `main.py` e registrar os aliases `volatilidade` e `voltarget`, conforme `contracts/cli-volatilidade.md`
- [ ] T018 [US1] Implementar a exibição em `main.py`: parâmetros, contagem por status **antes** da tabela, tabela pareada com deltas

**Checkpoint**: US1 funcional. **Ainda não é MVP defensável — falta US2.**

---

## Phase 4: User Story 2 — Impedir que redução de exposição seja lida como habilidade (P1)

**Goal**: distinguir melhora real de participação menor.

**Independent Test**: combinação cujo drawdown cai e cujo ganho de timing não
sobe recebe `sem_vantagem`.

**⚠️ Sem esta fase, US1 produz resposta inutilizável.** Dimensionar por
volatilidade reduz exposição por construção — ~10% em média, medido em
`research.md` — e num mercado em queda isso sozinho melhora o retorno relativo
ao buy-and-hold. É o achado M7.

### Tests for User Story 2 ⚠️

- [ ] T019 [P] [US2] Teste em `tests/test_volatilidade.py`: drawdown cai e `delta_timing` ≤ 0 produz `sem_vantagem`, não `melhora` — FR-008, o teste mais importante da spec
- [ ] T020 [P] [US2] Teste em `tests/test_volatilidade.py`: drawdown cai e `delta_timing` > 0 produz `melhora`
- [ ] T021 [P] [US2] Teste em `tests/test_volatilidade.py`: `delta_exposicao` é calculado e reportado em toda comparação avaliada — FR-007

### Implementation for User Story 2

- [ ] T022 [US2] Implementar `delta_exposicao` e `delta_timing` em `ComparacaoPareada`, reusando `ganho_de_timing_pp` de `cross_sectional.py` sem redefinir a métrica
- [ ] T023 [US2] Implementar a classificação de status em `backtesting/volatilidade.py` com `sem_vantagem` como estado próprio, e `inconclusivo` precedendo qualquer avaliação de métrica
- [ ] T024 [US2] Exibir `delta_exposicao` e `delta_timing` na tabela de `main.py`, adjacentes ao delta de drawdown, para que a comparação seja legível sem cálculo mental
- [ ] T025 [US2] Adicionar legenda em `main.py` declarando que `sem vantagem` significa que o ganho desapareceu ao descontar exposição

**Checkpoint**: MVP defensável. As duas histórias P1 completas.

---

## Phase 5: User Story 3 — Separar vantagem de custo de giro (P2)

**Goal**: distinguir efeito do mecanismo de efeito do custo adicional.

### Tests for User Story 3 ⚠️

- [ ] T026 [P] [US3] Teste em `tests/test_volatilidade.py`: `delta_operacoes` e `delta_custo` são calculados entre as versões
- [ ] T027 [P] [US3] Teste em `tests/test_volatilidade.py`: reexecução sem custo produz retorno maior ou igual em ambas as versões

### Implementation for User Story 3

- [ ] T028 [US3] Implementar `retorno_sem_custo_base` e `retorno_sem_custo_dim` em `comparar_combinacao`, reexecutando as duas versões com custo zerado
- [ ] T029 [US3] Exibir operações e custo de cada versão na tabela de `main.py`
- [ ] T030 [US3] Adicionar ao resumo de `main.py` o agregado de custo de giro, permitindo verificar se a diferença entre versões persiste com custo zerado

**Checkpoint**: as três histórias funcionam de forma independente.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T031 [P] Exportar o resultado para `reports/volatilidade_{timestamp}.{json,csv,md}` via `utils/report_export.py`
- [ ] T032 [P] Documentar o comando em `CLAUDE.md` e `AGENTS.md` **no mesmo commit** — a constituição exige sincronia
- [ ] T033 [P] Documentar em `docs/08-comandos-cli.md`, incluindo o significado de `sem vantagem`
- [ ] T034 Executar a varredura completa e registrar o veredito de H12 em `docs/research/registro-de-hipoteses.md`, confrontando a predição de `research.md` com o observado
- [ ] T035 Reordenar a fila de hipóteses em `docs/research/registro-de-hipoteses.md` conforme o resultado
- [ ] T036 Executar os oito cenários de `quickstart.md` e confirmar que todos passam
- [ ] T037 Confirmar `git diff --stat risk/manager.py` vazio e rodar a suíte completa sem redução na contagem

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (F1)**: sem dependências
- **Foundational (F2)**: depende de F1 — **BLOQUEIA todas as histórias**
- **US1 (F3)**: depende de F2
- **US2 (F4)**: depende de F2 e de US1 — as duas formam o MVP
- **US3 (F5)**: depende de F2; testável isoladamente
- **Polish (F6)**: depende das histórias desejadas

### Dependência específica

T034 depende de T031: o veredito só pode ser registrado depois que a varredura
rodar e o relatório existir.

### Within Each User Story

- Testes escritos e **falhando** antes da implementação (Constituição III)
- Entidades antes dos serviços; serviços antes da exibição
- História completa antes da próxima prioridade

### Parallel Opportunities

- T003–T006 em paralelo (testes do fator)
- T011–T013 em paralelo
- T019–T021 em paralelo
- T026 e T027 em paralelo
- T031, T032 e T033 em paralelo

**Restrição real:** T007, T014–T018, T022–T025 e T028–T030 escrevem em
`backtesting/volatilidade.py` ou `main.py` e **não** podem ser paralelizados
entre si, mesmo pertencendo a histórias diferentes.

---

## Implementation Strategy

### MVP = US1 **e** US2

Diferente da spec anterior, o MVP aqui exige duas histórias. US1 sozinha produz
uma tabela em que redução de exposição aparece como melhoria — resposta que
parece boa e não é. Parar em US1 seria pior que não implementar, porque
produziria evidência enganosa que entraria no registro.

1. F1 Setup
2. F2 Foundational — bloqueia tudo
3. F3 US1
4. F4 US2
5. **PARAR e VALIDAR**: cenário 2 do `quickstart.md` — combinação cujo drawdown
   cai sem ganho de timing recebe `sem_vantagem`
6. Só então a pergunta de H12 está respondida de forma utilizável

### Entrega incremental

Cada fase termina em commit próprio, testes passando, push antes da próxima —
Fluxo Incremental do `CLAUDE.md` e Princípio IV.

---

## Notes

- **Predição registrada em `research.md` antes da execução:** o drawdown vai
  cair, porque é o que o mecanismo faz. A pergunta aberta é se o retorno cai na
  mesma proporção. Se cair, H12 está encerrada e o drawdown de H7 não era
  problema de dimensionamento.
- Se a implementação produzir fator maior que 1,0 em qualquer situação, é
  defeito, não achado — viola FR-003 e a proibição de alavancagem da
  constituição.
- Nenhuma tarefa altera `risk/manager.py`. T010 e T037 verificam.
- Nenhuma tarefa adiciona dependência.
