# Implementation Plan: Refresh periódico de pares dinâmicos

**Branch**: `031-refresh-pares-dinamicos` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

## Summary

`trading/runner.py::_load_active_pairs()` só roda no boot. Passa a rodar a
cada `DYNAMIC_PAIRS_REFRESH_CYCLES` ciclos (D1: 1440, ~24h — medido: uma
execução de `select_dynamic_pairs()` custa 36s, 60% de um ciclo de 60s,
incompatível com cadência mais curta). A alteração central de segurança:
`active_pairs = selecionados ∪ {símbolos com posição aberta}` — nunca remove
um par que `manager.has_position()` ainda considera aberto (US2/FR-002),
achado de auditoria feito **antes** de qualquer código, documentado em
`spec.md`/Contexto. Falha durante um refresh preserva a lista vigente (D2).
Todo refresh gera `log_event("dynamic_pairs_refreshed", ...)` (D3).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — reusa `market/selector.py`
(`select_dynamic_pairs`, `selected_symbols`) e `utils/logger.py::log_event`,
ambos já existentes

**Storage**: N/A além do já existente (`logs/events-*.jsonl`)

**Testing**: pytest, `tests/test_runner_dynamic_pairs_refresh.py` (arquivo
novo, mesmo padrão de `tests/test_runner_reconciliation.py` — uma função
extraída e testável com `_FakeManager`, não o loop `run()` inteiro)

**Target Platform**: `trading/runner.py::run()`, loop principal do bot —
`TRADING_MODE` paper e live, só ativo quando `DYNAMIC_PAIRS_ENABLED=true`
(não é a configuração atual do bot)

**Performance Goals**: refresh custa ~36s (medido, research.md D1), uma vez
a cada ~24h — < 0,04% do tempo de operação, sem paralelizar nem otimizar
`select_dynamic_pairs()` (fora de escopo)

**Constraints**: FR-002 é hard constraint — nenhum código de remoção de par
pode rodar sem primeiro consultar `manager.has_position()` para cada símbolo
que sairia da lista

**Scale/Scope**: uma função nova (`_refresh_active_pairs` ou equivalente) +
integração de ~5 linhas no loop principal + 1 constante nova em
`config/settings.py`

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme, com atenção — é o ponto central da spec.** Toca o loop principal de produção. FR-002 existe exatamente para que a mudança nunca comprometa gestão de risco de uma posição aberta. `DYNAMIC_PAIRS_ENABLED=false` (config atual) faz o código novo nunca executar — risco zero até o operador ligar a flag deliberadamente. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre US2 (a guarda de posição aberta) com teste antes de qualquer implementação — é o requisito mais crítico da spec. |
| **IV. Incremental Delivery** | **Conforme.** US1+US2 (o refresh + a guarda, inseparáveis por design — ver spec.md) num tópico; US3 (auditoria) em outro. |
| **V. Observability Mandatory** | **Conforme, e é requisito explícito (US3/D3).** `dynamic_pairs_refreshed` no pipeline já existente. |
| **VI. Idempotency and Reconciliation** | **N/A direto.** Nenhuma ordem enviada por esta mudança; não interage com `clientOrderId` nem reconciliação de saldo. |
| **VII. Explain Before Code** | **Conforme.** D1 (medição real), D2, D3 commitados em `research.md` antes de qualquer código; o achado de segurança central já estava no `spec.md` antes do `plan.md`. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/031-refresh-pares-dinamicos/
├── plan.md              # este arquivo
├── research.md          # Fase 0 (D1 medido, D2, D3)
├── data-model.md         # Fase 1
└── quickstart.md         # Fase 1
```

Sem `contracts/`: mudança é interna ao loop de produção
(`trading/runner.py`), não expõe CLI nem interface nova — mesmo critério de
024-028/030.

### Source Code (repository root)

```text
config/
└── settings.py           # +DYNAMIC_PAIRS_REFRESH_CYCLES

trading/
└── runner.py              # _load_active_pairs() vira ponto de partida;
                            # nova funcao de refresh + chamada periodica no
                            # loop principal (padrao de
                            # RECONCILIATION_INTERVAL_CYCLES)

tests/
└── test_runner_dynamic_pairs_refresh.py   # NOVO: refresh muda a lista,
                            # posicao aberta nunca sai, falha preserva
                            # lista vigente, evento gravado
```

`market/selector.py` **não é alterado** — `select_dynamic_pairs()` e
`selected_symbols()` já fazem exatamente o que esta spec precisa consumir.

## Complexity Tracking

Vazio — nenhuma violação de princípio a justificar.

## Fases

**Fase 0 ✅** — D1 (1440 ciclos, medido: 36s/execução), D2 (falha preserva
lista vigente), D3 (evento `dynamic_pairs_refreshed`).

**Fase 1 ✅** — `data-model.md` (sem entidade nova — `active_pairs` passa a
mutável em runtime) + `quickstart.md`. Sem `contracts/`.

**Fase 2** — `tasks.md` (`/speckit-tasks`).

**Fase 3** — implementação (`/speckit-implement`), dois tópicos:
1. `DYNAMIC_PAIRS_REFRESH_CYCLES` + função de refresh com a guarda de
   posição aberta (US1+US2, inseparáveis) + integração no loop principal
2. Evento de auditoria (US3)
