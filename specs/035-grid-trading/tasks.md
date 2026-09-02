---

description: "Task list for H18 -- grid trading com gestao de cauda (spec 035)"
---

# Tasks: H18 — Grid trading com gestão de cauda

**Input**: Design documents from `/specs/035-grid-trading/`

**Prerequisites**: plan.md, spec.md, data-model.md, research.md, quickstart.md

**Tests**: obrigatórios — Princípio III da constitution. `tests/test_grid.py`
(novo).

**Organization**: US1 (reuso do motor de métricas) e US2 (gestão de
cauda) são a **mesma** função (`simular_grade`) — spec.md já declara que
são inseparáveis: medir sem a gestão de cauda reproduziria exatamente o
grid "sem controle" que a objeção original de H18 já julgava reprovável,
sem acrescentar nada. US3 (custo) é uma propriedade da mesma
implementação.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

Nenhuma — sem dependência nova.

---

## Phase 2: User Story 1 + User Story 2 - Grade com gestão de cauda, motor existente (Priority: P1) 🎯 MVP

**Goal**: `simular_grade(df, params)` produz um `BacktestResult` compatível
com `evaluate_approval()`, com a grade ativa só em regime `"sideways"` e
liquidação total ao `close` quando o regime vira `"trending"`.

**Independent Test**: rodar `simular_grade` sobre um `df` sintético
determinístico com uma transição de regime conhecida, e confirmar
preenchimentos, liquidação forçada e o `BacktestResult` resultante.

### Tests for User Story 1 + 2

> **NOTE**: escrever os testes primeiro — `backtesting/grid.py` ainda não
> existe.

- [X] T001 [P] [US1] Teste em `tests/test_grid.py`: nível vazio preenche compra quando `low` do candle `<= preco_compra` do nível — `preco_entrada_ajustado` reflete o slippage (D3)
- [X] T002 [P] [US1] Teste: nível ocupado preenche venda quando `high` do candle `>= preco_venda` (nível seguinte acima) — gera `Trade` com `exit_reason="grid"`, `pnl` positivo antes de custo igual ao espaçamento entre níveis
- [X] T003 [P] [US1] Teste: num candle em que uma venda **e** uma compra ocorreriam, a venda é processada primeiro — o capital liberado por ela está disponível para a compra no mesmo candle (D3, ordem declarada)
- [X] T004 [P] [US2] Teste: com regime `"trending"` ou `"indefinido"` em todos os candles, a grade nunca abre — zero `Trade`s (FR-002/FR-008)
- [X] T005 [P] [US2] Teste **crítico**: grade ativa com 2+ níveis ocupados; regime do candle seguinte é `"trending"` — todos os níveis liquidam nesse mesmo candle, ao `close`, com `exit_reason="regime mudou para trending"` (FR-003/D4)
- [X] T006 [P] [US2] Teste: após a liquidação forçada de T005, quando o regime volta a `"sideways"` num candle posterior, uma grade nova abre com `bb_lower`/`bb_upper` **desse** candle, não os antigos (D5)
- [X] T007 [P] [US1] Teste: o `BacktestResult` retornado por `simular_grade` é aceito por `evaluate_approval()` sem exceção, produzindo um `ApprovalVerdict` válido (`status` em `{"aprovado","reprovado","inconclusivo"}`)

### Implementation for User Story 1 + 2

- [X] T008 [US1][US2] Implementar `ParametrosGrade` (`n_niveis=10`, `capital_inicial=1000.0`) e `NivelGrade` (dataclasses, `data-model.md`) em `backtesting/grid.py`
- [X] T009 [US1][US2] Implementar `simular_grade(df: pd.DataFrame, params: Optional[ParametrosGrade] = None, fee_rate=BACKTEST_FEE_RATE, slippage_pct=BACKTEST_SLIPPAGE_PCT) -> BacktestResult` em `backtesting/grid.py`: percorre candles, abre grade em `"sideways"` (bandas do candle de abertura), processa vendas antes de compras por candle (D3), liquida tudo ao `close` em `"trending"` (D4), reabre com bandas novas (D5); monta `Trade`s e chama `_calculate_advanced_metrics` para o `BacktestResult` (D6) (depende de T001-T007)

