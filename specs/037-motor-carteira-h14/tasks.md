---

description: "Task list for motor de carteira para aprovacao de H14 (spec 037)"
---

# Tasks: Motor de carteira para aprovação de H14

**Input**: Design documents from `/specs/037-motor-carteira-h14/`

**Prerequisites**: plan.md, spec.md, data-model.md, research.md, quickstart.md

**Tests**: obrigatórios — Princípio III da constitution. `tests/test_modelo.py`
(extensão) e `tests/test_portfolio_h14.py` (novo).

**Organization**: Foundational (D2, extensão de `avaliar_par`) bloqueia
tudo o resto — o motor de carteira não tem de onde tirar a previsão
candle a candle sem ela. US1 (mecânica de carteira) e US2 (buy-hold +
aprovação) são P1 porque juntas respondem a pergunta da spec; US3
(comparação lado a lado) é P2, valor incremental sobre o que US1+US2 já
produzem.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

Nenhuma — sem dependência nova.

---

## Phase 2: Foundational — expor a previsão de teste de `avaliar_par` (D2)

**Goal**: `avaliar_par(par, ..., retornar_previsao=True)` devolve
`AvaliacaoH14.previsao_teste`, sem mudar nada no caminho default.

**Blocks**: US1, US2, US3 (nenhuma consegue simular carteira sem a
previsão candle a candle).

### Tests for Foundational

- [X] T001 [P] Teste em `tests/test_modelo.py`: `avaliar_par(df=..., retornar_previsao=True)` devolve `previsao_teste` como `pd.Series` indexada pelo timestamp da janela de teste, com valores idênticos aos já calculados internamente por `prever()` sobre os mesmos dados
- [X] T002 [P] Teste de regressão em `tests/test_modelo.py`: `avaliar_par(df=..., retornar_previsao=False)` (default) devolve `previsao_teste=None` e reproduz exatamente os valores de referência já capturados por `test_avaliar_par_sem_parametros_novos_reproduz_resultado_atual` — zero mudança no caminho existente

### Implementation for Foundational

- [X] T003 [US1] Adicionar `retornar_previsao: bool = False` a `avaliar_par` e o campo `previsao_teste: Optional[pd.Series] = None` a `AvaliacaoH14`, em `backtesting/modelo.py` — populado só quando `retornar_previsao=True`, reusando a chamada de `prever()` já feita internamente (D2) (depende de T001-T002)

**Checkpoint**: `pytest tests/test_modelo.py -v` — T001-T002 passam, 0
regressão nos testes já existentes.

---

## Phase 3: User Story 1 - Simular os 12 pares com capital compartilhado (Priority: P1) 🎯 MVP

**Goal**: `simular_carteira(pares, capital_inicial)` produz um
`BacktestResult` com uma única curva de capital, caixa compartilhado,
teto `MAX_POSITIONS`, saída só por take-profit ATR + stop trailing (D7,
mesmo mecanismo do backtest publicado de H14).

**Independent Test**: rodar `simular_carteira` sobre um conjunto sintético
de poucos pares/candles determinístico e confirmar que nunca há mais
posições simultâneas que `MAX_POSITIONS`, nem caixa negativo.

### Tests for User Story 1

- [X] T004 [P] [US1] Teste em `tests/test_portfolio_h14.py`: caixa nunca fica negativo — uma posição só abre se `caixa >= tamanho_calculado` (FR-004/FR-011)
- [X] T005 [P] [US1] Teste: número de posições simultâneas nunca excede `MAX_POSITIONS`, mesmo com mais pares sinalizando compra que slots livres (FR-006)
- [X] T006 [P] [US1] Teste **crítico**: dois pares sinalizam compra no mesmo candle com só 1 slot livre — abre o par de maior `previsao_teste` naquele candle, nunca o outro (D4/FR-011)
- [X] T007 [P] [US1] Teste: posição fecha exatamente quando o preço toca o take-profit por ATR (`entrada + ATR_TP_MULTIPLIER×entry_atr`) ou o stop trailing (`_stop_price`, só sobe com novo máximo) — mesmo mecanismo já usado pelo backtest publicado de H14, D7, sem barreira de tempo nem mecanismo novo (FR-003)
- [X] T008 [P] [US1] Teste: posição aberta no candle final do histórico fecha a mercado com `exit_reason="Fim do periodo"` (mesmo rótulo do motor genérico, `_close_trade`)
- [X] T009 [P] [US1] Teste: o `BacktestResult` retornado por `simular_carteira` é aceito por `evaluate_approval()` sem exceção, produzindo um `ApprovalVerdict` válido

### Implementation for User Story 1

- [X] T010 [US1] Implementar `CarteiraH14`/`PosicaoCarteira` (dataclasses, `data-model.md`) em `backtesting/portfolio_h14.py`
- [X] T011 [US1] Implementar `simular_carteira(pares=UNIVERSO_H11, capital_inicial=1000.0) -> BacktestResult` em `backtesting/portfolio_h14.py`: chama `run_modelo_scan(..., retornar_previsao=True)`, une timelines (D3), avança candle a candle fechando por take-profit ATR/stop trailing (D7, reusa `_take_profit_price`/`_stop_price`/`_close_trade` de `backtesting/engine.py`) antes de abrir novas posições, dimensiona via `min(MAX_ORDER_SIZE_USDT, (caixa/slots_livres_restantes)*0.95)` com desempate por `previsao_teste` (D4), monta `Trade`s e `_calculate_advanced_metrics` (D6) (depende de T004-T009)

