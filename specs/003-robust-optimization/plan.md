# Implementation Plan: Otimização Sem Overfitting

**Branch**: `003-robust-optimization` | **Date**: 2026-08-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-robust-optimization/spec.md`

## Summary

Fecha o gap de overfitting no `backtesting/optimizer.py`: hoje o grid search escolhe o "melhor"
conjunto de parâmetros olhando só para o histórico inteiro de cada par, sem nunca medir esse conjunto
num período que não influenciou a escolha. Três capacidades, cada uma reusando o motor de backtest
existente sem reescrevê-lo: (US1) split treino/validação no otimizador, reusando
`split_train_validation()` já existente (spec 001); (US2) validação walk-forward — o conjunto vencedor
é testado em ≥3 janelas deslizantes independentes, não só uma; (US3) análise Monte Carlo — reamostra a
ordem da sequência de trades já observada para estimar risco de drawdown/ruína além do valor único já
calculado. Módulo novo `backtesting/robustness.py` concentra US2 e US3 (compartilhado com qualquer
resultado de backtest, não só o do otimizador); US1 estende `backtesting/optimizer.py` in-place.

## Technical Context

**Language/Version**: Python 3.12 (mesmo ambiente das specs 001/002)

**Primary Dependencies**: `pandas`, `random`/`statistics` (stdlib, para o resample Monte Carlo — sem
nova dependência de runtime), `rich` (relatórios), `pytest`.

**Storage**: N/A — mesma natureza de feature de relatório/decisão das specs 001/002, nada novo
persistido em disco.

**Testing**: `pytest` (suíte existente, 132 testes após a spec 002), estendida por esta feature.
Monte Carlo usa `random.Random(seed)` com seed fixo nos testes para determinismo (US3 Acceptance
Scenario 3 exige resultado "consistente entre execuções dentro de uma margem razoável" — testável só
com seed controlado).

**Target Platform**: Mesma CLI local (`python main.py optimize [--validate|--walk-forward]`,
`python main.py backtest --montecarlo`).

**Project Type**: CLI (mesmo monolito modular).

**Performance Goals**: O grid search já é o passo mais caro (centenas de combinações × pares); US1
adiciona 1 `simulate_backtest` extra por conjunto de parâmetros já avaliado (validação), não
multiplica o grid. US2 roda o backtest do conjunto vencedor (já escolhido) em K janelas — K
simulate_backtest extras, não uma nova busca em grade. US3 roda milhares de reamostragens em memória
(sem I/O de rede), custo é CPU pura sobre uma lista de trades já calculada — deve completar em segundos
para as amostras típicas deste bot (dezenas de trades).

**Constraints**: Não pode alterar a saída de `python main.py optimize` sem as novas flags (FR-009);
continua sem exigir credenciais (FR-010, herdado das specs 001/002).

**Scale/Scope**: Mesma escala das specs anteriores — `OPTIMIZE_PAIRS` (5 pares) × grid de parâmetros
já existente (centenas de combinações).

## Constitution Check

*GATE: Deve passar antes da Fase 0. Reavaliado após a Fase 1.*

Referência: `.specify/memory/constitution.md` v1.0.0.

| Princípio | Avaliação |
|---|---|
| I. Safety First | PASS — feature é só de relatório/backtest (leitura), não toca `risk/manager.py`, `execution/order_manager.py` nem `trading/position_lifecycle.py`. |
| II. No Secrets in Code | PASS — nenhuma configuração nova envolve segredo. |
| III. Test Before Implement | PASS — cada tarefa em `tasks.md` terá teste escrito antes da implementação, mesmo padrão das specs 001/002. |
| IV. Incremental Delivery | PASS — plano dividido em Foundational (se necessário) → US1 → US2 → US3 → Polish, cada uma um commit pequeno. |
| V. Observability Mandatory | N/A — feature não introduz decisão de risco operacional; é relatório de otimização/backtest, fora do pipeline de eventos JSONL/Telegram. |
| VI. Idempotency and Reconciliation | N/A — não toca execução de ordens. |
| VII. Explain Before Code | PASS — este `plan.md` documenta as decisões de design (módulo novo `robustness.py`, superfície de CLI) antes de qualquer tarefa de implementação. |

Nenhuma violação identificada. Nenhuma entrada necessária em Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/003-robust-optimization/
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

```text
backtesting/
├── optimizer.py               # ✏️ --validate: split treino/validacao no grid search (US1);
│                                 --walk-forward: chama robustness.py para o conjunto vencedor (US2)
├── robustness.py               # NOVO — walk_forward_validate() (US2), monte_carlo_resample() (US3);
│                                 modulo compartilhado, nao preso ao optimizer (US3 opera sobre
│                                 qualquer lista de Trade ja calculada)
├── validation.py               # sem alteracao — split_train_validation() reusado por optimizer.py
└── engine.py                   # sem alteracao — Trade/BacktestResult reusados
config/
└── settings.py                 # sem alteracao nesta spec (limiares de amostra reusam
                                   EDGE_MIN_TRADES de backtesting/approval.py, ver research.md)
main.py                         # ✏️ cmd_otimizar le --validate/--walk-forward de sys.argv (mesmo
                                   padrao de cmd_backtest --validate, spec 001); cmd_backtest le
                                   --montecarlo
tests/
├── test_optimizer.py            # NOVO — testes de US1 (nao havia teste dedicado a optimizer.py
│                                   antes desta spec)
├── test_robustness.py           # NOVO — testes de US2 (walk-forward) e US3 (Monte Carlo)
└── test_main_backtest.py        # ✏️ estende para os novos dispatches de CLI
```

**Structure Decision**: `backtesting/robustness.py` novo em vez de espremer walk-forward e Monte Carlo
dentro de `optimizer.py` — as duas capacidades operam sobre um resultado/params já escolhidos (não
sobre a busca em grade em si) e o Monte Carlo (US3) explicitamente não depende do otimizador (pode
rodar sobre qualquer lista de `Trade`). Mesmo critério de extração já usado nas specs 001/002 (extrair
quando a lógica serve ≥2 consumidores conceituais, aqui: `optimizer.py` e, potencialmente, `edge`/
`backtest` para Monte Carlo). `optimizer.py` ganha as flags mas delega o cálculo pesado para o módulo
novo.

## Complexity Tracking

*Nenhuma violação da Constitution Check — seção vazia intencionalmente.*
