# Specification Quality Checklist: H13 — Barras dirigidas por informação

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-01
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
- [X] Success criteria are technology-agnostic (no implementation details)
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

### Iteração 1 — falhas encontradas e corrigidas

1. **Detalhe de implementação vazando em FR-001.** A redação inicial nomeava o
   módulo onde a conversão viveria. Reescrito para declarar apenas *quando* a
   conversão ocorre (antes do cálculo de indicadores), que é a restrição real e
   é verificável sem conhecer a estrutura de arquivos.

2. **SC-004 mencionava a técnica de teste em vez do resultado.** Reescrito para
   descrever a propriedade observável — igualdade exata entre construção
   incremental e construção completa — em vez do mecanismo de verificação.

3. **US3 estava em P2 na primeira redação.** Promovida a P1: causalidade não é
   refinamento. Uma barra construída com conhecimento do próprio total futuro
   produziria o resultado mais convincente e mais falso possível, e M2 documenta
   que exatamente essa classe de defeito passou meses despercebida no projeto.

### Nenhum [NEEDS CLARIFICATION] emitido — justificativa

A descrição de entrada resolveu antecipadamente as três áreas que normalmente
exigiriam esclarecimento:

- **Escopo**: declarado explicitamente em "o que entra" e "o que não entra".
- **Granularidade de base**: a restrição 1 da entrada já declara o problema, dá
  a direção (candle de base mais fino) e autoriza o desfecho inconclusivo. É
  decisão de **pesquisa** com critério declarado, não ambiguidade de requisito —
  registrada em Assumptions e endereçada na Fase 0 do plano.
- **Medida de exposição**: a entrada declara que pode ser uma quarta forma da
  família M7/M10/M11 e que, se for, é o achado principal. O requisito
  (FR-008) exige *declarar* a medida usada, o que é testável independentemente
  de qual venha a ser.

### Riscos herdados que o plano precisa endereçar

- FR-003 e FR-004 (causalidade) são a maior fonte de falso positivo desta spec.
- FR-010 (aquecimento em dias) foi problema real em H11.
- FR-012 (inércia) foi problema real em H12: 37 de 48 combinações não mediram
  nada e apareciam como reprovação.
