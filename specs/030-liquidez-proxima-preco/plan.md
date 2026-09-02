# Implementation Plan: Profundidade de liquidez próxima ao preço

**Branch**: `030-liquidez-proxima-preco` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

## Summary

`execution/liquidity.py::check_liquidity` soma o valor de **todos** os níveis
do lado ask (até 20) ao calcular `depth_usdt`, sem considerar a distância de
preço em relação ao melhor ask. Passa a somar só os níveis com
`preço ≤ best_ask × (1 + MAX_SPREAD_PCT_ENTRY)` (D1) — reusa a constante já
existente, sem novo parâmetro de `.env`. Medido em 22 pares reais: **zero
divergência de decisão no tamanho de ordem que o bot roda hoje** (US$ 100);
divergência real a partir de ~US$ 5.000 em pares de book mais fino (ORCA,
ROBO, COW, HEMI) — o gap que esta spec fecha, adormecido na config atual,
mas real assim que `MAX_ORDER_SIZE_USDT` crescer.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova — `ccxt` (já em uso via
`data/fetcher.py::fetch_order_book`)

**Storage**: N/A — decisão pontual por chamada, nada persistido

**Testing**: pytest, estendendo `tests/test_liquidity.py`

**Target Platform**: caminho de execução real (`trading/position_lifecycle.py`
→ `execution/liquidity.py::check_liquidity`), `TRADING_MODE` paper e live

**Performance Goals**: mesma chamada a `fetch_order_book` já existente;
a soma limitada por preço é O(níveis), idêntica em custo à soma atual

**Constraints**: FR-002 — o requisito de profundidade
(`max(MIN_ORDERBOOK_DEPTH_USDT, 3 × order_size_usdt)`) não muda, só a medição
de quanto está disponível; FR-005/FR-008 — spread check e `order_manager`/
`risk/manager` intocados

**Scale/Scope**: uma função (`check_liquidity`), ~5 linhas alteradas

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme, com atenção.** Toca o caminho de execução real (`check_liquidity` é chamado antes de toda entrada). Mudança é estritamente mais conservadora (nunca aprova o que a versão atual recusaria) — ver research.md, "o novo critério nunca soma mais". Precisa rodar em paper antes de qualquer consideração de live, mas o repo já roda só em paper (VPS). |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` define teste por task antes da implementação, estendendo `tests/test_liquidity.py` já existente. |
| **IV. Incremental Delivery** | **Conforme.** Mudança pequena o bastante para um único tópico/commit — ver Fases. |
| **V. Observability Mandatory** | **Conforme, sem mudança.** `LiquidityCheck.reason` já é o canal de decisão de risco existente; a mensagem de motivo passa a refletir a medição nova, mesmo campo. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada por esta função; ela só aprova/recusa. |
| **VII. Explain Before Code** | **Conforme.** D1 commitado em `research.md` antes de qualquer alteração de código, com medição real anexada. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/030-liquidez-proxima-preco/
├── plan.md              # este arquivo
├── research.md          # Fase 0 (D1, medição)
├── data-model.md         # Fase 1
└── quickstart.md         # Fase 1
```

Sem `contracts/`: `check_liquidity` é uma função interna do caminho de
execução (chamada por `trading/position_lifecycle.py`), não uma interface
exposta a usuário ou outro sistema — mesmo critério que já levou 024-028 a
não terem `contracts/` quando não expõem CLI novo.

### Source Code (repository root)

```text
execution/
└── liquidity.py         # check_liquidity: depth_usdt limitado por preco
tests/
└── test_liquidity.py    # +casos: profundidade fantasma distante, sem
                          #  regressao nos casos ja aprovados
```

Nada mais é criado ou movido. `estimate_slippage_pct` não é alterado (D1,
Alternativas consideradas).

## Complexity Tracking

| Decisão | Por que necessária | Alternativa rejeitada |
|---|---|---|
| Reusar `MAX_SPREAD_PCT_ENTRY` em vez de nova constante | Mesma pergunta ("desvio de preço aceito") já tem resposta declarada no mesmo módulo | Constante dedicada: duplicaria o conceito, risco de divergir em edição futura de `.env` |
| Não compartilhar código com `estimate_slippage_pct` (FR-004 lido como princípio, não como função única) | As duas funções fixam variáveis diferentes — depth fixa o desvio de preço e mede volume; slippage fixa o volume e mede preço médio. Forçar o mesmo laço inverteria qual é a entrada e qual é a saída em uma das duas | Uma função genérica "caminha o book" parametrizada pelas duas formas: abstração para dois usos, quando a soma limitada por preço é uma linha (comprehension) — violaria a diretriz do projeto contra abstração prematura |

## Fases

**Fase 0 ✅** — D1 (critério de proximidade = `MAX_SPREAD_PCT_ENTRY` reusado),
medição em 22 pares reais, teste de divergência de decisão em 4 tamanhos de
ordem.

**Fase 1 ✅** — `data-model.md` (só o campo `depth_usdt` de `LiquidityCheck`
muda de definição, nenhuma entidade nova) + `quickstart.md`. Sem
`contracts/` (função interna, não CLI).

**Fase 2** — `tasks.md` (`/speckit-tasks`).

**Fase 3** — implementação (`/speckit-implement`), um único tópico: alterar
`check_liquidity`, estender `tests/test_liquidity.py`, rodar suite completa
para confirmar zero regressão nos testes existentes de liquidez e nos
consumidores (`trading/position_lifecycle.py`, `execution/order_manager.py`).
