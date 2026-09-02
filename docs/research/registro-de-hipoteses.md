# Registro de Hipóteses — Avaliação Sistemática de Estratégias

**Documento vivo.** Última atualização: 2026-09-01
**Escopo:** todas as hipóteses de geração de retorno avaliadas neste projeto,
com veredito, evidência e procedência.

---

## 1. Objetivo e questão de pesquisa

**Questão:** existe alguma combinação de estratégia × mercado × parametrização
que produza retorno positivo ajustado a risco, de forma persistente fora da
janela em que foi descoberta?

A formulação é deliberada. Não se pergunta "como tornar este bot lucrativo",
porque a pergunta pressupõe a resposta. Pergunta-se se **existe** vantagem, o
que admite resposta negativa — e uma resposta negativa obtida em modo simulado
tem custo zero, ao passo que a mesma resposta obtida em produção tem custo igual
ao capital alocado.

---

## 2. Metodologia

### 2.1 Critério de aprovação

Implementado em `backtesting/approval.py::evaluate_approval`. Uma configuração é
classificada como **aprovada** se e somente se satisfizer simultaneamente:

| Critério | Limiar | Constante |
|---|---|---|
| Número mínimo de operações | ≥ 10 | `EDGE_MIN_TRADES` |
| Profit factor | ≥ 1,20 | `MIN_PROFIT_FACTOR_FOR_APPROVAL` |
| Drawdown máximo | ≤ 10,0% | `MAX_ACCEPTABLE_DRAWDOWN_PCT` |
| Retorno vs. buy-and-hold | superior | `require_beat_buy_hold` |

O critério é fixo e anterior a qualquer teste. Alterá-lo após observar
resultados constituiria seleção sobre o próprio critério.

### 2.2 Confirmação fora da amostra

Implementado em `backtesting/validation.py::split_train_validation` e
`backtesting/multimarket.py::run_scan`. A série é dividida em fatias contíguas e
não sobrepostas — sem embaralhamento, por se tratar de série temporal — na razão
`DEFAULT_VALIDATION_RATIO = 0,3`, com `MIN_WINDOW_CANDLES = 150` por fatia.

Estados possíveis:

- **confirmado** — aprovado na busca **e** na janela de confirmação
- **só na busca** — aprovado onde foi descoberto, não sustentado fora. **Não
  constitui aprovação.**
- **reprovado** — falha em ao menos um critério
- **inconclusivo** — histórico insuficiente para dividir

### 2.3 Walk-forward e ganho de timing

Implementado em `backtesting/cross_sectional.py::walk_forward`, introduzido em
2026-09-01 após uma janela única de confirmação quase aprovar uma estratégia
cujo desempenho não replicou.

Duas correções metodológicas:

**(a) Múltiplas janelas.** Uma janela de confirmação não distingue vantagem de
sorte de regime. Cinco janelas contíguas expõem o comportamento em regimes de
alta, baixa e lateralidade.

**(b) Desconto de exposição.** Uma estratégia que permanece em caixa durante
mercado em queda exibe retorno superior ao buy-and-hold sem possuir capacidade
de seleção. A referência correta é o buy-and-hold **mantido na mesma fração de
capital**:

```
ganho_de_timing = retorno_estratégia − (buy_and_hold × exposição)
```

Um ganho de timing nulo indica que todo o resultado decorre de exposição
reduzida, não de escolha de ativos.

### 2.4 Custos de execução

Todos os backtests aplicam `BACKTEST_FEE_RATE = 0,001` sobre o nocional e
`BACKTEST_SLIPPAGE_PCT = 0,0005` sobre o preço, em entrada e saída. O modo paper
aplica os mesmos custos (`execution/order_manager.py`), garantindo paridade
entre simulação histórica e simulação em tempo real.

### 2.5 Limitação reconhecida do instrumental

O backtest opera sobre dados OHLCV, que não registram movimento intra-candle,
spread bid-ask nem profundidade de livro. Consequentemente, não modela: falhas
de preenchimento, evaporação de liquidez, nem execução de stop em ausência de
contraparte. Estimativas de slippage são conservadoras por construção, mas
constituem premissa, não medição.

---

## 3. Cronologia do projeto

215 commits entre 2026-04-26 e 2026-09-01. A distribuicao temporal e
informativa: 83 commits na construcao inicial (abr-mai), interrupcao de tres
meses, e 132 commits na fase de validacao e auditoria (ago-set). A segunda fase
produziu mais codigo de *medicao* que de estrategia.

### Fase I — Construcao (2026-04-26 a 2026-05-03, 83 commits)

Implementacao do sistema. Nenhuma hipotese formalmente testada; a estrategia foi
adotada por convencao, nao por evidencia.

| Data | Marco |
|---|---|
| 2026-04-26 | Bot multi-par inicial; SL/TP dinamico via ATR(14); trailing stop; filtro de volume |
| 2026-04-27 | Bollinger Bands como filtro de entrada |
| 2026-05-01 | Validacao de configuracao na inicializacao; metricas avancadas de backtest; otimizacao de parametros; registro de decisoes por ciclo |
| 2026-05-03 | `MIN_PRICE_USDT`; relatorio de *edge* contra buy-and-hold; cooldown global entre entradas para evitar posicoes correlacionadas |

**Observacao retrospectiva.** O relatorio de *edge* (2026-05-03) introduziu a
comparacao contra buy-and-hold, primeira nocao de que retorno positivo isolado
nao constitui evidencia. Os criterios formais de aprovacao ainda nao existiam.

### Hiato (2026-06 a 2026-07)

Nenhum commit. O sistema permaneceu no estado da Fase I.

### Fase II — Rigor metodologico via desenvolvimento orientado a especificacao (2026-08-13 a 2026-08-16)

Onze especificacoes executadas pelo fluxo GitHub Spec Kit. A enfase deslocou-se
de funcionalidade para **verificabilidade**.

| Spec | Escopo | Contribuicao ao instrumental |
|---|---|---|
| 001 | Hardening incremental | Idempotencia, reconciliacao, circuit breaker, kill switch, **validacao out-of-sample** |
| 002 | Aprovacao multi-par | `backtesting/approval.py::evaluate_approval` — criterio formal, fixo e anterior aos testes |
| 003 | Otimizacao sem overfitting | Split treino/validacao, walk-forward, Monte Carlo |
| 004 | Metricas de risco avancadas | Sharpe, Sortino, Calmar, exposicao, expectancia |
| 005 | Protecoes para live | Limites diario/semanal/mensal, confirmacao de sessao, liquidez, ordens limit |
| 006 | Evolucao da estrategia | Regime via ADX, filtro de volatilidade, Bollinger adaptativo, RSI adaptativo — todos opcionais e desligados por padrao |
| 007 | Observabilidade operacional | Painel, diagnostico por par, curva de capital |
| 008 | Replay acelerado | Execucao do caminho de decisao real sobre historico, isolado do estado de producao |
| 009 | Itens remanescentes | Indicadores medios por sinal; `edge --validate` |
| 010 | **Paridade de custos paper/backtest** | Taxa e slippage identicos nos dois caminhos |
| 011 | Rate limit hardening | Singleton de exchange, retry |

**Marco metodologico da fase.** A spec 002 estabeleceu o criterio de aprovacao
como artefato de codigo, nao como julgamento *ad hoc*. A spec 010 eliminou a
divergencia de custo entre simulacao historica e simulacao em tempo real —
pre-requisito para que resultados de paper mode sejam comparaveis a backtests.

### Fase III — Auditoria e descoberta de defeitos de instrumentacao (2026-08-18 a 2026-08-24)

Fase iniciada por questionamento explicito sobre a existencia de falhas nao
detectadas. Produziu os achados M1-M3 da secao 5, os mais graves do projeto.

| Data | Achado |
|---|---|
| 2026-08-18 | Bloqueio de entrada correlacionada com posicao ja aberta (`risk/correlation.py`) |
| 2026-08-24 | **M1** — backtest nao simulava o trailing stop presente em producao |
| 2026-08-24 | **M3** — backtest nao aplicava `MIN_PRICE_USDT`, filtro existente apenas no loop ao vivo |
| 2026-08-24 | **M2** — `mtf_confirmed()` comparava preco historico contra EMA de tendencia corrente |

**Consequencia.** M1 implica que **toda decisao de par e parametro anterior a
2026-08-24 foi tomada com instrumento inconsistente**: backtest e producao
executavam estrategias diferentes. A evidencia e direta — tres operacoes reais
encerradas com motivo "Stop Loss" e resultado positivo (ORCA +0,35, ACE +2,04,
PLUME +0,43), impossivel sob stop fixo.

M3 implica que LUNC/USDT, entao `PAIRS[0]` e alvo padrao dos comandos
`backtest`, `edge` e `chart`, permaneceu oito dias na lista sem gerar uma unica
decisao, com vereditos calculados sobre um par que o bot nunca operou.

### Fase IV — Extensao multi-mercado (spec 023)

Capacidade de avaliar estrategias em acoes, forex, futuros e indices, com
objetivo declarado de responder "alguma combinacao de estrategia x mercado tem
vantagem real?" antes de investir em execucao para mercado novo.

Salvaguardas incorporadas: perfil de custo obrigatorio por mercado (mercado sem
perfil e recusado, nunca avaliado com custo de outro); deteccao de historico
insuficiente; marcacao de gap de pregao; `assert_pares_operaveis()` recusando
inicializacao com simbolo inoperavel em `PAIRS`.

**Resultado:** 10 combinacoes avaliadas em cripto, acoes EUA, acoes Brasil,
forex e futuros. **Zero confirmadas fora da amostra.**

### Fase V — Bateria sistematica de hipoteses (2026-08-31 a 2026-09-01)

