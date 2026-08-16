---

description: "Task list for 009-itens-remanescentes-roadmap"
---

# Tasks: Itens Remanescentes do ROADMAP

**Input**: Design documents from `/specs/009-itens-remanescentes-roadmap/`

**Tests**: Incluídos — mesmo rigor test-first das specs anteriores (constitution III).

---

## Phase 1: User Story 1 - Exportação de relatórios (Priority: P1) 🎯 MVP

- [ ] T001 [P] [US1] Teste: `export_report(name, params, result)` gera 3 arquivos
      (`.json`/`.csv`/`.md`) em `reports/` com timestamp no nome — novo `tests/test_report_export.py`
- [ ] T002 [P] [US1] Teste: `export_report` cria `reports/` se não existir — `tests/test_report_export.py`
- [ ] T003 [P] [US1] Teste: duas chamadas seguidas produzem arquivos distintos (timestamps
      diferentes), sem sobrescrever — `tests/test_report_export.py`
- [ ] T004 [US1] Novo `utils/report_export.py`: `export_report(name, params, result,
      ranking=None)` — `dataclasses.asdict(result)`, `Path("reports").mkdir(parents=True,
      exist_ok=True)`, escreve JSON/CSV/Markdown (depende de T001 falhando, T002 falhando, T003
      falhando)
- [ ] T005 [US1] `main.py`: `cmd_backtest`/`cmd_scan`/`cmd_multibacktest`/`cmd_otimizar` chamam
      `export_report()` com params relevantes após a execução (depende de T004)

**Checkpoint**: US1 completa — MVP desta spec.

---

## Phase 2: User Story 2 - Diagnóstico agressivo (Priority: P2)

- [ ] T006 [P] [US2] Teste: `diagnose_profile()` com drawdown alto e retorno bem acima do
      buy-hold retorna diagnóstico de perfil agressivo — `tests/test_backtesting_approval.py`
      (arquivo já existente)
- [ ] T007 [P] [US2] Teste: `diagnose_profile()` com resultado nem defensivo nem agressivo continua
      retornando `None` — `tests/test_backtesting_approval.py`
- [ ] T008 [US2] `backtesting/approval.py` `diagnose_profile()`: adiciona checagem de perfil
      agressivo (depende de T006 falhando, T007 falhando)

**Checkpoint**: US1 e US2 completas.

---

## Phase 3: User Story 3 - Out-of-sample no edge (Priority: P3)

- [ ] T009 [P] [US3] Teste: `run_edge_report(..., validate=True)` retorna treino + validação +
      veredito calculado sobre a validação — novo teste em `tests/test_backtesting_validation.py`
      (arquivo já existente)
- [ ] T010 [P] [US3] Teste: `run_edge_report(..., validate=False)` (default) mantém o
      comportamento já existente — `tests/test_backtesting_validation.py`
- [ ] T011 [US3] `backtesting/validation.py` `run_edge_report()`: parâmetro `validate: bool =
      False`, reusa `split_train_validation`/`simulate_backtest` quando `True` (depende de T009
      falhando, T010 falhando)
- [ ] T012 [US3] `main.py` `cmd_edge()`: lê `--validate` de `sys.argv`, mesmo padrão já usado por
      `cmd_backtest`/`cmd_otimizar` (depende de T011)

**Checkpoint**: US1-US3 completas.

---

## Phase 4: User Story 4 - Indicadores médios por decisão (Priority: P4)

- [ ] T013 [P] [US4] Teste: `DecisionRecord` inclui `rsi`; linhas sem RSI não quebram o parsing —
      novo teste em `tests/test_decisions_analysis.py` (arquivo já existente)
- [ ] T014 [P] [US4] Teste: `analyze_decisions()` calcula RSI médio por sinal corretamente com
      fixture sintética — `tests/test_decisions_analysis.py`
- [ ] T015 [US4] `data/decisions_analysis.py`: `DecisionRecord.rsi`, `_load_decisions()` popula o
      campo, `analyze_decisions()` calcula `avg_indicators_by_signal` (depende de T013 falhando,
      T014 falhando)
- [ ] T016 [US4] `print_decisions_analysis()`: exibe a nova seção de indicadores médios por sinal
      (depende de T015)

**Checkpoint**: Todas as 4 User Stories completas.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [ ] T017 [P] Atualizar `ROADMAP.md`: Fase 1 item 4, Fase 1.1 item 4 (parcial → completo), Fase
      1.1 item 7, Fase 3 item 4 (parcial → completo)
- [ ] T018 [P] Atualizar `specs/BACKLOG.md` com a spec 009
- [ ] T019 Sincronizar `CLAUDE.md`/`AGENTS.md` com `reports/`, `edge --validate`, indicadores
      médios por decisão
- [ ] T020 Adicionar `reports/` ao `.gitignore` (artefato de runtime, mesmo padrão de
      `data/trades.csv` etc.)

---

## Dependencies & Execution Order

Todas as 4 User Stories são independentes entre si — nenhuma depende de outra. Podem ser
implementadas em qualquer ordem; a numeração de prioridade (P1-P4) reflete valor, não dependência
técnica.

## Notes

- Toda a spec é read-only/informativa — nenhuma tarefa toca `execution/`, `risk/manager.py` ou o
  loop principal do bot.
