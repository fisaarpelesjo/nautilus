# Feature Specification: H17 — Sinais on-chain

**Feature Branch**: `034-sinais-onchain`

**Created**: 2026-09-02

**Status**: Draft

**Input**: User description: H17 — sinais on-chain
(`docs/research/registro-de-hipoteses.md` §6.3). Décima sétima hipótese do
registro. Consome a infraestrutura de `specs/033-fonte-dados-onchain/`
(`data/onchain.py::fetch_onchain_series`), a única das quatro hipóteses de
prioridade baixa (H16-H19) em que infraestrutura era de fato o obstáculo
removível — as outras três têm motivo de reprovação independente de infra.

---

## Contexto e tese

**Tese.** Métricas da blockchain do Bitcoin (endereços ativos, hash rate,
volume on-chain) capturam demanda/oferta orgânica antes de aparecer no
preço — um sinal que a família técnica (EMA/RSI/ADX/MACD, já esgotada pelo
registro) não vê, porque deriva do livro de ordens, não da rede.

**Procedência.** H14 (`specs/027-*`) já mediu sinal real e mensurável na
família técnica (z = +5,21) que não cobre o obstáculo econômico da
geometria de saída. H20 mostrou que reduzir o obstáculo não ajuda (a margem
é aproximadamente invariante à geometria). Um sinal **on-chain**, se
existir, entraria pela mesma porta que H14 já validou (modelo supervisionado
sobre eventos de barreira tripla) — não como estratégia nova, mas como
**atributo adicional** ao conjunto já declarado de H14.

**Por que "aditivo a H14" e não um pipeline novo**: H14 já resolveu rotulagem
causal, purga temporal, embargo, três linhas de base e o critério de
aprovação (razão de chances 0,500). Testar H17 como avaliação isolada
reproduziria esse trabalho inteiro para responder uma pergunta mais estreita
— "este atributo a mais muda o veredito?" — que só faz sentido comparado
contra a mesma régua.

---

## Restrição estrutural desta hipótese

`data/onchain.py` (spec 033) só cobre **Bitcoin** — não existe fonte
gratuita e sem chave equivalente para os outros pares do bot. Isso limita
H17 a uma comparação **BTC/USDT isolada**: 5 atributos originais de H14
contra 5 + o atributo on-chain, **mesmo par, mesmo período** — nunca uma
reavaliação do resultado pooled de 12 pares que H14 já publicou (amostras
diferentes tornariam a comparação inválida).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Comparação isolada com e sem o atributo on-chain (Priority: P1)

O pesquisador obtém, para BTC/USDT e sobre o mesmo período, a razão de
chances no subconjunto decidido do modelo com os 5 atributos originais de
H14 contra o modelo com os 5 + o atributo on-chain declarado.

**Why this priority**: é a pergunta da hipótese. Sem essa comparação isolada
(mesmo par, mesmo período), qualquer diferença observada poderia vir da
troca de 12 pares pooled para 1 par, não do atributo novo.

**Independent Test**: rodar a avaliação e obter as duas razões de chances
lado a lado, com os mesmos estados já definidos por H14 (melhora, sem
sinal, insuficiente, confundido, etc.).

**Acceptance Scenarios**:

1. **Given** o histórico de BTC/USDT e a série on-chain declarada, **When**
   a avaliação roda, **Then** reporta a razão de chances no subconjunto
   decidido para os dois conjuntos de atributos (com e sem on-chain), sobre
   exatamente os mesmos eventos rotulados.
2. **Given** o mesmo resultado, **When** classificado, **Then** usa os
   mesmos estados já definidos por H14 (`sem_sinal`, `insuficiente`,
   `melhora`, `confundido`, `inconclusivo`, etc.) — nenhum critério novo.

---

### User Story 2 - Nenhum candle vê o dia on-chain ainda incompleto (Priority: P1)

O atributo on-chain de cada candle usa só dias de calendário estritamente
anteriores ao dia daquele candle — nunca o dia corrente, cujo dado ainda
está sendo acumulado.

