# Implementation Plan: H31 — viabilidade de dados alternativos (sentimento social/notícia)

**Branch**: `068-h31-dados-alternativos-sentimento` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

Investigação de viabilidade, não implementação de hipótese. Duas
chamadas reais (GitHub `stats/commit_activity`, `pytrends`) decidem se
a spec avança para um pipeline de medição (padrão H17) ou encerra aqui.
Resultado: **nenhuma fonte passa a barra** — spec encerra em
`research.md` D1, sem código de produção.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: `requests` (já dependência do projeto, testa
GitHub); `pytrends` testado via instalação isolada em diretório
temporário (`pip install --target=`), NUNCA adicionado ao `.venv`
compartilhado do projeto — não vira dependência real porque a
viabilidade falhou.

**Storage**: Nenhuma — nenhum dado é persistido, a checagem é
transitória.

**Testing**: Nenhum teste automatizado — esta spec não produz código
de produção para testar. A "prova" é o resultado das chamadas reais,
documentado em `research.md`.

**Target Platform**: Investigação ad-hoc, sem comando CLI novo (não há
funcionalidade para expor).

**Performance Goals**: N/A.

**Constraints**: FR-003 — sem instalar dependência nova no ambiente
compartilhado; FR-004 — sem conta paga nem infraestrutura de contorno
de rate limit.

**Scale/Scope**: Duas chamadas de API reais, documentação do
resultado. Nenhum módulo novo no código do projeto.

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Só leitura de API pública, sem credencial, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** Nenhuma chave usada. |
| **III. Test Before Implement** | **N/A.** Não há implementação — a spec é a própria checagem de viabilidade. |
| **IV. Incremental Delivery** | **Conforme.** Um único tópico (a checagem em si), commit único de documentação. |
| **V. Observability Mandatory** | **N/A.** Nenhum comando de produção criado. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** A barra de viabilidade (spec.md) foi declarada antes de qualquer chamada real ser feita. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/068-h31-dados-alternativos-sentimento/
├── spec.md
├── plan.md
├── research.md
├── quickstart.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
(nenhum arquivo de produção criado — viabilidade negativa, spec encerra em research.md)
```

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — barra de viabilidade declarada em `spec.md` antes de
qualquer chamada real.

**Fase 1** — checagem real das duas fontes candidatas, documentada em
`research.md`. Resultado: viabilidade negativa nas duas. Spec encerra
aqui — sem Fase 2/3 de implementação.
