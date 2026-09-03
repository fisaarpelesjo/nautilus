---

description: "Task list for H14 saida por barreira tripla (spec 056)"
---

# Tasks: H14 — saída por barreira tripla em vez de trailing stop

**Input**: Design documents from `/specs/056-h14-saida-barreira/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D4), quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Medir o profit factor sob saída por barreira (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [P] [US1] Teste em `tests/test_portfolio_h14.py`: posição fecha no candle exato em que `velas_decorridas` atinge `limite_velas`, sem tocar alvo/stop, motivo "Limite de tempo (barreira)"
- [X] T002 [P] [US1] Teste: sob `usar_saida_barreira=True`, o stop NÃO sobe quando o preço faz novo máximo (regressão invertida de `test_stop_trailing_sobe_e_dispara`)
- [X] T003 [P] [US1] Teste: barreiras fixas (alvo/stop) ainda disparam normalmente antes do limite de velas sob o novo modo
- [X] T004 [P] [US1] Teste: `usar_saida_barreira=False` (default, omitido) reproduz o comportamento trailing existente sem mudança

### Implementation

- [X] T005 [US1] `PosicaoCarteira` ganha `velas_decorridas: int = 0` (`backtesting/portfolio_h14.py`, depende de T001-T004)
- [X] T006 [US1] `_simular_carteira_core`/`simular_carteira` ganham `usar_saida_barreira: bool = False` + `limite_velas: int = LIMITE_VELAS_PADRAO`; laço de fechamento pula trailing e fecha por tempo sob o novo modo (depende de T005)
- [X] T007 [US1] Criar `cmd_carteira_barreira()` em `main.py`: chama `simular_carteira(usar_saida_barreira=True)` sobre `UNIVERSO_H11`, imprime resultado ao lado do já publicado (spec 037), exporta via `export_report`; registrar `"carteira_barreira": cmd_carteira_barreira` em `COMMANDS` (depende de T006)
- [X] T008 Rodar `python main.py carteira_barreira` contra dados reais (VPS `vps-limulus`/`nautilus-research`)
- [X] T009 Registrar o resultado real de T008 em `docs/research/registro-de-hipoteses.md` §4.15 (H14) — nova "Atualização" após spec 055, confirma ou refuta o descasamento de saída
- [X] T010 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T007 implementação e testes) + (T008-T010 execução real e registro).

---

## Implementation Strategy

T001-T007 (testes + mecânica + comando CLI) → commit → push;
T008-T010 (execução real + registro + suite completa) → commit → push.
