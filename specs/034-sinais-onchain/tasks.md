---

description: "Task list for H17 -- sinais on-chain (spec 034)"
---

# Tasks: H17 — Sinais on-chain

**Input**: Design documents from `/specs/034-sinais-onchain/`

**Prerequisites**: plan.md, spec.md, data-model.md, research.md, quickstart.md

**Tests**: obrigatórios — Princípio III da constitution. `tests/
test_modelo.py` (regressão de `avaliar_par`) + `tests/
test_onchain_hipotese.py` (novo).

**Organization**: Foundational é bloqueante e de alto risco — parametrizar
`avaliar_par()` (código de H14 já publicado) precisa de um teste de
regressão que prove zero mudança **antes** de qualquer outra task tocar o
arquivo. US1 e US2 andam juntas (mesma implementação: extrator +
`avaliar_par` parametrizada). US3 verifica uma propriedade (colinearidade
exposta) da mesma implementação.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

Nenhuma — sem dependência nova.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: `avaliar_par()` ganha os parâmetros novos sem mudar o
resultado de H14 em nenhum caminho existente. **Bloqueante**: nenhuma task
de US1/US2/US3 pode tocar `avaliar_par` antes desta garantia existir e
estar testada.

- [ ] T001 Teste de regressão em `tests/test_modelo.py`: `avaliar_par(par, df=fixture_pequeno_deterministico)` chamado **sem** `atributos`/`extrair_atributos_fn` produz `AvaliacaoH14` com os mesmos campos (status, motivo, `n_treino`, `n_teste`, coeficientes) que o comportamento atual — grava o resultado atual como fixture de referência antes de qualquer mudança em `avaliar_par`
- [ ] T002 Implementar `atributos: list[str] = ATRIBUTOS` e `extrair_atributos_fn: Callable = extrair_atributos` como parâmetros de `avaliar_par()` em `backtesting/modelo.py`, substituindo as referências internas à constante/função módulo pelos parâmetros (D4, research.md) (depende de T001 — deve continuar passando)

**Checkpoint**: `pytest tests/test_modelo.py -v` — 100% dos testes
existentes de `avaliar_par`/`run_modelo_scan` continuam passando, mais T001.

---

## Phase 3: User Story 1 + User Story 2 - Comparação isolada e causal (Priority: P1) 🎯 MVP

**Goal**: obter a razão de chances no subconjunto decidido com e sem
`onchain_addr_growth_7d`, para BTC/USDT, sem nenhum candle ver o dia
on-chain ainda incompleto.

**Independent Test**: rodar `python main.py onchain` e obter as duas razões
de chances lado a lado; inspecionar que nenhum valor do atributo on-chain
muda dentro do mesmo dia calendário do candle.

### Tests for User Story 1 + 2

- [ ] T003 [P] [US2] Teste `onchain_addr_growth_7d(serie)` em `tests/test_onchain_hipotese.py`: sobre uma série sintética de 20+ dias, calcula `(ma7 - ma7.shift(7)) / ma7.shift(7)` corretamente (valores conhecidos calculados à mão)
- [ ] T004 [P] [US2] Teste `_merge_causal(indice_candles, serie_diaria)`: para uma série sintética com um valor distinto por dia, um candle no meio do dia `D` MUST receber o valor do dia `D-1`, nunca o de `D` — mesmo quando o dia `D` já tem valor disponível na série de entrada (garante que a função não "trapaceia" olhando o dia corrente só porque o dado existe)
- [ ] T005 [P] [US1] Teste `construir_extrator_onchain(serie_growth)`: a função retornada, aplicada a um `prep` de teste, devolve `DataFrame` com as 5 colunas de `extrair_atributos` mais `onchain_addr_growth_7d`
- [ ] T006 [P] [US1] Teste `avaliar_par` com `atributos=ATRIBUTOS + ["onchain_addr_growth_7d"]` e `extrair_atributos_fn` do extrator on-chain, sobre um `df` de teste pequeno e determinístico — retorna `AvaliacaoH14` cujo `modelo.coeficientes` inclui a chave `onchain_addr_growth_7d`

### Implementation for User Story 1 + 2

