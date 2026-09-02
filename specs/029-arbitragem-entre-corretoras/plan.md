# Implementation Plan: H15 — Arbitragem entre corretoras

**Branch**: `029-arbitragem-entre-corretoras` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

## Summary

Construir o **instrumento de amostragem**, não um veredito: medir, a cada
execução, o diferencial líquido de arbitragem entre pares de seis corretoras
(D1), sobre volume de US$ 10.000 por perna (D2), descontando taxa de tomador
dos dois lados (D3), qualificado pelo intervalo entre leituras contra um teto
de 2.000 ms (D4), e persistir cada observação em `data/arbitragem.jsonl` (D5)
para que execuções sucessivas acumulem a amostra que um veredito real vai
exigir. Executabilidade operacional é declarada estática (D6): inexecutável
hoje por capital pré-posicionado, chaves múltiplas e ausência de execução
simultânea — independente do que a medição encontrar.

A medição preliminar (research.md) já mediu o instantâneo: diferencial bruto
máximo +0,0203% contra custo mínimo de 0,200%, uma ordem de grandeza abaixo.
Esta fase não recalcula esse número — constrói o mecanismo que o repete,
execução após execução, até existir amostra suficiente para um veredito.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: `ccxt` (já usado, `binance` era o único exchange
instanciado até aqui — esta spec instancia `bybit`/`okx`/`kucoin`/`gate`/
`kraken` também, todos via `fetch_order_book` público, sem chave) — **nenhuma
dependência nova**

**Storage**: `data/arbitragem.jsonl`, um arquivo por acréscimo (D5) — mesmo
padrão de `logs/events-*.jsonl`

**Testing**: pytest, estendendo `tests/`

**Target Platform**: CLI local; produção (`trading/runner.py`) intocada — FR-014

**Performance Goals**: uma execução consulta até 6 corretoras uma vez cada
(latência quente medida: 272–1.082 ms por consulta, research.md) e produz até
15 combinações (C(6,2), todas mesma cotação USDT). Segundos, não minutos —
compatível com execução manual repetida ou agendamento futuro.

**Constraints**: nenhuma ordem enviada (FR-012); nenhuma chave de API exigida
(FR-013); comparação nunca entre cotações diferentes (FR-003); custo
desconhecido nunca vira zero (FR-006).

**Scale/Scope**: 6 corretoras, 1 par por execução (`BTC/USDT`, default),
crescendo por acréscimo em `data/arbitragem.jsonl` a cada execução.

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Nenhum arquivo de `risk/`, `execution/order_manager.py` ou `trading/position_lifecycle.py` é tocado. `execution/liquidity.py` é referência de padrão (caminhar o book), não é importado — arbitragem lê corretoras que o bot nunca opera. |
| **II. No Secrets in Code** | **Conforme.** FR-013: nenhuma chave de API é exigida ou usada; as seis corretoras são consultadas só por endpoint público. |
| **III. Test Before Implement** | **Conforme.** `tasks.md` define critério de teste por task antes da implementação; suite única em `tests/test_arbitragem.py`. |
| **IV. Incremental Delivery** | **Conforme.** Ver Fases abaixo — normalização de livro, comparação, persistência e comando CLI em tópicos separados. |
| **V. Observability Mandatory** | **Conforme.** Persistência em `data/arbitragem.jsonl` é o pipeline de observação desta spec, análogo a `logs/events-*.jsonl` — não introduz um segundo sistema de log paralelo, é dado de pesquisa, não evento de risco. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem é enviada; não há posição para reconciliar. |
| **VII. Explain Before Code** | **Conforme.** Este `plan.md`, com D1–D6 já commitados em `research.md` antes de qualquer código (commit `34e8eaa`). |

Nenhuma violação a justificar em Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/029-arbitragem-entre-corretoras/
├── plan.md              # este arquivo
├── research.md          # Fase 0 (já commitado)
├── data-model.md         # Fase 1
├── contracts/
│   └── cli-arbitragem.md # Fase 1
├── quickstart.md         # Fase 1
└── tasks.md               # Fase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
data/
├── paths.py                 # +ARBITRAGEM_FILE
└── arbitragem_store.py      # NOVO: append/leitura de data/arbitragem.jsonl

backtesting/
└── arbitragem.py            # NOVO: normalização de livro, comparação,
                              #       ciclo de medição, agregação histórica

main.py                      # +cmd_arbitragem, comando "arbitragem"

tests/
└── test_arbitragem.py       # NOVO
```

**Structure Decision**: segue o padrão já estabelecido pelas hipóteses
anteriores (`backtesting/geometria.py`, `backtesting/barras.py`,
`backtesting/modelo.py` — nenhuma delas é um backtest literal, todas vivem em
`backtesting/` porque é onde o projeto já agrupa a bateria de pesquisa H*) com
uma exceção: a persistência ganha módulo próprio em `data/arbitragem_store.py`
em vez de viver dentro de `backtesting/arbitragem.py`, porque **acumula entre
execuções** — o mesmo motivo pelo qual `data/killswitch_store.py` é arquivo
próprio e não uma função dentro de `execution/order_manager.py`. `backtesting/
arbitragem.py` importa o store, nunca escreve o arquivo diretamente.

`execution/liquidity.py` **não é importado**: seu `estimate_slippage_pct`
caminha o book para dimensionar uma ordem que o bot vai enviar; aqui a leitura
é de corretoras que o bot nunca toca, e misturar os dois caminhos aproximaria
código de pesquisa do código de execução real — o oposto do que o Princípio I
pede. A lógica de caminhar o book é pequena o bastante (< 20 linhas) para
duplicar em vez de abstrair entre os dois domínios.

## Complexity Tracking

Vazio — nenhuma violação de princípio a justificar.

## Fases

**Fase 0 ✅** — `research.md`: D1 (seis corretoras), D2 (US$ 10k), D3 (custo
tomador dos dois lados), D4 (teto de 2.000 ms), D5 (JSONL por acréscimo), D6
(inexecutável hoje). Medição preliminar registrada.

**Fase 1** — este `plan.md` + `data-model.md` + `contracts/cli-arbitragem.md`
+ `quickstart.md`.

**Fase 2** — `tasks.md` (`/speckit-tasks`).

**Fase 3** — implementação (`/speckit-implement`), tópico por tópico:
1. `data/arbitragem_store.py` + `ARBITRAGEM_FILE`
2. `backtesting/arbitragem.py`: normalização de livro (2 e 3 campos, D1) +
   preço médio de execução sobre volume declarado
3. `backtesting/arbitragem.py`: comparação (custo, latência, cotação) e ciclo
   de medição multi-corretora com falha isolada (FR-011)
4. `backtesting/arbitragem.py`: agregação histórica (período coberto, N,
   estado)
5. `python main.py arbitragem [PAR]` + saída em terminal + `export_report`

**Fase 4 (fora desta spec)** — o veredito. Só quando `N` acumulado em
`data/arbitragem.jsonl` atingir o mínimo declarado em `data-model.md`
(`MIN_OBSERVACOES_AGREGACAO`), e é tempo passando, não código, o que falta
para chegar lá.
