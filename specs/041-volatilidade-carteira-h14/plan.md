# Implementation Plan: Dimensionamento por volatilidade na carteira de H14

**Branch**: `041-volatilidade-carteira-h14` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`_simular_carteira_core` (spec 037) ganha um parâmetro opt-in
`usar_dimensionamento_vol: bool = False`. Quando `True`, multiplica o
`order_size` de cada nova entrada por
`fator_volatilidade(row["atr_ratio"])` (`backtesting/volatilidade.py`,
spec 025, reusado sem alteração), aplicado **depois** do teto por ordem
e da reserva de caixa já existentes (FR-002). Default `False` reproduz o
resultado já publicado (28,66% de drawdown, spec 037) byte a byte —
regressão testada antes de qualquer execução real.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova —
`backtesting/volatilidade.py::fator_volatilidade`/`ParametrosVolatilidade`
(spec 025), `backtesting/portfolio_h14.py::_simular_carteira_core`/
`simular_carteira` (spec 037)

**Storage**: `reports/carteira_vol_*.json` (padrão `export_report` já
existente)

**Testing**: pytest, `tests/test_portfolio_h14.py` (extensão)

**Target Platform**: CLI local (`python main.py carteira_vol`); produção
intocada

**Performance Goals**: mesma ordem de grandeza de `carteira` (spec 037,
12 pares) — mais leve que `carteira_ampla` (spec 040, 34 pares)

**Constraints**: FR-003 — o fator só pode reduzir o tamanho, nunca
ampliar (herdado de `fator_volatilidade`, não revalidado aqui); FR-004 —
comportamento default idêntico byte a byte ao já publicado

**Scale/Scope**: 1 parâmetro novo em função já existente, 1 comando CLI

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/` (FR-006). |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre a regressão do caminho default e o teto do fator antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Parâmetro + regressão num tópico; comando CLI + execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão de `carteira`/`carteira_ampla`. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** `fator_volatilidade`/alvo/piso já declarados e medidos em spec 025 — nada novo a declarar além do ponto de chamada (D1, `research.md`). |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/041-volatilidade-carteira-h14/
├── plan.md              # este arquivo
├── research.md          # Fase 0 (D1)
├── data-model.md         # Fase 1
└── quickstart.md         # Fase 1
```

Sem `contracts/`: comando de pesquisa segue o padrão já estabelecido.

### Source Code (repository root)

```text
backtesting/
└── portfolio_h14.py       # ~_simular_carteira_core/simular_carteira
                            # ganham usar_dimensionamento_vol=False
                            # (opt-in); backtesting/volatilidade.py
                            # consumido, nao alterado

main.py                    # +cmd_carteira_vol

tests/
└── test_portfolio_h14.py   # +regressao do caminho default +teste do fator
```

`backtesting/volatilidade.py`, `backtesting/engine.py`,
`backtesting/approval.py` **não são alterados** — só consumidos.

## Complexity Tracking

Vazio — nenhuma violação de princípio a justificar.

## Fases

**Fase 0 ✅** — D1 (ponto de aplicação do fator: depois do
dimensionamento existente, mesmo princípio de spec 025).

**Fase 1 ✅** — `data-model.md` + `quickstart.md`. Sem `contracts/`.

**Fase 2** — `tasks.md` (`/speckit-tasks`).

**Fase 3** — implementação (`/speckit-implement`), dois tópicos:
1. `usar_dimensionamento_vol` em `_simular_carteira_core`/`simular_carteira`
   + regressão do caminho default
2. `cmd_carteira_vol()` (CLI) + execução real (VPS) + comparação
   registrada em `docs/research/registro-de-hipoteses.md` §4.13/§4.15
