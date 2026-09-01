# Implementation Plan: H11 — Momentum em horizonte temporal superior

**Branch**: `024-horizonte-temporal-momentum` | **Date**: 2026-09-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/024-horizonte-temporal-momentum/spec.md`

## Summary

Avaliar as quatro estratégias já implementadas em horizonte diário e semanal,
além do horizonte atual como linha de base, submetendo cada combinação à bateria
E1–E6 já usada pelas hipóteses anteriores.

**Abordagem técnica:** um orquestrador novo (`backtesting/horizonte.py`) que
varre estratégia × horizonte × par e delega inteiramente às peças existentes —
`run_backtest` para simular, `evaluate_approval` para julgar,
`split_train_validation` para confirmar fora da amostra, `walk_forward` para as
janelas múltiplas e `ganho_de_timing_pp` para descontar exposição. Nenhum
critério novo: a régua tem de ser a mesma que reprovou as anteriores, ou a
comparação não vale.

O trabalho real do módulo não é simular — é **declarar limitação de dado**. A
medição prévia de disponibilidade (ver `research.md`) mostrou que o horizonte
semanal não comporta a bateria completa, e o módulo precisa reportar isso como
inconclusivo em vez de produzir um número que parece resultado.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: pandas, ccxt (via `data/fetcher.py`), rich (exibição).
Nenhuma dependência nova.

**Storage**: leitura de OHLCV pelo cache existente em `data/ohlcv/`; saída de
relatório em `reports/` pelo `utils/report_export.py` já existente.

**Testing**: pytest, estendendo `tests/`. Sem suíte paralela (Constitution III).

**Target Platform**: CLI local e VPS Linux; não roda dentro do loop do bot.

**Project Type**: ferramenta de pesquisa dentro do projeto existente (single
project).

**Performance Goals**: a varredura completa (4 estratégias × 3 horizontes × 12
pares = 144 combinações, cada uma com E2–E6) deve terminar sem intervenção. Não
há requisito de latência; há requisito de **não travar** — um par que falha ao
buscar dados vira entrada de erro e não interrompe os demais, como já faz
`multimarket.run_scan`.

**Constraints**: não altera `TIMEFRAME` de produção (FR-012); não altera
parâmetros de estratégia; não introduz critério de aprovação novo.

**Scale/Scope**: 144 combinações, 12 pares, 3 horizontes, histórico de 311 a
2000 candles conforme o horizonte.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Aplicabilidade | Situação |
|---|---|---|
| **I. Safety First** | Não toca `risk/manager.py`, `execution/order_manager.py` nem `trading/position_lifecycle.py`. FR-012 exige explicitamente preservar o horizonte de produção | **PASSA** |
| **II. No Secrets in Code** | Nenhuma credencial envolvida; usa apenas endpoint público de OHLCV | **PASSA** |
| **III. Test Before Implement** | Cada tarefa terá critério de teste antes da implementação, estendendo `tests/` | **PASSA** (a verificar em `tasks.md`) |
| **IV. Incremental Delivery** | Entrega em tópicos pequenos: medição de disponibilidade → orquestrador → veredito por amostra → relatório → registro | **PASSA** |
| **V. Observability Mandatory** | Não introduz pipeline de log paralelo. Reusa `utils/report_export.py`. Não gera evento de risco porque não decide risco — é ferramenta de pesquisa, não caminho de execução | **PASSA** |
| **VI. Idempotency and Reconciliation** | Não envia ordem; não há `clientOrderId` nem estado a reconciliar | **N/A** |
| **VII. Explain Before Code** | O desenho e o porquê estão nesta seção e em `research.md`; o commit de implementação resume a decisão | **PASSA** |

**Restrições técnicas:** a feature não opera, apenas mede. Não introduz
alavancagem, não sai de spot, não altera persistência.

**Nenhuma violação a justificar.** A seção Complexity Tracking foi removida.

## Project Structure

### Documentation (this feature)

```text
specs/024-horizonte-temporal-momentum/
├── plan.md              # Este arquivo
├── research.md          # Fase 0: disponibilidade medida e decisões dela decorrentes
├── data-model.md        # Fase 1: entidades do relatório
├── quickstart.md        # Fase 1: como executar e validar
├── contracts/
│   └── cli-horizonte.md # Contrato do comando de CLI
├── checklists/
│   └── requirements.md  # Checklist de qualidade da spec (já criado)
└── tasks.md             # Fase 2: gerado por /speckit-tasks, NÃO por este comando
```

### Source Code (repository root)

```text
backtesting/
├── horizonte.py         # NOVO: orquestra estratégia × horizonte × par
├── engine.py            # reusado: run_backtest
├── approval.py          # reusado: evaluate_approval (critério inalterado)
├── validation.py        # reusado: split_train_validation
└── cross_sectional.py   # reusado: walk_forward, ganho_de_timing_pp

data/
└── fetcher.py           # reusado: fetch_ohlcv (paginação já existente)

utils/
└── report_export.py     # reusado: exportação para reports/

main.py                  # ALTERADO: registra o comando novo

tests/
└── test_horizonte.py    # NOVO: cobre veredito por amostra, janela vazia,
                         # marcação de histórico e sensibilidade a custo

docs/research/
└── registro-de-hipoteses.md  # ALTERADO: recebe o veredito de H11
```

**Structure Decision**: módulo único novo em `backtesting/`, seguindo o padrão
já estabelecido por `multi.py`, `scanner.py`, `compare.py`, `multimarket.py` e
`cross_sectional.py` — cada um orquestra uma forma de varredura sobre o mesmo
motor. `horizonte.py` é o sexto desses e não introduz camada nova.

## Complexity Tracking

Sem violações constitucionais a justificar.
