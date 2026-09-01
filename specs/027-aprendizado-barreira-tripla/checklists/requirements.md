# Specification Quality Checklist: H14 — Aprendizado supervisionado com barreira tripla

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

1. **Nome do estimador vazando na spec.** A redação inicial nomeava a técnica
   estatística e a biblioteca. Removidos: a spec declara apenas que o
   classificador deve ser de **baixa capacidade** e que nenhuma dependência pode
   ser adicionada, que são as restrições verificáveis. A escolha do estimador é
   decisão de pesquisa (Fase 0).

2. **SC-004 descrevia a técnica de verificação.** Reescrito para a propriedade
   observável — nenhuma amostra de treino com horizonte alcançando teste ou
   embargo — em vez do mecanismo que a verifica.

3. **US3 estava em P2 na primeira redação.** Promovida a P1. O teste de rótulo
   embaralhado não é refinamento: é a única linha de base que separa sinal de
   capacidade do modelo. Sem ele, qualquer desempenho aparece como descoberta,
   e o MVP produziria evidência enganosa — o mesmo argumento que tornou US2 das
   specs 025 e 026 obrigatória.

### Nenhum [NEEDS CLARIFICATION] emitido — justificativa

As três áreas que normalmente exigiriam esclarecimento estão resolvidas na
entrada ou por precedente do projeto:

- **Escopo**: declarado explicitamente em "o que entra" e "o que não entra".
- **Escolha do estimador**: é decisão de **pesquisa** com restrição declarada
  (baixa capacidade, sem dependência nova), não ambiguidade de requisito.
  Registrada em Assumptions e endereçada na Fase 0.
- **Universo e período**: mesmos das avaliações anteriores, por precedente
  estabelecido nas specs 024, 025 e 026.

### Riscos herdados que o plano precisa endereçar

- FR-004, FR-005 e FR-006 (causalidade, purga, embargo) são a maior fonte de
  falso positivo desta spec. O análogo é M2, e o precedente de que uma guarda
  declarada pega defeito não previsto é M12, achado por teste de fumaça em dado
  real na spec 026.
- FR-007 e FR-008 (rótulo embaralhado) são o que torna o resultado interpretável.
- FR-010 é a família M7/M10/M11, que já apareceu em três formas distintas.
- FR-011 é a regra de amostra de H10, H11, M9.
- FR-012 (convergência, classe única) é específico desta hipótese e não tem
  precedente no registro — o plano deve tratá-lo como caminho de falha de
  primeira classe, não como exceção genérica.
