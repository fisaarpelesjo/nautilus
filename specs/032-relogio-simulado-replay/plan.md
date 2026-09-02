# Implementation Plan: Relógio simulado no replay

**Branch**: `032-relogio-simulado-replay` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

## Summary

`execution/order_manager.py` ganha `_simulated_now` (módulo, default
`None`) e `_now()`, que substitui 14 dos 15 pontos de chamada de
`datetime.now()` levantados por medição (D2, research.md) — a exceção
(salt de `client_order_id`) fica fora por não afetar decisão nem
timestamp reportado. Fora do ambiente isolado do replay, `_now() ==
datetime.now()` sempre (FR-002, garantia testada). `trading/replay.py`
avança `_simulated_now` para o timestamp de cada candle (D3) e passa a
chamar `check_circuit_breaker_timeout()` a cada ciclo — chamada que hoje
não existe no replay (achado de auditoria do spec.md, confirmado por
leitura de código). A ressalva de `compare_to_backtest()` sobre relógio
real é reescrita (D5) para não descrever um defeito já corrigido.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: nenhuma nova

**Storage**: N/A — `_simulated_now` é estado de módulo em memória, nunca
persistido

**Testing**: pytest, estendendo `tests/test_replay.py` (ou arquivo
equivalente de `trading/replay.py`) + `tests/test_order_manager*.py`
(cooldown/drawdown/circuit breaker com `_now()`)

**Target Platform**: `trading/replay.py::run_replay()` e
`execution/order_manager.py` — usado por `TRADING_MODE` paper e live
(intocado fora do replay) e pelo comando `python main.py replay`

**Performance Goals**: `_now()` é uma comparação + eventual chamada a
`datetime.now()` — custo desprezível, mesma ordem de grandeza da chamada
direta que substitui

**Constraints**: FR-002 é hard constraint — `_now()` sem
`_simulated_now` setado MUST ser idêntico a `datetime.now()`, testado
explicitamente antes de qualquer outra mudança ser aceita

**Scale/Scope**: 14 pontos de chamada substituídos numa função de
indireção, `Position.opened_at` (default factory), 3 mudanças em
`trading/replay.py` (avanço do relógio, chamada de timeout, ressalva
reescrita)

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme, com atenção — mesma nota da spec 020/032 anteriores.** Toca `execution/order_manager.py`, código do caminho de execução real. Mitigação: `_now()` é idêntica a `datetime.now()` fora do replay **por construção** (`_simulated_now` só é setado dentro de `_isolated_order_manager_environment`), e isso é testado, não só alegado (US3 do spec.md). |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Conforme.** `tasks.md` cobre a garantia de zero-mudança (US3) antes de qualquer outra task tocar `order_manager.py` — mesmo padrão do Foundational da spec 034. |
| **IV. Incremental Delivery** | **Conforme.** `_now()`/migração dos 14 pontos num tópico; avanço do relógio + chamada de timeout ausente + ressalva reescrita noutro. |
| **V. Observability Mandatory** | **N/A.** Não é evento de risco novo — `_now()` não muda o que é logado, só a fonte do instante. |
| **VI. Idempotency and Reconciliation** | **N/A.** Replay nunca envia ordem real; reconciliação é no-op em paper e o replay nunca chama. |
| **VII. Explain Before Code** | **Conforme.** D1-D5 commitados em `research.md`, com o levantamento completo dos 15 pontos de chamada medido antes de qualquer edição. |

**Nota sobre tocar `execution/order_manager.py`, declarada e não
minimizada.** Mesma classe de risco que a extensão de
`backtesting/modelo.py` na spec 034 — a garantia de comportamento
idêntico fora do escopo alterado é testável e será testada, não uma
alegação em `research.md`.

## Project Structure

### Documentation (this feature)

```text
specs/032-relogio-simulado-replay/
├── plan.md              # este arquivo
├── research.md          # Fase 0 (D1-D5, 15 pontos de chamada levantados)
├── data-model.md         # Fase 1
└── quickstart.md         # Fase 1
```

Sem `contracts/`: mudança interna a `execution/order_manager.py` e
`trading/replay.py`, sem CLI nova (`python main.py replay` já existe,
assinatura intocada).

### Source Code (repository root)

```text
execution/
└── order_manager.py      # +_simulated_now, +_now(); 14 pontos de
                           # datetime.now() -> _now()

trading/
└── replay.py              # _isolated_order_manager_environment: +
                            # restaura _simulated_now
                            # run_replay: avanca _simulated_now por
                            # candle + chama check_circuit_breaker_timeout
                            # compare_to_backtest: ressalva reescrita

tests/
├── test_order_manager_*.py  # +testes: _now() sem _simulated_now ==
│                            # datetime.now() (regressao)
└── test_replay.py           # (ou arquivo equivalente) +testes:
                             # cooldown/drawdown/circuit breaker avancam
                             # com o candle simulado; timeout e chamado;
                             # relogio real restaurado ao sair
```

## Complexity Tracking

Vazio — nenhuma violação de princípio a justificar.

## Fases

**Fase 0 ✅** — D1 (mecanismo `_now()`) → D2 (15 pontos de chamada
levantados, 14 no escopo) → D3 (avanço do relógio + chamada de timeout
ausente) → D4 (restauração) → D5 (ressalva reescrita).

**Fase 1 ✅** — `data-model.md` + `quickstart.md`. Sem `contracts/`.

**Fase 2** — `tasks.md` (`/speckit-tasks`).

**Fase 3** — implementação (`/speckit-implement`), dois tópicos:
1. `_simulated_now`/`_now()` em `execution/order_manager.py` + garantia
   de zero-mudança testada (mesmo padrão do Foundational da spec 034)
2. `trading/replay.py`: avanço do relógio, chamada de timeout ausente,
   ressalva reescrita — com testes de cooldown/drawdown/circuit breaker
   avançando por tempo simulado
