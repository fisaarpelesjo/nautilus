# Feature Specification: H10 — reseleção de pares desacoplada da formação

**Feature Branch**: `054-h10-reselecao-frequente`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: Spec 052 refutou universo amplo como
causa da fome de amostra de H10 (continua exatamente 6 trades na
validação com 12 ou 22 pares candidatos). Diagnóstico direto sobre a
janela de validação real (22 pares, `UNIVERSO_AMPLO_HISTORICO_COMPLETO`,
sem tocar em nenhum parâmetro) mediu a causa: `run_pairs_scan` amarra
`reselecionar_a_cada` a `p.formacao` (500) — só **4 ciclos de
reseleção** ocorrem nos ~2.300 candles de validação, elegendo 1 a 3
pares por ciclo (9 pares distintos ao todo). Dentro dessa janela, o
z-score dos pares elegíveis cruza o limiar de entrada (`entrada_z=2,0`)
apenas **6 vezes em toda a validação** — o mesmo número exato dos 6
trades já publicados. `max_pares=3` nunca é o gargalo: 1.794 dos 2.300
candles têm slot livre e nenhuma oportunidade entre os pares
selecionados no momento. `run_pairs_backtest` já aceita
`reselecionar_a_cada` como parâmetro independente de `formacao`
(default 250) — só `run_pairs_scan` nunca expôs essa independência,
sempre chamando com `reselecionar_a_cada=p.formacao`. Corrigir isso e
testar uma cadência mais frequente, DESACOPLADA da formação (que
continua em 500 candles de lookback, preservando o poder de detecção
de 60% já medido em spec 039).

---

## Contexto e tese

**O que o diagnóstico já eliminou.** `max_pares` não é o gargalo —
medido diretamente: quase 80% dos candles da validação têm capacidade
livre sem nenhuma oportunidade para preencher. Testar `max_pares` maior
não mudaria nada; essa spec não o testa.

**Por que reselecionar mais devagar que a formação não perde poder de
detecção.** `selecionar_pares(precos, p, ate=i)` sempre olha
`p.formacao` candles para trás a partir de `i`, **independente** de
quantas vezes por período `i` avança entre chamadas. Reselecionar a
cada 120 candles em vez de a cada 500 não encolhe a janela de
formação (continua 500, o mesmo poder de detecção de 60% de spec 039)
— só aumenta quantas VEZES essa janela de 500 candles é reavaliada ao
longo da validação, capturando relações de cointegração que se
formaram e se desfizeram entre um checkpoint de 500 e outro.

**Por que `120`, não um número escolhido para produzir mais trades.**
`meia_vida_max` (já existente, `PairsParams.meia_vida_max=120`) é o
teto declarado de meia-vida negociável — a relação de reversão mais
lenta que a regra ainda considera elegível. Reselecionar mais devagar
que o ciclo de reversão mais lento que a própria regra aceita
arrisca perder pares cuja relação já completou um ciclo inteiro e
mudou de caráter entre um checkpoint e outro. `reselecionar_a_cada =
meia_vida_max` é o maior intervalo que ainda garante pelo menos um
checkpoint por ciclo de reversão completo, para a mais lenta das
relações que a regra aceita — critério mecânico, amarrado a uma
constante já declarada em spec 039/028, não uma escolha nova.

**Zero mecânica de seleção/entrada/saída nova.** `selecionar_pares`,
`PairsParams` (entrada/saída/stop/meia-vida/ADF), `evaluate_approval`
continuam intocados — só a cadência de reseleção passa a ser
parâmetro explícito de `run_pairs_scan`, desacoplada de `formacao`.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reavaliar H10 com reseleção mais frequente (Priority: P1)

O pesquisador obtém o resultado de treino e validação de H10 com
`reselecionar_a_cada=120` (era 500, amarrado à formação), formação
continuando em 500 candles, comparado explicitamente contra os dois já
publicados (12 pares/spec 039, 22 pares/spec 052 — ambos com 6 trades
na validação).

**Why this priority**: é a pergunta da hipótese — sem o comparativo,
não há como saber se mais checkpoints de reseleção geram mais
oportunidades de entrada dentro da mesma janela de validação.

**Independent Test**: confirmar que `run_pairs_scan` aceita
`reselecionar_a_cada` como parâmetro independente de `p.formacao`, e
que passar um valor diferente de `p.formacao` de fato muda quantas
vezes `selecionar_pares` é chamada dentro de `run_pairs_backtest` (não
só que o parâmetro existe — que ele realmente desacopla).

**Acceptance Scenarios**:

1. **Given** `PairsParams(formacao=500)` e
   `reselecionar_a_cada=120`, **When** `run_pairs_scan` roda, **Then**
   `selecionar_pares` é chamado com `ate=i` a cada 120 candles (não
   500), sempre olhando 500 candles para trás a partir de cada `i`.
2. **Given** o resultado com reseleção a cada 120, **When** comparado
   aos dois já publicados (6 trades, 12 e 22 pares), **Then** os três
   aparecem lado a lado no registro — nunca um substitui o outro.
3. **Given** `total_trades` da validação, **When** atinge
   `EDGE_MIN_TRADES` (10), **Then** o veredito deixa de ser bloqueado
   por amostra insuficiente.

---

### Edge Cases

- `reselecionar_a_cada` não fornecido: `run_pairs_scan` MUST preservar
  o comportamento já publicado (`reselecionar_a_cada=p.formacao`) —
  regressão explícita antes de qualquer medição nova.
- Reseleção mais frequente aumenta o custo computacional (mais
  chamadas de `selecionar_pares`, cada uma testando até 231
  combinações) — aceitável para um comando de pesquisa, não para o
  loop de produção (que não usa `pairs_trading.py`).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST adicionar `reselecionar_a_cada:
  Optional[int] = None` a `run_pairs_scan` — quando `None`, preserva o
  comportamento já publicado (`= p.formacao`); quando fornecido, usa o
  valor explícito, desacoplado da formação.
- **FR-002**: O sistema MUST testar com `reselecionar_a_cada=120`
  (`PairsParams.meia_vida_max`, já existente) — critério mecânico
  declarado, não escolha ajustada ao resultado.
- **FR-003**: O sistema MUST manter `formacao=500` e todos os demais
  `PairsParams` idênticos aos já publicados — só a cadência de
  reseleção muda.
- **FR-004**: O sistema MUST reportar o resultado ao lado dos dois já
  publicados (12 pares/spec 039, 22 pares/spec 052) — nunca
  substituindo.
- **FR-005**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/`.

### Key Entities

- Nenhuma entidade nova.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `run_pairs_scan` aceita `reselecionar_a_cada`
  independente de `formacao`, com regressão confirmando que omiti-lo
  reproduz o resultado já publicado byte a byte.
- **SC-002**: Um resultado de treino/validação com reseleção a cada
  120 candles é produzido, comparável aos dois já publicados.
- **SC-003**: Nenhuma ordem real é enviada; produção permanece
  idêntica.

---

## Assumptions

- **Diagnóstico já medido** (sem código novo, script de investigação):
  4 ciclos de reseleção, 6 oportunidades de entrada, `max_pares` nunca
  binding em 2.300 candles de validação sobre 22 pares — base
  empírica desta spec, não hipótese.
- **`meia_vida_max=120`**: já declarado em `PairsParams` (spec
  028/039) — reusado sem remedição.
- Reprovação, aprovação ou inconclusão por outro motivo desta spec não
  invalida os vereditos já publicados de H10 — é a mesma pergunta, com
  a cadência de reseleção desacoplada da formação.
