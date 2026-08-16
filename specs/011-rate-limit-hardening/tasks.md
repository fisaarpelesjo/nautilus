---

description: "Task list for 011-rate-limit-hardening"
---

# Tasks: Singleton de Exchange + Retry de Rate Limit

**Input**: Design documents from `/specs/011-rate-limit-hardening/`

**Tests**: Incluídos — mesmo rigor test-first das specs anteriores (constitution III).

---

## Phase 1: User Story 1 - Reusar uma única conexão com a exchange (Priority: P1) 🎯 MVP

- [X] T001 [P] [US1] Teste: chamadas repetidas a `get_exchange()` (mesmo `sandbox`) retornam a
      mesma instância — novo teste em `tests/test_fetcher.py`
- [X] T002 [P] [US1] Teste: `get_exchange(sandbox=True)` e `get_exchange(sandbox=False)` retornam
      instâncias diferentes, cada uma cacheada independentemente — `tests/test_fetcher.py`
- [X] T003 [P] [US1] Teste: `reset_exchange_cache()` força `get_exchange()` a criar uma instância
      nova na próxima chamada — `tests/test_fetcher.py`
- [X] T004 [US1] `data/fetcher.py`: `get_exchange()` cacheia por `sandbox` em `_exchange_cache`;
      nova função `reset_exchange_cache()` (depende de T001-T003 falhando)
- [X] T005 [US1] Atualizar os 2 testes já existentes de `get_exchange()` (credenciais) em
      `tests/test_fetcher.py` para chamar `reset_exchange_cache()` antes de cada um, evitando que
      o segundo receba a instância cacheada do primeiro (depende de T004)

**Checkpoint**: US1 completa — uma única conexão reusada por processo.

---

## Phase 2: User Story 2 - Retry automático em erro de rate limit (Priority: P1)

- [X] T006 [P] [US2] Teste: uma chamada que falha uma vez com `ccxt.RateLimitExceeded` e tem
      sucesso na tentativa seguinte retorna o resultado normalmente — novo teste em
      `tests/test_fetcher.py`
- [X] T007 [P] [US2] Teste: mesmo comportamento com `ccxt.DDoSProtection` (HTTP 418, classe
      diferente de `RateLimitExceeded`) — `tests/test_fetcher.py`
- [X] T008 [P] [US2] Teste: falhas persistentes de rate limit até esgotar o número máximo de
      tentativas propagam o erro original — `tests/test_fetcher.py`
- [X] T009 [P] [US2] Teste: um erro que não é de rate limit (ex: `ccxt.BadSymbol`) propaga
      imediatamente, sem retry nem espera — `tests/test_fetcher.py`
- [X] T010 [US2] `data/fetcher.py`: helper `_call_with_rate_limit_retry()` (3 tentativas, backoff
      exponencial curto via `time.sleep`); `fetch_ohlcv`/`fetch_ticker`/`fetch_balance`/
      `fetch_order_book` roteiam a chamada real ao ccxt por esse helper (depende de T006-T009
      falhando)

**Checkpoint**: US1 e US2 completas — MVP desta spec.

---

## Phase 3: Polish & Cross-Cutting Concerns

- [X] T011 `backtesting/scanner.py`: `get_top_pairs()`/`_get_volume()` reusam
      `data.fetcher.get_exchange()`/`fetch_ticker()` em vez de instanciar `ccxt.binance`
      diretamente (FR-008, achado durante a especificação — mesma causa raiz fora de
      `data/fetcher.py`)
- [X] T012 Rodar `tests/test_scanner.py` para confirmar que a suíte já existente continua passando
      sem ajuste (os testes mockam `get_top_pairs`/`_get_volume` inteiros)
- [X] T013 [P] Atualizar `specs/BACKLOG.md`: marcar spec 011 concluída
- [X] T014 Marcar `spec.md` desta spec como Concluída

---

## Dependencies & Execution Order

US1 (singleton) é pré-requisito conceitual de US2 (retry) só na ordem de implementação sugerida —
tecnicamente independentes (retry funcionaria mesmo sem singleton, só não resolveria o problema
completo). T011 (scanner.py) depende de US1 já existir (reusa `get_exchange()`).

## Notes

- Nenhuma task toca `risk/manager.py`, `execution/order_manager.py` ou
  `trading/position_lifecycle.py`.
- Toda validação é unitária com exchange fake, sem dependência de dados reais da Binance nem tempo
  real passando.
