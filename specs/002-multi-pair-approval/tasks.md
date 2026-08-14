---

description: "Task list for 002-multi-pair-approval"
---

# Tasks: Decisão de Aprovação Multi-Par

**Input**: Design documents from `/specs/002-multi-pair-approval/`

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

Projeto único na raiz do repositório (mesmo da spec 001) — ver `plan.md` → Project Structure para o
mapeamento completo de módulos.

---

## Phase 1: Setup

**Purpose**: Nenhuma — ambiente (`.venv`, ruff, mypy, pytest, pre-commit, CI) já está configurado
pela spec `001-hardening-incremental` e não muda nesta feature. Fase mantida só por consistência com
o template; nenhuma tarefa nova.

**Checkpoint**: Ambiente já pronto (herdado da spec 001).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extrair o veredito de aprovação para um módulo compartilhado, sem mudar nenhum
comportamento observável — pré-requisito de US1 e US2 (US3 só depende de `edge_score` estar público,
que é tarefa de US1).

**⚠️ CRITICAL**: Nenhuma tarefa de US1/US2 deve começar antes de T002 (extração de `approval.py`)
estar concluída.

- [ ] T001 [P] Teste: mover os testes de veredito puro (não relacionados a split treino/validação —
      `evaluate_validation`/`ValidationVerdict` sobre um `BacktestResult` isolado) de
      `tests/test_backtesting_validation.py` para novo `tests/test_backtesting_approval.py`,
      importando de `backtesting.approval` (ainda não existe — teste deve falhar por
      `ModuleNotFoundError` antes de T002)
- [ ] T002 Extrair `ValidationVerdict`/`evaluate_validation()` de `backtesting/validation.py` para
      novo `backtesting/approval.py`, renomeados para `ApprovalVerdict`/`evaluate_approval()`
      (mesma assinatura/comportamento — puro refactor). `validation.py` importa e reexporta
      `ValidationVerdict = ApprovalVerdict`, `evaluate_validation = evaluate_approval` (depende de
      T001 falhando)
- [ ] T003 [P] `EDGE_MIN_TRADES` em `config/settings.py` (default `10`, mesmo valor hoje hardcoded em
      `MIN_TRADES_FOR_APPROVAL`), validação em `validate_config()`; `evaluate_approval()` usa como
      default do parâmetro `min_trades` no lugar da constante de módulo
- [ ] T004 Confirmar que `tests/test_backtesting_validation.py` (testes de split/orquestração
      out-of-sample que continuam lá) e `python main.py backtest --validate` continuam com
      comportamento idêntico após T002/T003 — rodar a suíte completa e comparar a saída manual do
      comando contra a spec 001 (depende de T002, T003)

**Checkpoint**: `backtesting/approval.py` existe e é a fonte única do veredito; nenhuma mudança de
comportamento observável em `backtest --validate`.

---

## Phase 3: User Story 1 - Ver de relance em quais pares a estratégia tem vantagem real (Priority: P1) 🎯 MVP

**Goal**: `multibacktest` e `scan` mostram veredito (aprovado/reprovado/inconclusivo) + motivo por
par, ordenados por qualidade (`edge_score`), com pares que falharam marcados em vez de somem.

**Independent Test**: Ver `quickstart.md` → US1.

### Tests for User Story 1 ⚠️

- [ ] T005 [P] [US1] Teste: `evaluate_approval()` aplicado a um `BacktestResult` de janela única
      (sem split treino/validação) produz veredito coerente com os mesmos critérios já usados em
      `backtest --validate` — em `tests/test_backtesting_approval.py`
- [ ] T006 [P] [US1] Teste: `MultiResult` ganha campos `profit_factor`, `buy_hold_return_pct`,
      `edge_score`, `verdict` populados a partir do `BacktestResult` subjacente — em novo
      `tests/test_multi_backtest.py`
- [ ] T007 [P] [US1] Teste: resultados de `run_all()` vêm ordenados por `edge_score` decrescente
      dentro de cada timeframe, com desempate por `profit_factor` e depois por número de trades — em
      `tests/test_multi_backtest.py`
- [ ] T008 [P] [US1] Teste: um par que lança exceção durante `run_all()` aparece como linha de erro
      (`pair` + mensagem), não desaparece silenciosamente da lista de resultados — em
      `tests/test_multi_backtest.py`
- [ ] T009 [P] [US1] Teste: `ScanResult` ganha os mesmos campos de veredito/`edge_score`; `run_scan()`
      ordena por `edge_score` em vez do `.score` ad hoc atual — em novo `tests/test_scanner.py`
- [ ] T010 [P] [US1] Teste: par com erro em `run_scan()` aparece marcado, não desaparece — em
      `tests/test_scanner.py`

### Implementation for User Story 1

- [ ] T011 [US1] Tornar `_edge_score` público (`edge_score`) em `backtesting/engine.py`, sem alterar
      a fórmula (depende de T005 falhando)
