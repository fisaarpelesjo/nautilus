# Feature Specification: H32 — on-chain mais rico (valor transacionado)

**Feature Branch**: `069-h32-onchain-rico`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: H17 testou só `n-unique-addresses`
(crescimento de rede), status `insuficiente` (sinal indistinguível do
embaralhado). A fila (§6.2) pedia investigar se outro atributo on-chain
gratuito existe antes de comprometer uma spec nova. Investigado (D1):
`estimated-transaction-volume-usd` (valor movimentado on-chain, USD) é
gratuito, na mesma fonte já integrada, e mede POSICIONAMENTO/magnitude
em vez de atividade de rede — categoricamente diferente do já testado.

---

## Contexto e tese

**Por que não é uma repetição de H17.** `n-unique-addresses` conta
QUANTOS endereços estão ativos; `estimated-transaction-volume-usd` mede
QUANTO valor está se movendo. Um evento de reposicionamento
concentrado (poucas carteiras grandes, valor alto) apareceria em um e
não no outro — os dois atributos podem, em princípio, carregar
informação diferente, mesmo vindo da mesma fonte.

**Hipótese declarada antes de medir.** Igual peso para duas leituras:
(a) o atributo sobrevive à colinearidade e desloca a razão de chances
decidida na mesma direção de H14 (melhora ou ao menos não piora); (b)
o atributo é colinear com `volume_ratio` (já um dos 5 atributos de H14)
ou com `onchain_addr_growth_7d` (H17), e é descartado antes de medir
desempenho.

**Zero mecânica nova de trading.** Reusa `backtesting/modelo.py`
(H14) e o padrão de comparação isolada de `backtesting/onchain_hipotese.py`
(H17) sem alterar nenhum dos dois.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir se o atributo sobrevive à colinearidade e muda o resultado (Priority: P1)

**Acceptance Scenarios**:

1. **Given** BTC/USDT, 6.000 candles, **When** o atributo
   `onchain_txn_volume_growth_7d` é calculado e comparado contra os 5
   atributos de H14 + `onchain_addr_growth_7d`, **Then** reporta a
   correlação com cada um.
2. **Given** colinearidade abaixo de 0,80 com todos, **When** o modelo
   é retreinado com o atributo extra, **Then** compara razão de chances
   geral e decidida contra o modelo original — mesmo par, mesmo
   período (nunca contra o resultado pooled de 12 pares).
3. **Given** colinearidade acima de 0,80 com qualquer atributo
   existente, **When** detectado, **Then** o atributo é descartado e o
   relatório documenta isso explicitamente, sem prosseguir a comparação
   de desempenho.

---

## Requirements *(mandatory)*

- **FR-001**: O sistema MUST calcular `onchain_txn_volume_growth_7d`
  usando a mesma transformação de `onchain_addr_growth_7d` (H17), só
  trocando a série-fonte.
- **FR-002**: O sistema MUST checar colinearidade contra os 5 atributos
  de H14 e contra `onchain_addr_growth_7d`, limiar 0,80 (mesmo de H17).
- **FR-003**: O sistema MUST comparar isoladamente (mesmo par BTC/USDT,
  mesmo período) o modelo com e sem o atributo — nunca contra o
  resultado pooled de 12 pares já publicado.
- **FR-004**: O sistema MUST NOT alterar `strategy/`, `risk/`,
  `execution/` ou `trading/`.

---

## Success Criteria *(mandatory)*

- **SC-001**: `python main.py onchain_volume` produz o relatório de
  colinearidade e a comparação com/sem o atributo.
- **SC-002**: Nenhuma ordem real é enviada; produção intocada.

---

## Assumptions

- Fonte: `api.blockchain.info` (já integrada, `data/onchain.py`),
  Bitcoin-only — mesma limitação de H17.
- Se colinear, a spec fecha na checagem de colinearidade — resultado
  válido e completo, mesmo padrão de M-catálogo do registro.
