# Specification Quality Checklist: Relógio simulado no replay

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-02
**Feature**: [spec.md](../spec.md)

## Content Quality

- [X] No implementation details (languages, frameworks, APIs)
- [X] Focused on user value and business needs
- [X] Written for non-technical stakeholders
- [X] All mandatory sections completed

## Requirement Completeness

- [X] No [NEEDS CLARIFICATION] markers remain
- [X] Requirements are testable and unambiguous
- [X] Success criteria are measurable
- [X] Success criteria are technology-agnostic
- [X] All acceptance scenarios are defined
- [X] Edge cases are identified
- [X] Scope is clearly bounded
- [X] Dependencies and assumptions identified

## Feature Readiness

- [X] All functional requirements have clear acceptance criteria
- [X] User scenarios cover primary flows
- [X] Feature meets measurable outcomes defined in Success Criteria
- [X] No implementation details leak into specification

## Notes

### O achado que amplia o escopo declarado no backlog

O item 022 do `BACKLOG.md` descreve "relógio real em vez do timestamp do
candle" — um problema de **precisão**. A leitura de código antes de
qualquer requisito revelou um segundo problema, de **ausência**: o replay
nunca chama `manager.check_circuit_breaker_timeout()`, então o circuit
breaker, uma vez ativado, nunca destrava dentro de uma execução de replay,
com relógio certo ou errado. Corrigir só o relógio sem adicionar essa
chamada deixaria o sintoma do backlog intacto — por isso FR-004/US2 tem a
mesma prioridade P1 de US1, não é um extra.

### Risco do arquivo tocado, e por que a mudança é aceitável

`execution/order_manager.py` é código do caminho de execução real
(Constitution, Princípio I). A mudança proposta (FR-001/FR-002) é uma
indireção que, por construção, é idêntica a `datetime.now()` fora do
ambiente isolado do replay — mesmo risco/padrão já aceito na spec 020
(`mtf_confirmed(..., as_of=None)`, default preserva comportamento atual).
US3 existe especificamente para tornar essa garantia um requisito
verificável, não uma alegação.

### Nomear módulos existentes

Mesma justificativa das specs 029/030/031: `execution/order_manager.py`,
`trading/replay.py` são módulos já existentes sendo estendidos.

### Nenhum [NEEDS CLARIFICATION] emitido

Todos os pontos técnicos (qual timestamp usar como relógio simulado, onde
inserir a checagem de timeout) têm resposta direta da leitura de código —
reusar o mesmo valor já usado pelo `as_of` do MTF (spec 020) e o mesmo
padrão de chamada já usado pelo loop de produção. Nenhuma decisão de
negócio ambígua.

### Iteração 1 — nenhuma falha encontrada

Spec escrita já com os dois achados (relógio + chamada ausente)
incorporados desde a primeira versão.
