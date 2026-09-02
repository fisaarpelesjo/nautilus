# Specification Quality Checklist: H17 — Sinais on-chain

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

### Por que aditiva a H14, não pipeline novo

H14 já resolveu rotulagem causal, purga temporal, embargo, três linhas de
base e o critério de aprovação. H17 testa uma pergunta mais estreita —
"este atributo a mais muda o veredito?" — que só é válida comparada contra
a mesma régua, mesmo par, mesmo período. Reavaliar do zero seria refazer
trabalho já feito para responder uma pergunta que não precisa disso.

### A restrição BTC-only não é um detalhe, é o que impede uma comparação errada

FR-005 existe especificamente para impedir a comparação inválida óbvia
(BTC-only com on-chain vs pooled-12-pares sem on-chain, que misturaria dois
efeitos — atributo novo E tamanho de amostra diferente — numa única
diferença observada). A comparação certa é sempre mesmo-par-mesmo-período.

### Disciplina "declarar antes de medir" herdada de H14

`strategy/barreira_tripla.py` já documenta essa disciplina para os 5
atributos existentes ("NENHUMA métrica de acerto participou da seleção").
US3/FR-001/FR-002 estendem a mesma disciplina ao atributo novo — sem isso,
H17 reintroduziria o problema de busca de atributos que a própria estrutura
de H14 foi desenhada para evitar.

### Nenhum [NEEDS CLARIFICATION] emitido

A escolha do atributo candidato (Assumptions) é decisão de pesquisa com
precedência na literatura já registrada no projeto, não ambiguidade de
negócio — mesmo padrão de todas as specs de hipótese anteriores. A janela
exata da transformação fica para research.md (Fase 0), declarada e medida
antes de qualquer resultado.

### Iteração 1 — nenhuma falha encontrada

Spec escrita já com a restrição estrutural (BTC-only) e a comparação
isolada (FR-005) incorporadas desde a primeira versão — não uma correção
posterior a um erro de design óbvio.