Fase corrente. Avaliacao das hipoteses H2-H9 da secao 4, com introducao de
`walk_forward` e do desconto de exposicao (M6, M7).

| Data | Marco |
|---|---|
| 2026-08-31 | Paginacao de `fetch_ohlcv` (teto de 1000 candles da Binance superado); status "defensivo" distinto de reprovado no multimarket |
| 2026-09-01 | **M4** e **M5** corrigidos (poluicao do log por testes; `.env.bak` fora do `.gitignore`) |
| 2026-09-01 | H3-H6 avaliadas e reprovadas |
| 2026-09-01 | H7 avaliada; **M6** e **M7** introduzidos em consequencia |
| 2026-09-01 | H8 e H9 avaliadas e reprovadas |

### Evolucao do resultado em modo paper

| Data | Trades | PnL acumulado | Profit factor |
|---|---|---|---|
| ~2026-08-2x (1) | 17 | -18,27 USDT | — |
| 2026-09-01 | 28 | -27,87 USDT | 0,62 |

(1) registro de sessao anterior.

A trajetoria e monotonicamente decrescente, porem o intervalo de confianca
permanece contendo zero (secao 4.2). O aumento amostral de 17 para 28 operacoes
nao alterou a conclusao de indistinguibilidade estatistica.

---

## 4. Hipóteses avaliadas

### 4.1 Quadro-resumo

| # | Hipótese | Categoria | Veredito | Evidência decisiva |
|---|---|---|---|---|
| H1 | EMA crossover + RSI | Direcional, série temporal | **REPROVADA** | 0/20 confirmadas fora da amostra |
| H2 | Donchian breakout (150) | Direcional, série temporal | **REPROVADA** | PF 0,60–1,13; 0/4 confirmadas |
| H3 | Reversão à média (BB+RSI) | Direcional, série temporal | **REPROVADA** | Win rate 20–31%; 0/4 confirmadas |
| H4 | Squeeze breakout | Direcional, série temporal | **REPROVADA** | 0/4 confirmadas |
| H5 | Filtro de dia da semana | Filtro sobre H1 | **REPROVADA** | "só na busca" no melhor caso |
| H6 | Supressão da saída por SELL | Filtro sobre H1 | **REPROVADA** | 0/8 confirmadas |
| H7 | Momentum transversal | Direcional, carteira | **REPROVADA** | Ganho de timing médio −1,37pp |
| H8 | Arbitragem de funding rate | Neutra, estrutural | **REPROVADA** | +3,21% a.a. (BTC), abaixo do custo de oportunidade |
| H9 | Prêmio de rebalanceamento | Não-direcional, aritmética | **REPROVADA** | Pré-condição de correlação não atendida |
| H10 | Arbitragem estatística por cointegração (long-only) | Reversão relativa, par | **INCONCLUSIVA** | Aprovada em E2; reprovada em E3/E4; seletor com 20% de poder |
| H11 | Horizonte temporal superior (diário/semanal) | Escala temporal | **REPROVADA** (4h, 1d) · **INCONCLUSIVA** (1w) | 144 combinações, 0 confirmadas fora da amostra |
| H12 | Dimensionamento por volatilidade | Gestão de risco, não-direcional | **INCONCLUSIVA** | 48 combinações, 0 melhoras; apenas 2 interpretáveis, ambas negativas |
| H13 | Barras dirigidas por informação | Esquema de amostragem | **REPROVADA** | 96 combinações, 1 melhora — **abaixo** do que o acaso produziria |
| H14 | Aprendizado supervisionado (barreira tripla) | Direcional, aprendizado | **INSUFICIENTE** | Sinal real (z = +5,21) que não paga as barreiras (z = +0,50) |
| H20 | Geometria de barreira | Geometria de saída | **REPROVADA** | Tese refutada por medição; sinal aterrissa no empate em **duas** geometrias |

**Taxa de aprovação: 0 de 15.** Três inconclusivas (H10; H11 em escala
semanal; H12 por impossibilidade estrutural de teste — ver 4.13).

---

### 4.2 H1 — EMA crossover com filtro RSI

**Especificação.** `strategy/ema_rsi.py`. Sinal de compra no cruzamento da EMA(9)
acima da EMA(21), condicionado a preço acima da EMA(50), RSI(14) < 70, volume ≥
média(20), confirmação multi-timeframe em 1d e preço abaixo da banda superior de
Bollinger. Entrada alternativa por pullback. Saída por cruzamento inverso, stop
loss por ATR, trailing stop e take profit.

**Evidência acumulada.**

| Fonte | n | Métrica | Resultado |
|---|---|---|---|
| Paper mode¹ | 28 trades / 15 dias | PnL | **−27,87 USDT** (−2,79%) |
| Paper mode¹ | 28 trades | Profit factor | **0,62** |
| Paper mode¹ | 28 trades | Win rate | 36% |
| Scan 30 pares² | — | PF mediano | 0,60 |
| Otimização 648 combinações² | ~333 dias | Retorno médio | +0,23% |
| `compare`¹ | 3 pares | Aprovadas | 1 de 3 (ETH, PF 1,67) |
| `multimarket`¹ | 4 símbolos | **Confirmadas** | **0 de 4** |

¹ medido em 2026-09-01 · ² trabalho anterior

**Análise estatística do paper mode.** Sob hipótese nula de PnL esperado nulo:

```
n = 28
μ = −0,995 USDT/trade
σ = 6,334
EP = σ/√n = 1,197
t = −0,83                          →  |t| < 2, não significativo
IC 95% (bootstrap, 20.000 reamostragens) = [−93,27; +36,06] USDT
P(PnL total < 0) = 80,9%
```

O intervalo de confiança contém zero. **Não é possível afirmar que a estratégia
perde dinheiro** com n = 28; é possível afirmar que provavelmente perde, com 81%
de probabilidade. Para |t| = 2 ao efeito medido seriam necessários ~162 trades,
o que ao ritmo observado (1,9 trades/dia) demanda ~87 dias adicionais.

**Fragilidade a extremos.** Remoção do pior trade (ACE/USDT, −19,95) eleva o
resultado a −7,93; remoção do melhor (ROBO/USDT, +17,49) o reduz a −45,36. Um
resultado que dois trades em vinte e oito revertem materialmente não caracteriza
propriedade da estratégia.

**Exposição.** 3,0% em backtest. A estratégia permanece fora do mercado 97% do
tempo. O "edge de +49,28pp contra buy-and-hold" reportado em janela de queda de
50,02% é, em sua maior parte, ausência — não capacidade preditiva.

**Veredito: REPROVADA.** Nenhuma combinação confirmou fora da janela de
descoberta.

---

### 4.3 H2 — Rompimento de canal de Donchian

**Especificação.** `strategy/breakout.py`, janela de 150 períodos.

| Par | Trades | PF | Retorno | Status |
|---|---|---|---|---|
| SOL/USDT | 14 | 1,09 | +0,17% | reprovado |
| ETH/USDT | 12 | 1,13 | +0,18% | reprovado |
| BTC/USDT | 14 | 0,60 | −0,63% | reprovado |

Em `multimarket`, retorno negativo na busca e positivo na confirmação nos quatro
símbolos — inversão de sinal entre janelas, característica de ruído e não de
vantagem: uma vantagem genuína manifesta-se em ambas.

**Veredito: REPROVADA.**

---

### 4.4 H3 — Reversão à média (Bollinger + RSI)

**Especificação.** `strategy/mean_reversion.py`. Compra no toque da banda
inferior com RSI em sobrevenda; venda no retorno à banda média ou RSI em
sobrecompra.

**Motivação teórica.** Tese oposta à de H1. Se o universo apresentasse
comportamento de reversão em vez de continuação, isso explicaria parcimoniosamente
o fracasso de uma estratégia seguidora de tendência.

| Par | Trades | Win rate | PF | Retorno |
|---|---|---|---|---|
| SOL/USDT | 25 | 20,0% | 0,54 | −1,61% |
| ETH/USDT | 30 | 20,0% | 0,62 | −1,60% |
| BTC/USDT | 35 | 31,4% | 0,77 | −0,95% |

Pior desempenho do conjunto testado. A hipótese explicativa é refutada: o
universo não paga reversão nos horizontes examinados.

**Veredito: REPROVADA.**

---

### 4.5 H4 — Squeeze breakout

**Especificação.** `strategy/squeeze_breakout.py`. Rompimento após compressão de
volatilidade.

Única aprovação em janela única (ETH/USDT, PF 1,25). Em `multimarket`,
reprovada nos quatro símbolos, com o mesmo padrão de inversão observado em H2.

**Veredito: REPROVADA.**

---

### 4.6 H5 — Filtro de dia da semana

**Especificação.** `strategy/day_filter.py`. Envoltório que suprime entradas em
dias da semana especificados, preservando as saídas.

**Procedência do parâmetro.** Segunda-feira selecionada a partir da amostra de
paper (8 trades, PnL −35,42 USDT, contra total de −27,87 — isto é, superior ao
prejuízo agregado). Testada sobre histórico de backtest, dado distinto daquele
que originou a escolha. Bloqueio restrito a um único dia: com ~4 trades por dia
da semana, bloquear os quatro dias negativos configuraria ajuste a ruído.

| Par | PF base | PF com filtro | Δ |
|---|---|---|---|
| BTC/USDT | 0,81 | 1,49 | +0,68 |
| SOL/USDT | 0,51 | 0,58 | +0,07 |
| ETH/USDT | 1,67 | 1,37 | −0,30 |

Melhor status em `multimarket`: "só na busca" (BTC/USDT), com PF de confirmação
0,01.

**Veredito: REPROVADA.**

---

### 4.7 H6 — Supressão da saída por sinal de venda

