---

description: "Task list for H31 viabilidade de dados alternativos (spec 068)"
---

# Tasks: H31 — viabilidade de dados alternativos (sentimento social/notícia)

**Input**: Design documents from `/specs/068-h31-dados-alternativos-sentimento/`

**Prerequisites**: plan.md, spec.md, research.md (D1-D2), quickstart.md

**Tests**: N/A — esta spec não produz código de produção (viabilidade negativa, ver research.md).

**Organization**: uma única user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: User Story 1 - Determinar se alguma fonte gratuita de sentimento é utilizável (Priority: P1) 🎯 MVP

- [X] T001 [US1] Declarar a barra de viabilidade em `spec.md` antes de qualquer chamada real
- [X] T002 [US1] Testar GitHub `stats/commit_activity` com chamada real, sem autenticação — registrar histórico/granularidade em `research.md` D1
- [X] T003 [US1] Testar rate limit não-autenticado do GitHub (`/rate_limit`) — registrar em `research.md` D1
- [X] T004 [US1] Testar `pytrends` com chamada real (instalação isolada, nunca no `.venv` compartilhado) — registrar histórico/granularidade em `research.md` D1
- [X] T005 [US1] Testar confiabilidade entre chamadas sucessivas do `pytrends` (simulando campanha multi-par) — registrar em `research.md` D1
- [X] T006 [US1] Comparar as duas fontes contra a barra declarada (`research.md` D2) — resultado: nenhuma passa
- [X] T007 [US1] Registrar o resultado em `docs/research/registro-de-hipoteses.md` §6.2 (H31) — viabilidade negativa, full transparência
- [X] T008 Confirmar que nenhuma dependência nova entrou no `.venv` compartilhado do projeto e nenhuma conta/chave paga foi criada (FR-003/FR-004)

**Fora de escopo (viabilidade negativa, não alcançado):** T009+ construir pipeline de medição (`data/sentimento.py`, comando CLI, testes) — não se aplica, spec encerra em research.md.

**Checkpoint**: spec fechada num único commit de documentação (viabilidade negativa não gera código de produção).

---

## Implementation Strategy

T001-T008 (investigação de viabilidade + registro) → commit → push. Sem fase de implementação — resultado negativo é o resultado completo.
