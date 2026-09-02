# Specification Quality Checklist: Fonte de dados on-chain

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

### Por que infra separada da hipótese

Mesmo padrão de 023 (camada de dados) → 024-029 (hipóteses que a
consomem): infra genérica e reusável não deveria carregar a decisão
específica de uma hipótese (qual métrica, qual critério). Se H17 for
reprovada, esta infra continua útil para qualquer avaliação on-chain
futura; se estivesse embutida na spec de H17, seria descartada junto.

### API verificada antes da spec, não suposta

`api.blockchain.info/charts/*` foi testada diretamente (6 séries, todas
`status: ok`, ~720 pontos/2 anos) antes de qualquer requisito ser escrito
— mesmo padrão das medições em research.md das specs 029/030/031.

### Escopo BTC-only declarado explicitamente

Não é uma limitação escondida: Assumptions já declara que isso restringe
qualquer hipótese consumidora a avaliação de um único par. Melhor
descobrir isso lendo a spec da infra do que no meio da spec da hipótese.

### Nenhum [NEEDS CLARIFICATION] emitido

A única decisão de escopo real (BTC-only) não é ambígua — é consequência
direta de qual fonte gratuita existe, verificada por medição, não uma
escolha de negócio em aberto.