**Especificação.** `strategy/no_sell_exit.py`. Suprime o sinal SELL; a posição
encerra exclusivamente por stop loss, trailing stop ou take profit.

**Procedência da hipótese.** Decomposição das 28 operações de paper por motivo de
saída:

| Motivo | n | Total | Média |
|---|---|---|---|
| Take Profit | 5 | +37,21 | **+7,44** |
| Stop Loss | 17 | −35,53 | −2,09 |
| **Sinal de venda** | 6 | −29,55 | **−4,93** |

A saída por cruzamento apresenta a pior média, inferior ao próprio stop loss,
sugerindo encerramento prematuro de recuos que o stop absorveria.

**Resultado em janela única.** Melhora em 3 de 4 pares; soma dos retornos de
−2,71% para −1,97% (+0,74pp).

**Resultado fora da amostra.** 8 combinações, **0 confirmadas**. Ambas as
variantes convergem para retorno negativo e PF entre 0,00 e 0,87.

**Veredito: REPROVADA.** A melhora de +0,74pp é ruído de janela.

---

### 4.8 H7 — Momentum transversal

**Especificação.** `backtesting/cross_sectional.py`. Ranqueamento do universo por
retorno em janela retrospectiva; manutenção dos `top_k` primeiros; rebalanceamento
periódico. Motor próprio, uma vez que `BaseStrategy.generate_signal` opera sobre
um símbolo isolado e a decisão transversal é, por definição, relativa.

**Fundamentação.** Liu et al. (2022) documentam que modelo de três fatores
(mercado, tamanho, momentum) explica o corte transversal de retornos em
criptoativos. Replicações subsequentes reportam evidência fraca, com efeito
condicionado a períodos de alta atenção do investidor.

**Resultado inicial (janela única de confirmação).**

```
lookback = 30, top_k = 3, rebalance_every = 12
retorno   = +28,97%    buy-and-hold = −0,32%    edge = +29,29pp
profit factor = 1,96
reprovação única: drawdown 11,76% (teto 10,0%)
```

Primeiro resultado da investigação a falhar **no limite de risco** e não por
ausência de vantagem.

**Resultado em walk-forward (5 janelas contíguas, 400 candles cada).**

| Variante | Ret. médio | Pior janela | Janelas positivas | DD máx | Aprovadas |
|---|---|---|---|---|---|
| base | −11,85% | −31,80% | 1/5 | 35,19% | 0 |
| diluída (top_k 6) | −8,70% | −24,28% | 1/5 | 26,30% | 0 |
| exigente (min_mom 10%) | −8,11% | −18,38% | 1/5 | 18,63% | 0 |
| lenta (lookback 90) | −8,77% | −26,61% | 1/5 | 30,23% | 0 |
| exigente+ | −3,49% | −9,52% | 2/5 | 9,66% | 0 |

**Decomposição por ganho de timing (período contínuo de 333 dias).**

| Variante | Exposição | Retorno | Passivo equivalente | Ganho de timing |
|---|---|---|---|---|
| exig 20% | 13,2% | −6,54% | −7,26% | **+0,72pp** |
| exigente+ | 55,8% | −17,42% | −30,70% | +13,27pp |
| exig lenta | 92,7% | −7,22% | −51,00% | **+43,78pp** |

A variante de melhor retorno bruto (`exig 20%`, −6,54% em mercado de −55%)
apresenta o menor ganho de timing: o resultado decorre quase integralmente de
não-participação.

**Walk-forward da variante de maior ganho de timing (`exig lenta`).**

| Janela | Regime | B&H | Estratégia | Exposição | Ganho de timing |
|---|---|---|---|---|---|
| 1 | baixa | −35,1% | −1,42% | 17,3% | +4,65pp |
| 2 | baixa | −27,3% | −4,98% | 78,2% | +16,38pp |
| 3 | lateral | +0,2% | −9,81% | 91,7% | −9,99pp |
| 4 | baixa | −26,8% | −0,10% | 12,0% | +3,11pp |
| 5 | **alta** | **+24,8%** | **+3,78%** | **100,0%** | **−21,01pp** |

**Média: −1,37pp. Três janelas positivas de cinco.**

A janela 5 é dirimente: com exposição integral em alta de 24,8%, a estratégia
capturou 3,78%. Não se trata de redução de exposição, mas de seleção incorreta
de ativos. Os ganhos das janelas 1 e 4 ocorrem sob exposição de 17,3% e 12,0%,
caracterizando novamente efeito de ausência.

**Veredito: REPROVADA.** O resultado inicial de +29,29pp constituía propriedade
da janela, não da estratégia.

---

### 4.9 H8 — Arbitragem de funding rate (delta-neutro)

**Especificação.** Posição comprada em spot e vendida em perpétuo, mesmo
nocional. O componente direcional cancela-se; a receita provém da taxa de
financiamento paga a cada 8 horas.

**Motivação.** Primeira hipótese que não depende de previsão de preço.
Literatura comercial reporta 10–30% a.a.; firmas profissionais, 19,26% em 2025.

**Medição.** Histórico público da Binance, 2025-09-01 a 2026-09-01, 1.095
pagamentos por símbolo, sem alavancagem, custo de 0,04% por ponta em quatro
pontas.

| Símbolo | % pagamentos negativos | Bruto a.a. | **Líquido a.a.** |
|---|---|---|---|
| BTC | 23,7% | 3,37% | **+3,21%** |
| ETH | 27,4% | 2,43% | **+2,27%** |
| XRP | 44,7% | 0,36% | **+0,20%** |
| SOL | 46,6% | −1,68% | **−1,84%** |

**Origem da discrepância com a literatura comercial.** A projeção de 10–30%
deriva da taxa de referência de 0,01% por período de 8 h, equivalente a 10,95%
a.a. Trata-se do valor de referência da exchange, não da média realizada: entre
23,7% e 46,6% dos pagamentos foram negativos no período. Não há erro aritmético
nas fontes; há premissa não sustentada pelo dado.

**Custo de implementação.** Requereria: permissão de futuros nas chaves de API
(atualmente spot-only), modelagem de posição de duas pernas em `state.json`,
monitoramento de margem, re-hedge com custo, e fonte de funding rate em
`data/fetcher.py`. Introduziria risco de liquidação, classe de falha não coberta
pelos limites de drawdown nem pelo circuit breaker vigentes.

**Veredito: REPROVADA.** Retorno inferior a renda fixa, com risco de liquidação,
execução e contraparte adicionados.

---

### 4.10 H9 — Prêmio de rebalanceamento (demônio de Shannon)

**Especificação.** Rebalanceamento periódico a pesos-alvo fixos entre ativos
voláteis e descorrelacionados. Decorre da desigualdade entre média aritmética e
geométrica; não constitui previsão.

**Pré-condição.** Ativos voláteis **e** de correlação baixa ou negativa.

**Verificação da pré-condição.** 12 pares, 2000 candles de 4 h:

| | |
|---|---|
| Correlação mediana | **0,71** |
| Correlação mínima | 0,34 |
| Pares com ρ < 0,3 | **0 de 72** |
| Pares com ρ < 0,0 | **0 de 72** |

**Verificação empírica do prêmio.**

Carteira igualmente ponderada (12 pares):

| Rebalanceamento | Retorno | Drawdown |
|---|---|---|
| a cada 6 candles | −56,53% | −67,00% |
| a cada 42 candles | −56,33% | −66,96% |
| a cada 180 candles | −56,70% | −67,05% |
| **nunca (B&H)** | **−54,87%** | −64,82% |

BTC + caixa:

| Alocação | Retorno | Predição por escala pura |
|---|---|---|
| 50% | −17,84% | −17,63% |
| 25% | −8,89% | −8,81% |

A insensibilidade à frequência de rebalanceamento (−17,84% contra −17,26%) e a
aderência à predição por escalonamento puro caracterizam prêmio nulo. O prêmio
exige volatilidade em **ambos** os ativos; caixa possui volatilidade zero.

**Veredito: REPROVADA.** A formulação matemática não é refutada; sua
pré-condição foi medida e não é satisfeita pelo universo disponível.

---

### 4.11 H10 — Arbitragem estatística por cointegração (variante long-only)

**Especificação.** `backtesting/pairs_trading.py`. Seleção de pares por
cointegração; entrada quando o z-score do spread cai abaixo de −2,0; saída no
retorno a −0,5; stop em −4,0. Janela de formação de 250 candles, reseleção a
cada 250.

**Restrição de escopo.** A formulação canônica exige posição vendida na perna
sobrevalorizada. As chaves de API são spot-only; vender a descoberto exigiria
margem e introduziria risco de liquidação. A variante implementada assume apenas
a perna comprada do ativo subvalorizado. **Consequência declarada:** sacrifica a
neutralidade a mercado — o beta de 0,09–0,18 reportado na literatura não se
aplica a esta variante.

**Seleção de pares.** Dois critérios independentes, ambos obrigatórios:

- **Estacionariedade** — teste ADF sobre o spread, α = 0,05. Responde "existe
  reversão?".
- **Negociabilidade** — meia-vida de reversão via AR(1), dentro de faixa
  absoluta e limitada a 10% da janela de formação. Responde "a reversão é rápida
  o bastante para pagar taxa e slippage?".

`statsmodels` figura em `requirements-dev.txt`, não em `requirements.txt`: o bot
em produção não negocia pares e não deve carregar a biblioteca. Na ausência
dela, `teste_adf` devolve p = 1,0 (não rejeita), seguindo a política de falha
fechada do projeto.

**Resultados da bateria.**

