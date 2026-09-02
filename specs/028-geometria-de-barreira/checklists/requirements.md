# Specification Quality Checklist: H20 — Geometria de barreira

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

### O risco que define esta spec

H20 é, estruturalmente, uma varredura de parâmetro — a coisa que a metodologia
deste projeto mais combate. A diferença entre pesquisa legítima e testes
múltiplos disfarçados está inteiramente em **FR-003, FR-004 e FR-014**:

- a regra de seleção é escrita **antes** da medição;
- ela **não pode** consultar desempenho de modelo;
- exatamente **uma** geometria é avaliada com modelo.

Sem os três, o resultado não entra no registro. US2 é P1 por isso, e não por
importância relativa às demais histórias.

### Iteração 1 — falhas encontradas e corrigidas

1. **A tese soava como conclusão antecipada.** A primeira redação dizia que
   baixar o ponto de empate "faria o sinal caber". Reescrita: mudar a geometria
   muda os rótulos, a razão de chances cai junto, e a hipótese pode sair **pior**
   que H14. O contra-argumento passou para o corpo da tese, não para uma nota
   de rodapé.

2. **FR-008 não existia na primeira versão.** Faltava proibir reutilizar a
   elevação de +31,8% medida em H14 como se valesse na geometria nova. É o erro
   mais provável desta spec: tratar um número medido noutro contexto como dado.

3. **FR-009 acrescentado.** A razão de chances descreve apenas eventos que tocam
   alvo ou stop. Com alvo mais distante, mais eventos terminam por tempo, e a
   razão passa a descrever uma fatia menor da amostra — omitir isso deixaria a
   comparação entre geometrias sutilmente desonesta.

### Nenhum [NEEDS CLARIFICATION] emitido

A formulação da regra de seleção é a única questão em aberto, e é **decisão de
pesquisa com restrição declarada** (Assumptions + FR-004), não ambiguidade de
requisito. Fase 0 a resolve.