**Why this priority**: é a mesma classe de defeito que a spec 020 corrigiu
no MTF (filtro baseado no futuro) — um atributo que vazasse o dia corrente
inflaria artificialmente qualquer sinal encontrado, e a causalidade é um
MUST não negociável de H14 (`rotular()`, "nada além do limite conta").

**Independent Test**: para um candle em qualquer instante `T`, confirmar
que o valor on-chain usado corresponde a um dia cujos dados já estavam
completos antes de `T`, nunca ao dia de `T`.

**Acceptance Scenarios**:

1. **Given** um candle no meio de um dia calendário, **When** o atributo
   on-chain é calculado para esse candle, **Then** usa o valor do dia
   anterior completo, não o dia corrente (ainda parcial).
2. **Given** a série de atributos resultante, **When** inspecionada,
   **Then** nenhum valor muda dentro do mesmo dia calendário — o dado só
   atualiza na virada do dia (granularidade da fonte, spec 033).

---

### User Story 3 - Atributo declarado e checado antes de medir desempenho (Priority: P2)

O atributo on-chain e sua transformação são declarados, e sua colinearidade
contra os 5 atributos já existentes é medida, antes de qualquer resultado
de desempenho ser calculado.

**Why this priority**: mesma disciplina que `strategy/barreira_tripla.py`
já documenta para os 5 atributos existentes — "NENHUMA métrica de acerto
participou da seleção; consultar desempenho aqui seria busca de atributos".
Sem essa ordem, adicionar um atributo e medir resultado antes de declarar a
transformação abriria a mesma porta de multiplicidade de testes que o
registro já documenta em M9/M13.

**Independent Test**: o research.md da spec (Fase 0) declara o atributo, a
transformação e a colinearidade medida, antes de o plano avançar para
qualquer avaliação com o modelo.

**Acceptance Scenarios**:

1. **Given** a fonte de dados on-chain (spec 033), **When** um atributo é
   escolhido, **Then** a escolha e a transformação exata são registradas
   antes de qualquer razão de chances ser calculada.
2. **Given** o atributo declarado, **When** sua colinearidade contra os 5
   atributos existentes é medida, **Then** o resultado é registrado —
   inclusive se ultrapassar o limiar de 0,80 já estabelecido, o que
   descartaria o atributo antes da avaliação, não depois.

---

### Edge Cases

- **Colinearidade do atributo on-chain acima de 0,80 contra um dos 5
  existentes.** Mesmo critério de exclusão já usado pelos 5 (`rsi`,
  `pos_bb`, `dist_ema_fast`, `dist_ema_trend` foram descartados assim) —
  a hipótese não avança para a avaliação com modelo, e isso é o resultado,
  não uma falha.
- **Amostra BTC-only abaixo do mínimo de treino/teste.** MUST produzir
  `inconclusivo`, nunca `reprovado` — mesmo princípio de M9, já reusado em
  H14 (`MIN_TREINO`, `EDGE_MIN_TRADES`).
- **Fonte on-chain indisponível no momento da avaliação.** A avaliação MUST
  falhar de forma explícita (mesmo princípio de FR-003 da spec 033), nunca
  prosseguir com dado ausente tratado como zero.
