# Specification Quality Checklist: H11 — Momentum em horizonte temporal superior

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-01
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

Iteração 1 identificou três violações, todas corrigidas antes desta versão:

1. **Nomes de função e módulo nas Functional Requirements.** A redação inicial
   citava `evaluate_approval`, `run_scan` e `walk_forward` — detalhes de
   implementação. Reescritas em termos de comportamento: "aplicar o critério de
   aprovação vigente sem alteração de limiar", "submeter à confirmação em janela
   que não participou da descoberta". O *quê* permanece; o *como* sai para o
   plano.

2. **Timeframes literais nos Success Criteria.** SC citava "4h", "1d" e "1w".
   Substituído por "horizonte atual", "diário" e "semanal" — o critério de
   sucesso não deve depender da notação de uma fonte de dados específica.

3. **Constantes de configuração citadas diretamente.** `EDGE_MIN_TRADES = 10` e
   `MIN_WINDOW_CANDLES` apareciam nos requisitos. Substituídos por "o mínimo
   exigido pelo critério" — se o limiar mudar, a spec não fica errada.

Nenhum marcador [NEEDS CLARIFICATION] foi necessário. Os três pontos que
poderiam exigi-lo têm padrão razoável derivado do próprio projeto:

- **Universo de pares**: o mesmo das avaliações anteriores, por comparabilidade.
- **Parâmetros das estratégias**: mantidos nos valores vigentes, porque otimizar
  por horizonte reintroduziria testes múltiplos.
- **Horizontes avaliados**: diário e semanal, que é a faixa que a literatura
  citada documenta, mais o atual como linha de base.

Todos registrados na seção Assumptions.
