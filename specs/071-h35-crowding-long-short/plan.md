# Implementation Plan: H35 — Crowding via long/short ratio e open interest (Binance)

**Branch**: `071-h35-crowding-long-short` | **Date**: 2026-09-06 | **Spec**: [spec.md](spec.md)

## Summary

`data/long_short_ratio.py` (novo): `fetch_long_short_ratio_history`/
`fetch_open_interest_history` via os métodos unificados ccxt
(`fetch_long_short_ratio_history`/`fetch_open_interest_history`, mesma
exchange futures de `data/funding.py`). `backtesting/crowding_extremo.py`
(novo): `avaliar_par` busca preço + os dois indicadores, corta
cronologicamente treino/validação DENTRO da janela curta real (retenção
medida do endpoint, não os 2000 candles usados por funding), calibra o
limiar do decil mais baixo de long/short ratio só no treino, exige open
interest acima da mediana de treino no mesmo instante, rotula pela barreira
tripla (sem alteração) e aplica `supera_empate_com_confianca` sobre a
contagem agregada. `cmd_crowding()` (novo, `main.py`) roda sobre
`UNIVERSO_H11` e imprime o pooled, incluindo a retenção real medida.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova como pacote — `ccxt` já expõe
`fetch_long_short_ratio_history`/`fetch_open_interest_history` como
métodos unificados (confirmado por probe real nesta sessão); reusa
`strategy/barreira_tripla.py`, `backtesting/modelo.py`
(`limiar_de_empate`/`supera_empate_com_confianca`), `backtesting/horizonte.py`
(`UNIVERSO_H11`/`preparar`) sem alteração

**Storage**: `reports/crowding_*.json` (padrão `export_report`)

**Testing**: pytest — cálculo de decil/mediana só no treino (não vaza
validação), descarte de candles anteriores ao início real do histórico do
endpoint (nunca ffill retroativo), evento exige AMBAS confirmações
(long/short ratio no decil E open interest acima da mediana), agregação
pooled, `supera_empate_com_confianca` delegado sem reimplementar Wilson CI,
par sem mercado perpétuo é descartado sem abortar os demais

**Target Platform**: CLI local (`python main.py crowding`); produção
intocada

**Performance Goals**: mesma ordem de custo de `python main.py
funding_extremo` — 12 pares × busca de preço + long/short ratio + open
interest, janela de dados muito menor (retenção real do endpoint, ~31
dias) que reduz o custo de rede por par em relação a H26

**Constraints**: FR-002 — retenção real medida antes de dimensionar a
janela, nunca presumida igual à de funding; FR-003 — candles anteriores ao
início do histórico do endpoint são descartados, nunca ffill retroativo;
FR-004 — limiar calibrado só no treino; FR-006/FR-007 — significância
sempre via `supera_empate_com_confianca` sobre a contagem agregada, nunca
razão pontual isolada por par

**Scale/Scope**: 2 módulos novos (~50 + ~110 linhas), 1 comando CLI novo

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Módulo de pesquisa, sem import por `trading/`, `execution/` ou `risk/`. |
| **II. No Secrets in Code** | **Conforme.** Endpoints públicos, sem chave. |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre calibração/descarte de candles antigos/confirmação dupla/agregação antes da execução real. |
| **IV. Incremental Delivery** | **Conforme.** Módulos + comando + testes num tópico; execução real + registro noutro. |
| **V. Observability Mandatory** | **N/A direto.** Resultado via `export_report`, mesmo padrão dos comandos de pesquisa. |
| **VI. Idempotency and Reconciliation** | **N/A.** Nenhuma ordem enviada. |
| **VII. Explain Before Code** | **Conforme.** Hipótese, achado empírico de retenção e expectativa honesta (REPROVADA, base histórica de §6.3-b) declarados em `spec.md`/`research.md` antes de qualquer medição de estratégia. |

Nenhuma violação a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/071-h35-crowding-long-short/
├── spec.md
├── plan.md
├── research.md
├── quickstart.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
data/
└── long_short_ratio.py         # novo: fetch_long_short_ratio_history, fetch_open_interest_history

backtesting/
└── crowding_extremo.py         # novo: avaliar_par, avaliar_universo, agregar_pooled

main.py                         # +cmd_crowding, +"crowding" em COMMANDS

tests/
└── test_crowding_extremo.py    # novo
```

## Complexity Tracking

Vazio.

## Fases

**Fase 0 ✅** — D1-D6 (limiar, confirmação de open interest, mecânica de
trade, alinhamento causal, disciplina estatística, retenção real medida)
declarados em `research.md` antes de qualquer medição real.

**Fase 1** — sem `data-model.md`/`contracts/` formais (entidade trivial,
já descrita em `spec.md`).

**Fase 2** — `tasks.md`.

**Fase 3** — implementação: módulos + comando + testes num tópico;
execução real + registro noutro.