| Etapa | Resultado | Status |
|---|---|---|
| E1 — Sanidade | Recupera o par construído; meia-vida estimada 24,9 contra 20 construída | **passa** |
| E2 — Janela única | 16 trades, +3,96%, PF 1,58, DD 6,62%, exposição 23,0% | **APROVADA** |
| E3 — Fora da amostra | Busca −2,83% (PF 0,52); confirmação +10,58% com 7 trades (abaixo do mínimo de 10) | **reprova** |
| E4 — Walk-forward | Ganho de timing médio +0,92pp, mas 1 de 4 janelas positiva | **reprova** |
| E5 — Desconto de exposição | Ganho de timing positivo na média; janela 1 sem operação alguma | inconclusivo |
| E6 — Sensibilidade a custo | +3,96% com custo, +5,56% sem. Custo consome 29% da vantagem bruta | passa |

**Primeira aprovação em E2 de toda a investigação.**

**Walk-forward detalhado.**

| Janela | Regime | B&H | Estratégia | Trades | Exposição | Ganho de timing |
|---|---|---|---|---|---|---|
| 1 | baixa | −16,5% | 0,00% | **0** | 0,0% | +0,00pp |
| 2 | alta | +6,9% | +0,11% | 3 | 40,2% | −2,67pp |
| 3 | baixa | −23,7% | −3,71% | 5 | 47,0% | +7,44pp |
| 4 | alta | +14,6% | +6,98% | 7 | 55,4% | −1,09pp |

**Por que INCONCLUSIVA e não REPROVADA.**

O poder estatístico do seletor foi medido. Taxa de detecção de par cointegrado
**construído**, 30 sementes:

| Meia-vida construída | Janela de formação | Detecção |
|---|---|---|
| 5 | 250 | 100% |
| 10 | 250 | 70% |
| 20 | 250 | **20%** |
| 20 | 500 | 60% |

Com formação de 250 candles, o seletor perde 80% dos pares de reversão lenta. O
resultado negativo em E3/E4 **não distingue "não há vantagem" de "não
detectamos os pares"**. Some-se a isso a contagem de operações: 0 a 7 por
janela, contra o mínimo de 10 exigido pelo critério — as janelas de walk-forward
são curtas demais em relação à janela de formação.

**Reavaliação necessária antes de veredito definitivo:** histórico mais longo
que permita formação de 500+ candles com janelas de teste que comportem ≥ 10
operações. A paginação de `fetch_ohlcv` (2026-08-31) removeu o teto de 1000
candles da Binance, tornando isso viável.

---

### 4.12 H11 — Momentum em horizonte temporal superior

**Especificação.** `backtesting/horizonte.py`, spec 024. Avalia EmaRsiStrategy,
BreakoutStrategy, MeanReversionStrategy e SqueezeBreakoutStrategy em 4h, 1d e 1w
sobre os 12 pares usados em H7 e H9, submetendo cada combinação à bateria E1–E6
sem alteração de critério.

**Fundamentação.** Liu & Tsyvinski (2021) documentam momentum de série temporal
em criptoativos em horizontes de **uma a quatro semanas**. O bot opera em 4h. Se
o efeito existe nessa escala e não na atual, as nove hipóteses direcionais já
reprovadas mediram a escala, não a estratégia — e a investigação inteira
precisaria ser relida.

**Resultado — 144 combinações, zero confirmadas fora da amostra.**

| Horizonte | Avaliadas | Confirmadas | Reprovadas | Inconclusivas | Só na busca | Julgadas com amostra suficiente |
|---|---|---|---|---|---|---|
| 4h | 48 | **0** | 34 | 13 | 1 | 35 / 48 |
| 1d | 48 | **0** | 35 | 13 | 0 | 35 / 48 |
| 1w | 48 | **0** | 0 | 48 | 0 | **0 / 48** |

**A escala semanal era inconclusiva por construção, e isso foi previsto.**

`research.md` da spec 024 registrou, **antes de qualquer código ser escrito**,
que o horizonte semanal não comportaria a bateria: 311 a 473 candles por par,
menos 50 de aquecimento (350 dias, quase um ano), produzindo janela de validação
de 78 a 127 — abaixo do mínimo de 150 de `MIN_WINDOW_CANDLES`. O `tasks.md`
registrou o critério de falsificação: **se a implementação produzisse 1w como
`confirmado` ou `reprovado`, seria defeito de dimensionamento, não achado.**

Resultado observado: 48 de 48 inconclusivas. A previsão se sustentou.

**O achado real está na comparação entre 4h e 1d.**

Decompondo as combinações julgadas por critério isolado:

| Horizonte | Passaram profit factor ≥ 1,20 | Superaram buy-and-hold |
|---|---|---|
| 4h | **0 de 35 (0%)** | 31 de 35 (89%) |
| 1d | **7 de 35 (20%)** | 21 de 35 (60%) |

Subir de 4h para 1d **melhora a qualidade do sinal de forma mensurável**: o
profit factor sai de 0% de aprovação para 20%. Isso é consistente com a direção
que Liu & Tsyvinski preveem — o efeito existe mais na escala maior.

Mas o ganho é anulado pela outra ponta. Em 4h o histórico cobre 333 dias de
mercado em queda, e 89% das combinações "superam" o buy-and-hold — em boa parte
por estarem fora do mercado. Em 1d o histórico cobre 2000 dias de apreciação
forte, e a taxa cai para 60%. A barra de bater um buy-and-hold de 5,5 anos de
cripto é substancialmente mais alta que a de bater 333 dias de queda.

Mudam também os motivos de reprovação: em 4h, 30 de 34 reprovações são por
profit factor; em 1d, apenas 21 de 35, com 14 passando a falhar por não superar
o buy-and-hold.

**Veredito.** REPROVADA em 4h e 1d, com amostra suficiente nas duas escalas (35
de 48 combinações julgadas em cada). INCONCLUSIVA em 1w, por limitação
estrutural de histórico — e a inconclusividade é a resposta correta, não uma
falha da avaliação.

**O que isso fecha.** A hipótese de que as nove reprovações anteriores mediram a
escala errada **não se sustenta**. A escala importa — e o efeito medido tem o
sinal previsto pela literatura — mas não o bastante para produzir vantagem que
sobreviva à confirmação fora da amostra. As reprovações anteriores continuam
válidas.

**O que permanece aberto.** A escala semanal segue sem teste possível com o
histórico disponível na Binance. Testá-la exigiria fonte de dados com
profundidade maior que a da exchange, o que está fora do escopo atual.

---

### 4.13 H12 — Dimensionamento de posição por volatilidade

**Tese.** Escalar a posição inversamente à volatilidade realizada mantém a
exposição ao risco aproximadamente constante, em vez do valor nocional. É o
mecanismo padrão de controle de drawdown em gestão sistemática.

**Procedência interna.** H7 foi a única hipótese do registro a reprovar
**exclusivamente** no limite de risco: drawdown de 11,76% contra o teto de
10,0%, com profit factor, número de operações e retorno contra buy-and-hold
todos passando. Se o excesso fosse consequência do dimensionamento, H7 voltaria
a ser testável.

**Implementação.** `fator = min(1,0; alvo / atr_ratio)`, alvo 0,02 — próximo à
mediana medida de `atr_ratio` (0,0187 em 23.412 observações de 4h, 12 pares). O
teto de 1,0 é a fórmula, não validação defensiva: o mecanismo só pode reduzir
posição. `risk/manager.py` não foi tocado.

**Predição registrada antes da execução** (`specs/025-dimensionamento-por-volatilidade/research.md`):
o drawdown vai cair, porque é o que o mecanismo faz; a pergunta aberta é se o
retorno cai na mesma proporção.

#### Resultado

| Estado | Combinações |
|---|---|
| **melhora** | **0** |
| só na busca | 0 |
| confundida (base perde dinheiro) | 6 |
| sem vantagem | 1 |
| piora | 1 |
| inconclusiva (amostra) | 3 |
| inerte (mecanismo não pôde atuar) | 37 |
| **total** | **48** |

Fator médio efetivamente aplicado: 0,933.

**Resposta à predição: o retorno não caiu na mesma proporção — caiu mais.**
`ret_dim / ret_base` teve mediana de **0,830** enquanto a exposição de capital
caiu apenas ~3%. O mecanismo encolhe a magnitude do resultado
desproporcionalmente, e o faz **nos dois sentidos**.

#### Por que 37 combinações são inertes

Das quatro estratégias do universo, apenas `EmaRsiStrategy` calcula
`atr_ratio`. Nas demais o fator ficou preso em 1,0 e as duas versões eram a
mesma execução. Isto é limitação do instrumento, **não evidência sobre a
hipótese**.

#### Por que 6 combinações são confundidas

As seis têm retorno base **negativo**. Encolher uma estratégia de expectativa
negativa aproxima o resultado de zero, e qualquer métrica de melhora registra
isso como ganho. O limite dessa lógica é `fator_minimo` tendendo a zero: **não
operar maximizaria o critério sem ganhar nada.** Ver M11.

#### A evidência interpretável

Restam **duas** combinações com base lucrativa, onde "melhorar" não se confunde
com encolher uma perdedora:

| Par | Ret base | Ret dim | DD base | DD dim | dTiming | Status |
|---|---|---|---|---|---|---|
| ETH/USDT | +2,20% | +1,90% | 0,69% | 0,69% | −0,598 | sem vantagem |
| BTC/USDT | +0,13% | +0,07% | 0,89% | 0,89% | −0,136 | piora |

Nas duas, o dimensionamento **custou retorno e não reduziu drawdown nenhum**.

#### Veredito: INCONCLUSIVA

Não REPROVADA, pela regra que o próprio projeto aplicou em H10 e H11 e que M9
formalizou: amostra insuficiente precede reprovação. Duas combinações
interpretáveis não sustentam a reprovação de uma hipótese.

