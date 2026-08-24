# Specification Quality Checklist: Camada de dados multi-mercado para pesquisa

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-24
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

## Notas de validação

**Passagem 1 (2026-08-24)** — corrigidos antes de registrar:

- FR-003/FR-004 estavam fundidos num requisito só ("aplicar custo do mercado"), sem cobrir o caso de mercado *sem* perfil definido. Separados, porque o comportamento na ausência de configuração é justamente onde este projeto já se queimou (custo de cripto aplicado a par de book fino).
- História 2 estava em P2. Promovida a P1: entregar avaliação multi-mercado com custo errado é pior que não entregar, porque produz número que parece confiável. Precedente concreto no projeto (ACE/BIO/ALLO).
- FR-007 não existia. Adicionado após revisar o Princípio I da Constituição: sem ele, um símbolo não-cripto em `PAIRS` cairia no caminho de operação sem execução implementada.
- Critérios de sucesso continham menções a ferramentas específicas. Reescritos em termos de resultado observável pelo operador.

**Passagem 2 (2026-08-24)** — clarificação resolvida:

Questão sobre descoberta por acaso decidida pelo operador: **confirmação obrigatória fora da
janela de busca**, entre três opções (só advertir / exigir amostra maior / validar fora da
amostra). Escolhida por ser a única que efetivamente impede o erro em vez de sinalizá-lo, e por
reusar a infraestrutura de validação out-of-sample que o projeto já possui — evitando um caminho
paralelo, padrão que já causou dois defeitos graves neste projeto.

FR-012 substituído por três requisitos (FR-012/013/014) cobrindo: proibição de aprovar na janela
de descoberta, registro do número de combinações avaliadas, e distinção visual entre "passou na
busca" e "confirmado fora dela". SC-007 adicionado. Custo aceito e registrado em Riscos: divide o
histórico disponível, reduzindo a amostra de cada janela.

**Status**: todos os itens do checklist passam. Spec pronta para `/speckit-plan`.
