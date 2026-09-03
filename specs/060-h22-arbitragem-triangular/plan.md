# Implementation Plan: H22 — arbitragem triangular intra-corretora

**Branch**: `060-h22-arbitragem-triangular` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

`backtesting/arbitragem_triangular.py` (novo): `medir_triangulo` lê os
três livros do triângulo em paralelo (`ThreadPoolExecutor`, reusa
`LeituraLivro`/`normalizar_niveis` de `backtesting/arbitragem.py`),
calcula as duas direções do ciclo caminhando profundidade real
(`_comprar`/`_vender`), classifica e persiste
(`data/arbitragem_triangular_store.py`, JSONL por acréscimo). `agregar`
conta observações por (triângulo, direção). `cmd_triangular()` (novo,
`main.py`) mede um ciclo e imprime.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — reusa `data/fetcher.py::get_exchange`
(spot, já cacheado), `backtesting/arbitragem.py::LeituraLivro`/`normalizar_niveis`
sem alteração

**Storage**: `data/arbitragem_triangular.jsonl` (novo, mesmo padrão de
`data/arbitragem.jsonl`), `reports/triangular_*.json` (`export_report`)

**Testing**: pytest — `_comprar`/`_vender` puros (preenchimento total e
parcial), `_preenchido`, ciclo balanceado (sem oportunidade após custo),
ciclo desbalanceado (detecta oportunidade), perna indisponível aborta
sem medição parcial, profundidade insuficiente, persistência,
`agregar` conta por (triângulo, direção) e exige mínimo na direção
menos coberta

**Target Platform**: CLI local (`python main.py triangular`), campanha
real no VPS; produção intocada, nenhuma permissão de API muda

**Performance Goals**: três leituras de order book em paralelo por
ciclo — mesma ordem de custo de uma combinação de H15

**Constraints**: FR-002 — nunca extrapola além da profundidade real
entregue pela perna anterior; FR-006 — zero execução real; FR-007 —
nunca produz veredito de aprovação/reprovação

**Scale/Scope**: 2 módulos novos (~230 linhas), 1 comando CLI novo

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Só leitura de order book público, sem credencial, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre a mecânica pura e os casos de borda antes da campanha real. |
| **IV. Incremental Delivery** | **Conforme.** Módulos + comando + testes num tópico; campanha real (VPS) + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report` + persistência JSONL, mesmo padrão de H15. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Hipótese (sem oportunidade líquida na maioria) e alternativa (desalinhamentos momentâneos capturáveis) declaradas em `spec.md`/`research.md` antes de qualquer campanha. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/060-h22-arbitragem-triangular/
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
└── arbitragem_triangular.py    # novo

data/
├── paths.py                     # +ARBITRAGEM_TRIANGULAR_FILE
└── arbitragem_triangular_store.py   # novo

main.py                          # +cmd_triangular, +"triangular" em COMMANDS

tests/
└── test_arbitragem_triangular.py   # novo
```

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — hipótese e alternativa declaradas em `spec.md`;
`research.md` documenta por que o obstáculo dominante de H15 (latência
entre corretoras) não se aplica aqui, e o que continua incerto
(concorrência de bots de alta frequência intra-corretora).

**Fase 1** — sem `data-model.md`/`contracts/` formais (entidades já
descritas em `spec.md`).

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: módulos + comando + testes num tópico;
campanha real (VPS) + registro noutro.
