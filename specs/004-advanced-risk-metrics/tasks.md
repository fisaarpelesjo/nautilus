---

description: "Task list for 004-advanced-risk-metrics"
---

# Tasks: Métricas de Risco Avançadas

**Input**: Design documents from `/specs/004-advanced-risk-metrics/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/cli.md](./contracts/cli.md)

**Tests**: Incluídos — a constitution (III. Test Before Implement) exige critério de teste definido
antes de cada implementação.

**Organization**: Tarefas agrupadas por User Story (US1/US2/US3, ver `spec.md`) para permitir
implementação e validação independentes de cada uma.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependência)
- **[Story]**: A qual User Story a tarefa pertence (US1, US2, US3)
- Caminhos de arquivo reais do repositório incluídos em cada descrição

## Path Conventions

Projeto único na raiz do repositório (mesmo das specs 001-003) — ver `plan.md` → Project Structure
para o mapeamento completo de módulos.

---

## Phase 1: Setup

**Purpose**: Nenhuma — ambiente já configurado pelas specs anteriores.

**Checkpoint**: Ambiente já pronto.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Calmar Ratio (US1) precisa de retorno anualizado, que também é o próprio entregável da
US2 — em vez de calcular duas vezes (ou fazer US1 depender de US2 estar completa), o helper de
anualização nasce aqui, compartilhado pelas duas.

**⚠️ CRITICAL**: Nenhuma tarefa de US1 (Calmar especificamente) deve começar antes de T002.

- [x] T001 [P] Teste: `_annualized_return_pct(total_return_pct, period_start, period_end)` calcula via
      juros compostos (base 365 dias) e retorna `0.0` quando `period_days <= 0` — em
      `tests/test_backtesting_engine.py`
- [x] T002 Implementar `_annualized_return_pct()` em `backtesting/engine.py` (depende de T001 falhando)

**Checkpoint**: Helper de anualização pronto, sem alterar `BacktestResult` ainda (US1/US2 fazem isso).

---

## Phase 3: User Story 1 - Avaliar risco ajustado ao downside (Priority: P1) 🎯 MVP

**Goal**: Todo relatório de backtest mostra Sortino Ratio e Calmar Ratio ao lado do Sharpe já
existente.

**Independent Test**: Ver `quickstart.md` → US1.

### Tests for User Story 1 ⚠️

- [x] T003 [P] [US1] Teste: Sortino usa desvio padrão só dos retornos negativos (produz valor
      diferente do Sharpe quando há mistura de ganhos e perdas com volatilidades distintas) — em
      `tests/test_backtesting_engine.py`
- [x] T004 [P] [US1] Teste: Sortino `== float("inf")` quando não há trades com prejuízo e a média de
      retornos é positiva; `== 0.0` quando a média não é positiva — `tests/test_backtesting_engine.py`
- [x] T005 [P] [US1] Teste: Calmar `== annualized_return_pct / max_drawdown_pct`; `== float("inf")`
      quando `max_drawdown_pct == 0` e retorno anualizado positivo; `== 0.0` caso contrário —
      `tests/test_backtesting_engine.py`

### Implementation for User Story 1

- [x] T006 [US1] `BacktestResult` ganha campos `sortino: float`, `calmar: float`
      (`backtesting/engine.py`)
- [x] T007 [US1] `_calculate_advanced_metrics` calcula `sortino` (mesmo padrão de
      `_simplified_sharpe`, desvio só dos retornos negativos) (depende de T003 falhando, T004
      falhando, T006)
- [x] T008 [US1] `_calculate_advanced_metrics` calcula `calmar` usando `_annualized_return_pct()`
      (Foundational) e `max_drawdown_pct` já recebido pela função (depende de T005 falhando, T002,
      T007)
- [x] T009 [US1] `print_report` exibe linhas "Sortino" e "Calmar" no bloco de métricas já existente
      (depende de T008)

**Checkpoint**: US1 completa e testável de forma independente — todo backtest mostra Sortino/Calmar.

---

## Phase 4: User Story 2 - Julgar retorno pela eficiência do capital exposto (Priority: P2)

**Goal**: Todo relatório de backtest mostra retorno anualizado e retorno por tempo exposto.

**Independent Test**: Ver `quickstart.md` → US2.

### Tests for User Story 2 ⚠️

- [x] T010 [P] [US2] Teste: `BacktestResult.annualized_return_pct` bate com
      `_annualized_return_pct()` chamado com os mesmos parâmetros (mesmo helper da Foundational, não
      um segundo cálculo) — em `tests/test_backtesting_engine.py`
- [x] T011 [P] [US2] Teste: `return_per_exposure_pct == total_return_pct / (exposure_pct / 100)`
      quando `exposure_pct > 0` — `tests/test_backtesting_engine.py`
- [x] T012 [P] [US2] Teste: `return_per_exposure_pct is None` (não `0.0` nem `inf`) quando
      `exposure_pct == 0` — `tests/test_backtesting_engine.py`

### Implementation for User Story 2

- [x] T013 [US2] `BacktestResult` ganha campos `annualized_return_pct: float`,
      `return_per_exposure_pct: Optional[float]` (`backtesting/engine.py`)
- [x] T014 [US2] `_calculate_advanced_metrics` expõe `annualized_return_pct` (reusa o valor já
      calculado internamente para Calmar em US1 — T008 — não recalcula) e calcula
      `return_per_exposure_pct` (depende de T010 falhando, T011 falhando, T012 falhando, T008, T013)
- [x] T015 [US2] `print_report` exibe linhas "Retorno anualizado" e "Retorno por exposição" (`"n/a"`
      quando `None`) (depende de T014)

**Checkpoint**: US1 e US2 completas. Nota: Calmar (US1, T008) e `annualized_return_pct` (US2, T013)
compartilham o mesmo cálculo interno via `_annualized_return_pct()` (Foundational) — dependência
intencional e documentada, diferente do padrão usual de independência total entre stories.

---

## Phase 5: User Story 3 - Entender por que o bot não está entrando (Priority: P3)

**Goal**: `python main.py decisions` resume `data/decisions.csv` — sinais, bloqueios mais frequentes.

**Independent Test**: Ver `quickstart.md` → US3.

### Tests for User Story 3 ⚠️

- [x] T016 [P] [US3] Teste: `analyze_decisions()` conta ciclos por `signal` e entradas bloqueadas a
      partir de uma fixture CSV sintética (este ambiente não tem `decisions.csv` real, ver
      `spec.md` → Assumptions) — novo `tests/test_decisions_analysis.py`
- [x] T017 [P] [US3] Teste: `blocker_counts` vem ranqueado por frequência decrescente —
      `tests/test_decisions_analysis.py`
- [x] T018 [P] [US3] Teste: arquivo ausente ou vazio retorna `status="sem_dados"`, sem lançar exceção
      — `tests/test_decisions_analysis.py`
- [x] T019 [P] [US3] Teste: linha com coluna ausente (schema antigo) não interrompe a análise das
      demais linhas; conta em `total_cycles` mas não em agregações que dependem da coluna ausente —
      `tests/test_decisions_analysis.py`

### Implementation for User Story 3

- [x] T020 [US3] Novo `data/decisions_analysis.py`: dataclasses `DecisionRecord`/
      `DecisionsAnalysisResult`, `_load_decisions()` via `csv.DictReader` (tolerante a coluna
      ausente) (depende de T016 falhando, T019 falhando)
- [x] T021 [US3] `analyze_decisions()`: `signal_counts`, `blocked_entries`, `blocker_counts`
      ranqueado, `status="sem_dados"` quando vazio/ausente (depende de T017 falhando, T018 falhando,
      T020)
- [x] T022 [US3] `print_decisions_analysis()` + `run()`, mesmo padrão de
      `backtesting/analysis.py` (depende de T021)
- [x] T023 [US3] Novo comando `decisions` (alias `decisoes`) em `main.py`: `COMMANDS` dict +
      `cmd_decisions()` (depende de T022)

**Checkpoint**: US1, US2 e US3 funcionam de forma independente (à parte da dependência documentada
Calmar/anualizado da Foundational).

Uma rodada de `/code-review medium` sobre o acumulado (Foundational + US1 + US2 + US3) — 1 achado,
corrigido:

1. **`_annualized_return_pct()` podia lançar `OverflowError` não capturado**: com período curto
   (ex: `TIMEFRAME=1m`, poucas horas de histórico) e retorno acumulado grande (ex: >1000%, alcançável
   compondo vários trades vencedores num par volátil), `growth_factor ** (365/period_days)` estoura o
   range de `float`, derrubando `python main.py backtest` inteiro (sem `try/except` no caminho
   principal de `main.py`/`optimizer.py`). Corrigido: `try/except OverflowError` retornando `inf`
   explícito, mesma convenção já usada para outros denominadores extremos no arquivo. Teste de
   regressão reproduzindo o cenário exato (`TIMEFRAME=1m`, ~1900 minutos, retorno 1300%) adicionado.

167 testes passando (19 novos desde a spec 003), ruff/mypy limpos. **Status: aprovada.**

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentação — não altera comportamento do bot.

- [x] T024 [P] Atualizar `ROADMAP.md` marcando Fase 3 itens 1 (Sortino), 2 (Calmar), 3 (tempo em
      posição/anualizado) e 4 (análise de `decisions.csv`) como concluídos, com link para esta spec
- [x] T025 [P] Atualizar `specs/BACKLOG.md`: status da spec 004 para concluída
- [x] T026 Rodar `quickstart.md` (as três User Stories) — US1/US2 contra dados reais da Binance, US3
      com a fixture sintética (e com dados reais se o operador já tiver `data/decisions.csv`) — e
      registrar resultado relevante em `STRATEGY_REVIEW.md`, seguindo o padrão das specs 001-003

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem tarefas.
- **Foundational (Phase 2)**: BLOQUEIA especificamente o Calmar de US1 (T008) e o
  `annualized_return_pct` de US2 (T014) — as duas dependem do mesmo helper. Sortino (US1) e
  `return_per_exposure_pct` (US2) não dependem da Foundational.
- **User Stories (Phase 3+)**: US3 é totalmente independente de US1/US2 e da Foundational (opera
  sobre `decisions.csv`, não sobre `BacktestResult`).
- **Polish (Phase 6)**: Depende das User Stories que forem concluídas.

### User Story Dependencies

- **US1 (P1)**: Sortino independente; Calmar depende de T002 (Foundational).
- **US2 (P2)**: `return_per_exposure_pct` independente; `annualized_return_pct` reusa o mesmo cálculo
  interno de T008 (US1) — na prática, T014 depende de T008 já existir (não só de T002), porque
  `_calculate_advanced_metrics` calcula o valor uma única vez e ambos os campos o leem.
- **US3 (P3)**: Totalmente independente de US1/US2/Foundational.

### Within Each User Story

- Testes MUST ser escritos e falhar antes da implementação (constitution III).
- Dentro de US1: T006 antes de T007/T008 (campos antes de popular); T007 antes de T008 (Sortino não
  depende de Calmar, mas T008 é escrita depois por conveniência de diff); T008 antes de T009 (dados
  antes do print).
- Dentro de US2: T013 antes de T014; T014 antes de T015.
- Dentro de US3: T020 antes de T021 (leitura antes da agregação); T021 antes de T022 (dados antes do
  print); T022 antes de T023 (função pronta antes do dispatch de CLI).

### Parallel Opportunities

- T003, T004, T005 (testes de US1) podem ser escritos em paralelo.
- T010, T011, T012 (testes de US2) podem ser escritos em paralelo.
- T016, T017, T018, T019 (testes de US3) podem ser escritos em paralelo — e em paralelo com
  qualquer tarefa de US1/US2/Foundational, já que US3 não depende de nada delas.
- T024, T025 (Polish) podem rodar em paralelo.
- Seguindo o Fluxo Incremental do `CLAUDE.md`, a prática real é sequencial, tópico por tópico, commit
  por commit.

---

## Implementation Strategy

### MVP First (User Story 1)

1. Completar Phase 1: Setup — nenhuma tarefa.
2. Completar Phase 2: Foundational (helper de anualização).
3. Completar Phase 3: User Story 1 (Sortino + Calmar).
4. Validar US1 isoladamente (`quickstart.md` → US1) antes de seguir.

### Incremental Delivery

1. Foundational → helper pronto, sem mudança de comportamento observável ainda.
2. US1 → validar → é o MVP desta spec (Sortino + Calmar, extensão pura do relatório já existente).
3. US2 → validar → retorno anualizado e por tempo exposto completam a visão de eficiência.
4. US3 → validar → diagnóstico de `decisions.csv` sem abrir planilha manualmente.
5. Polish → documentação (`ROADMAP.md`, `BACKLOG.md`, `STRATEGY_REVIEW.md`).

Cada etapa segue o Fluxo Incremental do `CLAUDE.md`: tarefa pequena → testes → commit Conventional
Commit em português → push para `origin/main` → próxima tarefa. Seguindo o padrão estabelecido nas
specs 001-003, `/code-review medium` roda sobre o diff acumulado antes do commit final de cada etapa
significativa.

---

## Notes

- [P] = arquivos diferentes, sem dependência.
- [Story] mapeia a tarefa à User Story correspondente, para rastreabilidade.
- Verificar que os testes falham antes de implementar (constitution III).
- Commit após cada tarefa ou grupo lógico pequeno — nunca uma User Story inteira em um commit só.
- Nenhuma tarefa desta lista toca `risk/`, `execution/` ou `trading/position_lifecycle.py` — feature
  é só relatório/análise, fora do escopo de `TRADING_MODE=live`.
