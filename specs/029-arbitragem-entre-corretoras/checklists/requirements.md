# Specification Quality Checklist: H15 — Arbitragem entre corretoras

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

### A diferença estrutural que define esta spec

H15 é a **primeira hipótese do registro que não pode ser retrotestada**.
Corretoras não publicam histórico de livro de ofertas, e o diferencial num
instante passado é irrecuperável. As quinze anteriores rodaram sobre candles
históricos; aqui não há equivalente.

Isso muda a forma da spec: ela entrega um **instrumento de amostragem** e a
primeira medição, não um veredito. US4 (persistência) existe por isso — sem ela,
cada execução seria um instantâneo e a hipótese ficaria permanentemente
inconclusiva.

Declarar isso em Assumptions, antes de qualquer resultado, evita que um
instantâneo seja depois apresentado como evidência.

### Três armadilhas específicas desta hipótese

1. **Moeda de cotação (US2, FR-003).** Comparar `BTC/USDT` com `BTC/USD` mistura
   arbitragem com desvio da paridade USDT/USD. Medição preliminar: 0,104% entre
   cotações diferentes contra 0,037% entre iguais — a maior parte do
   "diferencial" era a paridade. É a mesma família de falso positivo que M7, M10,
   M11 e M13 documentam: um número que parece bom porque mede outra coisa.

2. **Latência (US3, FR-004, FR-005).** Medido neste ambiente: 2,0 a 6,1 segundos
   por consulta de livro. Reportar diferencial sem reportar o tempo descreveria
   uma oportunidade que ninguém poderia executar.

3. **Profundidade (FR-001, FR-007).** O topo do livro pode ter volume
   irrelevante. Kraken mostrou 0,0020 BTC no melhor lance na medição preliminar.
   Diferencial sobre volume que não existe não é oportunidade.

### Iteração 1 — falhas encontradas e corrigidas

1. **A spec prometia um veredito.** A primeira redação tratava H15 como as
   anteriores. Reescrita para declarar que o veredito exige tempo decorrido, não
   mais método — e que esta spec entrega o instrumento.

2. **FR-002 dizia "descontar custos" sem dizer "dos dois lados".** Arbitragem
   paga taxa na compra **e** na venda. A ambiguidade dobraria o diferencial
   líquido reportado.

3. **A observação preliminar desfavorável não estava na spec.** Movida para
   Assumptions: 0,037% de diferencial contra ~0,2% de custo. Registrá-la antes
   impede apresentar o resultado como surpresa depois, e impede a mim mesmo
   racionalizar um número ruim.

### Nenhum [NEEDS CLARIFICATION] emitido

O conjunto de corretoras e o volume de referência são decisões de **pesquisa com
restrição declarada** (Assumptions: acessibilidade pública e liquidez, nunca
diferencial observado), não ambiguidades de requisito. Fase 0 as resolve.
