# Feature Specification: H8 — arbitragem de funding rate, revisão com universo amplo e eficiência de capital

**Feature Branch**: `058-h8-funding-rate-revisao`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: H8 (arbitragem de funding rate, delta-neutro)
foi a única hipótese deste registro com edge líquido real e positivo já
medido (BTC +3,21% a.a., ETH +2,27% a.a.) — reprovada em 2026-09-01 por
ser menor que renda fixa e exigir infraestrutura que o bot não tem
(permissão de futuros, gestão de margem/liquidação). É também a única
família de hipótese que não depende de prever direção — H14/H20
esgotaram as duas frentes direcionais deste registro (§6.3-b). Antes de
qualquer decisão sobre construir a infraestrutura de execução (a maior
mudança de arquitetura do projeto até aqui), revisar a medição original
com dois pontos que ela não tinha: universo mais amplo que 4 pares, e a
eficiência de capital de uma posição sem alavancagem (que a medição
original não modelou — reportou retorno sobre o nocional, não sobre o
capital realmente implantado).

---

## Contexto e tese

**Por que revisar antes de construir.** A medição original de H8 (2026-09-01)
testou 4 pares (BTC/ETH/XRP/SOL) com custo de 0,04% por perna — abaixo
da taxa real de spot (0,10%, verificada 2026-09-03) — e reportou
retorno sobre o **nocional** da posição. Mas uma posição delta-neutra
**sem alavancagem** (a única configuração que praticamente elimina risco
de liquidação, porque a margem cobre o nocional inteiro da perna
perpétua) exige capital = nocional (perna spot) + margem (perna
perpétua, ≈ nocional a 1x) = **2x o nocional**. O retorno real sobre
capital implantado é, portanto, aproximadamente **metade** do que a
medição original reportou — uma correção que só piora a leitura
original, não melhora. Medir isso corretamente, com um universo maior
que 4 pares, é obrigatório antes de decidir se vale abrir permissão de
futuros na API e construir gestão de margem — não depois.

**Hipótese declarada antes de medir.** Com a correção de capital
aplicada e o universo ampliado, a maioria dos pares continua abaixo do
benchmark de custo de oportunidade (5% a.a., piso conservador da faixa
real de empréstimo de USDT) — reforçando o veredito original, agora com
mais rigor. **Não é a hipótese esperada como mais provável de aprovar**
— é a mais honesta de medir antes de investir em infraestrutura.

**Hipótese alternativa, com igual peso.** Algum subconjunto do universo
ampliado (pares de alta volatilidade idiossincrática, historicamente
associados a funding mais alto e persistente por viés de posição comprada
do varejo) supera o benchmark mesmo sobre capital implantado — um
resultado que justificaria uma spec de construção de infraestrutura de
execução como próximo passo.

**Zero execução real.** Esta spec mede apenas — nenhuma ordem é
enviada, nenhuma permissão de API muda, nenhuma posição é aberta. É
puro levantamento de dados públicos (histórico de funding rate via
`ccxt`, endpoint público, sem credencial).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir o retorno líquido sobre capital implantado por par (Priority: P1)

O pesquisador obtém, para cada par do universo com mercado perpétuo
ativo, o retorno bruto anualizado, o retorno líquido sobre o nocional
(taxas atuais) e o retorno líquido sobre capital implantado (corrigido
por eficiência de capital), comparado contra um benchmark declarado.

**Why this priority**: é a pergunta central da revisão.

**Independent Test**: `avaliar_par` sobre um histórico de funding
sintético produz os três números corretamente e sinaliza corretamente
se supera o benchmark — sem rede.

**Acceptance Scenarios**:

1. **Given** um par com mercado perpétuo ativo e ≥ 90 dias de histórico
   de funding, **When** `avaliar_par` roda, **Then** devolve bruto a.a.,
   líquido a.a. sobre nocional, líquido a.a. sobre capital implantado
   (metade do anterior) e se supera o benchmark de 5% a.a.
2. **Given** um par sem mercado perpétuo (só listado a vista) ou com
   menos de 90 dias de histórico, **When** avaliado, **Then** é
   excluído do universo (`None`), nunca contado como zero.
3. **Given** o universo inteiro avaliado, **When** reportado, **Then**
   aparece ao lado dos quatro números já publicados (BTC/ETH/XRP/SOL,
   medição original sobre nocional) — nunca substituindo.

---

### Edge Cases

- **Par com mercado perpétuo mas funding sempre positivo ou sempre
  negativo**: não é tratado como anômalo — `pct_negativos` reporta o
  valor real, incluindo 0% ou 100%.
- **Histórico de funding mais curto que 365 dias mas ≥ 90**: anualizado
  proporcionalmente (`fator_anual`), incluído no universo — não
  descartado só por não ter um ano completo.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST buscar histórico de funding rate via
  `ccxt` (endpoint público, sem credencial) para o perpétuo
  correspondente a cada par spot do universo.
- **FR-002**: O sistema MUST excluir do universo pares sem mercado
  perpétuo ativo ou com menos de 90 dias de histórico — nunca contá-los
  como zero.
- **FR-003**: O sistema MUST calcular o retorno líquido sobre capital
  implantado como metade do retorno líquido sobre nocional (posição sem
  alavancagem, margem ≈ nocional).
- **FR-004**: O sistema MUST usar as taxas de custo atuais (spot 0,10%,
  futuros 0,05%, VIP0, verificadas 2026-09-03) — não as de 0,04% da
  medição original.
- **FR-005**: O sistema MUST comparar cada par contra um benchmark
  declarado (5% a.a.) e reportar quantos superam.
- **FR-006**: O sistema MUST NOT enviar ordem real, alterar permissão de
  API nem modificar `trading/`, `execution/` ou `risk/`.

### Key Entities

- **ResultadoFundingPar**: par, dias cobertos, nº pagamentos, %
  negativos, bruto a.a., líquido a.a. sobre nocional, líquido a.a. sobre
  capital implantado, se supera o benchmark.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `python main.py funding` produz uma tabela por par,
  ordenada por retorno sobre capital implantado.
- **SC-002**: O registro documenta quantos pares (de quantos avaliados)
  superam o benchmark sobre capital implantado — resultado explícito,
  não implícito.
- **SC-003**: Nenhuma ordem real é enviada; nenhuma permissão de API
  muda; produção permanece idêntica.

---

## Assumptions

- **Universo**: `UNIVERSO_AMPLO` (`backtesting/portfolio_h14.py`, 34
  pares) — já existente, já filtrado por liquidez de spot para outra
  pesquisa, não escolhido especificamente para este teste.
- **Benchmark de 5% a.a.**: piso conservador da faixa observada (5-8%)
  em produtos de empréstimo de USDT em plataformas estabelecidas
  (Binance Earn, Aave), verificada por busca em 2026-09-03.
- Se a maioria do universo continuar abaixo do benchmark, fecha a
  revisão sem justificar a próxima etapa (construir infraestrutura de
  futuros). Se algum subconjunto superar de forma consistente, uma spec
  nova (fora do escopo desta) decidiria os próximos passos de
  infraestrutura — não decidido aqui.