Mas a inconclusão tem causa estrutural, e ela é a conclusão útil:

> **H12 não pode ser testada enquanto nenhuma estratégia tiver expectativa
> positiva.** Sobre base perdedora, "reduzir posição melhora o resultado" é
> verdade trivial e nada informa sobre dimensionamento. O teste exige uma
> estratégia lucrativa para dimensionar — e o registro não tem nenhuma.

H12 é portanto **descendente** da busca por vantagem, não um caminho até ela.
Reordenada na fila conforme 6.4.

**Sobre a motivação original:** o drawdown de H7 **não** se mostrou problema de
dimensionamento. Nas duas combinações limpas o drawdown não se moveu (0,69% para
0,69%; 0,89% para 0,89%) enquanto o retorno caiu. A explicação é direta: o
drawdown veio de trades perdedores concentrados, não de tamanho excessivo
uniforme.

**Custo de giro:** irrelevante nesta avaliação. `dOperacoes` foi 0 em todas as
combinações — o dimensionamento altera o tamanho da entrada, não a decisão de
entrar, então não há giro adicional. Diferença atribuível a custo: +0,03pp.

**Reprodução:** `python main.py volatilidade` · `reports/volatilidade_*.json` ·
spec `025-dimensionamento-por-volatilidade`.

---

### 4.14 H13 — Barras dirigidas por informação

**Tese.** Amostrar em intervalos de tempo fixos é uma escolha arbitrária, não
uma propriedade do mercado. Informação chega em rajadas: uma barra de 4h numa
madrugada parada e outra durante uma liquidação em cascata são tratadas como
observações equivalentes. Barras que fecham quando uma quantidade de
**atividade** se acumula produziriam retornos mais próximos das premissas que os
indicadores assumem.

**Procedência interna.** As doze hipóteses anteriores rodaram **todas** sobre
candles de tempo fixo. Se o esquema de amostragem fosse o problema, cada
hipótese direcional reprovada teria medido o **relógio**, não a estratégia — e
H1 a H7 precisariam de reavaliação. Esta é a pergunta que H13 fecha.

**Método.** Base de 1h × 8.000 candles = 333,3 dias, a mesma janela de
calendário do 4h × 2.000 usado por todas as avaliações anteriores. Cada
estratégia roda duas vezes sobre a **mesma base**: agrupada por relógio e
agrupada por atividade. Limiar calibrado até a contagem de barras parear com a
de tempo, consultando exclusivamente essa contagem.

#### Resultado

| Estado | Combinações |
|---|---|
| **melhora** | **1** |
| só na busca | 0 |
| confundida | 6 |
| sem vantagem | 14 |
| piora | 35 |
| inconclusiva | 40 |
| inerte | 0 |
| erro | 0 |
| **total** | **96** |

#### O instrumento funcionou — e isso é o que separa H13 de H12

| Verificação | Resultado |
|---|---|
| Divergência máxima de buy-and-hold entre as versões | **0,00000000 pp** |
| Combinações inertes | **0 de 96** |
| Barras por candle de base (mediana) | 0,243 (dollar) · 0,250 (cusum) |
| Barras de um candle só (mediana) | 15,7% (dollar) · 22,1% (cusum) |

A reamostragem **atuou em todas as combinações**, e a âncora de referência é
exata, não aproximada. Em H12, 37 de 48 combinações não mediram nada e o
veredito precisou ser inconclusivo. Aqui a evidência é utilizável.

#### A direção do efeito é negativa, não neutra

Agregado das 56 combinações avaliadas:

| Grandeza | Mediana | Média | Positivas |
|---|---|---|---|
| Ganho de timing (pp) | **−0,959** | −1,183 | 14 de 56 |
| Retorno (pp) | −0,444 | −0,461 | 19 de 56 |

Amostrar por informação **piorou** o resultado em três de cada quatro
combinações avaliadas.

**E não é custo de giro.** A separação de E6 mostra `dRet` médio de −0,46pp com
custo e **−0,57pp sem custo**: removendo taxa e slippage o resultado fica
ligeiramente pior, não melhor. A degradação vem da amostragem em si.

#### A única melhora é menos do que o acaso produziria

`Squeeze Breakout × SOL/USDT × CUSUM` — retorno +0,18% → +1,21%, drawdown 1,30%
→ 0,58%, ganho de timing +0,695pp na busca e +0,531pp na validação fora da
amostra. Passou a confirmação.

E ainda assim **não é evidência de efeito**. Foram **96 combinações testadas**.
Sob a hipótese nula, com o nível de significância convencional que a confirmação
fora da amostra aproxima, esperar-se-iam cerca de **cinco** aprovações
espúrias. Observar **uma** está *abaixo* da expectativa do acaso.

Este é o mesmo raciocínio que a seção 2.2 estabeleceu e que fundamentou a
rejeição de H5: uma aprovação isolada dentro de uma varredura ampla é o
resultado esperado de testar muitas coisas, não a descoberta de um efeito.
Registrar a combinação nominalmente é honesto; tratá-la como achado não seria.

Por variante: **dollar 0 melhoras em 48**; **CUSUM 1 em 48**.

#### Veredito: REPROVADA

Não inconclusiva. Diferente de H12, aqui todas as pré-condições de mensuração
foram satisfeitas: instrumento ativo em 100% das combinações, âncora exata, 56
combinações com amostra suficiente, confirmação fora da amostra aplicada. O
efeito medido é negativo e consistente.

**A pergunta que H13 fecha:** as doze reprovações anteriores **não** mediram o
relógio. Trocar o esquema de amostragem não as recupera — piora-as. A suspeita
de que a amostragem por tempo fosse a causa das reprovações está encerrada, e
H1 a H7 **não** precisam de reavaliação por esse motivo.

#### Predições registradas antes da execução

Ambas em `specs/026-barras-por-informacao/research.md`, escritas antes de
qualquer código:

| Predição | Observado |
|---|---|
| "O resultado mais provável é que a amostragem mude os números sem mudar o veredito" | **Confirmada**, e mais forte: mudou os números para pior |
| "Espera-se `delta_exposicao_tempo` diferente de zero, diferente de H12" | **Confirmada**: medido entre −3,2 e +8,0pp. A exposição de tempo responde, e a medida original de M7 serve — não há quarta forma da família nesta dimensão |

#### Executabilidade operacional (FR-017)

**Seria executável.** Construir barras ao vivo é aritmética sobre candles que o
bot já busca; não exige infraestrutura nova.

**Ressalva:** o limiar é calibrado sobre histórico e regimes de volume mudam. Um
limiar de 2025 aplicado em 2027 produziria barras sistematicamente mais largas
ou mais finas do que o pretendido. Operar isto exigiria recalibração periódica —
mecanismo que não existe e que a spec 026 não implementa. A ressalva é registrada
mesmo com o veredito negativo, porque a decisão sobre ela pertenceria ao usuário.

#### Limitação declarada

Barras dirigidas por informação canônicas se constroem de **dados de negociação
individuais**. Este projeto consome candles agregados, então uma barra é sempre
união de candles inteiros e suas fronteiras só caem em marcas de hora. Com
mediana de ~4 candles de 1h por barra, o erro de posicionamento de fronteira é
de até ±0,5h, cerca de **12% da largura típica**.

A reprovação vale para barras construíveis a partir de OHLCV agregado. Um
resultado diferente com dados de tick não está excluído por esta evidência — mas
exigiria uma fonte de dados que o projeto não possui, e o efeito precisaria ser
grande o bastante para inverter uma degradação mediana de −0,96pp no ganho de
timing.

**Reprodução:** `python main.py barras` · `reports/barras_*.json` · spec
`026-barras-por-informacao`.

---

### 4.15 H14 — Aprendizado supervisionado com barreira tripla

**Tese.** Rotular cada evento pela barreira que o preço toca primeiro — alvo,
stop ou limite de tempo — transforma a previsão de direção num problema de
classificação com rótulos economicamente significativos. Um classificador sobre
os indicadores já calculados poderia extrair estrutura que regras fixas de
cruzamento não capturam.

**Método.** Regressão logística binária, 5 atributos declarados e intercepto —
6 parâmetros sobre ~16.000 amostras de treino, 2.700 por parâmetro. Barreiras
do próprio bot (stop 1,5×ATR, alvo 3,0×ATR, limite 24 velas). Purga e embargo
**globais entre pares**. Três linhas de base: as regras, o buy-and-hold, e o
mesmo modelo com **rótulos embaralhados**.

#### O limiar foi declarado antes de qualquer código

`research.md` registrou, na Fase 0 e antes da implementação, que uma entrada
aleatória com essas barreiras tem expectativa de **−0,241 ATR**, razão de
chances alvo/stop de 0,372, e que **empatar exige 0,500 — uma elevação de
+34,3% relativo**.

#### Resultado: dois testes, respostas opostas

Agregado sobre os 12 pares, na janela de teste (1.580 decisões com desfecho):

| | alvo | stop | razão |
|---|---|---|---|
| Todos os eventos | 1.650 | 4.235 | 0,3896 |
| **Subconjunto decidido pelo modelo** | **536** | **1.044** | **0,5134** |

| Pergunta | Estatística | Resposta |
|---|---|---|
| **Há sinal?** (decidido vs taxa base) | esperado 443,0 alvos, observado 536 — **z = +5,21**, p < 0,0001 | **Sim, robustamente** |
| **Paga as barreiras?** (decidido vs empate) | esperado 526,7, observado 536 — **z = +0,50**, p = 0,318 | **Não resolvível** |

Elevação observada: **0,3896 → 0,5134, +31,8% relativo**. A elevação
pré-registrada como necessária era **+34,3%**. O modelo chegou praticamente ao
limiar declarado e parou nele.

