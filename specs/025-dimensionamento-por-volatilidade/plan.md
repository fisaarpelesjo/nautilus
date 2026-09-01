# Implementation Plan: H12 — Dimensionamento de posição por volatilidade

**Branch**: `025-dimensionamento-por-volatilidade` | **Date**: 2026-09-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/025-dimensionamento-por-volatilidade/spec.md`

## Summary

Camada que escala o tamanho da posição pela volatilidade realizada do ativo,
avaliada pela bateria E1–E6 contra a versão sem dimensionamento, nos mesmos
pares e escala temporal.

**Abordagem técnica:** um parâmetro opcional de dimensionamento em
`simulate_backtest`, com valor padrão que preserva o comportamento atual byte a
byte. O fator vem de `atr_ratio` — indicador de volatilidade normalizada que
`calculate_indicators` **já computa** e que já está no DataFrame preparado.
Nenhum indicador novo, nenhuma dependência.

O trabalho conceitual não é calcular o fator, que é uma divisão. É garantir que
a avaliação não confunda **redução de exposição** com **habilidade** — motivo
pelo qual a spec deu prioridade P1 a essa distinção.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: pandas. Nenhuma nova.

**Storage**: leitura de OHLCV pelo cache existente; relatório em `reports/`.

**Testing**: pytest, estendendo `tests/`.

**Target Platform**: CLI local e VPS; fora do loop do bot.

**Project Type**: ferramenta de pesquisa no projeto existente.

**Performance Goals**: a comparação pareada dobra o número de simulações (cada
combinação roda com e sem dimensionamento). Com o caminho já otimizado na spec
024 — indicadores calculados uma vez, sinais vetorizados quando disponíveis — a
varredura de 12 pares × 4 estratégias × 2 versões deve concluir sem intervenção.

**Constraints**: não altera `risk/manager.py` nem o caminho de produção
(FR-013); o fator só pode reduzir, nunca ampliar (FR-003); alvo e janela fixos,
não varridos.

**Scale/Scope**: 12 pares × 4 estratégias × 2 versões = 96 execuções de bateria.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Situação |
|---|---|
| **I. Safety First** | `risk/manager.py` **não é alterado**. O dimensionamento vive no caminho de backtest, atrás de parâmetro opcional cujo default reproduz o comportamento atual. FR-013 e SC-006 verificam | **PASSA** |
| **II. No Secrets in Code** | Sem credenciais | **PASSA** |
| **III. Test Before Implement** | Cada tarefa com critério de teste antes da implementação, estendendo `tests/` | **PASSA** (verificar em `tasks.md`) |
| **IV. Incremental Delivery** | Fases: fator → integração no motor → comparação pareada → relatório → veredito | **PASSA** |
| **V. Observability Mandatory** | Sem pipeline paralelo; reusa `utils/report_export.py`. Não decide risco em produção | **PASSA** |
| **VI. Idempotency and Reconciliation** | Não envia ordem | **N/A** |
| **VII. Explain Before Code** | Desenho e justificativa nesta seção e em `research.md` | **PASSA** |

**Restrição técnica relevante:** a constituição proíbe alavancagem
(`max_leverage = 1`). O fator é limitado a 1,0 por construção, então o
dimensionamento **só reduz** — não há caminho pelo qual esta feature amplie
exposição. É invariante de código, não convenção.

**Nenhuma violação a justificar.**

## Project Structure

### Documentation (this feature)

```text
specs/025-dimensionamento-por-volatilidade/
├── plan.md              # Este arquivo
├── research.md          # Fase 0: distribuição medida e escolha do alvo
├── data-model.md        # Fase 1: entidades da comparação pareada
├── quickstart.md        # Fase 1: cenários de validação
├── contracts/
│   └── cli-volatilidade.md
├── checklists/
│   └── requirements.md  # já criado
└── tasks.md             # Fase 2: gerado por /speckit-tasks
```

### Source Code (repository root)

```text
backtesting/
├── volatilidade.py      # NOVO: fator de dimensionamento e comparação pareada
├── engine.py            # ALTERADO: parâmetro opcional de dimensionamento
├── horizonte.py         # reusado: preparar(), _simular(), classificar_status()
├── approval.py          # reusado: evaluate_approval (critério inalterado)
└── cross_sectional.py   # reusado: WalkForwardFold, ganho_de_timing_pp

risk/
└── manager.py           # NÃO ALTERADO — verificado por teste

main.py                  # ALTERADO: comando novo

tests/
└── test_volatilidade.py # NOVO

docs/research/
└── registro-de-hipoteses.md  # ALTERADO: veredito de H12
```

**Structure Decision**: módulo novo em `backtesting/`, seguindo o padrão de
`compare.py`, `multimarket.py`, `cross_sectional.py`, `pairs_trading.py` e
`horizonte.py` — cada um orquestra uma forma de avaliação sobre o mesmo motor.
`volatilidade.py` é o sétimo e não introduz camada nova.

A única alteração fora de `backtesting/` e `main.py` é o parâmetro opcional em
`engine.simulate_backtest`. Poderia ser evitada duplicando o laço de simulação,
mas duplicá-lo criaria exatamente a divergência entre caminhos que o achado M1
documenta como o defeito mais caro do projeto.

## Complexity Tracking

Sem violações constitucionais a justificar.
