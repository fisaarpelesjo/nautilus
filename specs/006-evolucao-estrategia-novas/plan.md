# Implementation Plan: Evolução da Estratégia

**Branch**: `006-evolucao-estrategia-novas` | **Date**: 2026-08-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-evolucao-estrategia-novas/spec.md`

## Summary

Cinco capacidades aditivas sobre a estratégia e a infraestrutura de backtest já existentes: (US1)
regime de mercado via ADX(14), suspendendo/endurecendo entradas em lateralização; (US2) detecção de
volatilidade elevada via `ATR_ratio`, bloqueando entradas em candles de stress; (US3) filtro Bollinger
adaptativo, permitindo rompimentos com tendência/volume fortes; (US4) nova `strategy/breakout.py`
(Donchian channel), reusando a mesma infraestrutura de backtest via um parâmetro `strategy` novo em
`run_backtest()`; (US5) comando `compare` que roda múltiplas estratégias/presets nas mesmas condições
e reusa `evaluate_approval`/`edge_score` já estabelecidos. Todas as capacidades de filtro (US1-US3)
são desligadas por padrão via config, preservando 100% o comportamento já validado para quem não as
habilitar.

## Technical Context

**Language/Version**: Python 3.12 (mesmo ambiente das specs 001-005)

**Primary Dependencies**: `ta` (ADX via `ta.trend.ADXIndicator`, mesma lib já usada para EMA/RSI/MACD/
BB/ATR), `pandas`, `rich` (relatório de comparação), `pytest`. Nenhuma dependência nova.

**Storage**: Extensão de `data/decisions.csv` (nova coluna `regime`), mesmo mecanismo de escrita já
existente em `trading/decision_logger.py`. Nenhuma mudança em `state.json`.

**Testing**: `pytest` (suíte existente, 193 testes após a spec 005). Toda a validação funcional desta
spec é feita via backtest com dados públicos da Binance (FR-011) — nenhuma parte depende de operação
paper em tempo real (essa parte, "validar preset operacional atual", é explicitamente fora de escopo,
ver `spec.md` Input).

**Target Platform**: Mesma CLI (`python main.py <comando>`). Nenhuma mudança de plataforma.

**Project Type**: CLI + daemon de longa duração (mesmo monolito modular).

**Performance Goals**: ADX/`ATR_ratio` são cálculos vetorizados sobre o DataFrame já em memória
(mesmo custo de qualquer outro indicador `ta` já calculado) — sem impacto perceptível no ciclo de 60s
do bot nem no tempo de backtest. `strategy/breakout.py` usa `rolling().max()/.min()`, mesma classe de
custo que as médias móveis já calculadas.

**Constraints**: Constitution princípio VII (Explain Before Code) é particularmente relevante aqui —
mudanças em `strategy/ema_rsi.py` (US1-US3) são todas guardadas por flags desligadas por padrão
(`REGIME_FILTER_ENABLED`, `HIGH_VOLATILITY_FILTER_ENABLED`, `ADAPTIVE_BOLLINGER_ENABLED`), preservando
FR-010/SC-004 (compatibilidade total para quem não habilitar). `strategy/breakout.py` (US4) é um
arquivo novo, sem risco de regressão na estratégia existente. `run_backtest()` ganha um parâmetro
`strategy` opcional — mudança de assinatura verificada como retrocompatível com os 3 chamadores atuais
(`backtesting/multi.py`, `backtesting/scanner.py`, `main.py`).

**Scale/Scope**: Mesma escala das specs anteriores. `strategy/breakout.py` testada nas janelas 50,
150, 200 períodos citadas na spec.

## Constitution Check

*GATE: Deve passar antes da Fase 0. Reavaliado após a Fase 1.*

Referência: `.specify/memory/constitution.md` v1.0.0.

| Princípio | Avaliação |
|---|---|
| I. Safety First | PASS — nenhuma mudança toca `execution/`/`risk/manager.py`/dinheiro real. Todos os novos filtros de estratégia são desligados por padrão. |
| II. No Secrets in Code | PASS — nenhuma configuração nova envolve segredo. |
| III. Test Before Implement | PASS — cada tarefa em `tasks.md` terá teste escrito antes da implementação, mesmo padrão das specs anteriores. |
| IV. Incremental Delivery | PASS — plano dividido em US1 → US2 → US3 → US4 → US5 → Polish, cada uma um commit pequeno. |
| V. Observability Mandatory | PASS — regime de mercado (US1) registrado em `data/decisions.csv`; bloqueios de volatilidade elevada (US2) usam o mesmo campo `blockers`/`decision` já existente por ciclo. |
| VI. Idempotency and Reconciliation | N/A — esta spec não toca execução de ordens nem estado persistido em `state.json`. |
| VII. Explain Before Code | PASS — este `plan.md` e `research.md` documentam as decisões (limiares, precedência de bloqueios, reuso de `evaluate_approval`) antes de qualquer tarefa de implementação. |

Nenhuma violação identificada. Nenhuma entrada necessária em Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/006-evolucao-estrategia-novas/
├── spec.md                       # Especificação (User Stories, requisitos, sucesso)
├── plan.md                       # Este arquivo
├── research.md                   # Fase 0 — decisões técnicas e alternativas consideradas
├── data-model.md                 # Fase 1 — entidades novas/alteradas
├── quickstart.md                 # Fase 1 — como validar cada User Story manualmente
├── contracts/
│   └── cli.md                    # Fase 1 — contrato do comando `compare`/config afetados
├── checklists/
│   └── requirements.md           # Checklist de qualidade da spec
└── tasks.md                      # Fase 2 (/speckit-tasks) — tarefas executáveis
```

### Source Code (repository root)

```text
config/
└── settings.py                 # ✏️ REGIME_ADX_THRESHOLD, REGIME_FILTER_ENABLED,
                                   HIGH_VOLATILITY_ATR_RATIO, HIGH_VOLATILITY_FILTER_ENABLED,
                                   ADAPTIVE_BOLLINGER_ENABLED, BREAKOUT_WINDOW
strategy/
├── ema_rsi.py                  # ✏️ adx/regime/atr_ratio nos indicadores (US1/US2);
│                                  not_overextended adaptativo (US3) -- tudo atras de flag
└── breakout.py                 # NOVO (US4) -- BreakoutStrategy(BaseStrategy)
backtesting/
├── engine.py                   # ✏️ run_backtest() ganha parametro `strategy` opcional
│                                  (default EmaRsiStrategy(), retrocompativel)
└── compare.py                  # NOVO (US5) -- run_comparison(), reusa evaluate_approval
trading/
└── decision_logger.py          # ✏️ grava coluna `regime` em data/decisions.csv (US1)
data/
└── decisions_analysis.py       # sem alteracao de schema alem da coluna nova (mesmo padrao
                                   ja usado para `blockers` na spec 005)
main.py                         # ✏️ novo comando `compare`/`comparar`
```

**Structure Decision**: Mesmo monolito modular já estabelecido (`config/`, `strategy/`,
`backtesting/`, `trading/`, `execution/`, `data/`, `utils/`). Nenhuma reestruturação de diretórios.

## Complexity Tracking

Nenhuma violação de Constitution Check — seção vazia, nenhuma justificativa necessária.