- [ ] T012 [US1] `MultiResult` (`backtesting/multi.py`) ganha campos `profit_factor`,
      `buy_hold_return_pct`, `edge_score`, `verdict: Optional[ApprovalVerdict]`; `run_all()` popula
      via `evaluate_approval()` a partir do `BacktestResult` de cada par (depende de T002, T006, T011)
- [ ] T013 [US1] `run_all()` captura exceção por par como uma entrada de erro separada (`pair`,
      `error`) em vez de só logar e pular (depende de T008, T012)
- [ ] T014 [US1] `print_results()` exibe coluna de veredito, ordena cada grupo de timeframe por
      `edge_score` desc (desempate `profit_factor`, depois trades), e exibe a(s) linha(s) de erro de
      forma visualmente distinta (depende de T007, T012, T013)
- [ ] T015 [US1] Mesmo tratamento em `backtesting/scanner.py`: `ScanResult` ganha os campos novos,
      `run_scan()` popula via `evaluate_approval()`, captura erro como entrada própria (depende de
      T002, T009, T011)
- [ ] T016 [US1] `run_scan()`/ordenação trocam o `.score` ad hoc pelo `edge_score` compartilhado;
      `print_scan()` exibe veredito e linha de erro (depende de T010, T015)

**Checkpoint**: US1 completa e testável de forma independente — `multibacktest`/`scan` mostram
veredito e ranking por qualidade.

---

## Phase 4: User Story 2 - Entender por que um par foi reprovado sem interpretar números na mão (Priority: P2)

**Goal**: `python main.py edge` (hoje idêntico a `backtest`) passa a mostrar veredito, motivos e
diagnóstico "perfil defensivo" quando aplicável.

**Independent Test**: Ver `quickstart.md` → US2.

### Tests for User Story 2 ⚠️

- [ ] T017 [P] [US2] Teste: `diagnose_profile()` retorna "perfil defensivo" só quando drawdown ≤
      limiar aceitável, expectativa positiva e retorno abaixo do buy-and-hold; retorna `None` nos
      demais casos de reprovação — em `tests/test_backtesting_approval.py`
- [ ] T018 [P] [US2] Teste: nova função de relatório de edge roda um backtest de janela única (sem
      split) e retorna o resultado + veredito calculado sobre ele — em
      `tests/test_backtesting_engine.py`
- [ ] T019 [P] [US2] Teste: `cmd_edge` (`main.py`) chama a nova função de relatório de edge, não
      `run_backtest()` — dispatch diferente de `cmd_backtest`, hoje idênticos — em
      `tests/test_main_backtest.py`

### Implementation for User Story 2

- [ ] T020 [US2] `diagnose_profile(result: BacktestResult) -> Optional[str]` em
      `backtesting/approval.py`, reusando os limiares já definidos em `evaluate_approval()` (depende
      de T017 falhando, T002)
- [ ] T021 [US2] `run_edge_report(symbol, timeframe)` em `backtesting/engine.py`: roda backtest de
      janela única, calcula veredito via `evaluate_approval()`, imprime o relatório existente seguido
      da seção de veredito/motivos/diagnóstico (depende de T018 falhando, T020)
- [ ] T022 [US2] `cmd_edge` em `main.py` passa a chamar `run_edge_report(SYMBOL, TIMEFRAME)` em vez de
      `run_backtest(SYMBOL, TIMEFRAME)` (depende de T019 falhando, T021)

**Checkpoint**: US1 e US2 funcionam de forma independente uma da outra.

---

## Phase 5: User Story 3 - Comparar `edge_score` entre pares numa escala legível (Priority: P3)

**Goal**: `edge_score` vem acompanhado de uma faixa legível (Forte/Médio/Fraco/Reprovado) em
`edge`, `multibacktest` e `scan`.

**Independent Test**: Ver `quickstart.md` → US3.

### Tests for User Story 3 ⚠️

- [ ] T023 [P] [US3] Teste: `edge_score_band()` retorna Forte/Médio/Fraco/Reprovado nos limiares
      documentados em `research.md`, incluindo valores exatamente nas fronteiras (ex: `20`, `0`,
      `-20`) — em `tests/test_backtesting_engine.py`

### Implementation for User Story 3

- [ ] T024 [US3] `edge_score_band(score: float) -> str` em `backtesting/engine.py`, limiares
      documentados no docstring (depende de T023 falhando, T011)
- [ ] T025 [US3] Exibir a faixa junto do `edge_score` em `run_edge_report()` (edge), `print_results()`
      (multibacktest) e `print_scan()` (scan) (depende de T024, T014, T016, T021)

**Checkpoint**: US1, US2 e US3 funcionam de forma independente.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentação — não altera comportamento do bot.

