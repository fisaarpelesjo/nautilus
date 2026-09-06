---

description: "Task list for H35 crowding long/short ratio e open interest (spec 071)"
---

# Tasks: H35 — Crowding via long/short ratio e open interest (Binance)

**Input**: Design documents from `/specs/071-h35-crowding-long-short/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D6), quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Veredito pooled sobre crowding via posicionamento (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [P] [US1] Teste em `tests/test_long_short_ratio.py`: `fetch_long_short_ratio_history`/`fetch_open_interest_history` devolvem DataFrame vazio (nunca lançam) para par sem mercado perpétuo, com `ccxt` mockado (sem rede)
- [X] T002 [P] [US1] Testes em `tests/test_crowding_extremo.py`: limiar de decil E mediana de open interest calibrados exclusivamente sobre a fatia de treino (não mudam se a validação mudar); alinhamento long/short-ratio→candle e open-interest→candle são forward-fill causal; candles anteriores ao início real do histórico de qualquer uma das duas séries são descartados, nunca preenchidos por ffill retroativo; evento só conta com AMBAS confirmações (ratio no decil E open interest acima da mediana) — falha de qualquer uma sozinha não conta; eventos são rotulados corretamente pela barreira tripla existente; `agregar_pooled` soma alvo/stop entre pares e delega a `supera_empate_com_confianca` sem reimplementar Wilson CI; par sem mercado perpétuo é excluído do universo, nunca contado como zero; sem eventos confirmados na validação, razão fica `inf`/indefinida sem quebrar

### Implementation

- [X] T003 [P] [US1] Criar `data/long_short_ratio.py`: `fetch_long_short_ratio_history`/`fetch_open_interest_history` via os métodos unificados ccxt (`fetch_long_short_ratio_history`/`fetch_open_interest_history`, mesma exchange futures de `data/funding.py`), devolvem DataFrame vazio para par sem mercado perpétuo (depende de T001)
- [X] T004 [US1] Criar `backtesting/crowding_extremo.py`: docstring com D1-D6 declarados antes de medir; `avaliar_par` (corta treino/validação dentro da retenção real do par, calibra decil de ratio + mediana de open interest só no treino, descarta candles anteriores ao início real de qualquer série, rotula pela barreira tripla), `avaliar_universo` (loop sobre `UNIVERSO_H11`), `agregar_pooled` (delega a `supera_empate_com_confianca`) (depende de T002, T003)
- [X] T005 [US1] Criar `cmd_crowding()` em `main.py`: roda sobre `UNIVERSO_H11`, imprime a retenção real medida por par e o resultado pooled, exporta via `export_report`; registrar `"crowding": cmd_crowding` em `COMMANDS`; sincronizar `CLAUDE.md`/`AGENTS.md` (depende de T004)
- [X] T006 Rodar `python main.py crowding` contra dados reais
- [X] T007 Registrar o resultado real de T006 em `docs/research/registro-de-hipoteses.md` §6.1 (H35) — incluir a retenção real medida (FR-002/SC-002), "Atualização — testada" no mesmo estilo das demais hipóteses desta rodada
- [X] T008 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T005 implementação e testes) + (T006-T008 execução real e registro).

---

## Implementation Strategy

T001-T005 (testes + fetcher + módulo de avaliação + comando CLI) → commit → push;
T006-T008 (execução real + registro + suite completa) → commit → push.
