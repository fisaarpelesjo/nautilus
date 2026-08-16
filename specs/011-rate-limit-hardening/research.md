# Research: Singleton de Exchange + Retry de Rate Limit

Fase 0 do `/speckit-plan`.

## Exceções ccxt para limite de taxa

- **Decision**: capturar `ccxt.RateLimitExceeded` e `ccxt.DDoSProtection` (não só uma das duas).
- **Rationale**: verificado diretamente em `ccxt/base/exchange.py` (`httpExceptions`, mapeamento
  genérico usado por todas as exchanges incluindo Binance): HTTP 418 → `DDoSProtection`, HTTP 429
  → `RateLimitExceeded`. São classes irmãs (ambas sub de `NetworkError`), nenhuma é subclasse da
  outra — capturar só `RateLimitExceeded` deixaria o caso 418 (o mais severo, "banido
  temporariamente por excesso de peso de requisição") sem retry.
- **Alternatives considered**: capturar `ccxt.NetworkError` genérico (classe-mãe de ambas) —
  rejeitado, isso também englobaria timeout/erro de conexão genérico, que a spec (FR-005) exige
  propagar sem retry (um erro de rede genérico pode ser um problema real de conectividade, não um
  pico de taxa que se resolve sozinho em segundos).

## Escopo do singleton: por que não usar `functools.lru_cache`

- **Decision**: cache manual em `dict` module-level (`{sandbox: instancia}`), com
  `reset_exchange_cache()` explícito, em vez de `@lru_cache` no `get_exchange()`.
- **Rationale**: `lru_cache` não tem uma forma limpa e discoverable de invalidar seletivamente em
  teste sem acessar `get_exchange.cache_clear()` (funciona, mas é um detalhe de implementação do
  decorator vazando pro chamador) — um `dict` simples com uma função de reset nomeada é mais
  explícito sobre a intenção (FR-003) e seguindo o mesmo padrão já usado por `_cache` (candles) no
  mesmo módulo.

## Backoff do retry

- **Decision**: backoff exponencial curto, base 1s, dobrando a cada tentativa
  (`1s, 2s` entre as 3 tentativas), total de 3 tentativas (FR-007).
- **Rationale**: o objetivo declarado é absorver um pico temporário (spec Assumptions), não
  esperar um bloqueio prolongado se resolver sozinho — 3 tentativas com poucos segundos de espera
  cobre um pico de tráfego breve sem travar um ciclo de 60s do bot por muito tempo.
- **Alternatives considered**: usar o `retry-after` que a Binance devolve no header, quando
  disponível — mais preciso, mas ccxt não expõe esse header de forma uniforme em todas as chamadas
  testadas, e a spec pede simplicidade (Assumptions) proporcional ao porte do projeto.

## Testabilidade do backoff

- **Decision**: `time.sleep` chamado via `import time; time.sleep(...)` (não
  `from time import sleep`), para que os testes monkeypatchem `fetcher.time.sleep` e o retry não
  torne a suíte lenta de verdade.
- **Rationale**: mesmo padrão de direct-import-binding já estabelecido no projeto (`order_manager`
  importa `TRADING_MODE`/etc diretamente para poder ser monkeypatchado em teste) — `import time`
  preserva a capacidade de sobrescrever `time.sleep` no módulo sem afetar o `time` global.
