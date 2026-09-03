# Feature Specification: H27 — meta-labeling, pré-condição sobre o sinal primário

**Feature Branch**: `064-h27-meta-labeling`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: Depois do encerramento da busca ativa das 26
hipóteses originais (§8 do registro), o usuário pediu metodologias
genuinamente diferentes das 4 famílias já fechadas (direcional, carry
delta-neutro, arbitragem pura, estrutural). H27 é meta-labeling — técnica
de López de Prado (*Advances in Financial Machine Learning*): em vez de
treinar um classificador do zero para prever direção (H14), treina-se um
modelo SECUNDÁRIO que decide se um sinal PRIMÁRIO já existente (o
crossover EMA/RSI de produção) deve ser executado. Arquitetura diferente
de tudo já testado — filtra apostas de um sinal, não gera sinal novo.

---

## Contexto e tese

**Por que uma pré-condição antes de qualquer modelo.** O próprio
levantamento que adicionou H27 à fila já registrou o risco central: H1 (o
mesmo crossover EMA/RSI que seria filtrado) foi REPROVADO isoladamente
(0/20 confirmadas fora da amostra). Se o sinal primário não carrega
nenhuma informação real nos próprios eventos, um modelo secundário estaria
filtrando ruído, não sinal — risco estrutural análogo ao que bloqueou H12
por pré-condição (§6.4 do registro: "dimensionamento decide QUANTO, nunca
SE").

**A pergunta testável antes de treinar qualquer modelo secundário:** os
eventos de entrada que o EMA/RSI já geraria (`precompute_signals`,
`Signal.BUY`) têm, nos seus próprios desfechos (barreira tripla, mesma de
H14), uma razão de chances que supera o ponto de empate com confiança —
ou são estatisticamente indistinguíveis do baseline geral de todos os
candles?

**Zero mecânica de meta-modelo nesta spec se a pré-condição não for
atendida.** Treinar um classificador secundário sem essa checagem
gastaria esforço real testando algo que a pré-condição já teria
descartado — mesmo princípio de "declarar antes de medir" usado em toda
hipótese deste registro.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verificar se o sinal primário carrega informação suficiente (Priority: P1)

O pesquisador obtém, pooled sobre `UNIVERSO_H11`, a razão de chances dos
eventos de entrada do EMA/RSI (rotulados pela barreira tripla de H14)
comparada ao baseline de todos os candles — e um veredito explícito sobre
se a pré-condição para meta-labeling está atendida.

**Why this priority**: decide se vale a pena construir o modelo
secundário — sem essa resposta, qualquer investimento seguinte é
prematuro.

**Independent Test**: `avaliar_precondicao` sobre sinais/rótulos
sintéticos produz as contagens corretas e o veredito correto — sem rede.

**Acceptance Scenarios**:

1. **Given** `UNIVERSO_H11` e os parâmetros padrão da barreira tripla,
   **When** `avaliar_precondicao()` roda, **Then** devolve o baseline
   (todos os candles), a entrada primária (só onde EMA/RSI sinalizaria
   BUY) e se a entrada primária supera o empate com confiança.
2. **Given** o resultado, **When** a entrada primária NÃO supera o
   empate com confiança, **Then** o sistema reporta isso explicitamente
   como pré-condição não atendida — não como erro, não como sucesso
   disfarçado.

---

### Edge Cases

- **Par sem preparo suficiente** (`preparar` devolve `None`): excluído do
  pooled, nunca contado como zero.
- **Nenhum par produz dado**: `ValueError` explícito, nunca um resultado
  vazio silencioso.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST gerar os eventos de entrada do sinal
  primário via `precompute_signals` (o mesmo caminho vetorizado já usado
  por `optimize`/`backtest --validate`), não reimplementar a lógica de
  sinal.
- **FR-002**: O sistema MUST rotular os desfechos via `rotular` (barreira
  tripla, mesmos parâmetros de H14) — nunca um rótulo próprio novo.
- **FR-003**: O sistema MUST aplicar `supera_empate_com_confianca` (Wilson
  CI) sobre as contagens da entrada primária — nunca a razão pontual
  isolada.
- **FR-004**: O sistema MUST reportar o baseline (todos os candles) ao
  lado da entrada primária, para contexto — nunca só um número isolado.
- **FR-005**: O sistema MUST NOT treinar nenhum modelo secundário nesta
  spec — escopo é só a pré-condição.
- **FR-006**: O sistema MUST NOT alterar `trading/`, `execution/` ou
  `risk/`.

### Key Entities

- **ResultadoFaixa**: nome, n, alvo, stop, tempo, razão, se supera o
  empate com confiança.
- **ResultadoPrecondicao**: empate, nº de pares, baseline, entrada
  primária, se a pré-condição está atendida.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `python main.py meta_labeling` produz o veredito de
  pré-condição, reproduzível a qualquer momento.
- **SC-002**: O registro documenta explicitamente se a pré-condição foi
  atendida — e, se não, que a linha se encerra aqui (mesma categoria de
  H12), sem gastar esforço num modelo secundário sem precondição.
- **SC-003**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Universo e barreiras**: `UNIVERSO_H11` (12 pares) e
  `ParametrosBarreira()` padrão — mesmos de toda a linha de H14.
- Se a pré-condição não for atendida, esta spec se encerra na pré-condição
  — não é uma promessa de retomar com um sinal primário diferente (isso
  seria uma hipótese nova, não uma continuação desta).
- Se a pré-condição FOR atendida, um modelo secundário real (arquitetura,
  atributos, validação fora da amostra) seria uma spec seguinte — fora do
  escopo declarado aqui.
