---

description: "Task list for H20 reavaliada com historico estendido (spec 048)"
---

# Tasks: H20 reavaliada com histórico estendido

**Input**: Design documents from `/specs/048-h20-historico-estendido/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D3), data-model.md, quickstart.md

**Tests**: obrigatórios — Princípio III da constitution.
`tests/test_geometria.py` (extensão mínima).

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Reavaliar H20 com 6.000 candles (Priority: P1) 🎯 MVP

### Tests

- [X] T001 [US1] Teste em `tests/test_geometria.py`: `run_geometria_scan` chama `fetch_ohlcv` com `6000`, não `2000` (mock/spy sobre `fetch_ohlcv`)
- [X] T002 [P] [US1] Teste em `tests/test_geometria.py`: as constantes da regra de seleção (`ELEVACAO_H14`, `FOLGA`, `TETO_PCT_TEMPO`, `MIN_DESFECHOS`, `SL_FIXO`, `TPS_CANDIDATOS`) continuam idênticas às de spec 028 — regressão explícita (já coberto por `test_constantes_da_regra_sao_as_declaradas_em_d1`, pré-existente)

### Implementation

- [X] T003 [US1] Mudar `fetch_ohlcv(par, TIMEFRAME, 2000)` para `6000` em `backtesting/geometria.py::run_geometria_scan` (linha 204), comentário referenciando `specs/036-historico-estendido/research.md` D1 (depende de T001-T002)
- [X] T004 [US1] Criar `cmd_geometria()` em `main.py` (H20 nunca teve comando CLI): `run_geometria_scan()` + `run_modelo_scan`/`resumo_agregado` sobre a geometria selecionada, imprime perfis, razão pooled, `supera_empate` e comparação contra os números de 2.000 candles já publicados; registrar `"geometria": cmd_geometria` em `COMMANDS`; exportar via `export_report("geometria_estendida", ...)` (depende de T003)
- [X] T005 Rodar `python main.py geometria` contra dados reais (12 pares, VPS `vps-limulus`/`nautilus-research`) — resultado real
- [X] T006 Registrar o resultado real de T005 em `docs/research/registro-de-hipoteses.md` §4.16 (H20) — comparação explícita contra o já publicado (2.000 candles); atualizar §4.1 (quadro-resumo) e §6.1 (fila) se o veredito mudar; texto depende do resultado medido, não escrito antes de T005
- [X] T007 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão

**Checkpoint**: spec fechada em dois commits (T001-T004 implementação e testes) + (T005-T007 execução real e registro).

---

## Implementation Strategy

T001-T004 (testes + mudança de teto + CLI) → commit → push;
T005-T007 (execução real + registro + suite completa) → commit → push.
