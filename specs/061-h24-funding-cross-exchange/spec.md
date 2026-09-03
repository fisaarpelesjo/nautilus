# Feature Specification: H24 — diferencial de funding rate entre corretoras (perp × perp)

**Feature Branch**: `061-h24-funding-cross-exchange`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: Em vez de comprar à vista e vender
perpétuo (H8, spec 058, exige 2x capital sem alavancagem), comprar o
perpétuo de um ativo numa corretora e vender o mesmo perpétuo em outra
— sem perna à vista. Explora a DIFERENÇA de funding entre corretoras,
muitas vezes maior que o funding absoluto de uma corretora isolada,
porque cada corretora tem sua própria base de usuários e viés de
posicionamento. Medir se isso é mais eficiente em capital que H8 (não
presumir) e se o diferencial líquido supera o benchmark de custo de
oportunidade.

---

## Contexto e tese

**Por que medir isso separado de H8.** H8 mediu carry perpétuo-vs-spot
numa única corretora; H24 pergunta se a MESMA lógica de carry, aplicada
como um diferencial entre duas corretoras (perp × perp, sem perna à
vista), captura algo maior — cada corretora tem sua própria base de
usuários de varejo, e o viés de posicionamento (mais comprados ou mais
vendidos) varia entre elas, o que pode produzir uma diferença de
funding maior que o funding absoluto de qualquer uma isolada.

**Hipótese principal, declarada antes de medir:** o diferencial de
funding entre pelo menos um par de corretoras, para BTC ou ETH, supera
o benchmark de 5% a.a. sobre capital implantado.

**Hipótese alternativa, com igual peso:** os funding rates das
corretoras qualificadas são suficientemente correlacionados (todas
reagem ao mesmo mercado subjacente) que o diferencial médio fica
pequeno — o carry perp×perp não descobre uma vantagem que H8 (perp vs.
spot, uma corretora) já não tivesse.

**A eficiência de capital NÃO é presumida melhor que H8 — é
investigada.** Sem perna à vista, a intuição é que capital-eficiência
melhoraria; mas cada corretora gerencia margem de forma independente
(sem margem cruzada entre corretoras diferentes para uma conta de
varejo), então cada perna ainda exige margem própria. Se, ao investigar,
a margem necessária por perna for ~100% do nocional (mesma
configuração sem alavancagem de H8), a exigência de capital total é
2× o nocional — **igual a H8, não menor** — mais o risco adicional de
manter capital pré-posicionado em duas corretoras diferentes em vez de
uma. Essa investigação é parte do escopo desta spec, não uma suposição
resolvida antes de medir (ver `research.md` D3).

**Zero execução real.** Mede apenas — nenhuma ordem é enviada, nenhuma
permissão de API muda, nenhuma posição é aberta. Leitura de dado
público (histórico de funding rate via `ccxt`, sem credencial).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir o diferencial líquido por par de corretoras (Priority: P1)

O pesquisador obtém, para cada par de corretoras qualificadas × ativo
(BTC, ETH), o diferencial de funding bruto anualizado, líquido sobre
nocional (custo das duas corretoras) e líquido sobre capital
implantado, comparado contra o benchmark declarado.

**Why this priority**: é a pergunta central da hipótese.

**Independent Test**: `avaliar_par_corretoras` sobre históricos de
funding sintéticos de duas corretoras produz o diferencial, custo e
capital implantado corretamente — sem rede.

**Acceptance Scenarios**:

1. **Given** duas corretoras qualificadas com histórico de funding
   alinhável por período de 8h, **When** `avaliar_par_corretoras` roda,
   **Then** devolve o diferencial bruto anualizado, líquido sobre
   nocional (custo das duas corretoras) e líquido sobre capital
   implantado, com a direção (qual corretora vender/comprar).
2. **Given** uma corretora sem mercado perpétuo linear USDT-margined
   para o ativo (ex.: Kraken/BTC, só oferece inverso USD/BTC-margined),
   **When** avaliada, **Then** é excluída do universo de corretoras
   qualificadas — nunca forçada numa comparação que misturaria
   denominação de margem.
3. **Given** o universo de pares de corretoras × ativos avaliado,
   **When** reportado, **Then** aparece ao lado do resultado já
   publicado de H8 (spec 058) — nunca substituindo, e com a conclusão
   sobre eficiência de capital declarada explicitamente (igual, melhor
   ou pior que H8).

---

### Edge Cases

- **Corretoras com pequeno jitter de segundos no horário de funding**
  (medido: Gate varia poucos segundos em torno do horário cheio):
  alinhamento por hora arredondada, não timestamp exato.
- **Corretora sem histórico suficiente**: mesmo piso de 90 dias de H8
  (`MIN_DIAS_COBERTURA`), aplicado à interseção das duas séries, não a
  cada uma isoladamente.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST determinar, antes de medir, quais
  corretoras entre as seis já lidas por H15 (`binance`, `bybit`, `okx`,
  `kucoin`, `gate`, `kraken`) expõem histórico de funding rate via
  `ccxt` para um mercado perpétuo linear USDT-margined em BTC e ETH —
  documentado em `research.md` D1, não assumido.
- **FR-002**: O sistema MUST alinhar os históricos de funding de duas
  corretoras por período de 8h (arredondado à hora), não por timestamp
  exato.
- **FR-003**: O sistema MUST calcular o custo de abertura/fechamento
  usando a taxa real de cada corretora (verificada por busca, D2) — não
  reusar a taxa de uma corretora para outra.
- **FR-004**: O sistema MUST investigar e declarar explicitamente se a
  exigência de capital de H24 é menor, igual ou maior que a de H8 —
  não presumir melhoria.
- **FR-005**: O sistema MUST excluir do universo qualquer corretora sem
  mercado perpétuo linear USDT-margined comparável (ex.: Kraken/BTC) —
  nunca misturar denominação de margem numa mesma comparação.
- **FR-006**: O sistema MUST NOT enviar ordem real, alterar permissão de
  API nem modificar `trading/`, `execution/` ou `risk/`.

### Key Entities

- **ResultadoDiferencialCorretoras**: corretora A, corretora B, par,
  dias cobertos, diferencial bruto a.a., líquido a.a. sobre nocional,
  líquido a.a. sobre capital implantado, direção (qual corretora
  vender/comprar), se supera o benchmark.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `python main.py funding_cross` produz uma tabela por par
  de corretoras × ativo, ordenada por retorno sobre capital implantado.
- **SC-002**: O registro documenta explicitamente a conclusão sobre
  eficiência de capital (D3) e quantos pares superam o benchmark.
- **SC-003**: Nenhuma ordem real é enviada; nenhuma permissão de API
  muda; produção permanece idêntica.

---

## Assumptions

- **Universo de ativos**: BTC/USDT e ETH/USDT — mesmos de H23, para
  comparabilidade.
- **Benchmark**: reusa `BENCHMARK_RENDA_FIXA_AA` (5% a.a.) de
  `backtesting/funding_carry.py`, sem inventar novo número.
- Se a conclusão sobre capital (D3) mostrar que H24 não é mais
  eficiente que H8, isso não invalida a pergunta sobre o TAMANHO do
  diferencial — as duas perguntas (tamanho do diferencial, eficiência
  de capital) são reportadas separadamente.
