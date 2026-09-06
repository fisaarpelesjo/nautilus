---

description: "Task list for H38 dvol gate precondicao (spec 074)"
---

# Tasks: H38 — Gate por volatilidade implícita (Deribit DVOL)

**Input**: Design documents from `/specs/074-h38-dvol-gate/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D5), quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Verificar se o DVOL discrimina eventos de entrada bons de ruins (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [P] [US1] Testes em `tests/test_dvol_gate.py`: `fetch_dvol_history` levanta exceção em falha HTTP (nunca sucesso silencioso), decil calibrado sobre a própria série de DVOL, alinhamento causal usa o valor de D-1 (nunca o dia corrente), evento sem DVOL alinhável é excluído da divisão (nunca presumido), `avaliar_precondicao_dvol` funciona com fetchers mockados (sem rede), par sem evento com DVOL alinhável é pulado sem abortar os demais

### Implementation

- [X] T002 [P] [US1] Criar `data/deribit.py`: `fetch_dvol_history(currency, dias, resolution)` via `get_volatility_index_data` (mesmo padrão de `data/onchain.py` — levanta exceção em falha, nunca DataFrame parcial como sucesso) (depende de T001)
- [X] T003 [US1] Criar `backtesting/dvol_gate.py`: docstring com D1-D5 declarados antes de medir; reconstrói a população "entrada primária" de H27 (mesmos blocos — `EmaRsiStrategy`, `precompute_signals`, `rotular`, `UNIVERSO_H11` — sem importar/alterar `meta_labeling.py`), divide por decil de DVOL (D3), `avaliar_precondicao_dvol()` chama `meta_labeling.avaliar_precondicao()` uma vez para reportar o número já publicado de H27 lado a lado (depende de T002)
- [X] T004 [US1] Criar `cmd_dvol_gate()` em `main.py`: roda `avaliar_precondicao_dvol()`, imprime os dois subgrupos e o veredito de precondição, exporta via `export_report`; registrar `"dvolgate": cmd_dvol_gate` em `COMMANDS`; sincronizar `CLAUDE.md`/`AGENTS.md` (depende de T003)
- [ ] T005 Rodar `python main.py dvolgate` contra dados reais
- [ ] T006 Registrar o resultado real de T005 em `docs/research/registro-de-hipoteses.md` §6.1 (H38) — comparação explícita com H27 (FR-009), "Atualização — testada" no mesmo estilo das demais hipóteses desta rodada
- [ ] T007 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T004 implementação e testes) + (T005-T007 execução real e registro).

---

## Implementation Strategy

T001-T004 (testes + fetcher + módulo de precondição + comando CLI) → commit → push;
T005-T007 (execução real + registro + suite completa) → commit → push.
