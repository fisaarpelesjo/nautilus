# Feature Specification: H38 — Gate por volatilidade implícita (Deribit DVOL)

**Feature Branch**: `074-h38-dvol-gate`

**Created**: 2026-09-06

**Status**: Draft

**Input**: User description: Deribit publica DVOL (índice de volatilidade
implícita de 30 dias de BTC, derivado do mercado de opções) via API
pública, sem chave — fonte de dado categoricamente nova, nunca usada
neste registro (vem de opções, não de preço/posicionamento/on-chain).
Filtro aditivo de regime sobre a estratégia EMA/RSI já existente,
aplicado ao universo inteiro (DVOL é indicador sistêmico, papel análogo
ao VIX). Obstáculo: mesma disciplina de pré-registro de H28 e mesmo risco
estrutural de H27 — precisa verificar se o gate REALMENTE discrimina
eventos de entrada bons de ruins antes de declarar qualquer aprovação,
reusando a mesma população "entrada primária" que H27 já calcula. Quinta
hipótese da leva H34-H40 (deepsearch 2026-09-06).

---

## Contexto e tese

**Por que isso é diferente de qualquer filtro já testado.** Todos os
filtros de regime já avaliados neste registro (ADX, `HIGH_VOLATILITY_FILTER_ENABLED`)
derivam de indicadores INTERNOS ao próprio preço cripto. DVOL vem do
mercado de OPÇÕES — a expectativa do mercado sobre volatilidade futura,
não a volatilidade já realizada no passado — fonte de informação
categoricamente distinta. Diferente de H26/H35/H36 (que usam dado externo
como sinal de ENTRADA), aqui o dado externo é um GATE que só SUSPENDE
entradas, nunca as cria — mesmo papel estrutural de `REGIME_FILTER_ENABLED`.

**Por que a precondição vem antes do resultado.** Um filtro aditivo sobre
uma estratégia primária sem edge comprovado (H1/EMA-RSI puro, já
reprovada em backtest histórico) só tem valor real se a variável do gate
DISCRIMINAR eventos de entrada bons de ruins — senão, qualquer aprovação
aparente seria coincidência de amostra, não um filtro funcionando. Esta
spec reusa o mesmo desenho de verificação de precondição que H27
(meta-labeling) já implementou e já tem módulo publicado
(`backtesting/meta_labeling.py::avaliar_precondicao`): a MESMA população
de eventos de entrada do sinal primário (EMA/RSI, rotulados pela barreira
tripla) é dividida em dois subconjuntos por nível de DVOL no momento da
entrada, e os dois são comparados.

**Hipótese declarada antes de medir.** Eventos de entrada do sinal
primário que ocorrem com DVOL no decil mais alto da própria série (stress
de volatilidade implícita) têm razão alvo/stop pior que os demais eventos
— evidência de que o gate discrimina, justificando medir uma versão
completa do filtro depois.

**Hipótese alternativa, com peso igual.** Os dois subconjuntos não diferem
de forma que importe — o nível de DVOL no momento da entrada não carrega
informação sobre o resultado do trade primário, e a precondição não é
atendida (mesmo desfecho de H27: spec encerrada por desenho, sem
prosseguir para uma implementação completa do gate que não teria o que
filtrar).

**Zero mecânica de trading nova.** Reusa a mesma extração de eventos
"entrada primária" de H27, a mesma barreira tripla, o mesmo critério de
significância — sem inventar critério de comparação novo. Não toca
`trading/`, `execution/`, `risk/` nem a estratégia em produção.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verificar se o DVOL discrimina eventos de entrada bons de ruins (Priority: P1)

O pesquisador obtém, numa única execução, se os eventos de entrada do
sinal primário (EMA/RSI) com DVOL em stress (decil mais alto da própria
série) têm resultado pior que os demais eventos, com significância
estatística sobre a contagem agregada entre pares.

**Why this priority**: é a precondição que decide se vale medir uma
versão completa do gate.

**Independent Test**: a divisão dos eventos por nível de DVOL pode ser
testada isoladamente sobre uma população sintética de eventos com DVOL e
rótulo conhecidos.

**Acceptance Scenarios**:

1. **Given** a população de eventos de entrada do sinal primário (EMA/RSI)
   já rotulados pela barreira tripla, **When** divididos por DVOL no
   momento da entrada (decil mais alto vs. o resto), **Then** cada
   subgrupo reporta sua própria razão alvo/stop e status de significância.
2. **Given** o nível de DVOL no dia do evento, **When** alinhado ao
   candle, **Then** usa o valor completo do dia anterior — nunca o dia
   corrente, ainda incompleto na fonte.
