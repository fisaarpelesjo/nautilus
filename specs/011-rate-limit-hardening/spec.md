# Feature Specification: Singleton de Exchange + Retry de Rate Limit

**Feature Branch**: `011-rate-limit-hardening`

**Created**: 2026-08-16

**Status**: Concluída (US1-US2 implementadas, revisadas e commitadas; Polish completo)

**Input**: User description: "Singleton do cliente ccxt + retry/backoff de rate limit em
data/fetcher.py: `get_exchange()` hoje instancia um `ccxt.binance(...)` novo a cada chamada, e
`enableRateLimit: True` do ccxt so protege dentro de uma mesma instancia -- com uma instancia nova
a cada chamada, o rate-limiter interno e zerado toda vez, sem nenhuma protecao real. Achado de
auditoria (2026-08-16): com o bot rodando 26 pares numa VPS, risco real de bloqueio temporario
(HTTP 418/429) da Binance sem retry/backoff. Escopo: (1) `get_exchange()` retorna uma instancia
unica reusada por processo (singleton), cacheada separadamente por `sandbox`; (2) retry com
backoff exponencial curto para erros de rate limit especificamente, sem mascarar outros erros."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reusar uma única conexão com a exchange (Priority: P1)

Como operador rodando o bot continuamente com muitos pares, quero que o bot reuse uma única
conexão com a Binance em vez de abrir uma nova a cada chamada, para que a proteção de limite de
taxa que o cliente da exchange já oferece funcione de verdade.

**Why this priority**: É a causa raiz do problema — sem isso, qualquer retry adicionado não
resolve o desperdício de conexões nem a falta de throttling real entre chamadas.

**Independent Test**: Chamar `fetch_ohlcv()`/`fetch_ticker()`/`fetch_balance()`/`fetch_order_book()`
várias vezes seguidas e confirmar, via mock, que apenas uma instância de exchange foi criada.

**Acceptance Scenarios**:

1. **Given** o bot faz múltiplas chamadas de dados de mercado no mesmo processo, **When** cada uma
   invoca `get_exchange()`, **Then** todas recebem a mesma instância (nenhuma nova instância é
   criada depois da primeira).
2. **Given** uma chamada com `sandbox=True` e outra com `sandbox=False` no mesmo processo,
   **When** ambas invocam `get_exchange()`, **Then** cada uma recebe sua própria instância cacheada
   (sandbox e produção nunca compartilham conexão).

---

### User Story 2 - Tentar de novo automaticamente quando a Binance sinaliza limite de taxa (Priority: P1)

Como operador, quero que uma chamada que falhe especificamente por limite de taxa da Binance seja
repetida automaticamente com espera crescente, para que um pico temporário de chamadas não derrube
um ciclo inteiro do bot nem exija intervenção manual.

**Why this priority**: Mesma urgência da US1 — sem retry, mesmo com o singleton reduzindo o risco,
um pico legítimo de tráfego (ex: MTF diário mais liquidez de 26 pares no mesmo ciclo) ainda pode
esbarrar no limite e derrubar o ciclo sem necessidade.

**Independent Test**: Simular (via mock) uma chamada que falha uma vez com erro de rate limit e
tem sucesso na tentativa seguinte, e confirmar que a função retorna o resultado da tentativa
bem-sucedida sem propagar o erro.

**Acceptance Scenarios**:

1. **Given** uma chamada a `fetch_ohlcv()`/`fetch_ticker()`/`fetch_balance()`/`fetch_order_book()`
   falha com um erro de limite de taxa da Binance (HTTP 418 ou 429), **When** uma tentativa
   posterior (dentro do número máximo de tentativas) tem sucesso, **Then** a função retorna o
   resultado normalmente, sem propagar o erro original.
2. **Given** uma chamada falha repetidamente por limite de taxa até esgotar o número máximo de
   tentativas, **When** a última tentativa também falha, **Then** o erro é propagado normalmente
   (o chamador continua responsável por lidar com falha persistente, igual hoje).
3. **Given** uma chamada falha por um motivo que **não** é limite de taxa (ex: símbolo inválido,
   erro de rede genérico), **When** o erro ocorre, **Then** nenhum retry é tentado — o erro
   propaga imediatamente, igual ao comportamento atual.

---

### Edge Cases

