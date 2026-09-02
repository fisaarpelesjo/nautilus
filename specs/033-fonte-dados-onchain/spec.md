# Feature Specification: Fonte de dados on-chain

**Feature Branch**: `033-fonte-dados-onchain`

**Created**: 2026-09-02

**Status**: Draft

**Input**: User description: infraestrutura que falta para poder avaliar
H17 (sinais on-chain) — `docs/research/registro-de-hipoteses.md` §6.3.
`data/fetcher.py` hoje só busca OHLCV; não existe nenhuma fonte de métrica
de blockchain (endereços ativos, hash rate, taxas, volume on-chain). Esta
spec entrega só a capacidade de busca — a hipótese em si (qual métrica, qual
critério de aprovação) é uma spec separada, que consome esta.

---

## Contexto

Toda pesquisa anterior deste projeto (specs 023-029) mede em cima de dados
que o projeto já sabia buscar (OHLCV via ccxt/yfinance, order book via
ccxt). H17 precisa de uma classe de dado nova: métricas agregadas
diariamente sobre a blockchain do Bitcoin (endereços únicos, número de
transações, hash rate, taxas totais, tamanho de bloco) — dado estruturalmente
diferente de candle (uma série temporal diária de um único valor por
métrica, não OHLCV).

**Fonte verificada antes desta spec**: `api.blockchain.info/charts/<nome>`
— pública, sem chave de API, JSON, granularidade diária. Testado em
2026-09-02 contra seis séries (`n-unique-addresses`, `n-transactions`,
`hash-rate`, `transaction-fees-usd`, `avg-block-size`, `difficulty`, todas
`status: ok`, ~720 pontos em 2 anos de histórico). Só cobre Bitcoin — não
existe equivalente gratuito e sem chave para os demais pares do bot.

Esta spec entrega uma função de busca genérica (qualquer série do
blockchain.info), sem decidir qual métrica a hipótese vai usar — essa
decisão, e o critério de aprovação, pertencem à spec da hipótese (H17),
não a esta.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Buscar uma série on-chain diária (Priority: P1)

O pesquisador obtém uma série temporal diária de uma métrica on-chain do
Bitcoin, por nome, sem precisar de chave de API.

**Why this priority**: é a capacidade central que falta — sem ela, H17 não
tem dado nenhum para avaliar.

**Independent Test**: chamar a função com o nome de uma métrica válida e
obter uma série com datas e valores, sem exceção nem chave de API.

**Acceptance Scenarios**:

1. **Given** um nome de métrica válido (ex. `n-unique-addresses`), **When**
   a busca roda, **Then** retorna uma série indexada por data, crescente,
   sem duplicatas.
2. **Given** a mesma busca, **When** repetida, **Then** não exige nenhuma
   variável de ambiente nem chave — mesmo padrão de "sem credencial" já
   estabelecido em H15 (FR-013 da spec 029).

---

### User Story 2 - Falha nunca vira dado inventado (Priority: P1)

Uma métrica inválida, uma falha de rede, ou uma resposta malformada da API
produz um erro explícito — nunca uma série vazia ou parcial tratada como
válida.

**Why this priority**: mesmo princípio já aplicado em `data/sources/` (spec
023, `DataSource` protocol: "MUST levantar exceção... nunca DataFrame vazio
ou parcial silencioso") e em `execution/liquidity.py` (custo/profundidade
desconhecidos nunca viram zero). Um dado on-chain silenciosamente ausente
tratado como zero contaminaria qualquer medição de correlação ou modelo que
o consumir.

**Independent Test**: chamar a função com um nome de métrica inexistente e
com uma falha de rede simulada, e confirmar que ambas levantam exceção.

**Acceptance Scenarios**:

1. **Given** um nome de métrica que a API não reconhece, **When** a busca
   roda, **Then** levanta exceção com o motivo.
2. **Given** uma falha de rede durante a busca, **When** a busca roda,
   **Then** levanta exceção — nunca retorna série vazia silenciosa.
3. **Given** uma resposta da API com `status` diferente de `ok`, **When**
   a busca roda, **Then** levanta exceção citando o status retornado.

---

### User Story 3 - Histórico suficiente é verificável (Priority: P2)

