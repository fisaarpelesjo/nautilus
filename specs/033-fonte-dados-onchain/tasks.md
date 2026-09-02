---

description: "Task list for fonte de dados on-chain (spec 033)"
---

# Tasks: Fonte de dados on-chain

**Input**: Design documents from `/specs/033-fonte-dados-onchain/`

**Prerequisites**: plan.md, spec.md, data-model.md, research.md, quickstart.md

**Tests**: obrigatórios — Princípio III da constitution. Arquivo novo
`tests/test_onchain.py`.

**Organization**: spec pequena (uma função). US1 (busca válida) e US2
(falha nunca vira dado inventado) no mesmo tópico — são as duas metades da
mesma função. US3 (série vazia é distinguível) é consequência natural da
mesma implementação, testada junto.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

Nenhuma — sem dependência nova, um único arquivo novo.

---

## Phase 2: User Story 1 + User Story 2 + User Story 3 - Busca on-chain confiável (Priority: P1) 🎯 MVP

**Goal**: `fetch_onchain_series(metric, timespan)` retorna uma série válida
quando a API responde `ok`, levanta exceção em qualquer falha real (rede,
nome inválido, status não-ok), e retorna série vazia (não erro) quando a
API confirma sucesso mas não tem dado no período.

**Independent Test**: chamar a função com `requests.get` mockado nos quatro
cenários (sucesso com dados, sucesso vazio, HTTP de erro, status não-ok) e
confirmar o resultado/exceção correspondente.

### Tests for User Story 1 + 2 + 3

> **NOTE**: escrever os testes primeiro — `fetch_onchain_series` ainda não
> existe, então todos devem falhar por `ImportError`/`AttributeError` antes
> da implementação.

- [X] T001 [P] [US1] Teste em `tests/test_onchain.py`: resposta mockada com `status: "ok"` e `values` preenchido — `fetch_onchain_series` retorna `DataFrame` com índice `DatetimeIndex` crescente sem duplicatas e coluna `value` com os valores corretos
- [X] T002 [P] [US1] Teste: a chamada a `requests.get` (mockada) inclui `sampled=false` e o `timespan` passado como parâmetro — confirma D1 (research.md), sem o qual a API poderia subamostrar o período
- [X] T003 [P] [US2] Teste: `requests.get` mockado levanta exceção de rede (`ConnectionError`/`Timeout`) — `fetch_onchain_series` propaga como exceção explícita, nunca série vazia silenciosa
- [X] T004 [P] [US2] Teste: resposta mockada com status HTTP não-200 — `fetch_onchain_series` levanta exceção
- [X] T005 [P] [US2] Teste: resposta mockada com HTTP 200 mas corpo `{"status": "error", ...}` (nome de métrica inválido) — `fetch_onchain_series` levanta exceção citando o status retornado
- [X] T006 [P] [US3] Teste: resposta mockada com `status: "ok"` e `values: []` — `fetch_onchain_series` retorna `DataFrame` vazio, **sem** levantar exceção (distingue ausência real de dado de falha, FR-004)

### Implementation for User Story 1 + 2 + 3

- [X] T007 [US1][US2][US3] Implementar `fetch_onchain_series(metric: str, timespan: str = "3years") -> pd.DataFrame` em `data/onchain.py`: monta a URL (`https://api.blockchain.info/charts/{metric}?timespan={timespan}&format=json&sampled=false`), chama `requests.get(..., timeout=15)`, levanta exceção em falha de rede/HTTP não-200/`status != "ok"`, parseia `values` (`x` unix seconds → `DatetimeIndex` UTC, `y` → coluna `value`), ordena e remove duplicatas de índice (depende de T001-T006)

**Checkpoint**: `pytest tests/test_onchain.py -v` — todos os testes passam.
MVP completo: a função existe, é confiável, e distingue erro de ausência
de dado.

---

## Phase 3: Polish & Cross-Cutting Concerns

- [X] T008 Validar manualmente o passo 2 do `quickstart.md` (`fetch_onchain_series("n-unique-addresses", timespan="1years")`) contra a API real — confirma ~365 pontos, sem exceção
- [X] T009 Validar manualmente o passo 3 do `quickstart.md` (métrica inexistente) contra a API real — confirma exceção
- [X] T010 Rodar a suite completa (`pytest -q`) para confirmar ausência de regressão em `data/fetcher.py` e `data/sources/` (intocados)

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: N/A
- **Phase 2 (US1+US2+US3)**: sem dependência — único tópico que cria `fetch_onchain_series`
- **Polish (Phase 3)**: depende de Phase 2 completa

### Parallel Opportunities

- T001-T006 (testes, cenários independentes) em paralelo
- T008 e T009 (validações manuais independentes) em paralelo

---

## Implementation Strategy

### MVP = Phase 2 inteira

Um commit: T001-T006 (testes falhando) → T007 (implementação, testes
passam) → T008-T010 (validação manual + suite completa) → commit → push.
Spec pequena o bastante para não precisar de mais de um tópico.