**Checkpoint**: `pytest tests/test_grid.py -v` — T001-T007 passam. MVP
completo: a grade mede com gestão de cauda, usando o motor existente.

---

## Phase 3: User Story 3 - Custo aplicado por transação (Priority: P2)

**Goal**: `BACKTEST_FEE_RATE`/`BACKTEST_SLIPPAGE_PCT` são aplicados a cada
round-trip de nível e a cada liquidação forçada — o custo cresce com o
número de transações, não é uma constante.

**Independent Test**: comparar `simular_grade` com `fee_rate=0,
slippage_pct=0` contra os valores padrão, sobre o mesmo `df` — a diferença
de retorno escala com o número de trades.

### Tests for User Story 3

- [X] T010 [P] [US3] Teste em `tests/test_grid.py`: `simular_grade` com custo zerado produz `total_return_pct` maior que com custo padrão, sobre o mesmo `df` sintético com múltiplos round-trips — a diferença é proporcional ao número de trades, não fixa (varia o `df` para produzir números diferentes de trades e confirma que a diferença de retorno também varia)

### Implementation for User Story 3

Nenhuma — `fee_rate`/`slippage_pct` já são parâmetros de `simular_grade`
(T009). T010 é a prova.

**Checkpoint**: as três user stories passam juntas.

---

## Phase 4: Polish & Cross-Cutting Concerns

- [X] T011 [P] Implementar `run_grid_scan(pares=UNIVERSO_H11) -> list[tuple[str, BacktestResult, ApprovalVerdict]]` em `backtesting/grid.py`: busca candles+indicadores por par (mesmo padrão de `avaliar_par`/`run_horizonte_scan`), chama `simular_grade`, aplica `evaluate_approval`
- [X] T012 Criar `cmd_grid()` em `main.py`: chama `run_grid_scan()`, imprime tabela por par (episódios, trades, retorno, buy-hold, drawdown, profit factor, veredito); registrar `"grid": cmd_grid` em `COMMANDS`; exportar via `export_report("grid", ...)`
- [X] T013 Rodar `python main.py grid` contra dados reais (`UNIVERSO_H11`) — validação manual do passo 2 do `quickstart.md`, resultado real
- [X] T014 Registrar o veredito real (resultado de T013) em `docs/research/registro-de-hipoteses.md` — H18 sai de "julgada por raciocínio" (§6.3) para avaliada (seção 4.x, com data e números, mesmo padrão de H1-H14/H17/H20); o texto exato depende do resultado medido, não pode ser escrito antes de T013
- [X] T015 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão em `backtesting/engine.py`, `backtesting/approval.py` e `strategy/ema_rsi.py` (intocados)

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: N/A
- **US1+US2 (Phase 2)**: sem dependência — único tópico que cria `simular_grade`
- **US3 (Phase 3)**: depende de T009 (Phase 2) já aceitar `fee_rate`/`slippage_pct`
- **Polish (Phase 4)**: depende de Phase 2 e Phase 3 completas — T014 depende do resultado real de T013

### Parallel Opportunities

- T001-T007 (testes, cenários independentes) em paralelo
- T011 e T012 podem ser desenvolvidos em paralelo até a integração final (T012 chama T011)

---

## Implementation Strategy

### MVP = Phase 2 (US1+US2)

Um commit: T008-T009 (implementação) precedida por T001-T007 (testes
falhando) → commit → push. É a mudança inteira que responde a pergunta da
hipótese com gestão de cauda.

### Incremental Delivery

1. Phase 2 (US1+US2) → simulador completo, MVP
2. Phase 3 (US3) → prova de que o custo escala com transações
3. Phase 4 (Polish) → scan sobre o universo, comando CLI, execução real,
   veredito registrado no registro-mestre, suite completa

Fluxo Incremental do `CLAUDE.md`: Phase 2 é um commit (o simulador em si,
maior risco de acerto de mecânica); Phase 3+4 podem ir juntas (comando CLI
+ execução real + registro do veredito), dado que Phase 3 não adiciona
código novo, só prova uma propriedade já presente.
