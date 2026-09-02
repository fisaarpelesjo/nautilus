# Implementation Plan: H17 — Sinais on-chain

**Branch**: `034-sinais-onchain` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

## Summary

Medir se `onchain_addr_growth_7d` (D1: variação de 7 dias da MA7 de
endereços ativos do Bitcoin, `data/onchain.py`, spec 033) eleva a razão de
chances no subconjunto decidido do modelo de H14, numa comparação isolada
BTC/USDT (5 atributos originais vs 5 + on-chain, mesmo par, mesmo período).
Atributo declarado e checado por colinearidade **antes** de qualquer
medição de desempenho (D2: correlação máxima 0,304, bem abaixo do limiar de
0,80). Amostra BTC-only medida e suficiente (D3: `n_treino=1.342`,
`n_teste=586`, ambos ordens de grandeza acima dos mínimos).
`backtesting/modelo.py::avaliar_par` ganha dois parâmetros opcionais com
default que preserva exatamente o resultado publicado de H14 (D4). Merge
causal do dado on-chain (D5) segue a mesma disciplina que corrigiu o MTF na
spec 020 — candle no dia `D` só vê o dia `D-1` completo, cobertura medida
em 100% das linhas.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `data/onchain.py` (spec 033),
`backtesting/modelo.py`/`backtesting/purga.py`/`strategy/
barreira_tripla.py` (spec 027, H14), todos já existentes

**Storage**: reusa `reports/modelo_*.json` (padrão já estabelecido)

**Testing**: pytest, estendendo `tests/test_modelo.py` (parâmetros novos
de `avaliar_par`) + `tests/test_onchain_hipotese.py` (novo, para o merge
causal e o extrator de atributo)

**Target Platform**: CLI local (`python main.py onchain` ou comando
equivalente); produção intocada

**Performance Goals**: uma execução de `avaliar_par` para 1 par (contra 12
do scan completo de H14) — mais rápida que `python main.py modelo`, não
que `python main.py modelo` seja lento hoje

**Constraints**: `avaliar_par()` sem os novos parâmetros MUST produzir
resultado byte-idêntico ao atual (D4) — é a garantia que torna a mudança
em `backtesting/modelo.py` aceitável apesar de H14 ser resultado já
publicado

**Scale/Scope**: 1 atributo novo, 1 par (BTC/USDT), extensão de 2
parâmetros em 1 função existente, 1 função nova de extração/merge

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Nenhum arquivo de `risk/`, `execution/` ou `trading/` tocado. `backtesting/modelo.py` é código de pesquisa, não de execução. |
| **II. No Secrets in Code** | **Conforme.** Fonte on-chain (spec 033) já não exige chave. |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre o merge causal e a garantia de zero-mudança em `avaliar_par` com teste antes da implementação. |
| **IV. Incremental Delivery** | **Conforme.** Extensão de `modelo.py` e o extrator on-chain em tópicos separados — ver Fases. |
| **V. Observability Mandatory** | **N/A direto.** Resultado de pesquisa via `export_report`, mesmo padrão de `modelo`/`barras`/`horizonte` — não é decisão de risco operacional. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** D1-D5 commitados em `research.md`, com medição real (correlação, amostra, cobertura) antes de qualquer alteração de código. |

**Nota sobre tocar `backtesting/modelo.py`, declarada e não minimizada.**
É código que já produziu o resultado publicado de H14. A garantia de D4
(default preserva comportamento exato) é testável e será testada
explicitamente (`tasks.md`) — não é só uma alegação no `research.md`.

## Project Structure

### Documentation (this feature)

```text
specs/034-sinais-onchain/
├── plan.md              # este arquivo
├── research.md          # Fase 0 (D1-D5, medido)
├── data-model.md         # Fase 1
└── quickstart.md         # Fase 1
```

Sem `contracts/`: comando de pesquisa segue o padrão já estabelecido por
`modelo`/`barras`/`horizonte` (sem contrato formal separado nessas specs
também).

### Source Code (repository root)

```text
backtesting/
├── modelo.py                 # +parametros opcionais em avaliar_par()
│                              # (atributos, extrair_atributos_fn) --
│                              # defaults preservam H14 exatamente
└── onchain_hipotese.py       # NOVO: onchain_addr_growth_7d,
                               # construir_extrator_onchain(), merge causal

main.py                       # +cmd_onchain (comando novo)

tests/
├── test_modelo.py             # +teste: avaliar_par() sem parametros novos
│                              # == resultado atual (regressao explicita)
└── test_onchain_hipotese.py   # NOVO
```

## Complexity Tracking

| Decisão | Por que necessária | Alternativa rejeitada |
|---|---|---|
| Parametrizar `avaliar_par` em vez de duplicar | H14 já é resultado publicado; duplicar ~100 linhas arriscaria uma correção futura ser aplicada só numa cópia | `avaliar_par_onchain` separada: ~90% código idêntico, risco de divergência |
| Módulo `onchain_hipotese.py` separado de `data/onchain.py` | spec 033 é infra genérica (não decide métrica); a transformação/merge é decisão específica de H17 | Colocar a lógica em `data/onchain.py`: misturaria infra genérica com decisão de uma hipótese |

## Fases

**Fase 0 ✅** — D1 (atributo declarado) → D2 (colinearidade 0,304, medida)
→ D3 (amostra suficiente, medida) → D4 (extensão de `avaliar_par`,
desenhada) → D5 (merge causal, cobertura 100% medida).

**Fase 1 ✅** — `data-model.md` + `quickstart.md`. Sem `contracts/`.

**Fase 2** — `tasks.md` (`/speckit-tasks`).

**Fase 3** — implementação (`/speckit-implement`), dois tópicos:
1. `avaliar_par()` parametrizada + teste de regressão (garante D4 antes de
   qualquer outra mudança)
2. `backtesting/onchain_hipotese.py` (extrator + merge) + comando CLI +
   execução real, veredito registrado
