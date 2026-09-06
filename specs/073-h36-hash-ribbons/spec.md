# Feature Specification: H36 — Hash Ribbons: capitulação de mineradores (BTC-only)

**Feature Branch**: `073-h36-hash-ribbons`

**Created**: 2026-09-06

**Status**: Draft

**Input**: User description: indicador de Charles Edwards/Capriole (2019):
cruzamento da média móvel de 30 dias sobre a de 60 dias do hashrate de
Bitcoin. "Capitulação" (30d < 60d, mineradores desligando) seguida de
"recuperação" (30d cruza acima de 60d de novo) historicamente precede
fundos de ciclo — mecanismo de OFERTA (economia de mineração),
categoricamente diferente de qualquer sinal de preço, posicionamento ou
atividade de rede já testado (H14, H17/H32). Sinal de saída simétrico
(cruzamento contrário) fecha a posição. Probe real desta sessão
(`fetch_onchain_series`, já existente): 1085 pontos diários, 16
cruzamentos de alta e 16 de baixa em ~2,7 anos. BTC-only por natureza.
Quarta hipótese da leva H34-H40 (deepsearch 2026-09-06).

---

## Contexto e tese

**Por que isso é diferente de H14/H17/H32.** H17 e H32 usam dado on-chain
(atividade de rede, volume transacionado) como ATRIBUTO ADICIONAL de um
classificador supervisionado (barreira tripla de H14) — o dado on-chain
ali é um insumo entre vários, não o próprio sinal de entrada. H36 usa o
hashrate como o SINAL DE ENTRADA/SAÍDA DIRETO — mecanismo de OFERTA
(custo de mineração vs. preço do BTC), não de demanda ou de padrão
técnico de preço. É a primeira hipótese deste registro em que um dado
on-chain dirige o sinal diretamente, não alimenta um modelo.

**Achado empírico que contextualiza o teste antes de medir resultado.**
Um probe real contra `data/onchain.py::fetch_onchain_series("hash-rate",
timespan="3years")` (mesma fonte já usada por H17/H32, sem infraestrutura
nova) mediu 1085 pontos diários (2023-09-07 a 2026-09-05) e, sobre essa
série, 16 cruzamentos de alta e 16 de baixa das médias móveis de 30/60
dias — mais frequente que os "~14 sinais em 13 anos" citados na
literatura original (a série bruta da fonte pública parece mais ruidosa
que o indicador original, possivelmente já suavizado). A definição do
cruzamento (média móvel simples de 30/60 dias, sem suavização adicional)
é declarada ANTES de medir qualquer desempenho — a frequência observada é
contexto, não motivo para ajustar a definição depois de ver o dado.

**Obstáculo já esperado: amostra e horizonte de holding.** Hashrate é uma
métrica exclusiva da rede Bitcoin — sem equivalente para os demais pares
do bot, então esta hipótese é BTC-only por natureza, mesmo risco de
amostra pequena já visto em H10 (antes da correção de spec 054) e em H34.
Adicionalmente, o holding histórico médio do sinal original (~253 dias) é
muito mais longo que o horizonte típico de qualquer outra hipótese deste
registro — o stop/alvo/trailing por ATR já genérico do motor de backtest
permanece ativo sem alteração (mesmo comportamento que a produção teria);
se isso interromper o hold longo antes do prazo histórico, é um achado
real sobre a interação entre o sinal e a gestão de risco do bot, não um
defeito a contornar desligando o SL/TP.

**Hipótese declarada antes de medir.** O cruzamento de alta das médias
móveis de 30/60 dias do hashrate antecede retorno positivo em BTC/USDT
acima do baseline, avaliado pela bateria comum E1-E6, mesmo com o
SL/TP/trailing por ATR do motor de backtest ativo sem alteração.

**Hipótese alternativa, com peso igual.** A amostra de eventos disponível
no histórico de candles é pequena demais para qualquer leitura ter peso
(mesmo padrão de risco já visto em H10/H34), ou o SL/TP por ATR do motor
de backtest interrompe sistematicamente o hold longo antes do sinal
completar seu ciclo histórico — resultado igualmente válido, já que o
objetivo desta rodada é medir a interação real entre o sinal e a
infraestrutura de risco existente, não confirmar a tese antes de medir.

**Zero mecânica de trading nova.** É um sinal de entrada/saída alternativo
avaliado pela infraestrutura de backtest já existente, sem SL/TP artificial
novo — não toca `trading/`, `execution/`, `risk/` nem a estratégia em
produção (`strategy/ema_rsi.py`).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Veredito completo E1-E6 sobre o cruzamento de hashrate (Priority: P1)

O pesquisador obtém, numa única execução, se o cruzamento de alta das
médias móveis de 30/60 dias do hashrate de Bitcoin antecede retorno
positivo em BTC/USDT, com o quadro completo das seis etapas da bateria
(sanidade, janela única, busca/confirmação fora da amostra, walk-forward,
desconto de exposição, sensibilidade a custo).

**Why this priority**: é a pergunta central da hipótese.

**Independent Test**: a detecção de cruzamento pode ser testada
isoladamente sobre uma série sintética de hashrate com cruzamentos em
posições conhecidas.

**Acceptance Scenarios**:

