# Implementation Plan: Singleton de Exchange + Retry de Rate Limit

**Branch**: `011-rate-limit-hardening` | **Date**: 2026-08-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/011-rate-limit-hardening/spec.md`

## Summary

`data/fetcher.py` `get_exchange()` passa a cachear uma instância de `ccxt.binance` por processo
(uma para `sandbox=True`, outra para `sandbox=False`), com `reset_exchange_cache()` explícito para
isolar testes. As 4 funções públicas (`fetch_ohlcv`/`fetch_ticker`/`fetch_balance`/
`fetch_order_book`) passam a rotear a chamada real ao ccxt por um helper de retry que tenta de novo
(até 3 tentativas, backoff exponencial curto) só para `ccxt.RateLimitExceeded`/`ccxt.DDoSProtection`
(HTTP 429/418), propagando qualquer outro erro imediatamente. `backtesting/scanner.py` (achado
durante a especificação: também instanciava `ccxt.binance` direto, num loop por par) passa a usar
o mesmo `get_exchange()`.

## Technical Context

**Language/Version**: Python 3.12 (mesmo ambiente das specs 001-010)

**Primary Dependencies**: `ccxt` (já existente) — `ccxt.RateLimitExceeded`/`ccxt.DDoSProtection`
já expostos pela lib, sem dependência nova.

**Storage**: Nenhuma — cache de instância em memória do processo (`dict` module-level, mesmo padrão
já usado por `_cache` de candles no mesmo arquivo).

**Testing**: `pytest`, com um exchange fake/mock que levanta `ccxt.RateLimitExceeded`/
`DDoSProtection` N vezes antes de suceder, e `time.sleep` mockado nos testes (backoff real não deve
tornar a suíte lenta).

**Target Platform**: Mesma CLI/daemon.

**Project Type**: CLI + daemon de longa duração (mesmo monolito modular).

**Performance Goals**: Retry adiciona no máximo ~3-7s de espera acumulada num pico raro de rate
limit (backoff curto) — não impacta o caminho feliz (0 espera quando não há erro).

**Constraints**: `reset_exchange_cache()` MUST existir para testes não vazarem instância entre
execuções (FR-003) — sem isso, os 2 testes já existentes de `get_exchange()` em
`tests/test_fetcher.py` quebrariam (o segundo receberia a instância cacheada do primeiro).

**Scale/Scope**: Pequeno e cirúrgico — `data/fetcher.py` (singleton + retry) e
`backtesting/scanner.py` (2 call sites trocados para reusar `get_exchange()`).

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Safety First | PASS — não toca `risk/manager.py`/`execution/order_manager.py`/`trading/position_lifecycle.py`; é infraestrutura de acesso a dados de mercado, não de execução de ordens. |
| II. No Secrets in Code | PASS — nenhuma configuração nova, credenciais continuam vindo só de `.env` via `BINANCE_API_KEY`/`SECRET` já existentes. |
| III. Test Before Implement | PASS — testes com exchange fake escritos antes de cada mudança. |
| IV. Incremental Delivery | PASS — US1 (singleton) → US2 (retry) → Polish (scanner.py), cada uma um commit pequeno. |
| V. Observability Mandatory | PASS — retry loga um warning por tentativa (mesmo logger `utils/logger.py` já usado em todo o projeto, sem pipeline novo). |
| VI. Idempotency and Reconciliation | N/A — não envia ordem nem toca `state.json`. |
| VII. Explain Before Code | PASS — este `plan.md` + `research.md` documentam a decisão antes do código. |

Nenhuma violação identificada.

## Project Structure

```text
data/
└── fetcher.py            # ✏️ get_exchange() cacheado + reset_exchange_cache() (US1);
                            #    retry de rate limit nas 4 funcoes publicas (US2)
backtesting/
└── scanner.py             # ✏️ get_top_pairs()/_get_volume() reusam get_exchange() em vez de
                            #    instanciar ccxt.binance direto (Polish/FR-008)
tests/
├── test_fetcher.py        # ✏️ reset_exchange_cache() entre os 2 testes existentes; novos testes
│                           #    de singleton e retry
└── test_scanner.py        # ✏️ ajusta mocks para o novo caminho via get_exchange()
```

## Complexity Tracking

Nenhuma violação — seção vazia.
