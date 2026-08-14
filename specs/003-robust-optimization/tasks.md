---

description: "Task list for 003-robust-optimization"
---

# Tasks: Otimização Sem Overfitting

**Input**: Design documents from `/specs/003-robust-optimization/`

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

Projeto único na raiz do repositório (mesmo das specs 001/002) — ver `plan.md` → Project Structure
para o mapeamento completo de módulos.

---

## Phase 1: Setup

**Purpose**: Nenhuma — ambiente já configurado pelas specs anteriores. Fase mantida só por
consistência com o template.

**Checkpoint**: Ambiente já pronto.

---

## Phase 2: Foundational

**Purpose**: Nenhuma tarefa bloqueante cross-story nesta spec — US1 reusa `split_train_validation()`
já existente (spec 001) sem precisar de infraestrutura nova; `backtesting/robustness.py` (usado por
US2 e US3) é criado dentro da própria US2 e estendido pela US3, não antes de ambas.

**Checkpoint**: N/A.

---

## Phase 3: User Story 1 - Saber se os parâmetros sobrevivem fora do histórico usado para escolhê-los (Priority: P1) 🎯 MVP

**Goal**: `python main.py optimize --validate` escolhe os `top_n` candidatos usando só a fatia de
treino de cada símbolo, e reporta o desempenho de cada um também na fatia de validação.

**Independent Test**: Ver `quickstart.md` → US1.

### Tests for User Story 1 ⚠️

- [x] T001 [P] [US1] Teste: `_optimize_multi(..., validate=True)` escolhe/pontua candidatos usando só
      a fatia de treino de cada símbolo (não o histórico inteiro) — novo `tests/test_optimizer.py`
- [x] T002 [P] [US1] Teste: cada candidato retornado tem `validation_avg_return`/
      `validation_avg_drawdown`/`validation_total_trades` calculados contra a fatia de validação —
      `tests/test_optimizer.py`
- [x] T003 [P] [US1] Teste: símbolo sem histórico suficiente para validação aparece em
      `validation_symbols_skipped` e não distorce as médias de validação dos demais símbolos —
      `tests/test_optimizer.py`
- [x] T004 [P] [US1] Teste: `cmd_otimizar` (`main.py`) sem `--validate` continua chamando
      `optimizer.run()` com `validate=False` (comportamento idêntico ao de antes desta spec) — em
      `tests/test_main_backtest.py`

### Implementation for User Story 1

- [x] T005 [US1] `MultiOptResult` (`backtesting/optimizer.py`) ganha campos
      `validation_avg_return: Optional[float] = None`,
      `validation_avg_drawdown: Optional[float] = None`, `validation_total_trades: int = 0`,
      `validation_symbols_skipped: List[str] = field(default_factory=list)` (depende de T001 falhando)
- [x] T006 [US1] `_optimize_multi` ganha parâmetro `validate: bool = False`; quando `True`, cada
      símbolo é dividido via `split_train_validation()` (import de `backtesting.validation`) antes de
      montar `indicator_cache`; o grid search passa a pontuar/escolher usando só `train_df` de cada
      símbolo (depende de T005)
- [x] T007 [US1] Após escolher os `top_n`, cada candidato é reavaliado (`simulate_backtest`) contra a
      fatia de validação de cada símbolo onde ela existir; símbolos sem validação possível entram em
      `validation_symbols_skipped` e não contam nas médias (depende de T006, T002 falhando, T003
      falhando)
- [x] T008 [US1] `_print_results` exibe colunas de validação quando `validate=True` (retorno/drawdown
      de validação ao lado dos de treino) e lista `validation_symbols_skipped` quando não vazia
      (depende de T007)
- [x] T009 [US1] `run()` (`backtesting/optimizer.py`) ganha parâmetro `validate: bool = False`,
      repassado a `_optimize_multi`; `cmd_otimizar` (`main.py`) lê `--validate` de `sys.argv` (mesmo
      padrão de `cmd_backtest --validate`, spec 001) e repassa (depende de T004 falhando, T008)

**Checkpoint**: US1 completa e testável de forma independente — `optimize --validate` mostra
treino/validação lado a lado; `optimize` sem flag inalterado.