**Checkpoint**: `pytest tests/test_portfolio_h14.py -v` — T004-T009 passam.
MVP completo: a carteira simula com risco compartilhado de verdade.

---

## Phase 4: User Story 2 - Decidir aprovação sobre o resultado agregado (Priority: P1)

**Goal**: o `BacktestResult` de `simular_carteira` carrega um
`buy_hold_return_pct` de carteira igualmente ponderada (D5), e
`evaluate_approval()` decide sobre ele sem critério novo.

**Independent Test**: comparar `buy_hold_return_pct` do resultado contra
um cálculo manual de carteira igualmente ponderada sobre o mesmo período.

### Tests for User Story 2

- [X] T012 [P] [US2] Teste em `tests/test_portfolio_h14.py`: `buy_hold_return_pct` reflete uma carteira igualmente ponderada nos pares simulados (D5) — não a média dos buy-holds individuais, não zero
- [X] T013 [P] [US2] Teste: `evaluate_approval()` sobre o `BacktestResult` real produz veredito em `{"aprovado","reprovado","inconclusivo"}` usando os mesmos limiares já existentes, sem parâmetro novo

### Implementation for User Story 2

- [X] T014 [US2] Implementar o cálculo de `buy_hold_return_pct` de carteira (D5) dentro de `simular_carteira` — capital inicial dividido igualmente entre os pares no primeiro candle da janela, sem rebalanceamento (depende de T012-T013)

**Checkpoint**: US1+US2 juntas respondem a pergunta central da spec —
veredito de aprovação sobre risco de carteira real.

---

## Phase 5: User Story 3 - Comparar drawdown de carteira contra drawdown por par isolado (Priority: P2)

**Goal**: o drawdown agregado e o maior drawdown por par isolado (já
registrado em H14) aparecem juntos, explicitamente rotulados.

**Independent Test**: chamar a função de comparação com um
`BacktestResult` de carteira e uma lista de `AvaliacaoH14` e confirmar que
os dois números retornam separados, nunca um substituindo o outro.

### Tests for User Story 3

- [X] T015 [P] [US3] Teste em `tests/test_portfolio_h14.py`: função de comparação devolve `(drawdown_carteira, maior_drawdown_por_par)` como uma tupla/dict explícito — nunca um único número combinado

### Implementation for User Story 3

- [X] T016 [US3] Implementar a função de comparação em `backtesting/portfolio_h14.py` (depende de T015)

**Checkpoint**: as três user stories passam juntas.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T017 Criar `cmd_carteira()` em `main.py`: chama `simular_carteira()`, imprime a curva de capital agregada (patrimônio final, retorno, drawdown, buy-hold, profit factor), o veredito de `evaluate_approval()`, e a comparação de T016; registrar `"carteira": cmd_carteira` em `COMMANDS`; exportar via `export_report("carteira", ...)`
- [ ] T018 Rodar `python main.py carteira` contra dados reais (`UNIVERSO_H11`) — validação manual do passo 2 do `quickstart.md`, resultado real
- [ ] T019 Registrar o resultado real de T018 em `docs/research/registro-de-hipoteses.md` §4.15 (H14) — a última barra de aprovação que faltava desde spec 036; texto depende do resultado medido, não escrito antes de T018
- [ ] T020 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão em `backtesting/engine.py`/`backtesting/approval.py` (intocados, D6)

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: N/A
- **Foundational (Phase 2)**: sem dependência — bloqueia Phase 3-5
- **US1 (Phase 3)**: depende de Phase 2 (T003)
- **US2 (Phase 4)**: depende de Phase 3 (T011 — `simular_carteira` já precisa existir para carregar o buy-hold)
- **US3 (Phase 5)**: depende de Phase 3 (T011, drawdown de carteira) e do drawdown por par já disponível em `AvaliacaoH14`/H14
- **Polish (Phase 6)**: depende de Phase 3+4+5 completas — T019 depende do resultado real de T018

### Parallel Opportunities

- T001-T002 (Foundational, testes) em paralelo
- T004-T009 (US1, testes, cenários independentes) em paralelo
- T012-T013 (US2, testes) em paralelo, após T011
- T015 (US3, teste) pode ser escrito em paralelo com T012-T013

---

## Implementation Strategy

### MVP = Phase 2 + Phase 3 (Foundational + US1)

Dois commits pequenos: Foundational (T001-T003, extensão de `modelo.py`,
menor risco, isolado) → commit → push; depois US1 (T004-T011, o motor de
carteira em si, maior risco de acerto de mecânica) → commit → push. É a
mudança que já produz um drawdown agregado real, mesmo antes do veredito
formal de aprovação (US2).

### Incremental Delivery

1. Phase 2 (Foundational) → `avaliar_par` expõe a previsão, sem mudar
   comportamento default
2. Phase 3 (US1) → motor de carteira completo, drawdown agregado real
3. Phase 4 (US2) → buy-hold de carteira + veredito de aprovação
4. Phase 5 (US3) → comparação lado a lado, drawdown de carteira vs por par
5. Phase 6 (Polish) → comando CLI, execução real, veredito registrado no
   registro-mestre, suite completa

Fluxo Incremental do `CLAUDE.md`: Phase 2 é um commit; Phase 3 é outro
(maior, o motor em si); Phase 4+5+6 podem ir num terceiro commit, dado que
nenhuma delas muda a mecânica central, só completa a resposta e a
publica.