O pesquisador consegue saber quantos dias de histórico uma série tem, antes
de tentar usá-la numa avaliação que exige um mínimo de amostra.

**Why this priority**: mesmo padrão de `BacktestResult.requested_candles`/
`last_shortfall` (spec 023) — pedir um período e receber menos, em
silêncio, desbalancearia qualquer comparação sem ninguém notar. Aqui o
risco é menor (H17 ainda não decidiu o período), mas a capacidade de
verificar precisa existir antes da hipótese depender dela.

**Independent Test**: buscar uma série com um período maior que o
histórico realmente disponível e confirmar que o tamanho retornado é
verificável (menor que o pedido), não just truncado silenciosamente sem
como saber.

**Acceptance Scenarios**:

1. **Given** uma busca por um período além do histórico existente,
   **When** a série retorna, **Then** o número de pontos obtidos é
   verificável pelo chamador (ex. `len(serie)`), refletindo o que a API
   de fato tinha.

---

### Edge Cases

- **Métrica com nome válido na API mas sem dado no período pedido.**
  Série vazia é um resultado válido (não é erro), diferente de uma falha —
  US2 trata falha de rede/nome inválido, não "sem dado no período".
- **Resposta da API incompleta (JSON corrompido).** Levanta exceção, mesmo
  tratamento de falha de rede.
- **Chamada repetida para a mesma métrica.** Sem exigência de cache nesta
  spec — cada chamada busca de novo. Cache fica para quando a hipótese
  mostrar necessidade real (não antecipar).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST buscar qualquer série diária publicada em
  `api.blockchain.info/charts/<nome>`, por nome, sem exigir chave de API.
- **FR-002**: O sistema MUST retornar a série indexada por data, crescente,
  sem duplicatas.
- **FR-003**: O sistema MUST NOT retornar série vazia ou parcial como se
  fosse sucesso quando a causa é falha de rede, nome de métrica inválido,
  ou resposta com `status` diferente de `ok` — MUST levantar exceção
  nesses casos.
- **FR-004**: Série vazia por ausência real de dado no período (não por
  falha) MUST ser distinguível de falha — não é erro.
- **FR-005**: O sistema MUST NOT introduzir nenhuma dependência nova além
  do que o projeto já usa para requisições HTTP.
- **FR-006**: O sistema MUST NOT alterar `data/fetcher.py` nem o protocolo
  `DataSource` de `data/sources/` (spec 023) — métrica on-chain não é
  OHLCV, é uma classe de dado estruturalmente diferente; misturar as duas
  abstrações forçaria uma a servir a outra mal.
- **FR-007**: O sistema MUST NOT decidir, nesta spec, qual métrica on-chain
  é relevante para nenhuma hipótese — é capacidade genérica de busca, a
  escolha da métrica pertence à spec que consome esta.

### Key Entities

- **Série on-chain**: sequência diária `(data, valor)` de uma métrica
  nomeada, obtida de `api.blockchain.info/charts/<nome>`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma série on-chain válida é obtida por nome, sem chave de
  API, com pelo menos 2 anos de histórico disponível (medido em
  2026-09-02 para as seis séries testadas).
- **SC-002**: Nome de métrica inválido, falha de rede, ou `status` não-ok
  nunca produzem série vazia silenciosa — sempre exceção.
- **SC-003**: O tamanho da série obtida é verificável pelo chamador em
  todos os casos.
- **SC-004**: Nenhuma mudança de comportamento em `data/fetcher.py` ou
  `data/sources/` — módulo novo, independente.

---

## Assumptions

- Cobertura é **só Bitcoin** — não existe fonte gratuita e sem chave
  equivalente para os demais pares do bot. Isso limita qualquer hipótese
  que consumir esta infra a avaliação BTC-only, declarado aqui para a
  spec da hipótese não redescobrir isso tarde.
- `api.blockchain.info` é de terceiro, fora do controle do projeto —
  disponibilidade e formato podem mudar; FR-003 (falha explícita) é a
  defesa contra isso, não uma garantia de uptime.
- Granularidade é diária, mais grossa que qualquer timeframe de produção
  do bot (`TIMEFRAME`, default 4h) — o merge causal (que candle pode ver
  qual dia de dado on-chain) é decisão da spec da hipótese, não desta.
