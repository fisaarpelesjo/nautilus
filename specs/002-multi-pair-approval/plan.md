# Implementation Plan: Decisão de Aprovação Multi-Par

**Branch**: `002-multi-pair-approval` | **Date**: 2026-08-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-multi-pair-approval/spec.md`

## Summary

Generalizar o veredito de aprovação (aprovado/reprovado/inconclusivo, com motivos) já implementado
em `backtesting/validation.py` (spec 001, US3) para os comandos multi-par existentes
(`multibacktest`, `scan`) e para o relatório de par único (`edge`) — hoje `edge` é um alias literal
de `backtest` sem nenhuma lógica própria. Abordagem: extrair a lógica de veredito para um módulo
compartilhado (`backtesting/approval.py`), reusada por `validation.py` (fluxo out-of-sample, sem
mudança de comportamento) e pelos três comandos multi-par/single-pair (fluxo de janela única, sem
split treino/validação). Ranking de pares reusa o `edge_score` já existente em `engine.py` como
critério de ordenação, no lugar do score ad hoc que `scanner.py` já tem hoje.

## Technical Context

**Language/Version**: Python 3.12 (mesmo ambiente da spec 001)

**Primary Dependencies**: `pandas`, `rich` (tabelas dos relatórios), `pytest` — todas já em uso;
nenhuma dependência nova.

**Storage**: N/A — feature é só de relatório/decisão sobre resultados de backtest já em memória, não
persiste nada novo em disco.

**Testing**: `pytest` (suíte existente, 114 testes após a spec 001), estendida por esta feature.

**Target Platform**: Mesma CLI local (`python main.py ...`), sem mudança de plataforma.

**Project Type**: CLI (mesmo monolito modular da spec 001).

**Performance Goals**: Sem requisito novo — `multibacktest`/`scan` já rodam N backtests
sequenciais; esta feature só adiciona uma chamada de função pura (`evaluate_approval`) por resultado
já calculado, custo desprezível comparado ao fetch de candles.

**Constraints**: Não pode alterar o comportamento de saída de `backtest` sem a flag `--validate`
(FR-011); precisa continuar funcionando só com dados públicos da Binance (FR-012, herdado da spec
001).

**Scale/Scope**: Mesma escala da spec 001 — `multibacktest` roda 5 pares × 3 timeframes,
`scan` roda até 30 pares; nenhum aumento de escala nesta feature.

## Constitution Check

*GATE: Deve passar antes da Fase 0. Reavaliado após a Fase 1.*

Referência: `.specify/memory/constitution.md` v1.0.0.

| Princípio | Avaliação |
|---|---|
| I. Safety First | PASS — feature é só de relatório/backtest (leitura), não toca `risk/manager.py`, `execution/order_manager.py` nem `trading/position_lifecycle.py`. |
| II. No Secrets in Code | PASS — nenhuma configuração nova envolve segredo; `EDGE_MIN_TRADES` (se adicionado) é um inteiro. |
| III. Test Before Implement | PASS — cada tarefa em `tasks.md` terá teste escrito antes da implementação, seguindo o mesmo padrão da spec 001. |
| IV. Incremental Delivery | PASS — plano dividido em Foundational (extrair `approval.py`) → US1 (multibacktest/scan) → US2 (edge) → US3 (edge_score em faixas), cada uma um commit pequeno. |
| V. Observability Mandatory | N/A — feature não introduz decisão de risco operacional (não é kill switch/circuit breaker/ordem); é relatório de backtest, fora do pipeline de eventos JSONL/Telegram. |
| VI. Idempotency and Reconciliation | N/A — não toca execução de ordens. |
| VII. Explain Before Code | PASS — este `plan.md` documenta a decisão de extrair `approval.py` e reusar `edge_score` antes de qualquer tarefa de implementação. |

Nenhuma violação identificada. Nenhuma entrada necessária em Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/002-multi-pair-approval/
├── spec.md                       # Especificação (User Stories, requisitos, sucesso)
├── plan.md                       # Este arquivo
├── research.md                   # Fase 0 — decisões técnicas e alternativas consideradas
├── data-model.md                 # Fase 1 — entidades novas/alteradas
├── quickstart.md                 # Fase 1 — como validar cada User Story manualmente
├── contracts/
│   └── cli.md                    # Fase 1 — contrato da saída dos comandos afetados
├── checklists/
│   └── requirements.md           # Checklist de qualidade da spec
└── tasks.md                      # Fase 2 (/speckit-tasks) — tarefas executáveis
```

### Source Code (repository root)

Projeto existente — a estrutura abaixo é a real do repositório. Esta feature estende os módulos
marcados com ✏️ e adiciona os marcados com NOVO.

```text
backtesting/
├── approval.py                # NOVO — ApprovalVerdict, evaluate_approval(), edge_score_band(),
│                                 diagnose_profile(); extraído/generalizado de validation.py
├── validation.py               # ✏️ passa a importar de approval.py em vez de definir localmente
│                                 (ValidationVerdict/evaluate_validation viram re-export por
│                                 compatibilidade com o que já existe)
├── engine.py                   # ✏️ nova run_edge_report() (par único, sem split, com veredito) +
│                                 edge_score_band() usado no relatório
├── multi.py                    # ✏️ MultiResult ganha campos de veredito/edge_score; resultados
│                                 ordenados por qualidade; pares com erro aparecem marcados, não
│                                 somem da tabela
└── scanner.py                  # ✏️ mesmo tratamento de multi.py; ranking troca o `.score` ad hoc
                                   pelo edge_score compartilhado
config/
└── settings.py                 # ✏️ nova var EDGE_MIN_TRADES (default 10), lida por approval.py
main.py                         # ✏️ cmd_edge passa a chamar run_edge_report() em vez de
                                   run_backtest() (hoje são idênticos)
tests/
├── test_backtesting_approval.py     # NOVO — testes de evaluate_approval/edge_score_band/
│                                       diagnose_profile (migrados + estendidos de
│                                       test_backtesting_validation.py)
├── test_backtesting_validation.py   # ✏️ mantém só os testes específicos de split/orquestração
│                                       out-of-sample; testes de veredito puro migram para o arquivo
│                                       acima
├── test_multi_backtest.py           # NOVO
├── test_scanner.py                  # NOVO
└── test_main_backtest.py            # ✏️ estende para o novo dispatch de cmd_edge
```

**Structure Decision**: Extrair `backtesting/approval.py` como módulo compartilhado (mesmo padrão de
extração já usado na spec 001 para `data/atomic_io.py` e `utils/logger.safe_step`, quando uma mesma
lógica passa a ter ≥3 pontos de chamada). `validation.py` mantém seus nomes públicos atuais
(`ValidationVerdict`, `evaluate_validation`) como alias de compatibilidade, evitando qualquer edição
não essencial em `tests/test_main_backtest.py`/código que já importa desses nomes. Nenhum arquivo
novo de "serviço" ou camada de abstração — a extração é só de uma função pura + dataclass que hoje
mora dentro de um módulo com escopo mais específico (split out-of-sample) do que o uso real
(qualquer resultado de backtest).

## Complexity Tracking

*Nenhuma violação da Constitution Check — seção vazia intencionalmente.*