Intervalo de confiança de 95% para a fração de alvos: [0,3196; 1,0], contra
0,3333 no ponto de empate. A razão no limite inferior é **0,4696 — abaixo do
empate**.

#### Veredito: INSUFICIENTE

Categoria nova neste registro, criada em `data-model.md` **antes** de ver o
resultado, precisamente para não colapsar este caso.

> **Há sinal detectável, estatisticamente robusto, e ele não paga as
> barreiras.**

Não é REPROVADA: o sinal existe com p < 0,0001, e reprovar afirmaria ausência
de efeito onde há efeito medido. Não é INCONCLUSIVA no sentido usual: a amostra
é adequada para **estabelecer** o sinal; é inadequada apenas para resolver se a
margem acima do empate é positiva. E não é aprovação: 0,5134 não se distingue
de empatar, e uma estratégia que empata perde para o custo de execução.

#### Por que este é o resultado mais informativo do registro até aqui

As treze hipóteses anteriores responderam "não há vantagem". Esta responde algo
diferente: **a direção é previsível a um grau mensurável, e o grau previsível é
menor que o obstáculo econômico.** Isso desloca a pergunta de "existe sinal?"
para "o obstáculo pode ser reduzido?".

#### O modelo embaralhado decide zero vezes — e está correto

Sem relação entre atributo e rótulo, a melhor previsão possível é a taxa base
(23,4%), que fica **abaixo do limiar de decisão de 33,3%**. O modelo de ruído
nunca cruza o limiar e nunca opera. Não é degeneração do teste: é o
comportamento esperado, e confirma que o limiar de decisão está no lugar certo.

Consequência metodológica: a comparação contra o embaralhado não pôde ser feita
no espaço de retornos (uma versão não opera), e foi feita no espaço de
**chances**, que é onde ela tem conteúdo.

#### Limitações declaradas

- **Por par, todas as 12 avaliações são `inconclusivo`**: a linha de base de
  regras faz de 1 a 9 operações na janela de teste, nunca as 10 do mínimo. A
  resposta veio do agregado, que é a unidade natural de um modelo único
  treinado sobre pares agrupados.
- **Drawdown não é agregado**: depende da trajetória conjunta de capital e
  exigiria um motor de carteira. Somar drawdowns de séries distintas produziria
  um número sem significado.
- **A margem acima do empate não é resolvível com 1.580 decisões.** Resolvê-la
  exigiria da ordem de dez vezes mais amostra, o que significa mais pares ou
  mais histórico — não mais modelo.

#### Executabilidade operacional (FR-017)

**Parcialmente executável, com ressalva maior que a de H13.** Avaliar o modelo a
cada ciclo é barato — cinco atributos e um produto interno sobre indicadores já
calculados.

Mas **não existe mecanismo de retreino nem de detecção de degradação**, e aqui a
degradação é **silenciosa**: o modelo continua emitindo probabilidades de
aparência normal enquanto a relação que aprendeu deixa de valer. Diferente do
limiar de H13, cuja degradação apareceria na contagem de barras.

Como o veredito é `insuficiente`, a questão é acadêmica — mas fica registrada,
porque se a margem for resolvida no futuro a ressalva volta a valer.

#### Predições registradas antes da execução

| Predição (`research.md`) | Observado |
|---|---|
| "O resultado mais provável é que o modelo não se distinga do embaralhado" | **Errada.** O modelo se distingue com z = +5,21 |
| "Se distinguir mas não atingir 0,500, o resultado é `insuficiente` — categoria nova e o achado desta spec" | **Confirmada.** Foi exatamente isso |

A primeira predição estar errada é o dado mais valioso desta spec: eu esperava
ausência de sinal e encontrei sinal. A segunda existir por escrito é o que
permite afirmar que `insuficiente` não foi uma categoria inventada depois para
acomodar um resultado incômodo.

**Reprodução:** `python main.py modelo` · `reports/modelo_*.json` · spec
`027-aprendizado-barreira-tripla`.

---

### 4.16 H20 — Geometria de barreira

**Origem.** Única hipótese do registro derivada de um **resultado** e não da
literatura. H14 mediu sinal robusto que não pagava as barreiras, e o ponto de
empate é `stop / alvo` — uma razão escolhida. H20 pergunta se escolher outra
resolve.

**Disciplina.** A regra de seleção da geometria foi escrita e **commitada antes
de qualquer medição existir** (`7cc19e0`). O histórico do git é a prova de que
ela não foi ajustada ao resultado — a única coisa que separa H20 de uma
varredura de parâmetro.

#### A tese foi refutada antes de treinar qualquer modelo

Stop fixo em `1,5 × ATR`, alvo variando, 12 pares, 2.000 candles:

| `tp` | Empate | Razão base | Folga sobre o critério |
|---|---|---|---|
| 2,0 | 0,750 | 0,6223 | **+0,3%** |
| 2,5 | 0,600 | 0,4892 | −1,4% |
| 3,0 | 0,500 | 0,3913 | −5,4% |
| 4,0 | 0,375 | 0,2497 | −19,5% |
| 5,0 | 0,300 | 0,1648 | −33,5% |
| 6,0 | 0,250 | 0,1076 | −48,0% |

**A razão de chances cai mais rápido que o ponto de empate.** Afastar o alvo
piora a margem monotonicamente. A tese — alvo mais distante baixa o obstáculo —
está invertida em relação ao que os dados fazem.

A única geometria elegível vai na direção **oposta**: alvo mais próximo.

#### E a avaliação da geometria selecionada fecha o argumento

`tp = 2,0`, ponto de empate 0,750:

| | alvo | stop | razão |
|---|---|---|---|
| Todos os eventos | 2.438 | 3.947 | 0,6177 |
| **Decidido pelo modelo** | **955** | **1.277** | **0,7478** |

| Pergunta | Estatística | Resposta |
|---|---|---|
| Há sinal? | z = **+4,48**, p < 0,0001 | **Sim** |
| Paga a geometria? | z = **−0,07**, p = 0,535 | **Não** |

#### O achado: o sinal aterrissa no empate em duas geometrias independentes

| Geometria | Ponto de empate | Razão obtida | Razão / empate |
|---|---|---|---|
| `tp = 3,0` (H14) | 0,500 | 0,5134 | **1,027** |
| `tp = 2,0` (H20) | 0,750 | 0,7478 | **0,997** |

Duas geometrias, pontos de empate **50% distantes entre si**, modelos treinados
sobre rótulos diferentes — e nos dois casos a razão obtida fica a menos de 3%
do empate, aproximando-se dele de lados opostos. Em `tp = 2,0` a diferença é de
**1,6 alvos em 2.232 desfechos**.

Não é margem estreita. É o mesmo resultado duas vezes, por caminhos
independentes.

**Leitura:** a componente previsível do movimento é aproximadamente igual ao
obstáculo imposto pela geometria de saída, e **muda junto com ele**. Mover a
geometria não move a margem, porque a previsibilidade acompanha. É o
comportamento que se esperaria de um mercado que precifica esta informação
eficientemente — medido aqui duas vezes, não postulado.

#### Veredito: REPROVADA

A hipótese afirmava que a geometria era uma alavanca sobre a margem. A medição
mostra que não é: a margem é aproximadamente invariante à geometria, e o único
sentido em que ela responde é o **contrário** do proposto.

Diferente de H14, este veredito **não** é `insuficiente`. Lá a pergunta era se o
sinal pagava as barreiras, e a resposta ficou irresolvida por amostra. Aqui a
pergunta era se mudar a geometria mudava a resposta, e ela está resolvida: não
muda.

#### O que isto fecha, e o que não fecha

**Fecha** a frente 2 identificada em §6.3-b — reduzir o obstáculo pela geometria
de saída. Ela foi testada e não é alavanca.

**Não fecha** a redução de obstáculo por **custo de execução**, que é a outra
componente. Taxa e slippage entram na margem por um canal distinto da geometria,
e nada aqui os avalia.

**Não fecha** a frente 1 — aumentar o sinal. Mas H14 e H20 juntas dão duas
medições independentes de que a capacidade do modelo não era o gargalo: seis
parâmetros extraíram sinal robusto nas duas geometrias, e nas duas o sinal parou
no mesmo lugar.

#### Limitações declaradas

- **A geometria selecionada passou por +0,33%**, praticamente na fronteira do
  critério. Se a regra exigisse folga um pouco maior, nenhuma geometria seria
  elegível e H20 se encerraria sem avaliação de modelo — desfecho previsto em
  FR-006. O veredito seria o mesmo; a evidência, mais fraca.
- **Apenas um eixo foi variado.** O stop permaneceu em `1,5 × ATR`. Variar os
  dois multiplicaria o conjunto sem evidência de que o segundo eixo se comporte
  diferente, e a monotonicidade observada no primeiro não sugere que se comporte.
- **A elevação não transferiu integralmente**: +31,8% em `tp = 3,0` contra
  +21,1% em `tp = 2,0`. Reutilizar a primeira teria sido erro, e FR-008 existia
  para impedi-lo.

**Reprodução:** `python main.py modelo` com `ParametrosBarreira(tp_mult=2.0)` ·
spec `028-geometria-de-barreira`.

---

## 5. Achados metodológicos (defeitos de instrumentação)

Distintos das hipóteses, estes achados dizem respeito à **confiabilidade do
instrumento de medição**. Cada um invalidou, retroativamente, decisões tomadas
com base em medições anteriores.