- O que acontece se o singleton for criado antes das credenciais (`BINANCE_API_KEY`/`SECRET`)
  estarem disponíveis, e elas mudarem depois (ex: hot-reload de `.env`)? Fora de escopo — o
  processo já assume `.env` carregado uma vez no início, igual hoje (nenhuma parte do projeto
  recarrega `.env` em tempo de execução).
- O que acontece com testes/replay que hoje criam uma exchange nova a cada chamada de propósito
  (isolamento entre testes)? O cache precisa poder ser resetado explicitamente entre execuções de
  teste, para um teste não vazar estado de instância para o próximo.
- O que acontece se todas as tentativas de retry se esgotarem dentro de um único ciclo de 60s do
  bot? O erro propaga normalmente para quem chamou — o comportamento de "ciclo falhou, tenta de
  novo no próximo" já existe hoje e não muda.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST reusar uma única instância de exchange por processo entre chamadas de
  `fetch_ohlcv`/`fetch_ticker`/`fetch_balance`/`fetch_order_book`, em vez de criar uma nova a cada
  chamada.
- **FR-002**: O sistema MUST manter instâncias cacheadas separadas para `sandbox=True` e
  `sandbox=False` — nunca reusar uma instância de um modo para o outro.
- **FR-003**: O sistema MUST oferecer uma forma explícita de resetar o cache de instância (para uso
  em testes), sem exigir reiniciar o processo.
- **FR-004**: O sistema MUST tentar novamente automaticamente, com espera crescente entre
  tentativas, quando uma chamada falha especificamente por limite de taxa da Binance (HTTP 418
  `DDoSProtection` ou 429 `RateLimitExceeded` no ccxt).
- **FR-005**: O sistema MUST propagar o erro normalmente (sem retry) quando a falha não é de
  limite de taxa.
- **FR-006**: O sistema MUST propagar o erro normalmente após esgotar o número máximo de
  tentativas de retry por limite de taxa.
- **FR-007**: O número de tentativas MUST ser pequeno (padrão: 3 tentativas totais, incluindo a
  primeira) — o objetivo é absorver um pico temporário, não mascarar um bloqueio prolongado.
- **FR-008**: `backtesting/scanner.py` MUST reusar `get_exchange()` de `data/fetcher.py` em vez de
  instanciar sua própria exchange, para herdar o singleton e o retry sem duplicar a lógica (ver
  Assumptions — mesma causa raiz encontrada fora de `data/fetcher.py`).

### Key Entities

- **Cache de exchange**: instância única de `ccxt.binance` por combinação de modo (`sandbox`/
  produção), mantida em memória pelo processo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Nenhuma chamada a `fetch_ohlcv`/`fetch_ticker`/`fetch_balance`/`fetch_order_book`
  cria uma nova instância de exchange quando uma já existe no cache para o mesmo modo.
- **SC-002**: Uma falha isolada de limite de taxa (1 falha seguida de sucesso) nunca é visível
  para quem chamou a função — o resultado bem-sucedido é retornado normalmente.
- **SC-003**: Um erro que não é de limite de taxa é propagado na primeira tentativa, sem atraso
  adicional de retry.
- **SC-004**: Toda a suíte de testes existente continua passando após a mudança.

## Assumptions

- O objetivo é resiliência a picos temporários, não uma fila de rate-limiting sofisticada (ex:
  token bucket compartilhado entre pares) — um retry curto e simples resolve o caso real
  identificado na auditoria sem introduzir complexidade desproporcional ao porte do projeto (bot
  pessoal, não uma operação institucional).
- **Correção em relação à auditoria original**: `backtesting/scanner.py` (`get_top_pairs()` e
  `_get_volume()`, esta última chamada uma vez **por par** dentro de um loop de até 30 pares em
  `python main.py scan`) também instancia `ccxt.binance(...)` diretamente, sem passar por
  `get_exchange()` — uma versão do mesmo problema, sem nenhuma pausa entre chamadas (ao contrário
  do bot, que já espera 60s entre ciclos). Passa a usar `data/fetcher.py` `get_exchange()` em vez
  de criar sua própria instância, herdando singleton e retry sem duplicar a lógica — dentro do
  escopo desta spec, não uma spec separada, por ser a mesma causa raiz e o mesmo tamanho de
  mudança.
