# Implementation Plan: Itens Remanescentes do ROADMAP

**Branch**: `009-itens-remanescentes-roadmap` | **Date**: 2026-08-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/009-itens-remanescentes-roadmap/spec.md`

## Summary

Quatro capacidades pequenas e independentes, todas extensões de código já existente: (US1)
exportação de relatórios de backtest/scan/multibacktest/otimização em `reports/` (JSON/CSV/
Markdown); (US2) diagnóstico "perfil agressivo" complementando o "defensivo" já existente em
`diagnose_profile()`; (US3) `python main.py edge --validate` reusando `split_train_validation` já
validado para mostrar o edge out-of-sample; (US4) indicadores médios por sinal em
`data/decisions_analysis.py`.

## Technical Context

**Language/Version**: Python 3.12 (mesmo ambiente das specs 001-008)

**Primary Dependencies**: Nenhuma nova — `json`/`csv` da stdlib para US1, reuso de
`backtesting/approval.py`/`backtesting/validation.py`/`data/decisions_analysis.py` já existentes.

**Storage**: Novo diretório `reports/` (US1), sem persistência nova além disso.

**Testing**: `pytest`. Toda validação usa dados públicos de backtest ou fixtures sintéticas (FR-007).

**Target Platform**: Mesma CLI.

**Project Type**: CLI + daemon de longa duração (mesmo monolito modular).

**Performance Goals**: Exportação de relatórios (US1) é I/O local simples, sem impacto perceptível.
Demais itens são cálculos já rodando sobre dados já em memória.

**Constraints**: Todas as capacidades são aditivas — nenhuma altera o comportamento default de
comandos já existentes sem uma flag explícita (US3) ou é puramente informativa (US1/US2/US4).

**Scale/Scope**: Escopo pequeno — 4 itens independentes, sem dependência entre si.

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Safety First | PASS — spec inteiramente read-only/informativa, sem tocar execução de ordens. |
| II. No Secrets in Code | PASS — nenhuma configuração nova envolve segredo. |
| III. Test Before Implement | PASS — testes escritos antes de cada implementação. |
| IV. Incremental Delivery | PASS — US1 → US2 → US3 → US4 → Polish, cada uma um commit pequeno. |
| V. Observability Mandatory | PASS — a própria spec é sobre observabilidade/auditoria. |
| VI. Idempotency and Reconciliation | N/A — nenhuma ordem, nenhum estado persistido além de `reports/` (append-only por timestamp). |
| VII. Explain Before Code | PASS — `research.md` documenta as 4 decisões antes de qualquer implementação. |

Nenhuma violação identificada.

## Project Structure

```text
utils/
└── report_export.py     # NOVO (US1) -- export_report()
backtesting/
├── approval.py           # ✏️ diagnose_profile() ganha perfil agressivo (US2)
└── validation.py         # ✏️ run_edge_report(..., validate=False) (US3)
data/
└── decisions_analysis.py # ✏️ DecisionRecord.rsi, avg_indicators_by_signal (US4)
main.py                   # ✏️ chamadas a export_report; --validate no edge
```

## Complexity Tracking

Nenhuma violação — seção vazia.
