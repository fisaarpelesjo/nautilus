# Specification Quality Checklist: H12 — Dimensionamento por volatilidade

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

Iteração 1 corrigiu quatro violações:

1. **Nomes de módulo e função nos requisitos.** A redação inicial citava
   `risk/manager.py`, `ganho_de_timing_pp` e `MAX_ORDER_SIZE_USDT`. Reescritos em
   termos de comportamento: "compor com as regras de dimensionamento já
   existentes — teto por ordem e reserva proporcional aos slots livres". O
   mapeamento para símbolos concretos é trabalho do plano.

2. **Identificadores de hipótese nos critérios de sucesso.** SC citava "H7" e
   "M7". Substituídos por descrição do comportamento, para o critério não
   depender da numeração interna do registro.

3. **Fórmula de volatilidade prescrita.** A versão inicial fixava desvio padrão
   de retornos logarítmicos em janela de N períodos — decisão de implementação.
   A spec agora exige apenas "variação típica dos retornos recentes", com a
   definição exata delegada ao plano e registrada em Assumptions.

4. **Constante de limiar citada.** `EDGE_MIN_TRADES` aparecia em FR-011,
   substituída por "o mínimo exigido".

Duas histórias receberam prioridade P1, o que é incomum. É deliberado: US2
(desconto de exposição) não é refinamento de US1 — sem ela, a resposta de US1 é
inutilizável, porque dimensionar por volatilidade **necessariamente** reduz
exposição e portanto **necessariamente** parece melhorar o retorno num mercado
em queda. As duas juntas formam o MVP mínimo defensável.

Nenhum marcador [NEEDS CLARIFICATION] foi necessário. Os três candidatos têm
padrão derivável do próprio registro e estão em Assumptions: janela de
estimativa fixa, alvo de volatilidade único, e universo idêntico ao das
avaliações anteriores.