3. **Given** o resultado dos dois subgrupos, **When** comparado, **Then**
   o veredito de precondição é explícito (atendida ou não) — nunca
   implícito atrás de um número isolado.
4. **Given** um par sem dado de DVOL disponível no período (limitação:
   DVOL só existe para BTC/ETH), **When** avaliado, **Then** eventos desse
   par sem DVOL alinhável são excluídos da divisão, sem abortar a
   avaliação dos demais.

---

### Edge Cases

- **DVOL indisponível para um trecho do histórico** (retenção da fonte
  pode ser menor que o histórico de candles): eventos sem DVOL alinhável
  nesse trecho são excluídos da divisão — nunca presumido um nível de
  DVOL sem dado real.
- **Nenhum evento cai no decil mais alto** (distribuição de DVOL
  degenerada num subconjunto pequeno de pares/período): subgrupo
  reportado com contagem zero, nunca erro.
- **Os dois subgrupos têm razão idêntica**: precondição não atendida —
  ausência de diferença é um resultado válido, não uma falha de execução.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST buscar o histórico de DVOL via a API pública
  da Deribit, sem exigir credencial.
- **FR-002**: O sistema MUST reusar a mesma população de eventos de
  entrada do sinal primário já calculada por
  `backtesting/meta_labeling.py` (EMA/RSI, rotulados pela barreira
  tripla) — sem reimplementar a extração de eventos.
- **FR-003**: O sistema MUST alinhar o DVOL ao candle por forward-fill
  causal, com o candle do dia D usando o valor completo do dia D-1.
- **FR-004**: O sistema MUST calibrar o limiar do decil mais alto de DVOL
  sobre a própria série histórica de DVOL — nunca um valor absoluto
  arbitrário compartilhado.
- **FR-005**: O sistema MUST dividir a população de eventos de entrada em
  dois subgrupos (DVOL no decil mais alto vs. o resto) e reportar a razão
  alvo/stop e o status de significância de cada um separadamente — nunca
  um único número agregando os dois.
- **FR-006**: O sistema MUST declarar a precondição atendida ou não,
  de forma explícita, com base na comparação entre os dois subgrupos —
  nunca implícita.
- **FR-007**: O sistema MUST excluir da divisão qualquer evento cujo par
  não tenha DVOL alinhável no período (par sem cobertura de DVOL) — nunca
  presumir nível de DVOL sem dado real.
- **FR-008**: O sistema MUST NOT enviar ordem real nem alterar `trading/`,
  `execution/`, `risk/` ou a estratégia em produção (`strategy/ema_rsi.py`).
- **FR-009**: O sistema MUST registrar o veredito final em
  `docs/research/registro-de-hipoteses.md`, incluindo comparação
  explícita com H27 (mesma arquitetura de precondição, fonte de dado e
  propósito diferentes).

### Key Entities

- Reaproveita `ResultadoFaixa`/`ResultadoPrecondicao` (já existentes em
  `backtesting/meta_labeling.py`) — nenhuma entidade de dado nova é
  necessária além do corte adicional por DVOL.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma execução única produz a razão alvo/stop e o status de
  significância dos dois subgrupos (DVOL alto vs. resto), agregados entre
  os pares do universo declarado.
- **SC-002**: O registro documenta explicitamente se a precondição foi
  atendida (o gate discrimina) ou não, com comparação direta contra H27 —
  nunca implícito.
- **SC-003**: Nenhuma ordem real é enviada; o comportamento de produção
  permanece idêntico ao anterior a esta feature.

---

## Assumptions

- **Escopo desta spec: só a precondição.** Mesma decisão estrutural de
  H27 — se a precondição não for atendida, a spec se encerra por desenho
  (sem prosseguir para uma implementação completa do gate aditivo em
  produção, que não teria o que filtrar).
- **DVOL aplicado market-wide**: o mesmo DVOL de BTC é usado como gate
  para eventos de entrada de QUALQUER par do universo — decisão já
  declarada na fundamentação (indicador sistêmico, não específico de um
  par), não fixada pelo `/speckit-plan`.
- **Decil e universo**: percentual exato do decil (mesmo valor de
  H26/H35, 10%) e o universo (`UNIVERSO_H11`, mesmo de H27) são reusados
  sem reajuste — decisão técnica de qual DVOL exatamente usar (BTC vs.
  ETH vs. combinação) cabe ao `/speckit-plan`.
- Resultado desta spec não substitui nenhum veredito já publicado — ataca
  uma precondição (o DVOL discrimina eventos de entrada) nunca verificada
  antes neste registro.
