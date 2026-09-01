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

**Taxa de aprovação: 0 de 10.** Uma inconclusiva (H10).

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
| M8 | Meia-vida de reversão usada como critério único de cointegração | O estimador OLS do coeficiente AR é enviesado para baixo (viés de Dickey-Fuller): passeio aleatório recebe meia-vida **finita**, e a estimativa **escala com a amostra** (mediana 38 em n=250, 173 em n=1000, 417 em n=3000). Taxa de falso positivo de **28%** na seleção de H10 | Corrigido (portão ADF, α=0,05, falso positivo para **4,8%**, 2026-09-01) |

**Observação.** M6 e M7 emergiram da própria investigação de H7 e são,
argumentavelmente, o produto de maior valor obtido: ambos previnem classes de
falso positivo, não instâncias.

---

## 6. Hipóteses não testadas

Fila de avaliação, ordenada por razão evidência-publicada / custo-de-implementação.

### 6.1 Prioridade alta

*(H10 avaliada em 2026-09-01 — ver secao 4.11. Status: inconclusiva, requer reavaliacao com historico mais longo.)*

**H11 — Horizonte temporal superior (diário/semanal)**

- *Fundamentação:* Liu & Tsyvinski (2021) documentam momentum de série temporal
  em horizontes de 1 a 4 semanas. A configuração atual opera em 4 h.
- *Custo:* trivial — alteração de parâmetro. Nenhuma nova infraestrutura.
- *Restrição:* reduz drasticamente o número de operações, agravando o problema
  de tamanho amostral.

**H12 — Dimensionamento por volatilidade (volatility targeting)**

- *Fundamentação:* redimensionar posição inversamente à volatilidade realizada é
  o mecanismo padrão de controle de drawdown em gestão sistemática. H7 reprovou
  exclusivamente por drawdown em sua melhor janela.
- *Custo:* baixo — camada sobre `risk/manager.py`.

### 6.2 Prioridade média

**H13 — Barras dirigidas por informação (CUSUM, volume bars, dollar bars)**

- *Fundamentação:* amostragem por tempo fixo viola homocedasticidade; barras por
  volume ou valor negociado produzem retornos mais próximos de normalidade.
- *Custo:* médio — nova camada de amostragem antes do cálculo de indicadores.

**H14 — Aprendizado de máquina supervisionado com rotulagem de barreira tripla**

- *Fundamentação:* literatura reporta ganho de acurácia preditiva; método de
  rotulagem consolidado.
- *Risco dominante:* sobreajuste. Exigiria walk-forward mais rigoroso que o atual.

**H15 — Arbitragem entre exchanges**

- *Fundamentação:* diferencial de preço entre corretoras é observável e não
  requer previsão.
- *Obstáculo:* exige capital em múltiplas corretoras, latência competitiva e
  gestão de risco de transferência. Provável dominância de participantes de alta
  frequência.

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

**Estado da fila em 2026-09-01:** 9 hipoteses nao testadas (H11-H19), mais a
reavaliacao pendente de H10 com historico mais longo. Proxima da fila: H11
(horizonte temporal superior), de custo trivial.

**Condição de parada:** não há. A resposta "nenhuma hipótese testada apresenta
vantagem" é um estado do registro, não seu encerramento.

---

## 8. Conclusão do estado atual

Dez hipóteses avaliadas, nenhuma aprovada em definitivo; uma inconclusiva por
poder estatístico insuficiente (H10). Oito defeitos de instrumentação
identificados e corrigidos.

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
