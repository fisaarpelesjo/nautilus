# Feature Specification: H15 — leitura das corretoras em paralelo

**Feature Branch**: `053-h15-leitura-paralela`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: A campanha real de H15 (spec 029, rodada
pela primeira vez em 2026-09-03) revelou um defeito de instrumento
real (M15, `docs/research/registro-de-hipoteses.md` §5): `medir_ciclo`
lê as seis corretoras **sequencialmente**
(`{corretora: ler_livro(corretora, par) for corretora in CORRETORAS}`),
então o intervalo entre a primeira e a última leitura do ciclo já
ultrapassa sozinho o teto de latência (`TETO_LATENCIA_MS=2000`) — média
medida de 11.431ms, até 30.324ms no pior caso. Das 15 combinações de
corretoras possíveis, só uma (as duas adjacentes na ordem fixa de
leitura) alguma vez ficou abaixo do teto em 615 observações reais.
Corrigir exige ler as seis corretoras **em paralelo** — `ler_livro` é
I/O de rede síncrono (chamada HTTP via `ccxt`, libera o GIL durante a
espera), então `concurrent.futures.ThreadPoolExecutor` resolve sem
precisar reescrever para `ccxt.async_support` (mudança bem menor, sem
tocar em como `ler_livro`/`ccxt.Exchange` funcionam por dentro).

---

## Contexto e tese

**Por que threads, não asyncio.** `ler_livro` já é uma função síncrona
que faz uma chamada de rede bloqueante (`exchange.fetch_order_book`).
Durante essa espera de rede, o GIL do Python já é liberado — múltiplas
threads podem estar cada uma bloqueada em sua própria chamada de rede
ao mesmo tempo, efetivamente paralelas para o que importa aqui
(latência de I/O, não CPU). Reescrever para `ccxt.async_support`
exigiria trocar a instanciação de `Exchange`, tornar `ler_livro`
`async`, e propagar `async`/`await` por toda a cadeia de chamada — uma
mudança bem maior para o mesmo resultado prático.

**O que isto NÃO muda.** `TETO_LATENCIA_MS` (2.000ms) continua o mesmo
— não é o teto que estava errado, era o instrumento que nunca dava a
ele uma chance real de passar. `ler_livro`, `mesma_cotacao`,
`comparar`, `agregar`, a regra de `MIN_OBSERVACOES_AGREGACAO` (30) —
nada disso muda. Só a ORDEM de execução das seis leituras dentro de um
ciclo: paralela em vez de sequencial.

**Risco declarado: cache de instâncias `ccxt.Exchange` sob
concorrência.** `_exchange_cache` (dict module-level) é lido e escrito
por `_get_exchange_publico`. Com seis threads chamando corretoras
DISTINTAS simultaneamente, nunca duas threads disputam a mesma chave —
mas um lock explícito ao redor da escrita no cache é adicionado por
correção defensiva, custo desprezível, sem depender de garantias
implícitas do GIL do CPython.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ler as seis corretoras em paralelo, não sequencial (Priority: P1)

O pesquisador confirma que `medir_ciclo` lê as seis corretoras
concorrentemente — o tempo total de um ciclo passa a ser próximo do
tempo da leitura MAIS LENTA, não da SOMA de todas.

**Why this priority**: é o defeito que M15 catalogou — sem isto, a
campanha de H15 nunca produz uma comparação válida para 14 das 15
combinações, não importa quantos ciclos rodem.

**Independent Test**: com `ler_livro` simulando uma latência de rede
conhecida (`time.sleep`), confirmar que o tempo total de `medir_ciclo`
para seis corretoras fica próximo de UMA leitura, não de seis somadas.

**Acceptance Scenarios**:

1. **Given** seis corretoras, cada uma respondendo em ~T segundos,
   **When** `medir_ciclo` roda, **Then** o tempo total fica próximo de
   T (paralelo), não de 6×T (sequencial).
2. **Given** o mesmo cenário, **When** os `intervalo_ms` das
   comparações resultantes são medidos, **Then** ficam
   consistentemente abaixo de `TETO_LATENCIA_MS` (quando a leitura em
   si é rápida) — não mais dominados pela ordem de leitura.
3. **Given** uma corretora que falha, **When** `medir_ciclo` roda,
   **Then** o comportamento de FR-011 (falha isolada não aborta o
   ciclo) continua idêntico — paralelizar não muda a tolerância a
   falha já existente.

---

### Edge Cases

- Falha de rede numa corretora sob paralelismo: já tratada por
  `ler_livro` (nunca levanta exceção, devolve `LeituraLivro(erro=...)`)
  — cada thread trata sua própria falha independentemente, sem afetar
  as demais.
- Duas corretoras respondendo em instantes muito próximos: o
  comportamento de `comparar`/`intervalo_ms` já existente não muda —
  só a probabilidade de isso acontecer aumenta (é o objetivo).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST ler as seis corretoras concorrentemente
  dentro de `medir_ciclo`, via `concurrent.futures.ThreadPoolExecutor`.
- **FR-002**: O sistema MUST preservar o comportamento de falha
  isolada já existente (FR-011 de spec 029) — uma corretora falhando
  não aborta as demais nem o ciclo.
- **FR-003**: O sistema MUST NOT alterar `TETO_LATENCIA_MS`,
  `ler_livro`, `mesma_cotacao`, `comparar`, `agregar`,
  `MIN_OBSERVACOES_AGREGACAO` — só a ordem de execução das leituras.
- **FR-004**: O sistema MUST proteger a escrita em `_exchange_cache`
  contra concorrência (lock explícito), por correção defensiva.
- **FR-005**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/`.

### Key Entities

- Nenhuma entidade nova — `LeituraLivro`, `Comparacao`, `RelatorioH15`
  já existem, inalterados.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um ciclo de seis corretoras com latência simulada
  conhecida completa em tempo próximo de UMA leitura, não da soma de
  seis.
- **SC-002**: Comportamento de falha isolada (FR-011) permanece
  idêntico sob paralelismo.
- **SC-003**: Nenhuma ordem real é enviada; produção permanece
  idêntica.

---

## Assumptions

- **`ler_livro` é I/O-bound, não CPU-bound**: a chamada de rede via
  `ccxt` libera o GIL durante a espera — premissa que torna threads
  suficientes sem precisar de `asyncio`.
- Corrigir o instrumento não decide o veredito de H15 — só permite que
  a campanha real (a ser rodada de novo depois desta correção) meça as
  14 combinações que nunca puderam ser medidas até aqui.