1. **Given** um candle cujo dia correspondente (D-1, alinhamento causal)
   teve cruzamento de alta das médias de 30/60 dias do hashrate, **When**
   o motor avalia o sinal, **Then** um sinal de entrada é gerado; no
   cruzamento de baixa simétrico, um sinal de saída é gerado.
2. **Given** a bateria completa rodando sobre `BTC/USDT`, **When** a
   execução termina, **Then** cada uma das seis etapas é reportada
   individualmente, com status explícito por etapa.
3. **Given** um teste de sanidade E1 com série sintética de hashrate sem
   nenhum cruzamento (série monotônica crescente, médias sempre na mesma
   ordem), **When** a bateria roda, **Then** zero entradas ocorrem.
4. **Given** candles anteriores ao início real do histórico de hashrate
   disponível, **When** alinhados, **Then** são descartados — nunca um
   cruzamento presumido antes de existir dado real.
5. **Given** o veredito final, **When** registrado, **Then** o registro
   compara explicitamente com H17/H32 (mesma fonte de dado, mecanismo de
   sinal categoricamente diferente).

---

### Edge Cases

- **Histórico de candles mais longo que o histórico de hashrate
  disponível**: candles anteriores ao início real do hashrate são
  descartados, nunca alinhados por extrapolação retroativa.
- **Posição aberta por um cruzamento de alta nunca encontra o cruzamento
  de baixa simétrico dentro do histórico disponível**: a posição é
  fechada ao fim do período avaliado (mesmo comportamento já existente do
  motor de backtest para qualquer posição aberta no último candle).
- **SL/TP por ATR interrompe a posição antes do cruzamento de saída**:
  contabilizado normalmente como uma saída por stop/alvo — não é tratado
  como falha do sinal, é o comportamento real do bot.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST detectar o cruzamento de alta (30d cruza
  acima de 60d) e o cruzamento de baixa (30d cruza abaixo de 60d) das
  médias móveis do hashrate de Bitcoin, usando a fonte de dado on-chain já
  existente, sem infraestrutura de coleta nova.
- **FR-002**: O sistema MUST alinhar o cruzamento diário ao candle por
  forward-fill causal, com o candle do dia D usando o valor completo do
  dia D-1 — nunca o dia corrente, ainda incompleto na fonte.
- **FR-003**: O sistema MUST descartar candles anteriores ao início real
  do histórico de hashrate disponível — nunca presumir cruzamento antes
  de existir dado real.
- **FR-004**: O sistema MUST usar o cruzamento de alta como sinal de
  entrada e o cruzamento de baixa como sinal de saída — sem introduzir
  SL/TP artificial novo; o SL/TP/trailing por ATR já genérico do motor de
  backtest permanece ativo sem alteração.
- **FR-005**: O sistema MUST orquestrar a avaliação pela bateria comum
  (`backtesting/bateria_hipotese.py::rodar_bateria`, E1-E6), sem
  reimplementar a orquestração por conta própria.
- **FR-006**: O sistema MUST incluir um teste de sanidade (E1) com série
  sintética de hashrate sem nenhum cruzamento, verificando zero trades.
- **FR-007**: O sistema MUST avaliar somente `BTC/USDT` — hashrate não
  tem equivalente para os demais pares, sem universo multi-par.
- **FR-008**: O sistema MUST comparar o veredito final explicitamente com
  H17/H32 no registro (mesma fonte de dado, mecanismo de sinal
  categoricamente diferente — atributo de classificador vs. sinal direto).
- **FR-009**: O sistema MUST NOT enviar ordem real nem alterar `trading/`,
  `execution/`, `risk/` ou a estratégia em produção (`strategy/ema_rsi.py`).
- **FR-010**: O sistema MUST registrar o veredito final em
  `docs/research/registro-de-hipoteses.md`.

### Key Entities

- Reaproveita `BacktestResult` e `RelatorioBateria` (já existentes) —
  nenhuma entidade de dado nova é necessária.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma execução única produz o `RelatorioBateria` completo
  (E1-E6) sobre `BTC/USDT`, usando o histórico real de candles alinhado à
  janela real de hashrate disponível.
- **SC-002**: O registro documenta explicitamente se o sinal sobrevive às
  seis etapas, em qual delas reprova, ou se a amostra é insuficiente para
  qualquer leitura — nunca implícito.
- **SC-003**: Nenhuma ordem real é enviada; o comportamento de produção
  permanece idêntico ao anterior a esta feature.

---

## Assumptions

- **Definição do cruzamento**: médias móveis simples de 30 e 60 dias
  sobre o hashrate bruto da fonte pública, sem suavização adicional —
  fixada antes de medir desempenho (FR-001), não ajustada pela frequência
  observada no probe.
- **Universo e histórico**: um único par (`BTC/USDT`), histórico de
  candles dimensionado para cobrir a mesma janela real do hashrate
  disponível (~2023-09 em diante) — decisão exata de quantos candles
  buscar cabe ao `/speckit-plan`.
- **SL/TP por ATR**: permanece o padrão do motor de backtest, sem
  parâmetro novo — reajustar especificamente para acomodar o holding
  longo do sinal original seria uma escolha de design que a spec não
  fixa antecipadamente, deixada para medir o comportamento real primeiro.
- Resultado desta spec não substitui nenhum veredito já publicado — ataca
  um mecanismo (oferta via hashrate, sinal direto) nunca testado antes
  neste registro.
