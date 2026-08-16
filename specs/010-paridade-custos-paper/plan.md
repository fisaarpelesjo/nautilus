# Implementation Plan: Paridade de Custos entre Paper e Backtest

**Branch**: `010-paridade-custos-paper` | **Date**: 2026-08-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/010-paridade-custos-paper/spec.md`

## Summary

`_paper_buy()`/`_paper_sell()` (`execution/order_manager.py`) ganham a mesma matemática de custo
que `backtesting/engine.py` já usa há várias specs: slippage no preço de entrada/saída
(`price * (1 ± BACKTEST_SLIPPAGE_PCT)`) e taxa sobre o valor nocional (`BACKTEST_FEE_RATE`),
debitada na entrada e descontada na saída. `_live_buy()`/`_live_sell()` não são tocados — execução
real já paga custo real de mercado. Achado de auditoria (2026-08-16): esse gap deixava o bot em
paper mode (rodando 24/7 numa VPS desde 2026-08-16 coletando os dados que vão validar a estratégia)
sistematicamente ~0,3%/round-trip mais otimista que a realidade.

## Technical Context

**Language/Version**: Python 3.12 (mesmo ambiente das specs 001-009)

**Primary Dependencies**: Nenhuma nova — reusa `BACKTEST_FEE_RATE`/`BACKTEST_SLIPPAGE_PCT` já
existentes em `config/settings.py`, já validados em `validate_config()`.

**Storage**: Nenhuma nova — mesmo `data/trades.csv`/`data/state.json` já existentes, só o valor
numérico gravado muda.

**Testing**: `pytest`. Toda validação é unitária (preços/saldos conhecidos), sem depender de dados
reais da Binance nem tempo real passando (FR de independência da spec).

**Target Platform**: Mesma CLI/daemon (`execution/order_manager.py`, caminho `TRADING_MODE=paper`).

**Project Type**: CLI + daemon de longa duração (mesmo monolito modular).

**Performance Goals**: Nenhum — é aritmética adicional trivial sobre valores já calculados, sem
I/O extra.

**Constraints**: Com `BACKTEST_FEE_RATE=0`/`BACKTEST_SLIPPAGE_PCT=0` o comportamento MUST ser
idêntico ao atual (FR-008) — a mudança é estritamente aditiva sobre a fórmula, não uma reescrita.

**Scale/Scope**: Escopo pequeno e cirúrgico — 2 funções (`_paper_buy`, `_paper_sell`), 2 user
stories fortemente acopladas (mesma fórmula, metades entrada/saída).

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Safety First | PASS — muda `execution/order_manager.py`, mas só o caminho `TRADING_MODE=paper` (`_paper_buy`/`_paper_sell`); `_live_buy`/`_live_sell` intocados. Validado inteiramente em paper mode/testes antes de qualquer consideração de live, conforme o princípio exige. |
| II. No Secrets in Code | PASS — nenhuma configuração nova, reusa variáveis já existentes. |
| III. Test Before Implement | PASS — testes com preços/saldos conhecidos escritos antes de cada mudança, incluindo a paridade exata com `simulate_backtest()` (SC-001). |
| IV. Incremental Delivery | PASS — US1 (slippage) → US2 (fee) → Polish, cada uma um commit pequeno testável isoladamente. |
| V. Observability Mandatory | PASS — nenhum pipeline de log novo; `data/trades.csv` continua sendo a única fonte, só com PnL líquido correto. |
| VI. Idempotency and Reconciliation | N/A — não muda como ordens são identificadas nem como o estado é reconciliado, só o valor de custo calculado. |
| VII. Explain Before Code | PASS — este `plan.md` + `research.md` documentam a decisão (reusar as mesmas variáveis do backtest, mesma fórmula) antes do código. |

Nenhuma violação identificada.

## Project Structure

```text
execution/
└── order_manager.py     # ✏️ _paper_buy()/_paper_sell() ganham slippage (US1) e fee (US2)
tests/
└── test_order_manager_safety.py  # ✏️ testes que assumiam custo exato sem taxa são atualizados
                                    #    (não contornados) + novos testes de paridade com o backtest
```

## Complexity Tracking

Nenhuma violação — seção vazia.