- [ ] T026 [P] Atualizar `ROADMAP.md` marcando os itens de ranking de pares, edge por par/timeframe,
      diagnóstico defensivo/agressivo e faixas de `edge_score` (Fase 1 item 3, Fase 1.1 itens 1-8)
      como concluídos, com link para esta spec
- [ ] T027 [P] Atualizar `specs/BACKLOG.md`: status da spec 002 para concluída
- [ ] T028 Rodar `quickstart.md` (as três User Stories) manualmente contra dados reais da Binance
      (`multibacktest`, `scan`, `edge`) e registrar o resultado em `STRATEGY_REVIEW.md`, seguindo o
      mesmo padrão já usado para T035 da spec 001

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem tarefas — ambiente já pronto.
- **Foundational (Phase 2)**: Depende de Setup — BLOQUEIA US1 e US2 (US3 só depende de T011, dentro
  de US1).
- **User Stories (Phase 3+)**: Todas dependem de Foundational completa.
  - US1 (P1) primeiro — é o MVP desta spec, resolve a limitação de amostra pequena da spec 001.
  - US2 (P2) depende de Foundational, não de US1 (usa `backtesting/approval.py` e `engine.py`
    diretamente).
  - US3 (P3) depende de `edge_score` estar público (T011, dentro de US1) e de `run_edge_report`
    existir (T021, dentro de US2) para T025 — não pode começar antes das duas.
- **Polish (Phase 6)**: Depende das User Stories que forem concluídas.

### User Story Dependencies

- **US1 (P1)**: Pode começar após Foundational. Sem dependência de US2/US3.
- **US2 (P2)**: Pode começar após Foundational. Sem dependência de US1 (arquivos diferentes:
  `main.py`/`engine.py` vs `multi.py`/`scanner.py`).
- **US3 (P3)**: Depende de T011 (US1) e T021 (US2) já existirem — não é totalmente independente das
  outras duas, ao contrário do padrão usual da spec 001. É a única exceção: T024
  (`edge_score_band`) pode ser escrita e testada isoladamente, mas T025 (exibir a faixa nos três
  relatórios) precisa que os três relatórios já existam.

### Within Each User Story

- Testes MUST ser escritos e falhar antes da implementação (constitution III).
- Dentro de US1: T011 (edge_score público) antes de T012/T015 (que o consomem); T012/T013 antes de
  T014 (print depende dos dados populados); mesmo padrão em T015/T016 para o scanner.
- Dentro de US2: T020 antes de T021 (relatório usa o diagnóstico); T021 antes de T022 (CLI chama a
  função do relatório).

### Parallel Opportunities

- T001, T003 (Foundational) podem ser feitas em paralelo — arquivos diferentes.
- T005, T006, T007, T008, T009, T010 (testes de US1) podem ser escritos em paralelo.
- T017, T018, T019 (testes de US2) podem ser escritos em paralelo.
- T026, T027 (Polish) podem rodar em paralelo.
- Seguindo o Fluxo Incremental do `CLAUDE.md`, a prática real é sequencial, tópico por tópico, commit
  por commit — mesmo quando há oportunidade teórica de paralelismo.

---

## Implementation Strategy

### MVP First (User Story 1)

1. Completar Phase 1: Setup — nenhuma tarefa (ambiente já pronto).
2. Completar Phase 2: Foundational (extração de `backtesting/approval.py`).
3. Completar Phase 3: User Story 1 (veredito + ranking em `multibacktest`/`scan`).
4. Validar US1 isoladamente (`quickstart.md` → US1) antes de seguir.

### Incremental Delivery

1. Foundational → base pronta, sem mudança de comportamento observável.
2. US1 → validar → é o MVP desta spec (resolve a limitação de amostra pequena que a spec 001
   esbarrou).
3. US2 → validar → `edge` deixa de ser um alias de `backtest`.
4. US3 → validar → `edge_score` fica interpretável numa faixa, não só um número.
5. Polish → documentação (`ROADMAP.md`, `BACKLOG.md`, `STRATEGY_REVIEW.md`).

Cada etapa segue o Fluxo Incremental do `CLAUDE.md`: tarefa pequena → testes → commit Conventional
Commit em português → push para `origin/main` → próxima tarefa. Seguindo o padrão estabelecido na
spec 001, `/code-review high` roda sobre o diff acumulado de cada User Story antes do commit final
dela.

---

## Notes

- [P] = arquivos diferentes, sem dependência.
- [Story] mapeia a tarefa à User Story correspondente, para rastreabilidade.
- Verificar que os testes falham antes de implementar (constitution III) — exceto T001/T004
  (Foundational), que são refactor puro sem mudança de comportamento esperada.
- Commit após cada tarefa ou grupo lógico pequeno — nunca uma User Story inteira em um commit só.
- Nenhuma tarefa desta lista toca `risk/`, `execution/` ou `trading/position_lifecycle.py` — feature
  é só relatório/backtest, fora do escopo de `TRADING_MODE=live`.
