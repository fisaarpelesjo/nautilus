# Feature Specification: H26 — reversão contra funding extremo (crowding/liquidação)

**Feature Branch**: `063-h26-reversao-funding-extremo`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: H8/H23/H24 exploram o funding rate como
fonte de *carry* (aposta a favor do sinal, mantida continuamente). H26
pergunta algo diferente: funding **extremamente negativo** (posição
majoritariamente vendida, pagando para manter a posição) prevê reversão
de curto prazo o bastante para servir de gatilho de entrada comprada,
avaliado pela mesma barreira tripla que H14 já usa? Esta é uma hipótese
**direcional**, a família que já falhou em 21 avaliações anteriores
deste registro (§6.3-b) — o teste deve ter o mesmo rigor de qualquer
outra, sem viés de confirmação a favor.

---

## Contexto e tese

**Por que é direcional, não carry.** H8 mede o retorno de MANTER uma
posição delta-neutra continuamente, recebendo/pagando funding a cada 8h
— não depende de prever direção de preço. H26 é o oposto: usa o funding
extremo como um EVENTO que dispara uma aposta direcional (long) sobre
o preço, na expectativa de reversão de curto prazo após um extremo de
posicionamento. É uma hipótese da família que o registro já testou 21
vezes sem sobreviver a custo de execução e confirmação fora da amostra
(§6.3-b) — a expectativa declarada é REPROVADA, não aprovação.

**Mecanismo restrito a long, por restrição de produção.** O bot só
opera posições compradas (`CLAUDE.md`: "Short não está implementado").
O lado testável é: funding extremamente **negativo** (shorts crowded)
como gatilho de entrada **longa** contrária. O lado espelhado (funding
extremamente positivo → contrário seria short) não é testável sem a
mesma infraestrutura de futuros que H8/H24 nunca construíram para
produção — fica como limitação declarada, não como parte do escopo.

**Reusa a barreira tripla de H14 diretamente — não constrói um novo
motor.** A pergunta "este evento prevê retorno suficiente para pagar
`stop 1,5×ATR / alvo 3,0×ATR`?" é exatamente a mesma que H14 já
responde para um classificador contínuo — aqui o "modelo" é mais simples
(um limiar sobre uma única variável, não uma regressão logística sobre
cinco atributos), mas a métrica de sucesso é idêntica:
`razao_de_chances` do subconjunto de eventos, testada contra
`limiar_de_empate` via `supera_empate_com_confianca` (Wilson CI) — nunca
o ponto estimado isolado (lição de M9/M13, `docs/research/
registro-de-hipoteses.md`).

**Limiar de extremo calibrado só no treino, aplicado à validação —
disciplina obrigatória.** Um limiar escolhido sobre toda a série
(incluindo a validação) vazaria informação futura para dentro do
critério de entrada. O decil mais negativo da distribuição de funding
do PAR é calculado exclusivamente na fatia de treino (primeiros 70% da
série, `DEFAULT_VALIDATION_RATIO` já existente) e aplicado sem
reajuste à fatia de validação.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir se funding extremo prevê reversão suficiente para pagar a barreira (Priority: P1)

O pesquisador obtém, para cada par com histórico de funding disponível,
o limiar de extremo calibrado no treino, quantos eventos de funding
extremo ocorrem na validação, a razão de chances alvo/stop desse
subconjunto e se ela supera o ponto de empate com 95% de confiança —
agregado (pooled) entre pares, mesmo padrão de H14.

**Why this priority**: é a pergunta inteira da hipótese.

**Independent Test**: `avaliar_par` sobre séries de preço e funding
sintéticas produz o limiar de extremo, a contagem de eventos e a razão
de chances corretamente, sem buscar dado real.

**Acceptance Scenarios**:

1. **Given** um par com histórico de funding e preço suficiente,
   **When** `avaliar_par` roda, **Then** calcula o limiar de extremo
   (decil mais negativo) exclusivamente sobre a fatia de treino.
2. **Given** o limiar calibrado, **When** aplicado à fatia de
   validação, **Then** os eventos extremos são rotulados pela mesma
   barreira tripla (`strategy/barreira_tripla.py::rotular`) já usada
   por H14, sem parâmetro novo de risco.
3. **Given** os eventos agregados de todos os pares, **When**
   reportado, **Then** a razão de chances pooled e o veredito de
   `supera_empate_com_confianca` aparecem lado a lado — nunca o ponto
   estimado isolado.

---

### Edge Cases

- **Par sem mercado perpétuo**: excluído do universo (mesma regra de
  exclusão de `data/funding.py`/spec 058) — nunca contado como zero.
- **Fatia de treino com cobertura de funding esparsa demais para um
  quantil confiável**: risco declarado, não bloqueado numericamente
  (universo pequeno o bastante para inspeção manual do resultado).
- **Nenhum evento extremo na validação**: razão fica indefinida (sem
  stop, sem alvo) — reportado como tal, não como zero.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST calcular o limiar de funding extremo
  (decil mais negativo, `PERCENTIL_EXTREMO`) exclusivamente sobre a
  fatia de treino de cada par — nunca sobre a série inteira.
- **FR-002**: O sistema MUST rotular os eventos de funding extremo pela
  barreira tripla já existente (`strategy/barreira_tripla.py::rotular`),
  sem alterar `ParametrosBarreira` nem introduzir parâmetro de risco
  novo.
- **FR-003**: O sistema MUST alinhar o funding (período de 8h) aos
  candles (`TIMEFRAME`, 4h) por *forward-fill* causal — cada candle
  herda a última leitura de funding publicada até aquele instante,
  nunca uma leitura futura.
- **FR-004**: O sistema MUST aplicar `supera_empate_com_confianca`
  (Wilson CI) sobre as contagens agregadas de alvo/stop da validação —
  nunca a razão pontual isolada.
- **FR-005**: O sistema MUST NOT testar o lado espelhado (short) nem
  assumir infraestrutura de futuros — só o lado long, compatível com a
  restrição de produção já declarada.
- **FR-006**: O sistema MUST NOT alterar `trading/`, `execution/` ou
  `risk/`.

### Key Entities

- **ResultadoParH26**: par, limiar de extremo calibrado, contagem de
  eventos e amostra de treino/validação, alvo/stop/razão de validação,
  se supera o empate com confiança.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `python main.py funding_extremo` produz o resultado
  pooled (razão de chances, veredito de confiança) sobre `UNIVERSO_H11`.
- **SC-002**: O registro documenta o resultado — aprovação ou
  reprovação — com o mesmo rigor de qualquer outra hipótese direcional
  já testada, sem tratamento especial.
- **SC-003**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Universo**: `UNIVERSO_H11` (12 pares), restrito aos que têm
  mercado perpétuo com histórico de funding suficiente.
- **Expectativa declarada**: REPROVADA é o resultado mais provável, por
  base histórica (§6.3-b) — não é um resultado a evitar reportar, é a
  hipótese nula honesta desta spec.
- Resultado desta spec não substitui nenhum veredito já publicado de
  H8/H14/H20 — é uma pergunta nova sobre um sinal diferente.