| # | Defeito | Consequência | Estado |
|---|---|---|---|
| M1 | Backtest não simulava trailing stop presente em produção | Backtest e produção executavam estratégias diferentes; toda decisão de par e parâmetro anterior foi tomada com régua inconsistente | Corrigido (2026-08-24) |
| M2 | `mtf_confirmed()` comparava preço histórico contra EMA de tendência corrente | Viés direcional no replay: descartava sistematicamente entradas antigas mais baratas | Corrigido via parâmetro `as_of` |
| M3 | `MIN_PRICE_USDT` aplicado apenas no loop ao vivo, ausente no backtest | LUNC/USDT permaneceu 8 dias em `PAIRS` sem gerar decisão, sendo `PAIRS[0]` e alvo padrão de `backtest`/`edge` | Corrigido |
| M4 | Suíte de testes gravava em `logs/events-*.jsonl` de produção | 73 linhas por execução; log de bot em paper mode continha `live_order_error`, `circuit_breaker_triggered` e `reconciliation_mismatch` inexistentes | Corrigido (`tests/conftest.py`, 2026-09-01) |
| M5 | `.gitignore` cobria `.env` mas não `.env.bak*` | 4 arquivos com chaves reais da Binance sujeitos a `git add -A` em repositório remoto | Corrigido (2026-09-01) |
| M6 | Janela única de confirmação insuficiente para distinguir vantagem de regime | H7 quase aprovada com +29,29pp que não replicou | Corrigido (`walk_forward`, 2026-09-01) |
| M7 | Retorno superior ao B&H sob exposição reduzida lido como habilidade | Ver H7: variante de melhor retorno bruto possui ganho de timing de +0,72pp | Corrigido (`ganho_de_timing_pp`, 2026-09-01) |
| M9 | Regra de amostra mínima aplicada só à janela de busca, não à de confirmação | `so_na_busca` afirma que a estratégia **não se sustentou** fora da janela de descoberta. Com menos operações que `EDGE_MIN_TRADES` na validação, a afirmação não tem suporte: não foi testada e reprovou, foi testada de menos. Na varredura de H11, **12 combinações** receberam esse rótulo indevidamente, uma delas com 2 operações na validação | Corrigido (`classificar_status`, 2026-09-01) |
| M8 | Meia-vida de reversão usada como critério único de cointegração | O estimador OLS do coeficiente AR é enviesado para baixo (viés de Dickey-Fuller): passeio aleatório recebe meia-vida **finita**, e a estimativa **escala com a amostra** (mediana 38 em n=250, 173 em n=1000, 417 em n=3000). Taxa de falso positivo de **28%** na seleção de H10 | Corrigido (portão ADF, α=0,05, falso positivo para **4,8%**, 2026-09-01) |

| M10 | Desconto de exposição medido em **tempo**, cego a mecanismos que variam **capital** | `_exposure_pct` mede segundos em posição sobre segundos do período. Dimensionar por volatilidade muda quanto capital entra, nunca quando entra ou sai. Consequência: `delta_exposicao` deu **exatamente 0,0 nas 48 combinações**, o desconto não descontou nada, e o estado `sem_vantagem` — a guarda contra M7 — era **inatingível por construção**. Zero ocorrências não era ausência do fenômeno: era um estado que o instrumento não conseguia produzir | Corrigido (`exposicao_de_capital`, 2026-09-01) |
| M11 | Melhora sobre base de expectativa negativa lida como vantagem | Reduzir posição encolhe a magnitude do resultado **nos dois sentidos**. Sobre estratégia perdedora isso aproxima o resultado de zero e a métrica registra ganho. Medido em H12: correlação de **−0,92** entre retorno base e ganho de timing, concordância de sinal em **8 de 8** combinações — a métrica seguia o sinal da base, não a qualidade do dimensionamento. O limite da lógica é não operar, que maximizaria o critério sem ganhar nada | Corrigido (status `confundido`, 2026-09-01) |

| M12 | Duas convenções de índice convivendo ao comparar amostragens | `pandas.resample` rotula a barra pela borda **esquerda** (abertura) enquanto a construção de barras dirigidas rotulava pelo último candle do grupo. O mesmo instante passava a ter preços de fechamento diferentes em cada versão — medido: 111.169,92 contra 110.422,10 — e o buy-and-hold de cada amostragem media um trecho ligeiramente distinto, desancorando a comparação. A guarda de ancoragem reprovava **todas** as combinações, corretamente. Correção: rotular pelo instante em que a barra **termina**, nas duas versões, o que faz `close` ser função apenas do rótulo e torna a âncora exata (divergência 0,00000000pp) | Corrigido (`data/bars.py`, `backtesting/barras.py`, 2026-09-01) |

| M13 | Estimativa pontual comparada a um limiar, sem banda de incerteza | A verificação de "a razão de chances supera o empate?" comparava o ponto contra 0,500. Medido em H14: razão de **0,5134** com 536 alvos e 1.044 stops — a checagem devolvia **sim**. Mas sob empate exato esperar-se-iam 526,7 alvos, erro padrão 18,7: a diferença é de **meio erro padrão**, p = 0,318, e o limite inferior do intervalo de confiança dá razão de 0,4696, **abaixo** do empate. A estimativa pontual passava e a evidência não existia | Corrigido (`supera_empate_com_confianca`, limite inferior de Wilson, 2026-09-01) |

**Observação.** M6 e M7 emergiram da própria investigação de H7 e são,
argumentavelmente, o produto de maior valor obtido: ambos previnem classes de
falso positivo, não instâncias.

**M7, M10 e M11 são a mesma família.** Os três descrevem uma estratégia que
*participa menos* sendo lida como uma estratégia que *escolhe melhor* — em
tempo (M7), em capital (M10) e no sinal do resultado base (M11). Cada vez que a
guarda foi construída, o mecanismo seguinte encontrou uma dimensão que ela não
cobria. É razoável supor que existam outras.

**Sobre a densidade de defeitos em H12.** Cinco defeitos de instrumentação numa
única hipótese, consolidados em M10 e M11, é o maior número do registro. Nenhum
apareceu em revisão de código: todos apareceram ao confrontar o resultado
observado com a predição registrada antes da execução. O primeiro fio foi o
fator médio de **0,983 medido contra 0,901 previsto** — discrepância pequena o
bastante para passar despercebida se a previsão não estivesse escrita.

**M13 é a quarta forma da família de M9 e M11**: um número que parece bom
porque a régua não tem tolerância. M9 lia amostra insuficiente como reprovação;
M11 lia encolher como vantagem; M13 lia ruído como aprovação. As três se
corrigem do mesmo jeito — exigindo que a evidência sobreviva à incerteza antes
de virar veredito.

**M12 tem procedência diferente das demais.** Não veio de confrontar resultado
com predição, e sim de um **teste de fumaça em dado real** rodado antes da
varredura. A guarda que o detectou (`FR-007`, buy-and-hold ancorado) tinha sido
escrita para outro propósito — verificar que as janelas cobriam o mesmo período
— e capturou uma causa que ninguém havia previsto. É argumento a favor de
guardas declaradas antes de existir suspeita: elas pegam o que não se pensou em
procurar.

---

## 6. Hipóteses não testadas

Fila de avaliação, ordenada por razão evidência-publicada / custo-de-implementação.

### 6.1 Prioridade alta

*(H10 avaliada em 2026-09-01 — ver seção 4.11. Status: inconclusiva, requer reavaliação com histórico mais longo.)*

*(H11 avaliada em 2026-09-01 — ver seção 4.12. Status: reprovada em 4h e 1d; inconclusiva em 1w por limitação estrutural de histórico.)*

*(H12 avaliada em 2026-09-01 — ver seção 4.13. Status: inconclusiva. **Movida
para 6.4**: depende de uma estratégia lucrativa existir antes.)*

*(H13 avaliada em 2026-09-01 — ver seção 4.14. Status: **reprovada**. 96
combinações, 1 melhora, abaixo do que o acaso produziria; efeito mediano
negativo em três de cada quatro combinações avaliadas.)*

*(H14 avaliada em 2026-09-01 — ver seção 4.15. Status: **insuficiente**. Sinal
real, z = +5,21, que não paga as barreiras, z = +0,50.)*

*(H20 avaliada em 2026-09-01 — ver seção 4.16. Status: **reprovada**. Tese
refutada por medição; o sinal aterrissa no ponto de empate em duas geometrias
independentes.)*

**H15 — Arbitragem entre exchanges** — *próxima da fila*

- *Fundamentação:* diferencial de preço entre corretoras é observável e **não
  requer previsão** — a família que H14 e H20 deixaram como única não testada.
- *Obstáculo:* exige capital em múltiplas corretoras, latência competitiva e
  gestão de risco de transferência. Provável dominância de participantes de alta
  frequência.
- *Por que subiu:* H14 e H20 mediram, por caminhos independentes, que a
  componente previsível do movimento é aproximadamente igual ao obstáculo e
  **muda junto com ele**. Isso esgota as duas frentes direcionais que §6.3-b
  identificou, e deixa a família relativa e não-preditiva como a leitura direta
  do registro.

<details>
<summary>H20 — entrada original da fila (mantida para procedência)</summary>

- *Fundamentação:* H14 mediu que o modelo eleva a razão de chances para 0,5134
  no subconjunto decidido, contra um ponto de empate de 0,500 imposto pela
  geometria `stop 1,5×ATR / alvo 3,0×ATR`. O ponto de empate é
  `sl/tp` — é **escolhido**, não dado pelo mercado. Uma geometria com alvo mais
  distante em relação ao stop baixa o ponto de empate e pode caber dentro do
  sinal que já foi demonstrado existir.
- *Risco dominante, e ele é grave:* varrer geometrias até uma passar é
  exatamente o problema de testes múltiplos que a metodologia contém. A
  geometria precisa ser **declarada e justificada antes** da avaliação, como o
  alvo de H12 e o limiar de H13 foram, e confirmada fora da amostra.