- [ ] T007 [US1][US2] Implementar `onchain_addr_growth_7d(serie: pd.Series) -> pd.Series`, `_merge_causal(indice_candles, serie_diaria) -> pd.Series` e `construir_extrator_onchain(serie_growth) -> Callable` em `backtesting/onchain_hipotese.py` (depende de T003-T006)
- [ ] T008 [US1] Implementar `RelatorioH17` (dataclass, `data-model.md`) e `avaliar_h17(par="BTC/USDT") -> RelatorioH17` em `backtesting/onchain_hipotese.py`: busca a série on-chain (spec 033), calcula `onchain_addr_growth_7d`, chama `avaliar_par` duas vezes (sem e com o atributo, mesmo `df` buscado uma vez só) e mede `correlacao_onchain` contra os 5 atributos originais
- [ ] T009 [US1] Criar `cmd_onchain()` em `main.py`: chama `avaliar_h17()`, imprime as duas razões de chances lado a lado, os estados de cada avaliação e a correlação medida; registrar `"onchain": cmd_onchain` em `COMMANDS`; exportar via `export_report("onchain", ...)`, mesmo padrão de `modelo`/`barras`

**Checkpoint**: `pytest tests/test_onchain_hipotese.py -v` — todos passam.
MVP completo: a comparação roda e é causal.

---

## Phase 4: User Story 3 - Atributo declarado e colinearidade verificável (Priority: P2)

**Goal**: a correlação do atributo on-chain contra os 5 existentes está
exposta no relatório, não só no `research.md`.

**Independent Test**: inspecionar `RelatorioH17.correlacao_onchain` e
confirmar que reflete os valores medidos em `research.md` (D2).

### Tests for User Story 3

- [ ] T010 [P] [US3] Teste em `tests/test_onchain_hipotese.py`: `avaliar_h17()` (ou a função que calcula `correlacao_onchain` isoladamente) retorna um dict com as 5 chaves de `ATRIBUTOS`, todos os valores com `abs() < 0.80` (guarda de regressão: se um valor cruzar o limiar no futuro — dado on-chain mudou de comportamento — o teste MUST falhar, não passar silenciosamente)

### Implementation for User Story 3

Nenhuma — `correlacao_onchain` já é calculado por T008. T010 é a prova.

**Checkpoint**: as três user stories passam juntas.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [ ] T011 Rodar `python main.py onchain` contra dados reais (BTC/USDT) — validação manual do passo 3 do `quickstart.md`, resultado real (não mockado) da comparação
- [ ] T012 Registrar o veredito real (resultado de T011) em `docs/research/registro-de-hipoteses.md` §6.3 (H17) — mesmo padrão de fechamento das demais hipóteses do registro; o texto exato depende do resultado medido em T011, não pode ser escrito antes dele
- [ ] T013 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão em `backtesting/modelo.py` (H14) e nos demais consumidores (`horizonte.py`, `volatilidade.py`, etc., que não usam os parâmetros novos)

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: N/A
- **Foundational (Phase 2)**: bloqueia tudo — `avaliar_par` precisa da garantia de zero-mudança testada antes de qualquer uso dos parâmetros novos
- **US1+US2 (Phase 3)**: depende de Phase 2 completa
- **US3 (Phase 4)**: depende de T008 (Phase 3) já calcular `correlacao_onchain`
- **Polish (Phase 5)**: depende de Phase 3 e Phase 4 completas — T012 depende do resultado real de T011, não pode ser escrito antes

### Parallel Opportunities

- T003-T006 (testes, funções/cenários independentes) em paralelo
- T010 é independente das demais tasks de Phase 4 (não há outras)

---

## Implementation Strategy

### MVP = Foundational + Phase 3 (US1+US2)

Dois commits: (1) T001-T002 — a garantia de zero-mudança em `avaliar_par`,
isolada e testada antes de qualquer outra coisa tocar o arquivo; (2)
T003-T009 — o extrator, o merge causal e o comando CLI, testes primeiro.
Phase 4 (US3) e Phase 5 (Polish, incluindo a execução real e o registro do
veredito) fecham a spec.

### Incremental Delivery

1. Foundational → garantia testada de que H14 não muda
2. US1+US2 → comparação causal funciona (MVP)
3. US3 → colinearidade verificável no relatório, não só no research.md
4. Polish → execução real, veredito registrado no registro-mestre, suite completa

Fluxo Incremental do `CLAUDE.md`: Foundational é seu próprio commit (risco
mais alto, isolado); Phase 3 outro; Phase 4+5 podem ir juntas dado o
tamanho pequeno de US3.
