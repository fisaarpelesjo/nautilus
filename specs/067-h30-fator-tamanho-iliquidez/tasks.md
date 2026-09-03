---

description: "Task list for H30 fator de tamanho/iliquidez (spec 067)"
---

# Tasks: H30 — fator de tamanho/iliquidez (cross-sectional, sem timing)

**Input**: Design documents from `/specs/067-h30-fator-tamanho-iliquidez/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D5), quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Comparar cesta ilíquida vs. líquida em treino e validação (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [P] [US1] Testes em `tests/test_fator_tamanho.py`: seleção por menor/maior volume médio, simulação sem movimento de preço devolve capital intacto, custo cobrado no rebalanceamento, valorização de um ativo capturada, multiplicador de slippage maior reduz capital final, ausência de pares válidos devolve resultado neutro, `avaliar_fator_tamanho` aceita dados sem rede

### Implementation

- [X] T002 [US1] Criar `backtesting/fator_tamanho.py`: `selecionar_cesta`, `simular_cesta`, `avaliar_fator_tamanho`, D1-D5 declarados no docstring do módulo (depende de T001)
- [X] T003 [US1] Criar `cmd_fator_tamanho()` em `main.py`: roda `avaliar_fator_tamanho()`, imprime tabela comparativa (2 fatias × 2 critérios × 3 multiplicadores), exporta via `export_report`; registrar `"fator_tamanho": cmd_fator_tamanho` em `COMMANDS`; sincronizar `CLAUDE.md`/`AGENTS.md` (depende de T002)
- [X] T004 Rodar `python main.py fator_tamanho` contra dados reais
- [X] T005 Registrar o resultado real de T004 em `docs/research/registro-de-hipoteses.md` §6.1 (H30) — "Atualização — testada" no mesmo estilo das demais hipóteses desta rodada
- [X] T006 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T003 implementação e testes) + (T004-T006 execução real e registro).

---

## Implementation Strategy

T001-T003 (testes + módulo + comando CLI) → commit → push;
T004-T006 (execução real + registro + suite completa) → commit → push.