- *Advertência:* mudar a geometria muda os **rótulos**, então o modelo é
  retreinado e as chances mudam junto. Não é substituir 0,500 por 0,333 no
  denominador de um resultado já obtido — é uma avaliação nova, e pode piorar.
- *Custo:* baixo — a infraestrutura de H14 já existe e é parametrizada por
  `ParametrosBarreira`.

</details>

### 6.2 Prioridade média

### 6.3 Prioridade baixa

**H16 — Market making (captura de spread)** — exige infraestrutura de baixa
latência e gestão de risco de inventário; competitividade dominada por
participantes profissionais.

**H17 — Sinais on-chain** — literatura classifica como nascente; qualidade de
dado heterogênea.

**H18 — Grid trading** — carece de fundamentação preditiva; equivale a venda de
volatilidade sem gestão de cauda.

**H19 — Estratégias com opções (covered calls)** — mercado de opções cripto de
liquidez restrita; fora do escopo spot.

### 6.3-b Padrão acumulado após quinze hipóteses

Vale registrar o que treze avaliações desenham, porque isso deveria informar a
ordem da fila mais do que a razão evidência/custo isolada de cada item.

**Até H13, o padrão era: toda hipótese que exige prever direção falhou** — H1 a
H7, H11, H13. As duas que chegaram mais perto não eram direcionais: H10
(cointegração) foi a única a passar em E2, com profit factor de 1,58, e falhou
por poder estatístico do seletor; H8 (funding rate) mediu um efeito **real**,
apenas pequeno demais — +3,21% ao ano contra os 10–30% alegados na literatura
popular.

**H14 corrigiu esse padrão, e a correção importa mais que o veredito dela.**

A direção **é** previsível a um grau mensurável: z = +5,21, p < 0,0001. O que
falhou não foi a previsão — foi ela não cobrir o obstáculo econômico. A leitura
anterior ("prever direção não funciona") estava errada; a leitura correta é:

> **A componente previsível existe e é menor que o obstáculo imposto pela
> geometria de saída e pelo custo de execução.**

Isso reordena a fila de forma substantiva. Antes de H14, a conclusão apontava
para abandonar a família direcional. Depois de H14, há duas frentes, e a
segunda é nova:

1. **Aumentar o sinal** — mais atributos, outros modelos. Caro, e H14 já mostra
   que a capacidade do modelo não era o gargalo: 6 parâmetros bastaram para
   extrair sinal robusto.
2. **Reduzir o obstáculo** — o ponto de empate `sl/tp` é escolhido, não dado
   pelo mercado. Originou H20.

**H20 fechou a frente 2, e o modo como fechou importa.** A margem não é apenas
insensível à geometria: ela é aproximadamente **invariante**. Em `tp = 3,0` a
razão obtida foi 1,027 vezes o empate; em `tp = 2,0`, 0,997 vezes — dois pontos
de empate 50% distantes entre si, e o resultado colado na linha nos dois,
aproximando-se de lados opostos.

A leitura de §6.3-b passa a ser:

> **A componente previsível existe, é robusta, e é aproximadamente igual ao
> obstáculo imposto pela geometria de saída — mudando junto com ele.**

Isso esgota as duas frentes direcionais. Resta a redução de obstáculo por
**custo de execução**, que entra na margem por canal distinto e não foi
avaliada; e a família **relativa e não-preditiva**, que volta a ser a leitura
direta do registro — agora por evidência, não por eliminação.

### 6.4 Bloqueadas por pré-condição

Hipóteses que **não são testáveis** no estado atual do registro. Não estão
reprovadas nem despriorizadas por mérito: falta-lhes uma pré-condição que
nenhuma hipótese avaliada até aqui satisfez.

**H12 — Dimensionamento por volatilidade** *(avaliada, inconclusiva — 4.13)*

- *Pré-condição:* uma estratégia com expectativa positiva para dimensionar.
- *Por quê:* dimensionamento decide QUANTO, nunca SE. Aplicado a uma estratégia
  perdedora, reduzir posição aproxima o resultado de zero e qualquer métrica de
  melhora registra isso como ganho — o limite da lógica é não operar. Medido:
  correlação de −0,92 entre retorno base e ganho de timing, 8 de 8 combinações
  concordando em sinal (M11).
- *Quando reavaliar:* assim que qualquer hipótese for aprovada. A infraestrutura
  já existe (`python main.py volatilidade`), com as guardas M10 e M11 no lugar.

**Regra geral que H12 estabeleceu.** Hipóteses de **gestão** (dimensionamento,
alocação, controle de risco) são descendentes de hipóteses de **sinal**, não
alternativas a elas. Enquanto a taxa de aprovação de sinal for 0, a fila deve
priorizar sinal. H14 (aprendizado supervisionado) e H15 (arbitragem entre
corretoras) não caem nesta categoria: a primeira gera sinal próprio, a segunda
não depende de previsão.

---

## 7. Protocolo de continuidade

### 7.1 Bateria de avaliacao

Toda hipotese da secao 6 e submetida a **mesma bateria**, sem excecao e sem
adaptacao do criterio ao candidato. Uma hipotese que exija afrouxar a bateria
para passar esta, por construcao, reprovada.

| Etapa | Instrumento | Reprova se |
|---|---|---|
| E1 — Sanidade | Teste sintetico com resposta conhecida | O motor nao recupera o resultado esperado em dado construido |
| E2 — Janela unica | `run_backtest` / motor proprio + `evaluate_approval` | Falha em qualquer criterio da secao 2.1 |
| E3 — Fora da amostra | `split_train_validation` + `run_scan` | Aprovada apenas na janela de descoberta ("so na busca") |
| E4 — Walk-forward | `walk_forward`, 5 janelas contiguas | Ganho medio negativo, ou menos de 3 janelas positivas |
| E5 — Desconto de exposicao | `ganho_de_timing_pp` | Ganho de timing proximo de zero: o resultado e ausencia, nao selecao |
| E6 — Sensibilidade a custo | Reexecucao com taxa e slippage zerados | Vantagem desaparece integralmente ao reintroduzir custo realista |

**E1 e E5 sao as etapas mais recentes e as que mais reprovaram.** E1 impede que
um defeito de motor seja lido como resultado de estrategia; E5 impede que
exposicao reduzida seja lida como habilidade.

### 7.2 Ciclo

O registro e um ciclo, nao uma lista:

1. **Testar** a hipotese de maior prioridade da secao 6 submetendo-a a bateria
   completa da secao 7.1, sem pular etapa.
2. **Registrar** o veredito neste documento, com evidência e procedência,
   independentemente do resultado. Resultado negativo é registro válido: encerra
   a hipótese e impede sua redescoberta.
3. **Reordenar** a fila quando um achado alterar a prioridade relativa.
4. **Reabastecer** a fila por revisão de literatura quando a seção 6 se esgotar.
5. **Reexecutar** a bateria sobre a fila renovada.

**Estado da fila em 2026-09-01:** 8 hipóteses não testadas (H12–H19), mais a
reavaliação pendente de H10 com formação de 500+ candles. Próxima da fila: H12
(dimensionamento por volatilidade), que ataca diretamente o critério de drawdown
— o único que H10 reprovou em sua melhor janela.

**Condição de parada:** não há. A resposta "nenhuma hipótese testada apresenta
vantagem" é um estado do registro, não seu encerramento.

---

## 8. Conclusão do estado atual

Onze hipóteses avaliadas, nenhuma aprovada. Duas inconclusivas: H10 por poder
estatístico do seletor, H11 em escala semanal por limitação estrutural de
histórico. Nove defeitos de instrumentação identificados e corrigidos.

O conjunto de resultados é consistente com a literatura, que documenta
sobrevivência rara de regras técnicas simples em criptoativos após custos de
transação e validação fora da amostra. As medições deste projeto reproduzem esse
resultado com rigor metodológico próprio, não o contradizem.

O produto mais durável da investigação não é uma estratégia, mas o instrumental:
`evaluate_approval`, `run_scan` com confirmação fora da amostra, `walk_forward` e
`ganho_de_timing_pp`. Os dois últimos foram construídos após um falso positivo de
+29,29pp que o instrumental anterior teria aprovado.

A operação em modo paper permanece ativa e constitui a única fonte de evidência
prospectiva. Estimativa de significância estatística ao ritmo corrente: ~87 dias.

---

## 9. Referências

**Literatura externa**

- Liu, Y., Tsyvinski, A., Wu, X. (2022). *Common Risk Factors in Cryptocurrency.*
- Liu, Y., Tsyvinski, A. (2021). *Risks and Returns of Cryptocurrency.*
- Fischer, T., Krauss, C. *Statistical Arbitrage in Cryptocurrency Markets.*
- *Copula-based trading of cointegrated cryptocurrency pairs.* Financial Innovation (2024).
- *The Two-Tiered Structure of Cryptocurrency Funding Rate Markets.* MDPI Mathematics (2026).
- *Cryptocurrency momentum has (not) its moments.* Financial Markets and Portfolio Management (2025).
- *A Trend Factor for the Cross Section of Cryptocurrency Returns.* Cambridge.

**Documentos internos**

- `docs/research/profitability-of-technical-trading-rules-among-cry.md`
- `docs/research/technical-analysis-in-cryptocurrency-markets.md`
- `docs/research/copula-based-trading-of-cointegrated-cryptocurrency-pairs.md`
- `docs/research/forecasting-and-trading-cryptocurrencies-with-machine-learning-under-changing-market-conditions.md`
- `docs/research/arbitragem-de-funding-rate-medicao-propria.md`
- `docs/research/momentum-transversal-walk-forward.md`
- `docs/research/premio-de-rebalanceamento-medicao.md`