---

## Phase 4: User Story 2 - Confirmar que os parâmetros funcionam em mais de um recorte de mercado (Priority: P2)

**Goal**: `python main.py optimize --walk-forward` avalia o conjunto de parâmetros vencedor em ≥3
janelas deslizantes independentes, reportando cada janela e um resumo (média + pior janela).

**Independent Test**: Ver `quickstart.md` → US2.

### Tests for User Story 2 ⚠️

- [x] T010 [P] [US2] Teste: `split_walk_forward_windows(df, min_windows=3)` retorna N fatias
      contíguas, não sobrepostas, cobrindo o df inteiro sem embaralhar — novo `tests/test_robustness.py`
- [x] T011 [P] [US2] Teste: `split_walk_forward_windows` retorna status "dados insuficientes" (não
      um número menor de janelas) quando o histórico não cobre `min_windows` janelas de tamanho
      mínimo — `tests/test_robustness.py`
- [x] T012 [P] [US2] Teste: `walk_forward_validate(df, strategy_params, min_windows=3)` roda o MESMO
      conjunto de parâmetros em cada janela (não reotimiza) e agrega `avg_return_pct`/`worst_window`
      — a pior janela nunca fica escondida atrás de uma média favorável — `tests/test_robustness.py`
- [x] T013 [P] [US2] Teste: `cmd_otimizar` com `--walk-forward` aciona `validate=True` implicitamente
      e chama `walk_forward_validate` sobre o candidato vencedor — `tests/test_main_backtest.py`

### Implementation for User Story 2

- [x] T014 [US2] Novo `backtesting/robustness.py`: `split_walk_forward_windows(df, min_windows=3,
      min_window_candles=150)`, generalização do fatiamento contíguo de `split_train_validation`
      (spec 001) para N fatias (depende de T010 falhando, T011 falhando)
- [x] T015 [US2] `walk_forward_validate(df, strategy, min_windows=3)` em `robustness.py`: roda
      `simulate_backtest` (import de `backtesting.engine`) em cada janela com os mesmos parâmetros,
      agrega resultado médio e pior janela (depende de T012 falhando, T014)
- [x] T016 [US2] `backtesting/optimizer.py` ganha `walk_forward: bool = False` em `run()`/
      `_optimize_multi`; quando `True`, força `validate=True` e chama `walk_forward_validate` sobre o
      df completo de cada símbolo usando os parâmetros do candidato #1 (depende de T015, T009)
- [x] T017 [US2] Nova seção "VALIDAÇÃO WALK-FORWARD" impressa após a tabela principal (janelas +
      resumo); `cmd_otimizar` (`main.py`) lê `--walk-forward` de `sys.argv` (depende de T013 falhando,
      T016)

**Checkpoint**: US1 e US2 funcionam de forma independente uma da outra — `--walk-forward` implica
`--validate` internamente, mas `--validate` sozinho continua funcionando sem walk-forward.

---

## Phase 5: User Story 3 - Entender o risco de uma sequência ruim de perdas (Priority: P3)

**Goal**: `python main.py backtest --montecarlo` reamostra a ordem dos trades do backtest (bootstrap
com reposição) e estima a distribuição de drawdown máximo e maior sequência de perdas.

**Independent Test**: Ver `quickstart.md` → US3.

### Tests for User Story 3 ⚠️

- [x] T018 [P] [US3] Teste: `monte_carlo_resample(trades, n_simulations=1000, seed=42)` com seed fixo
      produz resultado determinístico entre execuções repetidas — novo teste em
      `tests/test_robustness.py`
- [x] T019 [P] [US3] Teste: `monte_carlo_resample` sobre uma lista de trades sintética conhecida
      retorna `max_drawdown_median_pct`/`max_drawdown_p95_pct`/`worst_losing_streak_median` coerentes
      (p95 ≥ mediana) — `tests/test_robustness.py`
- [x] T020 [P] [US3] Teste: `low_confidence=True` quando `len(trades) < EDGE_MIN_TRADES`; `False`
      caso contrário — `tests/test_robustness.py`
- [x] T021 [P] [US3] Teste: `cmd_backtest` com `--montecarlo` aciona a análise sobre os trades do
      backtest já rodado, sem alterar o dispatch de `--validate` — `tests/test_main_backtest.py`