- **Dia on-chain ausente no meio da série** (feriado de processamento da
  fonte, falha pontual do provedor). O candle correspondente usa o último
  dia completo disponível (mesmo princípio de "levar adiante o último valor
  conhecido" já implícito no merge causal) — não interpola nem inventa.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST declarar, antes de qualquer medição de
  desempenho, exatamente um atributo on-chain derivado de
  `data/onchain.py::fetch_onchain_series` (spec 033), incluindo a
  transformação aplicada — nunca o nível bruto, por não-estacionariedade
  (mesmo motivo pelo qual os 5 atributos de H14 já são razões/distâncias
  normalizadas, não preços brutos).
- **FR-002**: O sistema MUST medir a colinearidade do atributo on-chain
  declarado contra os 5 atributos já existentes (`strategy/
  barreira_tripla.py::ATRIBUTOS`), usando o mesmo limiar de 0,80 já
  estabelecido, e registrar o resultado antes de prosseguir.
- **FR-003**: O merge do valor on-chain em cada candle MUST usar só dias de
  calendário estritamente anteriores ao dia do candle — nenhum atributo usa
  informação de um dia ainda em curso.
- **FR-004**: A avaliação MUST ser restrita a BTC/USDT — única cobertura da
  fonte de dados (spec 033, Assumptions).
- **FR-005**: A avaliação MUST comparar, sobre o mesmo par e mesmo período,
  o modelo com os 5 atributos originais contra o modelo com os 5 + o
  atributo on-chain — nunca contra o resultado pooled de 12 pares já
  publicado por H14.
- **FR-006**: O sistema MUST reusar a bateria de avaliação já existente de
  H14 (rotulagem por barreira tripla, purga temporal, embargo, três linhas
  de base) sem alterar o critério de aprovação (razão de chances 0,500) nem
  os estados já definidos.
- **FR-007**: O sistema MUST NOT enviar ordem nem alterar o caminho de
  produção (`trading/`, `execution/`, `risk/`).
- **FR-008**: Amostra insuficiente (esperada, dado que BTC-only tem menos
  eventos que o pool de 12 pares) MUST produzir estado `inconclusivo`,
  nunca `reprovado`.
- **FR-009**: Um dia on-chain ausente no meio da série MUST levar adiante o
  último valor completo conhecido, nunca interpolar nem tratar como zero.

### Key Entities

- **Atributo on-chain declarado**: a transformação exata (métrica +
  janela/forma) escolhida em FR-001, fixa durante toda a avaliação.
- **Comparação BTC-only**: par de resultados (modelo original de H14 vs
  modelo original + atributo on-chain), mesmo par, mesmo período, mesmos
  eventos rotulados.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O pesquisador obtém a razão de chances no subconjunto
  decidido com e sem o atributo on-chain, sobre exatamente os mesmos
  eventos de BTC/USDT.
- **SC-002**: Nenhum candle usa dado on-chain de um dia ainda incompleto —
  verificável por inspeção da série de atributos resultante.
- **SC-003**: O atributo on-chain e sua transformação estão declarados
  antes de qualquer resultado de desempenho existir.
- **SC-004**: A colinearidade do atributo contra os 5 existentes está
  medida e registrada.
- **SC-005**: Nenhuma ordem é enviada; produção permanece idêntica.

---

## Assumptions

- **Atributo candidato**: variação percentual de `n-unique-addresses`
  (endereços únicos ativos) — a métrica mais diretamente citada como proxy
  de demanda orgânica de rede na literatura já registrada
  (`docs/research/forecasting-and-trading-cryptocurrencies-with-machine-
  learning-under-changing-market-conditions.md`, Tabela 2, sinalizada
  "diferenciada", não em nível). Escolhida por precedência na literatura,
  não por desempenho prévio — nenhuma medição de resultado participou desta
  escolha.
- A janela exata da variação (ex.: 1 dia vs média móvel de N dias) MUST ser
  declarada em `research.md` (Fase 0) antes de qualquer medição — decisão
  de engenharia com restrição declarada, mesmo padrão de D1-D6 (spec 029) e
  D1 (specs 030/031/033), não ambiguidade de negócio.
- Reprovação ou resultado inconclusivo de H17 **não invalida H14** — H14
  segue baseado em 12 pares pooled; H17 é um teste aditivo e isolado sobre
  o mesmo modelo, não uma substituição.
- Expectativa registrada antes da avaliação: o próprio registro já classifica
  H17 como "literatura nascente, qualidade de dado heterogênea" (§6.3) —
  consistente com o padrão do registro (H8, H15) de declarar a expectativa
  antes de medir, para não reinterpretar o resultado depois.
