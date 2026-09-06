---

description: "Task list for H39 PCA eigenportfolio (spec 075)"
---

# Tasks: H39 — Arbitragem estatística via PCA/eigenportfolio (Avellaneda-Lee)

**Input**: Design documents from `/specs/075-h39-pca-eigenportfolio/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D6), quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Veredito por ativo e agregado sobre o resíduo PCA/OU (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [P] [US1] Testes em `tests/test_pca_eigenportfolio.py`: PCA sobre matriz sintética com estrutura de fator conhecida recupera o número esperado de componentes (≥55% variância, teto 10); ajuste OU (`_ajustar_ou`) recupera média/sigma de uma série sintética AR(1) gerada com parâmetros conhecidos; série não-revertente (passeio aleatório) devolve `None`; filtro de meia-vida exclui ativo fora de `[2,120]` sem abortar os demais; `ResiduoStrategy`/`precompute_signals` geram BUY exatamente no cruzamento de entrada e SELL no de saída, HOLD fora deles; `teste_sanidade` devolve zero trades sobre s-score constante; `avaliar_universo` funciona com `fetch_ohlcv` mockado (sem rede)

### Implementation

- [X] T002 [US1] Criar `backtesting/pca_eigenportfolio.py`: docstring com D1-D6 declarados antes de medir; `_indice_comum`, `_componentes_pca` (PCA via `numpy.linalg.eigh`), `_ajustar_ou` (AR(1) via `numpy.linalg.lstsq`), `ResiduoStrategy` (`BaseStrategy`), `precompute_signals`, `gerar_resultado_par`, `teste_sanidade`, `avaliar_universo` (reusa `UNIVERSO_AMPLO_HISTORICO_COMPLETO`/`meia_vida_reversao` de `pairs_trading.py`, `split_train_validation` de `validation.py`, `rodar_bateria` de `bateria_hipotese.py`) (depende de T001)
- [X] T003 [US1] Criar `cmd_pca_eigenportfolio()` em `main.py`: roda `avaliar_universo()`, imprime por ativo (componentes, variância explicada, meia-vida, status E1-E6 ou motivo de exclusão) e um resumo agregado com a limitação de não-hedge (D6), exporta via `export_report`; registrar `"pcaeigen": cmd_pca_eigenportfolio` em `COMMANDS`; sincronizar `CLAUDE.md`/`AGENTS.md` (depende de T002)
- [ ] T004 Rodar `python main.py pcaeigen` contra dados reais
- [ ] T005 Registrar o resultado real de T004 em `docs/research/registro-de-hipoteses.md` §6.3 (H39) — comparação explícita com a literatura (FR-008) e a limitação de não-hedge (FR-006), "Atualização — testada" no mesmo estilo das demais hipóteses desta rodada
- [ ] T006 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T003 implementação e testes) + (T004-T006 execução real e registro).

---

## Implementation Strategy

T001-T003 (testes + módulo + comando CLI) → commit → push;
T004-T006 (execução real + registro + suite completa) → commit → push.