### Implementation for User Story 3

- [x] T022 [US3] `monte_carlo_resample(trades: List[Trade], n_simulations=1000, seed=None)` em
      `backtesting/robustness.py`: bootstrap com reposição sobre os PnLs, reconstrói equity por
      simulação, calcula drawdown máximo e maior sequência de perdas por simulação, agrega percentis
      (depende de T018 falhando, T019 falhando)
- [x] T023 [US3] `low_confidence` calculado via `EDGE_MIN_TRADES` (import de `config.settings`, spec
      002) (depende de T020 falhando, T022)
- [x] T024 [US3] Nova função de relatório em `robustness.py` imprime a seção "ANÁLISE MONTE CARLO"
      após o relatório de backtest padrão; `cmd_backtest` (`main.py`) lê `--montecarlo` de `sys.argv`
      e aciona sobre os trades do resultado já calculado (depende de T021 falhando, T023)

**Checkpoint**: US1, US2 e US3 funcionam de forma independente.

Nota de design descoberta na implementação (não antecipada em `research.md`): em
`walk_forward_validate`, só a primeira janela usa `start_index=100` (pula o warmup de indicador que
só existe no início do df completo); as demais janelas usam `start_index=0`, já que herdam histórico
válido do mesmo df pré-computado — mesmo raciocínio já usado em `split_train_validation` (spec 001)
para treino vs validação, generalizado aqui para N janelas.

Duas rodadas de `/code-review medium` (seguindo a troca de `high` para `medium` combinada nesta
sessão, para gastar menos tokens):

Rodada 1 (US1+US2, antes de US3 existir): nenhum achado sobrevivente à verificação.

Rodada 2 (acumulado completo, US1+US2+US3) — 1 achado, corrigido:
1. `MIN_WINDOW_CANDLES=150` duplicado verbatim em `backtesting/robustness.py` em vez de importado de
   `backtesting/validation.py` (onde a spec 001 já define o mesmo limiar) — comentário no código já
   admitia que precisava ficar sincronizado manualmente, risco real de um ajuste futuro em um lugar
   não refletir no outro. Corrigido: `robustness.py` importa a constante em vez de redefinir.

148 testes passando (16 novos), ruff/mypy limpos. **Status: aprovada.**

Achado adicional durante T027 (validação manual com dados reais, fora do escopo de código review):
o console compartilhado em `utils/display.py` (usado por `optimizer.py`/`engine.py`/`validation.py`/
`robustness.py`) tinha o mesmo bug de largura já corrigido nos consoles locais de `multi.py`/
`scanner.py` na spec 002 — sem `width` fixo, cai para ~79 colunas em saída não-interativa e derruba
silenciosamente colunas de tabelas largas. As colunas novas desta spec ("retorno valid", "dd valid")
e até a coluna "parametros" sumiam da tabela de `optimize --validate` quando a saída era redirecionada
(exatamente o cenário de uso real, ex: `python main.py optimize --validate > log.txt`). Corrigido em
commit separado (`88586dc`), fora do fluxo normal de tasks.md por ter sido achado na validação final,
não numa rodada de review.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentação — não altera comportamento do bot.

- [x] T025 [P] Atualizar `ROADMAP.md` marcando Fase 2 itens 1 (split treino/teste no otimizador), 2
      (walk-forward validation) e 3 (análise Monte Carlo) como concluídos, com link para esta spec
- [x] T026 [P] Atualizar `specs/BACKLOG.md`: status da spec 003 para concluída
- [x] T027 Rodar `quickstart.md` (as três User Stories) manualmente contra dados reais da Binance
      (`optimize --validate`, `optimize --walk-forward`, `backtest --montecarlo`) e registrar
      resultado relevante em `STRATEGY_REVIEW.md`, seguindo o padrão já usado nas specs 001/002

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem tarefas.
- **Foundational (Phase 2)**: Sem tarefas — nada bloqueia US1; `robustness.py` nasce dentro de US2.
- **User Stories (Phase 3+)**:
  - US1 (P1) primeiro — é o MVP desta spec, resolve a causa raiz (overfitting no grid search).
  - US2 (P2) depende de US1 estar pronta o suficiente para produzir um candidato vencedor
    (`--walk-forward` implica `--validate`), mas o módulo `robustness.py` em si não depende de nada de
    US1 — só a integração via `optimizer.py` depende.
  - US3 (P3) é a mais independente das três: `monte_carlo_resample()` opera sobre qualquer lista de
    `Trade` já calculada, sem depender de US1/US2 nem de `optimizer.py`. Só a tarefa de dispatch no
    CLI (T024) depende de `robustness.py` já existir (criado em US2, T014).
