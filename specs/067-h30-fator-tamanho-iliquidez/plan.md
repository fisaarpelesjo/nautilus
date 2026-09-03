# Implementation Plan: H30 — fator de tamanho/iliquidez (cross-sectional, sem timing)

**Branch**: `067-h30-fator-tamanho-iliquidez` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/fator_tamanho.py` (novo): `selecionar_cesta` ordena pares
por volume médio (USDT); `simular_cesta` roda uma cesta igualmente
ponderada com rebalanceamento periódico, custo sobre o giro;
`avaliar_fator_tamanho` compara cesta ilíquida vs. líquida em treino e
validação (reusa `split_treino_validacao` de H10) sob 3 multiplicadores
de slippage. `cmd_fator_tamanho()` (novo, `main.py`) imprime a tabela
comparativa.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — reusa
`backtesting/pairs_trading.py::UNIVERSO_AMPLO_HISTORICO_COMPLETO`/
`split_treino_validacao`, `config.settings.BACKTEST_FEE_RATE`/
`BACKTEST_SLIPPAGE_PCT`

**Storage**: `reports/fator_tamanho_*.json` (padrão `export_report`)

**Testing**: pytest — seleção por volume (menor/maior), simulação sem
movimento de preço devolve capital intacto, custo é cobrado no
rebalanceamento, valorização de um ativo é capturada, multiplicador de
slippage maior reduz capital final, ausência de pares válidos não
quebra, `avaliar_fator_tamanho` aceita dados sem rede

**Target Platform**: CLI local (`python main.py fator_tamanho`);
produção intocada

**Performance Goals**: 22 pares × 6.000 candles, 2 fatias × 2 critérios
× 3 multiplicadores — mesma ordem de custo de outros comandos de
pesquisa desta sessão

**Constraints**: FR-003 — custo sobre giro, não nocional inteiro;
FR-004 — nunca um único número de custo; FR-006 — mesmo corte
compartilhado de H10

**Scale/Scope**: 1 módulo novo (~140 linhas), 1 comando CLI novo

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/`, `risk/` ou `strategy/`. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre seleção/simulação/sensibilidade antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Módulo + comando + testes num tópico; execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** D1-D5 (universo, construção da cesta, baseline, custo, disciplina fora da amostra) declarados no docstring do módulo antes de qualquer medição real. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/067-h30-fator-tamanho-iliquidez/
├── spec.md
├── plan.md
├── research.md
├── quickstart.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
backtesting/
└── fator_tamanho.py    # novo: selecionar_cesta, simular_cesta, avaliar_fator_tamanho

main.py                 # +cmd_fator_tamanho, +"fator_tamanho" em COMMANDS

tests/
└── test_fator_tamanho.py   # novo
```

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — D1-D5 declarados no docstring de `fator_tamanho.py`
antes de qualquer medição real.

**Fase 1** — sem `data-model.md`/`contracts/` formais (entidade
trivial, já descrita em `spec.md`).

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: módulo + comando + testes num tópico;
execução real + registro noutro.