- **Polish (Phase 6)**: Depende das User Stories que forem concluídas.

### User Story Dependencies

- **US1 (P1)**: Pode começar imediatamente. Sem dependência de US2/US3.
- **US2 (P2)**: Integração com `optimizer.py` (T016) depende de T009 (US1) existir — `run()` já
  precisa aceitar `validate`. O módulo `robustness.py`/`walk_forward_validate()` em si (T014, T015)
  não depende de nada de US1 e pode ser escrito em paralelo.
- **US3 (P3)**: Tecnicamente independente de US1/US2 (opera sobre `List[Trade]` genérico). T024
  depende de `robustness.py` existir (criado em T014, dentro de US2) — se US3 for implementada antes
  de US2, T014 precisa ser adiantada como pré-requisito informal.

### Within Each User Story

- Testes MUST ser escritos e falhar antes da implementação (constitution III).
- Dentro de US1: T005 antes de T006 (campos antes de popular); T006 antes de T007 (split antes de
  reavaliar candidatos); T007 antes de T008 (dados antes do print); T009 por último (CLI depende de
  tudo acima existir).
- Dentro de US2: T014 antes de T015 (split antes do backtest por janela); T015 antes de T016
  (função pronta antes de integrar ao optimizer); T016 antes de T017 (integração antes do print/CLI).
- Dentro de US3: T022 antes de T023 (cálculo antes do flag de confiança); T023 antes de T024
  (dados prontos antes do print/CLI).

### Parallel Opportunities

- T001, T002, T003, T004 (testes de US1) podem ser escritos em paralelo.
- T010, T011, T012, T013 (testes de US2) podem ser escritos em paralelo.
- T018, T019, T020, T021 (testes de US3) podem ser escritos em paralelo.
- T025, T026 (Polish) podem rodar em paralelo.
- Seguindo o Fluxo Incremental do `CLAUDE.md`, a prática real é sequencial, tópico por tópico, commit
  por commit — mesmo quando há oportunidade teórica de paralelismo.

---

## Implementation Strategy

### MVP First (User Story 1)

1. Completar Phase 1/2: Setup/Foundational — nenhuma tarefa.
2. Completar Phase 3: User Story 1 (split treino/validação no otimizador).
3. Validar US1 isoladamente (`quickstart.md` → US1) antes de seguir.

### Incremental Delivery

1. US1 → validar → é o MVP desta spec (resolve a causa raiz do overfitting no otimizador).
2. US2 → validar → confirma robustez em múltiplos regimes de mercado, não só um split.
3. US3 → validar → estima risco de sequência de perdas além do valor único já observado.
4. Polish → documentação (`ROADMAP.md`, `BACKLOG.md`, `STRATEGY_REVIEW.md`).

Cada etapa segue o Fluxo Incremental do `CLAUDE.md`: tarefa pequena → testes → commit Conventional
Commit em português → push para `origin/main` → próxima tarefa. Seguindo o padrão estabelecido nas
specs 001/002, `/code-review high` roda sobre o diff acumulado antes do commit final de cada etapa
significativa.

---

## Notes

- [P] = arquivos diferentes, sem dependência.
- [Story] mapeia a tarefa à User Story correspondente, para rastreabilidade.
- Verificar que os testes falham antes de implementar (constitution III).
- Commit após cada tarefa ou grupo lógico pequeno — nunca uma User Story inteira em um commit só.
- Nenhuma tarefa desta lista toca `risk/`, `execution/` ou `trading/position_lifecycle.py` — feature
  é só relatório/backtest/otimização, fora do escopo de `TRADING_MODE=live`.
