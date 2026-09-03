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
| H10 | Arbitragem estatística por cointegração (long-only) | Reversão relativa, par | **REPROVADA** (2026-09-03) | Universo amplo refutado (spec 052), reseleção mais frequente (a cada 120, não 500 candles) resolveu a fome de amostra (spec 054): validação foi de 6 para 10 trades, primeiro veredito não bloqueado por amostra insuficiente — PF 0,15, drawdown 16,61%, reprovada por ampla margem |
| H11 | Horizonte temporal superior (diário/semanal) | Escala temporal | **REPROVADA** (4h, 1d) · **INCONCLUSIVA** (1w) | 144 combinações, 0 confirmadas fora da amostra; confirmado com 3x histórico em 2026-09-02, inconclusivas caem de 27% para 2-8% e veredito se mantém |
| H12 | Dimensionamento por volatilidade | Gestão de risco, não-direcional | **INCONCLUSIVA** | 48 combinações, 0 melhoras; apenas 2 interpretáveis, ambas negativas |
| H13 | Barras dirigidas por informação | Esquema de amostragem | **REPROVADA** | 96 combinações, 1 melhora — **abaixo** do que o acaso produziria |
| H14 | Aprendizado supervisionado (barreira tripla) | Direcional, aprendizado | **REPROVADA** (2026-09-02, overlays de risco esgotados 2026-09-03) | Sinal estatístico robusto (z = +7,97, spec 036) que não sobrevive a capital compartilhado: drawdown de carteira 28,66%, profit factor 0,72 (spec 037). Teto medido de 5 mecanismos de risco + combinações (specs 040-047): melhor caso 19,88% de drawdown, PF 0,68 — ainda reprovado por margem substancial; o problema é o profit factor por trade, não a composição de risco |
| H20 | Geometria de barreira | Geometria de saída | **REPROVADA** (2026-09-03, mecanismo totalmente diagnosticado) | Rótulo confirma a margem com 6.000 candles (spec 048, z=+3,50) mas o backtest real não sustenta — 11/12 pares reprovados (spec 049). Custo domina (spec 050); dentro do custo, taxa domina slippage em 12/12 pares (spec 051) — nem execução mais barata (ordens limit) resolveria, taxa não muda com tipo de ordem neste projeto |
| H21 | Lead-lag BTC para altcoins | Direcional, cross-asset | **REPROVADA** | Correlação real (100% dos pares, spec 038) mas sinal binário dispara demais — 0/11 profit factor acima de 1,0, custo de giro consome a vantagem |

**Taxa de aprovação: 0 de 16.** Duas inconclusivas (H11 em escala
semanal; H12 por impossibilidade estrutural de teste — ver 4.13). H10
saiu de inconclusiva para REPROVADA em 2026-09-03 (spec 054) — reseleção
mais frequente resolveu a fome de amostra, revelando profit factor 0,15
na validação. H20
teve uma reversão de dois estágios em 2026-09-03: sinal de rótulo
confirmado com histórico estendido (spec 048), depois reprovada de
novo quando testada contra o backtest real (spec 049) — custo de
execução/trailing stop consomem a margem que o rótulo media. Volta a
0/16, mas com o mecanismo agora entendido em mais detalhe que antes.

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

#### Atualização — histórico estendido, instrumento corrigido (2026-09-02, spec 039)

`formacao` de 250 → 500 candles (D1, poder de detecção medido em 60%
contra 20% a 250, tabela acima) sobre 6.000 candles de histórico (spec
036), split treino/validação 70/30 com aquecimento causal (os 500 candles
finais do treino prepostos à validação, para o seletor não começar
"frio" — `specs/039-reavaliar-h10-pairs-trading/research.md`, D2).
Mesmo critério de seleção, entrada, saída e aprovação — só o instrumento
de amostragem muda.

**Resultado (`python main.py pairs`, 2026-09-02):**

| | Treino | Validação |
|---|---|---|
| Trades | 36 | **6** |
| Retorno | +10,30% | −6,92% |
| Buy-and-hold | +20,73% | −40,06% |
| Drawdown | 23,69% | 8,06% |
| Profit factor | **1,22** | **0,04** |

O treino passa profit factor (1,22 > 1,20) mas falha drawdown (23,69% >
10%). A validação tem drawdown aceitável (8,06%) mas só 6 trades — ainda
**abaixo do mínimo de 10** — e profit factor 0,04, dominado por 1-2
saídas ruins numa amostra pequena demais para ler o número como
significativo em qualquer direção. Notável à parte: a estratégia perdeu
muito menos que o mercado no período (−6,92% contra um buy-and-hold de
−40,06%, uma queda severa) — nenhum veredito se apoia nisso sozinho, mas
descarta a leitura de "a estratégia simplesmente não funciona".

**Por que o veredito automático ("reprovado") está sendo corrigido para
INCONCLUSIVA aqui — achado metodológico (M14, ver §5).** A correção de
formação resolveu o problema medido antes (poder de detecção do seletor,
20%→60%) — mas revelou um problema **diferente**: mesmo com o seletor
capaz de detectar o par, `UNIVERSO_H11` (12 pares, 66 combinações) produz
poucos pares que passam ADF **e** meia-vida negociável ao mesmo tempo, e
menos ainda geram sinal de entrada dentro de uma janela de validação de
~1.800 candles. `evaluate_approval()` (`backtesting/approval.py`,
compartilhada por `grid`/`carteira`/`leadlag`/`pairs`) trata amostra
abaixo do mínimo como **um motivo de reprovação a mais**, nunca como
categoria própria — diferente de `classificar_avaliacao()`
(`backtesting/modelo.py`, usada por H14), que devolve `"inconclusivo"`
explicitamente quando `total_trades < EDGE_MIN_TRADES`, **antes** de
sequer olhar profit factor ou drawdown. É a mesma família de M9 ("regra
de amostra mínima aplicada só à janela de busca, não à de confirmação"):
aqui a regra existe na validação, mas devolve o rótulo errado quando
falha sozinha. `evaluate_approval()` não foi alterada nesta spec — o
escopo de `specs/039-reavaliar-h10-pairs-trading/` era só a janela de
formação de H10; corrigir a função compartilhada afetaria todo veredito
que já a usa (`grid`, `carteira`, `leadlag`) e exige revisão própria,
registrada como M14 em vez de corrigida silenciosamente aqui.

**Novo status: INCONCLUSIVA (não reprovada).** O poder de detecção do
seletor deixou de ser a limitação — mas o universo de 12 pares não
produziu operações suficientes na validação para decidir. Resolver
exigiria mais pares candidatos (não `UNIVERSO_H11`, que foi fixado para
comparabilidade entre hipóteses) ou uma janela de validação ainda maior —
qualquer um dos dois seria uma escolha nova, não uma correção pontual
como esta.

**Reprodução:** `python main.py pairs` ·
`specs/039-reavaliar-h10-pairs-trading/`.

---

#### Atualização — universo amplo não resolve a fome de amostra: continua inconclusiva (2026-09-03, spec 052)

Spec 039 apontou o universo de 12 pares (66 combinações) como candidato
a explicar a amostra pequena da validação. Testado diretamente:
`UNIVERSO_AMPLO_HISTORICO_COMPLETO` (22 pares — subconjunto de
`UNIVERSO_AMPLO`, spec 040, filtrado para histórico completo de 6.000
candles, D1 de `specs/052-h10-universo-amplo/research.md`, depois de a
primeira tentativa com `UNIVERSO_AMPLO` bruto colidir com
`split_treino_validacao` — interseção de índices de tempo colapsada
por uma listagem recente de só 504 candles), 231 combinações contra 66.

**Resultado (`python main.py pairs_amplo`, 2026-09-03):**

| | 12 pares (spec 039) | 22 pares (spec 052) |
|---|---|---|
| Treino — trades | não reportado individualmente | 31 |
| Treino — retorno / PF | +10,30% / 1,22 | +12,55% / 1,22 |
| **Validação — trades** | **6** | **6** |
| Validação — retorno / PF | −6,92% / 0,04 | −0,58% / 0,73 |
| Validação — drawdown | 8,06% | 2,76% |
| Veredito | inconclusiva (< 10 trades) | inconclusiva (< 10 trades) |

**Quase dobrar o universo candidato (12→22 pares, 66→231 combinações)
não mudou o número de trades na validação — continua exatamente 6.**
A hipótese declarada em spec 039 ("resolver exigiria mais pares
candidatos") está refutada por medição direta: o gargalo não é
quantidade de combinações testadas por `selecionar_pares`. Read-out
mais provável: `max_pares=3` limita quantos pares operam
simultaneamente independente de quantos são elegíveis, e/ou a
reseleção a cada `formacao` (500 candles) dá poucas janelas de
oportunidade dentro dos ~1.800 candles de validação, independente de
quantos candidatos existem para preencher essas poucas janelas. Nenhum
dos dois foi isolado nesta spec.

**Segundo achado de instrumento no caminho** (não formalizado como M
numerado, documentado em `research.md` D1 de spec 052):
`split_treino_validacao` exige um índice de tempo comum entre **todos**
os pares recebidos — incompatível com listar pares de histórico
desigual (diferente de `backtesting/portfolio_h14.py`, que alinha cada
par independentemente). Filtrar por histórico completo antes de
chamar é agora prática declarada para qualquer futuro uso de universos
maiores com este motor específico.

**Continua INCONCLUSIVA — não REPROVADA.** O treino segue passando
profit factor (1,22, igual aos dois universos). O que falta ainda é
amostra na validação, mas "mais candidatos" já não é mais uma hipótese
em aberto para resolver isso — precisaria ser outra coisa (janela de
validação maior, mais `max_pares`, ou reseleção mais frequente), cada
uma delas uma escolha nova, não uma correção pontual.

**Reprodução:** `python main.py pairs_amplo` ·
`specs/052-h10-universo-amplo/`.

---

#### Atualização — reseleção mais frequente resolve a amostra: REPROVADA, não mais inconclusiva (2026-09-03, spec 054)

Antes de tocar em qualquer parâmetro, diagnóstico direto sobre a
janela de validação real (22 pares, sem código novo, script de
investigação) mediu a causa exata: `reselecionar_a_cada` estava
amarrado a `formacao` (500) — só **4 ciclos de reseleção** ocorrem em
~2.300 candles de validação, elegendo 1-3 pares cada. Dentro dessa
janela inteira, o z-score de algum par elegível cruza o limiar de
entrada (`entrada_z=2,0`) **exatamente 6 vezes** — o mesmo número dos
6 trades já publicados nos dois universos (specs 039, 052). `max_pares`
descartado como gargalo por medição direta: 1.794 de 2.300 candles
(78%) têm slot livre e nenhuma oportunidade entre os pares
selecionados no momento (`specs/054-h10-reselecao-frequente/research.md`,
D1).

`run_pairs_scan` ganhou `reselecionar_a_cada` desacoplado de
`formacao` (D2: `selecionar_pares` sempre olha `formacao=500` candles
para trás a partir de cada checkpoint, independente da cadência —
reselecionar mais não reduz o poder de detecção). Testado com
`reselecionar_a_cada=120` (`PairsParams.meia_vida_max`, já existente —
critério mecânico, D3: o maior intervalo que ainda garante um
checkpoint por ciclo de reversão completo da relação mais lenta que a
própria regra aceita).

**Resultado (`python main.py pairs_reselecao`, 2026-09-03):**

| | 12 pares, cadência 500 (spec 039) | 22 pares, cadência 500 (spec 052) | 22 pares, cadência 120 (spec 054) |
|---|---|---|---|
| Treino — trades | não reportado | 31 | **54** |
| Treino — PF | 1,22 | 1,22 | 1,20 |
| **Validação — trades** | 6 | 6 | **10** |
| Validação — retorno | −6,92% | −0,58% | **−12,28%** |
| Validação — drawdown | 8,06% | 2,76% | **16,61%** |
| Validação — PF | 0,04 | 0,73 | **0,15** |
| Veredito | inconclusiva | inconclusiva | **REPROVADA** |

**A reseleção mais frequente resolveu exatamente o problema
diagnosticado — validação foi de 6 para 10 trades, atingindo
`EDGE_MIN_TRADES`.** Pela primeira vez desde 2026-09-01, H10 produz um
veredito que não é bloqueado por amostra insuficiente. E o veredito é
claramente negativo: profit factor 0,15 (bem abaixo do mínimo 1,2) e
drawdown 16,61% (acima do teto de 10%) — não uma aprovação que a fome
de amostra escondia.

**Veredito final: REPROVADA.** Diferente de H14/H20 (sinal real que
não sobrevive a outro obstáculo), aqui a amostra maior revela que o
sinal em si não é bom o bastante — profit factor 0,15 é o pior já
medido para uma linha de base de treino que passava (1,20). O treino
com mais trades (54) ainda passa profit factor por uma margem mínima
(1,20, na fronteira de 1,2), mas a validação — a única janela que
conta — reprova por ampla margem nos dois critérios.

**Trajetória completa de H10, todos os estágios reais:** insuficiente
(2026-09-01) → poder de detecção corrigido, ainda inconclusiva por
amostra (spec 039, 2026-09-02) → universo amplo refutado como causa
(spec 052, 2026-09-03) → reseleção mais frequente resolve a amostra e
revela REPROVADA (spec 054, 2026-09-03). Quatro specs, cada uma
respondendo uma pergunta genuinamente diferente, nenhuma invalidando a
anterior — o padrão que definiu toda a investigação desta noite.

**Reprodução:** `python main.py pairs_reselecao` ·
`specs/054-h10-reselecao-frequente/`.

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

#### Atualização — histórico estendido (2026-09-02, spec 036)

`solicitado` (`backtesting/horizonte.py::run_horizonte_scan`/
`medir_disponibilidade`) trocado de `2000` para `6000` (D1,
`specs/036-historico-estendido/research.md`), mesmas 4 estratégias, mesmos
12 pares. `1w` não foi rerodado — fora do escopo (D1: a limitação
estrutural já é conhecida e não muda com mais histórico no timeframe
diário/4h).

| Horizonte | Candles medianos | Avaliadas | Confirmadas | Reprovadas | Inconclusivas |
|---|---|---|---|---|---|
| 4h (antes) | 2.000 | 48 | 0 | 34 | 13 |
| **4h (depois)** | **6.000** | 48 | **0** | **47** | **1** |
| 1d (antes) | ~2.000 | 48 | 0 | 35 | 13 |
| **1d (depois)** | **2.896** | 48 | **0** | **44** | **4** |

`1d` pediu 6.000 e recebeu 2.896 — teto real da Binance para o histórico
diário de vários pares do universo (`AVAX`/`DOT`/`SOL` marcados
`historico curto`, listagem mais recente), não sub-entrega silenciosa
(`medir_disponibilidade` mede e registra, não presume).

**O veredito não muda — a base de evidência atrás dele fica muito maior.**
Zero confirmadas continua zero confirmadas nas duas escalas. O que desloca é
a fração `inconclusivo`: em 4h, de 13/48 (27%) para 1/48 (2%); em 1d, de
13/48 (27%) para 4/48 (8%). Com 3x mais histórico em 4h, quase todas as
combinações que antes não tinham janela de confirmação suficiente agora
têm — e a resposta, com muito mais amostra, continua sendo reprovação, não
uma reversão como a de H14. Isso fortalece a leitura original: a fração
`inconclusivo` alta na primeira execução era mesmo limitação de amostra
(como previsto para `1w`), não sinal escondido que mais histórico
revelaria.

**Reprodução:** `python main.py horizonte 4h` · `python main.py horizonte
1d` · `specs/036-historico-estendido/`.

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

#### Atualização — mecanismo aplicado a H14 em vez de repetido aqui (2026-09-03, spec 041)

Pedido do usuário de "reabrir H12" redirecionado: `fator_volatilidade()`
(acima) foi aplicado à carteira de H14 (a única avaliação deste registro
com sinal real desde spec 036), não às 4 estratégias de regra de novo —
repetir o teste original teria o mesmo resultado estrutural (nenhuma base
lucrativa para proteger). Resultado: drawdown de carteira caiu de 28,66%
para 23,04% (~20% de redução), sem piorar profit factor — primeira
evidência de que o mecanismo tem efeito real, mesmo insuficiente para
aprovar H14 sozinho. Ver §4.15, atualização spec 041, para os números
completos.

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

#### Atualização — histórico estendido (2026-09-02, spec 036)

`fetch_ohlcv` já suportava paginação além do teto de ~1.000 candles da API
(spec 011) — o `2000` usado por `avaliar_par`/`coletar_eventos` era uma
escolha do chamador nunca revisada, não um limite do sistema. Trocado por
`6000` (~2,7 anos de 4h, D1 de `specs/036-historico-estendido/research.md`),
medido antes de qualquer resultado novo, para as hipóteses com sinal
promissor que dependiam de mais amostra (H10 fora do escopo — sem CLI, D3
do mesmo `research.md`).

Mesmos 12 pares, mesmas barreiras (stop 1,5×ATR, alvo 3,0×ATR, 24 velas),
mesmo modelo — só mais histórico:

| | antes (2.000 velas) | depois (6.000 velas) |
|---|---|---|
| n_treino / n_teste (globais) | ~16.000 / — | 49.696 / 1.786 |
| Todos os eventos: alvo/stop | 1.650 / 4.235 | 5.270 / 13.364 |
| Subconjunto decidido: alvo/stop | 536 / 1.044 | **971 / 1.394** |
| Razão de chances decidido | 0,5134 | **0,6966** |
| Há sinal? (decidido vs taxa base) | z = +5,21, p < 0,0001 | **z = +13,8**, p ≈ 0 |
| Paga as barreiras? (decidido vs empate) | z = +0,50, p = 0,318 — **não resolvível** | **z = +7,97**, p < 0,0001 — **sim, robustamente** |
| `supera_empate_com_confianca` (IC de Wilson) | **False** (limite inferior 0,4696 < 0,500) | **True** (limite inferior equivalente 0,6418 > 0,500) |

**O teste que definia `insuficiente` deixou de bloquear.** A categoria foi
criada especificamente para "sinal real que não paga a barreira" (Predição
2 acima, registrada antes de qualquer execução). Com 3x mais histórico, a
mesma pergunta agora responde **sim**, e a resposta não é marginal: o
intervalo de confiança de Wilson, que antes cruzava o ponto de empate,
agora fica inteiramente acima dele.

**O que isso NÃO decide.** Nenhuma das limitações declaradas originalmente
foi resolvida por ter mais histórico:

- **Drawdown continua não agregável** — depende de um motor de carteira que
  não existe, mesma razão de antes.
- **Nenhum dos 12 pares individualmente atinge `melhora`**: cinco ficam
  `insuficiente` (amostra por par pequena demais para uma CI robusta —
  mesmo padrão que motivou agregar desde o início, mesmo com razão de
  chances por par acima de 0,500 em três deles), três `piora` (drawdown por
  par sobe apesar de razão de chances alta — XRP 0,756, LTC 0,744, SOL
  0,978), um `sem_sinal` (TRX, `vs_embaralhado` **negativo**, −9,31pp —
  pior que ruído nesse par especificamente) e três `inconclusivo` (linha de
  base de regras abaixo do mínimo de operações). O sinal agregado é real;
  ele não se traduz uniformemente em vantagem por par.
- **H20 mediu, com 2.000 candles, que nenhuma geometria de barreira resolve
  a margem sobre o empate** (seção 4.16) — essa medição não foi refeita
  aqui, fora do escopo de `specs/036-historico-estendido/` (D2). Se a mesma
  elevação de amostra que resolveu H14 também desloca H20, é uma pergunta
  em aberto, não uma correção deste registro.

**Novo veredito: sinal detectável e agora estatisticamente robusto acima do
empate — a pergunta que a categoria `insuficiente` deixava em aberto está
respondida.** Aprovação operacional (drawdown de carteira, desempenho por
par, confirmação fora da amostra no agregado) segue não avaliada. Não é uma
promoção a `aprovada`: é a remoção do bloqueio específico que `insuficiente`
media.

**Reprodução:** `python main.py modelo` (6.000 candles, `TIMEFRAME=4h`) ·
`reports/modelo_20260902-114000.json` · `specs/036-historico-estendido/`.

#### Atualização — motor de carteira, aprovação operacional (2026-09-02, spec 037)

A atualização anterior (histórico estendido) deixou explícito o que
faltava: "aprovação operacional (drawdown de carteira, desempenho por
par, confirmação fora da amostra no agregado) segue não avaliada". Esta
spec constrói exatamente essa medição — `backtesting/portfolio_h14.py`
simula os 12 pares **simultaneamente**, com **um caixa compartilhado**
(não 12 capitais independentes), `MAX_POSITIONS` como teto de posições
concorrentes, e o mecanismo de saída **realmente usado pelo backtest já
publicado de H14** (take-profit por ATR + stop trailing, mesma fórmula de
produção) — não as barreiras de rotulagem do treino, que rotulam o alvo do
classificador, nunca geriram a posição no backtest real (correção
registrada em `specs/037-motor-carteira-h14/research.md`, D7, antes de
qualquer código).

**Resultado (`python main.py carteira`, 2026-09-02):**

| | Valor |
|---|---|
| Pares simulados | 12 |
| Trades | 931 |
| Capital | $1.000,00 → $798,79 |
| Retorno total | −20,12% |
| Buy-and-hold de carteira (igualmente ponderada, D5) | −41,57% |
| **Drawdown agregado de carteira** | **28,66%** |
| Profit factor | 0,72 |
| **Veredito (`evaluate_approval`, sem critério novo)** | **REPROVADO** — profit factor abaixo de 1,20; drawdown acima de 10% |

**O achado central: drawdown de carteira é 5x o maior drawdown isolado por
par.** O maior `max_drawdown_pct` entre as 12 avaliações isoladas de H14
(§4.15, medição anterior) é 5,54%. Sob capital compartilhado e
concorrência real, o drawdown agregado sobe para 28,66% — nenhuma
avaliação por par, isoladamente, deixava isso visível, porque nenhuma
simula mais de uma posição aberta ao mesmo tempo.

**Mecanismo provável, não coberto por esta spec.** Esta spec exclui
deliberadamente (`spec.md` FR-007) a checagem de correlação entre
posições que a produção já tem
(`risk/correlation.py::check_correlated_exposure`) — para isolar se o
problema é do sinal de H14 ou da pilha de risco inteira. Pares de cripto
correlacionados a ~0,71 (medido em H7, §4.7) abrindo posição ao mesmo
tempo se comportam como uma única posição grande concentrada numa queda
geral de mercado — exatamente o mecanismo que `check_correlated_exposure`
existe para impedir em produção, e que este motor de carteira, de
propósito, não usa. **O resultado aqui é reprovação sob uma pilha de
risco deliberadamente mais estreita que a de produção** — um piso, não
necessariamente o veredito final se a mesma simulação rodasse com o gate
de correlação ligado. Isso seria uma spec nova (hipótese de mecanismo
diferente, mesmo princípio já aplicado a H18, §6.3), não um ajuste de
parâmetro sobre esta.

**Novo veredito de H14: REPROVADA.** O sinal estatístico da classificação
(razão de chances no subconjunto decidido, `supera_empate_com_confianca`)
continua real e robusto — isso não muda. Mas "sinal estatístico que paga a
barreira" e "estratégia operável com risco aceitável" são perguntas
diferentes, e a segunda agora tem resposta: sob o mecanismo de saída
real de H14 e concorrência de capital real entre os 12 pares, a
carteira perde dinheiro (profit factor 0,72) com drawdown quase 3x acima
do teto aceitável. A trajetória completa de H14 neste registro —
INSUFICIENTE (2026-09-01) → sinal confirmado (2026-09-02, spec 036) →
REPROVADA (2026-09-02, spec 037) — fica preservada como histórico, não
substituída: cada etapa mediu uma pergunta genuinamente diferente, e
nenhuma invalida a anterior.

**Reprodução:** `python main.py carteira` · `reports/carteira_20260902-195909.json`
· `specs/037-motor-carteira-h14/`.

#### Atualização — universo amplo, hipótese de correlação refutada (2026-09-03, spec 040)

A seção anterior deixou uma pergunta em aberto: o drawdown de carteira
5x pior que o isolado por par seria explicado por correlação entre
poucos pares (12), corrigível ampliando o universo de candidatos? Testado
— mesmo modelo, mesmas barreiras, mesmo mecanismo de saída,
`MAX_POSITIONS` fixo no valor de produção, só o universo mudou (12 → 34
pares, medido via os limiares de liquidez já existentes do projeto, sem
escolher pares por resultado — `specs/040-carteira-universo-amplo/research.md`,
D1). Motivação: a estratégia comunitária mais usada do Freqtrade
(NostalgiaForInfinity) opera sobre 40-80 pares simultâneos — pesquisa
sobre bots de código aberto pedida nesta sessão.

**Resultado (`python main.py carteira_ampla`, 2026-09-03):**

| | 12 pares (spec 037) | 34 pares (spec 040) |
|---|---|---|
| Trades | 931 | 1.121 |
| Retorno | −20,12% | −28,07% |
| Buy-and-hold | −41,57% | −33,74% |
| **Drawdown agregado** | **28,66%** | **35,08%** |
| Profit factor | 0,72 | 0,82 |

**A hipótese está refutada — o drawdown piorou, não melhorou.** Profit
factor subiu um pouco e o retorno passou a bater o buy-and-hold (o que
não acontecia com 12 pares), mas o número que a spec existia para testar
— drawdown de carteira — foi na direção contrária à prevista.

**Mecanismo provável.** Ampliar o universo por liquidez, sem filtrar por
correlação, não necessariamente adiciona pares **descorrelacionados** —
adiciona pares **diferentes**, e boa parte dos 22 pares novos são
listagens recentes e de maior volatilidade idiossincrática (PUMP,
MUBARAK, ASTER, TRUMP, HEMI, BMT, SNDKB, CRCLB, TUT, T — vários tokens
especulativos/memecoin, ausentes de `UNIVERSO_H11`, que é só ativos
estabelecidos). Se o modelo tende a sinalizar entrada nesses ativos mais
voláteis com a mesma facilidade que nos estabelecidos, a carteira pode
ter passado a concentrar em ativos de risco mais alto, não menos
correlacionado — o oposto do que a hipótese previa. Também é consistente
com um fenômeno bem documentado em finanças: correlação entre ativos de
risco tende a **subir**, não descer, durante quedas de mercado amplas —
exatamente o cenário em que o drawdown de carteira se forma. Mais opções
de pares não ajuda se, no momento em que mais importa, quase todos se
movem juntos de qualquer forma.

**O que isso não decide.** Não refuta a ideia de que correlação seja o
mecanismo do drawdown de H14 — só refuta que **ampliar passivamente o
universo, sem filtrar por correlação**, seja a correção. A produção já
tem exatamente o mecanismo ativo que faltou aqui —
`risk/correlation.py::check_correlated_exposure`, que bloqueia uma
entrada nova especificamente por já haver posição aberta correlacionada,
não por escassez de opções — deliberadamente excluído tanto de spec 037
quanto de spec 040 (FR-007/FR-005 respectivas) para isolar cada variável.
Testar esse gate seria a hipótese natural seguinte, ainda não coberta.

**Reprodução:** `python main.py carteira_ampla` ·
`specs/040-carteira-universo-amplo/`.

#### Atualização — dimensionamento por volatilidade, primeira melhora real (2026-09-03, spec 041)

Terceira variável testada isoladamente sobre o drawdown de carteira de
H14 (depois de universo amplo, refutado em spec 040): dimensionamento
por volatilidade, reusando `fator_volatilidade()` já implementado e
medido para H12 (spec 025) sem alteração — reduz o tamanho de cada
entrada quando `atr_ratio` do candle está acima do alvo (0,02), nunca
amplia. Motivação: correlação entre ativos de risco tende a subir
durante quedas amplas, quando `atr_ratio` também sobe — encolher posição
exatamente nesses momentos ataca o mesmo mecanismo sem precisar de uma
checagem de correlação explícita.

**Redirecionamento de escopo, não repetição de H12.** O pedido original
era reabrir H12 — mas §4.13 já concluiu que H12 não é testável sobre
estratégias sem expectativa positiva, e nenhuma das 4 estratégias de
regra tinha. H14 é a primeira e única avaliação deste registro com sinal
real (`supera_empate_com_confianca`, spec 036) — a primeira vantagem
genuína disponível para o mecanismo de H12 proteger.

**Resultado (`python main.py carteira_vol`, 2026-09-03, mesmos 12 pares de `UNIVERSO_H11`):**

| | Sem dimensionamento (spec 037) | Com dimensionamento (spec 041) |
|---|---|---|
| Trades | 931 | 763 |
| Retorno | −20,12% | **−18,16%** |
| Buy-and-hold | −41,57% | −42,28% |
| **Drawdown agregado** | **28,66%** | **23,04%** |
| Profit factor | 0,72 | 0,72 |

**Primeira melhora real de drawdown medida nesta linha de investigação.**
Diferente do universo amplo (spec 040, drawdown piorou de 28,66% para
35,08%), o dimensionamento por volatilidade reduziu o drawdown em quase
6 pontos percentuais (28,66% → 23,04%, ~20% de redução relativa) e também
melhorou o retorno (−20,12% → −18,16%) — sem piorar o profit factor
(0,72 nos dois, idêntico). Consistente com o mecanismo proposto: reduzir
exposição em candles de alta volatilidade ajudou.

**Ainda reprovado — a melhora não é suficiente.** Drawdown de 23,04%
segue mais que o dobro do teto aceitável (10%), e profit factor 0,72
continua abaixo de 1,2. O veredito de H14 não muda.

**O que isso decide.** Diferente da hipótese de universo amplo
(refutada, §4.15 spec 040), esta não foi refutada — foi confirmada
parcialmente. É a primeira evidência empírica deste registro de que o
mecanismo de correlação/volatilidade por trás do drawdown de H14 é, pelo
menos em parte, real e mitigável — só não o bastante sozinho.
Combinar dimensionamento por volatilidade com o gate de correlação já
existente em produção (`risk/correlation.py::check_correlated_exposure`,
ainda não testado nesta carteira) é a hipótese natural seguinte.

**Reprodução:** `python main.py carteira_vol` ·
`specs/041-volatilidade-carteira-h14/`.

#### Atualização — gate de correlação, maior melhora medida até aqui (2026-09-03, spec 042)

Quarta variável isolada sobre o drawdown de carteira de H14. Diferente
das duas tentativas anteriores (universo amplo, indireto, refutado;
dimensionamento por volatilidade, indireto, ajudou parcialmente), esta
ataca o mecanismo de frente: bloqueia uma entrada nova especificamente
quando correlacionada (retornos ≥ 0,7 em 50 candles) com uma posição já
aberta — o mesmo texto e os mesmos limiares do gate real de produção
(`risk/correlation.py::check_correlated_exposure`), reimplementado
ponto-no-tempo (`_correlacionado_com_posicao_aberta`) porque a função de
produção busca dado ao vivo — inutilizável dentro de um backtest sem
vazar futuro (`specs/042-gate-correlacao-carteira-h14/research.md`, D1).

**Resultado (`python main.py carteira_corr`, 2026-09-03, mesmos 12 pares de `UNIVERSO_H11`):**

| | Sem overlay (spec 037) | Dimensionamento vol. (spec 041) | Gate de correlação (spec 042) |
|---|---|---|---|
| Trades | 931 | 763 | 595 |
| Retorno | −20,12% | −18,16% | **−16,04%** |
| **Drawdown agregado** | **28,66%** | **23,04%** | **20,74%** |
| Profit factor | 0,72 | 0,72 | 0,68 |

**Maior redução de drawdown medida nesta linha de investigação** — 28,66%
→ 20,74%, quase 8 pontos percentuais, ~28% de redução relativa (contra
~20% do dimensionamento por volatilidade). Retorno também é o melhor dos
três (−16,04%). Único recuo: profit factor cai de 0,72 para 0,68 — bloquear
entradas correlacionadas também bloqueia algumas que teriam dado certo,
não só as que teriam concentrado risco.

**Ainda reprovado.** Drawdown de 20,74% segue o dobro do teto aceitável
(10%), e profit factor 0,68 está mais distante de 1,2 que nos outros dois
testes. O veredito de H14 não muda.

**Confirma o mecanismo de forma mais direta que qualquer teste anterior.**
Bloquear correlação de verdade (não só reduzir exposição em momentos
voláteis, spec 041, nem ampliar o universo de candidatos, spec 040
refutado) produziu o maior efeito — evidência mais forte até agora de que
posições correlacionadas concorrentes são, de fato, o principal
mecanismo por trás do drawdown de carteira de H14.

**Reprodução:** `python main.py carteira_corr` ·
`specs/042-gate-correlacao-carteira-h14/`.

---

#### Atualização — combinação vol. + correlação, os dois efeitos não somam (2026-09-03, spec 043)

Os dois mecanismos que isoladamente melhoraram o drawdown (dimensionamento
por volatilidade, spec 041; gate de correlação, spec 042) ligados ao mesmo
tempo, sobre a mesma carteira de `UNIVERSO_H11` — zero mecânica nova,
`_simular_carteira_core(usar_dimensionamento_vol=True,
usar_gate_correlacao=True)`, gate roda antes do dimensionamento
(`specs/043-combinado-vol-correlacao-h14/data-model.md`).

**Resultado (`python main.py carteira_combo`, 2026-09-03, mesmos 12 pares):**

| | Sem overlay (spec 037) | Só volatilidade (spec 041) | Só correlação (spec 042) | Combinado (spec 043) |
|---|---|---|---|---|
| Trades | 931 | 763 | 595 | **595** |
| Retorno | −20,12% | −18,16% | −16,04% | **−15,98%** |
| Drawdown agregado | 28,66% | 23,04% | 20,74% | **20,24%** |
| Profit factor | 0,72 | 0,72 | 0,68 | **0,67** |

**Os efeitos não somam — o gate de correlação domina quase inteiramente.**
`total_trades` do combinado é idêntico ao do gate sozinho (595): o
dimensionamento por volatilidade não muda quais trades abrem/fecham, só o
tamanho de cada um, e a maioria dos pares voláteis-e-correlacionados que
ele reduziria já foi excluída pelo próprio gate antes do dimensionamento
rodar (ordem declarada em `data-model.md` — gate primeiro, por ser filtro
binário). O ganho marginal de somar volatilidade por cima do gate é
pequeno: drawdown 20,74% → 20,24% (~2% de redução relativa, contra ~28%
do gate sozinho sobre a base sem overlay), retorno quase igual
(−16,04% → −15,98%), profit factor levemente pior (0,68 → 0,67).

**Ainda reprovado** — mesmo motivo de sempre: drawdown 20,24% segue o
dobro do teto aceitável (10%), profit factor 0,67 abaixo do mínimo 1,2.
Combinar os dois melhores mecanismos encontrados até agora não tira H14
da faixa de reprovação; só confirma que o gate de correlação é, sozinho,
essencialmente todo o efeito disponível nessa direção — o passo seguinte
não é mais overlay de risco sobre a mesma decisão de entrada, é atacar
outra parte do mecanismo (ex.: o próprio classificador de entrada, ou o
mecanismo de saída).

**Reprodução:** `python main.py carteira_combo` ·
`specs/043-combinado-vol-correlacao-h14/`.

---

#### Atualização — circuit breaker de perdas consecutivas, drawdown cai mas a amostra desmorata junto (2026-09-03, spec 044)

Quinto mecanismo de risco isolado sobre a carteira de H14, e o primeiro
**temporal** em vez de espacial: bloqueia novas entradas depois de
`MAX_CONSECUTIVE_LOSSES` (3) trades fechados consecutivos com prejuízo,
reseta no primeiro trade lucrativo — mesma semântica de
`execution/order_manager.py`, nunca testada na carteira
(`specs/044-circuit-breaker-carteira-h14/`). Testado isolado (sem
dimensionamento nem gate de correlação), mesmos 12 pares.

**Resultado (`python main.py carteira_breaker`, 2026-09-03):**

| | Sem overlay (spec 037) | Só correlação (spec 042) | Combinado (spec 043) | Circuit breaker (spec 044) |
|---|---|---|---|---|
| Trades | 931 | 595 | 595 | **6** |
| Retorno | −20,12% | −16,04% | −15,98% | **−0,40%** |
| Drawdown agregado | 28,66% | 20,74% | 20,24% | **0,57%** |
| Profit factor | 0,72 | 0,68 | 0,67 | 0,36 |

**O drawdown despenca, mas não é uma vitória — é a amostra desmoronando
junto.** Com um profit factor de base ~0,7 (mais perdas que ganhos), a
sequência de 3 perdas seguidas acontece cedo e com frequência; sem o
cooldown por tempo de produção (decisão D1, `research.md`, deliberada —
ver justificativa lá), o único jeito de destravar é um trade lucrativo,
que num regime de baixo win rate demora. Na prática, o breaker passa a
maior parte dos ~2,7 anos ativo, bloqueando quase toda entrada nova —
6 trades no total contra 595-931 dos outros testes. Drawdown baixo
porque **quase não há capital em risco a maior parte do tempo**, não
porque o mecanismo melhorou a qualidade das entradas que passam.

**Caso real do achado M14 (§5).** No momento da execução,
`evaluate_approval()` retornou `"reprovado"` citando junto "apenas 6
trades na validação (mínimo 10)" e "profit factor 0.36 abaixo do mínimo
1.2" — mas 6 trades é abaixo do mínimo estatístico para qualquer
leitura do profit factor ter significado. Confirmou, por um segundo
caso além de H10 (spec 039), o defeito de instrumentação catalogado em
M14 — motivou a correção da função (§5, 2026-09-03, mesmo dia). Com a
correção aplicada, este mesmo resultado agora devolve `"inconclusivo"`,
motivo único ("apenas 6 trades na validação") — o veredito correto:
nada foi provado sobre a qualidade das entradas que passam, só que
quase nenhuma passou.

**Não aprova H14, e o resultado bruto não é comparável aos quatro
anteriores** — universo de decisão completamente diferente (6 trades vs
595-931). Não invalida os resultados já publicados dos outros quatro
mecanismos, só mostra que este mecanismo específico, do jeito declarado
(sem cooldown por tempo), não é um overlay de risco utilizável isolado
sobre uma estratégia de profit factor abaixo de 1 — ele não reduz risco
por trade, reduz risco por parar de operar.

**Reprodução:** `python main.py carteira_breaker` ·
`specs/044-circuit-breaker-carteira-h14/`.

---

#### Atualização — limite de drawdown diário, reset por calendário não colapsa a amostra (2026-09-03, spec 045)

Sexto mecanismo de risco isolado sobre a carteira de H14, e o segundo
temporal: bloqueia novas entradas quando o patrimônio do dia cai abaixo
de `1 - DAILY_DRAWDOWN_LIMIT` (5%) vezes o saldo de referência do dia,
resetado **por calendário** (novo dia), não por resultado — diferente
do circuit breaker de perdas consecutivas (spec 044), que só resetava
com um trade lucrativo e colapsou a amostra para 6 trades
(`specs/045-limite-drawdown-diario-h14/`, D1 declara a hipótese antes
de medir: reset incondicional não pode ficar preso esperando sorte).

**Resultado (`python main.py carteira_dd_diario`, 2026-09-03):**

| | Sem overlay (037) | Só volatilidade (041) | Só correlação (042) | Combinado (043) | Circuit breaker (044) | Limite diário (045) |
|---|---|---|---|---|---|---|
| Trades | 931 | 763 | 595 | 595 | 6 | **762** |
| Retorno | −20,12% | −18,16% | −16,04% | −15,98% | −0,40% | **−16,50%** |
| Drawdown | 28,66% | 23,04% | 20,74% | 20,24% | 0,57% | **22,17%** |
| Profit factor | 0,72 | 0,72 | 0,68 | 0,67 | 0,36 | **0,75** |

**Confirma a hipótese: reset por calendário não colapsa a amostra.**
762 trades — praticamente idêntico ao de "só volatilidade" (763), a
duas ordens de grandeza acima do circuit breaker (6). O mecanismo
continuou operando quase normalmente porque o reset diário garante uma
nova chance a cada ~6 candles de 4h, independente de qualquer trade ter
fechado bem. Drawdown caiu de 28,66% para 22,17% (∼23% de redução
relativa) com uma amostra grande o bastante para o número ter
significado — não é o caso degenerado de spec 044.

**Maior profit factor de todos os seis testes, incluindo o baseline.**
0,75 contra 0,72 (sem overlay) — o único mecanismo, entre os cinco
overlays de risco testados até aqui, que melhorou o profit factor em
vez de piorá-lo ou empatá-lo. Interpretação: pausar por um dia inteiro
depois de uma perda agregada grande evita reabrir exposição durante o
resto de um movimento de mercado adverso já em curso — diferente do
gate de correlação (que filtra por sobreposição espacial no instante da
entrada) e do dimensionamento (que só encolhe, nunca pausa), este
mecanismo é o único que reage à trajetória recente do patrimônio da
carteira inteira.

**Ainda reprovado** — profit factor 0,75 segue abaixo do mínimo 1,2, e
drawdown 22,17% quase o dobro do teto aceitável (10%). Não aprova H14.
Mas é o segundo mecanismo (depois do gate de correlação) a produzir uma
melhora real e não-degenerada, e o único a melhorar profit factor — bom
candidato a combinar com o gate de correlação numa spec futura, já que
ambos operam em dimensões diferentes (calendário vs. sobreposição
espacial) e nenhum dos dois, individualmente, colapsou a amostra.

**Reprodução:** `python main.py carteira_dd_diario` ·
`specs/045-limite-drawdown-diario-h14/`.

---

#### Atualização — combinação correlação + limite diário, o gate domina de novo (2026-09-03, spec 046)

Os dois únicos mecanismos com melhora real não-degenerada isolados —
gate de correlação (spec 042) e limite de drawdown diário (spec 045) —
ligados ao mesmo tempo, dimensões declaradamente ortogonais
(sobreposição espacial vs. trajetória temporal da carteira,
`specs/046-combinado-correlacao-limite-diario-h14/spec.md`).

**Resultado (`python main.py carteira_combo2`, 2026-09-03):**

| | Sem overlay (037) | Só correlação (042) | Limite diário (045) | Combinado corr+diário (046) |
|---|---|---|---|---|
| Trades | 931 | 595 | 762 | **594** |
| Retorno | −20,12% | −16,04% | −16,50% | **−15,63%** |
| Drawdown | 28,66% | 20,74% | 22,17% | **20,38%** |
| Profit factor | 0,72 | 0,68 | 0,75 | **0,68** |

**A hipótese de ortogonalidade não se confirmou como esperado — o gate
de correlação domina de novo, quase da mesma forma que dominou o
dimensionamento em spec 043.** `total_trades` do combinado (594) é
praticamente idêntico ao do gate sozinho (595), não ao do limite diário
(762) nem a algo intermediário. Mecanismo provável: o limite diário só
dispara depois de uma perda agregada grande num único dia — e boa parte
dessas perdas agregadas grandes vêm exatamente de várias posições
correlacionadas quebrando **juntas** no mesmo dia. Com o gate de
correlação já impedindo essa concentração no instante da entrada, os
dias de perda severa que disparariam o limite diário ficam raros — o
limite diário perde a maior parte de suas oportunidades de agir, não
porque as duas mecânicas competem pela mesma decisão (como
dimensionamento+correlação), mas porque o gate remove a **causa raiz**
do padrão de perda que o limite diário existe para conter. Drawdown
melhora só marginalmente sobre o gate sozinho (20,74% → 20,38%, ~1,7%
relativo) e retorno melhora um pouco mais (−16,04% → −15,63%, o melhor
retorno de todos os sete testes) — mas profit factor volta a 0,68,
perdendo o ganho que o limite diário tinha isolado (0,75).

**Ainda reprovado**, mesmo padrão dos seis testes anteriores. **Segunda
confirmação da mesma lição estrutural** (depois de spec 043): overlays
de risco que atacam consequências correlacionadas de um mesmo problema
subjacente (posições correlacionadas concentrando perda) tendem a se
sobrepor fortemente quando um deles ataca a causa direto — não importa
se a dimensão declarada parece ortogonal antes de medir. O gate de
correlação segue sendo, isoladamente, a intervenção mais eficaz medida
até aqui nesta linha de investigação.

**Reprodução:** `python main.py carteira_combo2` ·
`specs/046-combinado-correlacao-limite-diario-h14/`.

---

#### Atualização — combinação total (teto), a expectativa se confirma e fecha a linha de investigação (2026-09-03, spec 047)

Os três mecanismos não-degenerados (dimensionamento spec 041, correlação
spec 042, limite diário spec 045) ligados ao mesmo tempo — teto da
família inteira, expectativa declarada antes de medir: resultado perto
do gate de correlação sozinho, não soma aditiva
(`specs/047-combinado-total-h14/spec.md`).

**Resultado (`python main.py carteira_teto`, 2026-09-03) — todos os oito testes desta linha de investigação:**

| Overlay | Trades | Retorno | Drawdown | Profit factor |
|---|---|---|---|---|
| Sem overlay (037) | 931 | −20,12% | 28,66% | 0,72 |
| Só volatilidade (041) | 763 | −18,16% | 23,04% | 0,72 |
| Só correlação (042) | 595 | −16,04% | 20,74% | 0,68 |
| Vol + correlação (043) | 595 | −15,98% | 20,24% | 0,67 |
| Circuit breaker (044, degenerado) | 6 | −0,40% | 0,57% | 0,36 |
| Só limite diário (045) | 762 | −16,50% | 22,17% | 0,75 |
| Correlação + limite diário (046) | 594 | −15,63% | 20,38% | 0,68 |
| **Teto: vol + correlação + limite diário (047)** | **594** | **−15,56%** | **19,88%** | **0,68** |

**A expectativa se confirmou.** `total_trades` do teto (594) é
essencialmente idêntico ao do gate de correlação sozinho (595) — a
composição dos três não muda a decisão de QUAIS trades abrem além do
que a correlação já decide; dimensionamento e limite diário só
contribuem ajustes marginais (tamanho de posição e uma pausa ocasional)
por cima da mesma seleção. **Este é o melhor drawdown de toda a linha
de investigação não-degenerada: 19,88%** — pela primeira vez abaixo de
20%, mas por uma margem pequena (0,86 ponto percentual abaixo do gate
sozinho) que não muda a leitura qualitativa.

**Ainda reprovado, e por boa margem em ambos os critérios**: drawdown
quase o dobro do teto aceitável (10%), profit factor 0,68 bem abaixo do
mínimo 1,2. **Fecha a linha de investigação de overlays de risco sobre
a decisão de entrada de H14.** Oito testes, cinco mecanismos distintos
(dois espaciais/de tamanho — dimensionamento, correlação —, dois
temporais — circuit breaker, limite diário —, mais suas combinações),
e o teto medido da família inteira ainda reprova por margem
substancial. A composição de risco não resolve o problema porque o
problema não é de composição de risco: o sinal estatístico de H14 é
real (spec 036, z = +7,97) mas o profit factor por trade nunca passou
de 0,75 em nenhuma configuração testada — nenhum overlay que só decide
QUANDO/QUANTO abrir consegue consertar uma taxa de acerto por trade que
já nasce abaixo do necessário. Os próximos passos, se houver, atacam
outra parte do mecanismo — o classificador de entrada em si (por que o
profit factor por trade é baixo) ou o mecanismo de saída (take-profit
por ATR + stop trailing, nunca alterado em nenhuma das oito specs desta
linha) — não mais parâmetros ou combinações de quando entrar.

**Reprodução:** `python main.py carteira_teto` ·
`specs/047-combinado-total-h14/`.

---

#### Atualização — calibração do classificador, filtro de confiança refutado (2026-09-03, spec 055)

A linha de overlays de risco fechou (spec 047) apontando para dois
próximos passos: o classificador de entrada em si, ou o mecanismo de
saída. Esta spec ataca o primeiro, e o mais barato de medir: o
subconjunto já decidido em produção (`prob > limiar_de_decisao`,
0,3333) tem uma **cauda de alta confiança** explorável — um corte mais
estrito (menos trades, mais confiantes) que concentraria qualidade e
abriria caminho para uma variante de entrada por confiança?

**Resultado (`python main.py calibracao`, 2026-09-03, `UNIVERSO_H11`):**

| corte | n | alvo | stop | razão | supera_empate_ci95 |
|---|---|---|---|---|---|
| 0,3333 (real) | 2.486 | 968 | 1.378 | 0,7025 | **True** |
| 0,35 | 1.056 | 411 | 597 | 0,6884 | **True** |
| 0,40 | 80 | 32 | 44 | 0,7273 | **False** |
| 0,45 | 17 | 10 | 6 | 1,6667 | **True** (amostra minúscula) |
| 0,50 | 6 | 2 | 3 | 0,6667 | **False** |
| 0,55 | 1 | 1 | 0 | inf | **False** |
| 0,60 | 1 | 1 | 0 | inf | **False** |

**Hipótese refutada — não existe cauda explorável.** Entre 0,3333 e
0,35, a única faixa com amostra grande o bastante para comparar, a
razão não sobe (0,7025 → 0,6884, dentro do ruído). A partir de 0,40 a
amostra desaba (80 → 17 → 6 → 1 → 1) e a razão oscila sem padrão —
ruído amostral, não sinal crescente. O ponto em 0,45 "supera" com
`n=17`, exatamente o padrão que motivou `supera_empate_com_confianca`
existir (M9/M13): ponto estimado bom sem amostra para sustentar. Subir
o corte não troca trades ruins por bons — só descarta amostra até sobrar
ruído. A variante de entrada por confiança (filtro binário mais estrito)
está refutada; não vale a pena construí-la.

**O que isso não muda.** O subconjunto já decidido em 0,3333 continua
com razão real e significativa (0,70 > empate 0,50) — o mesmo achado de
spec 036, agora confirmado por uma medição independente (diferença de
0,3-1,1% nas contagens brutas, atribuída a detalhe de alinhamento de
índice entre scripts, não a divergência de metodologia; `research.md`
D2 documenta a reconciliação). Não testa **dimensionar** a posição pela
confiança (apostar menos nas previsões fracas em vez de descartá-las) —
mecanismo diferente de filtrar, ainda não coberto. Não testa o
mecanismo de saída (take-profit ATR + stop trailing, nunca alterado em
nenhuma das nove specs de H14 até aqui).

**M-catalog, nota lateral.** O diagnóstico ad-hoc que motivou esta spec
cometeu dois erros próprios antes de chegar ao resultado acima:
confundiu `limiar_de_empate` (razão de empate, 0,500) com
`limiar_de_decisao` (limiar de probabilidade real, 0,3333) — funções
lado a lado em `backtesting/modelo.py` com nomes parecidos — e contou
`rotulo_bruto == 0` (timeout genuíno) como `NaN` (reservado a ATR
inválido). Nenhum dos dois chegou a produzir uma conclusão publicada;
`research.md` D1 documenta ambos como parte do processo, não como
achado de instrumentação (M) — o defeito era do script de diagnóstico,
não de código do projeto.

**Reprodução:** `python main.py calibracao` ·
`specs/055-h14-calibracao-classificador/`.

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

#### Atualização — histórico estendido reverte o veredito: a margem paga (2026-09-03, spec 048)

Questão em aberto desde `specs/036-historico-estendido/` (D2 excluiu
`geometria.py` do escopo daquela spec, deliberadamente, não por
esquecimento): a margem medida em H20 aterrissava a **menos de 3% do
empate**, estreita o bastante para ser plausivelmente um artefato de
amostra pequena — o mesmo padrão que produziu o veredito original
errado de H14. `run_geometria_scan` migrado de 2.000 para 6.000 candles
(mesmo teto de spec 036), mesma regra de seleção, mesmo procedimento de
avaliação (`run_modelo_scan`/`resumo_agregado`,
`specs/048-h20-historico-estendido/`).

**Resultado (`python main.py geometria`, 2026-09-03, mesmos 12 pares):**

| | 2.000 candles (spec 028) | 6.000 candles (spec 048) |
|---|---|---|
| Geometria selecionada | tp=2,0 | tp=2,0 (mesma) |
| Razão base (todos os eventos) | 0,6223 | 0,6992 |
| Subconjunto decidido — alvo / stop | 333 (não reportado por par) | **1.675 / 1.989** |
| Razão pooled decidida | 0,7478 | **0,8421** |
| Ponto de empate | 0,750 | 0,750 |
| Razão / empate | 0,997 (abaixo) | **1,123 (acima)** |
| Supera o empate (banda de incerteza) | **Não** (z=−0,07, p=0,535) | **Sim** (z≈+3,50, p<0,001) |

**A margem não era invariante — era pequena demais para medir.** Com
3.664 desfechos (mais que o dobro dos 2.232 de spec 028), a razão
pooled subiu de 0,7478 para 0,8421 — **não caiu em direção ao empate,
subiu para além dele**, com um z-score que passou de essencialmente
zero (−0,07, exatamente no limiar) para +3,50 (p<0,001), um resultado
estatisticamente robusto, não mais borderline. A razão base (antes do
modelo decidir) também subiu, de 0,6223 para 0,6992 — o próprio sinal
subjacente ficou mais forte com mais dados, não só o subconjunto
decidido pelo modelo.

**Veredito revertido: a geometria PAGA o empate.** "Há sinal?" já era
sim (z=+4,48 em spec 028, presumivelmente mais forte ainda aqui — não
recomputado nesta spec, fora do escopo declarado). "Paga a geometria?"
muda de **Não** para **Sim**. Isto reverte o achado central de H20 —
"o sinal aterrissa no empate em duas geometrias independentes" não se
sustentou à mesma elevação de amostra que já havia corrigido H14.

**Não é aprovação operacional — é o mesmo estágio que H14 alcançou em
spec 036, antes do motor de carteira de spec 037.** Este resultado
confirma o sinal estatístico da geometria `tp=2,0`, exatamente como
spec 036 confirmou o sinal estatístico de H14 (`tp=3,0`) sem ainda
testar backtest real, custo de execução ou risco de carteira. Uma
avaliação operacional completa desta geometria — backtest real com
`ATR_TP_MULTIPLIER=2.0`, depois carteira com capital compartilhado
(mesmo padrão de spec 037) — é o próximo passo natural, não decidido
aqui.

**Reabre a linha de investigação da geometria de saída, fechada em
spec 047 do lado do risco de carteira.** A conclusão que fechou os
overlays de risco de H14 (§4.15, atualização spec 047) foi que o
gargalo é o profit factor por trade, e apontou o mecanismo de saída
como a próxima frente, não mais parâmetros de risco. Esta reversão é
exatamente essa frente — e ao contrário dos overlays de risco (oito
testes, ceiling medido, fechado), esta é uma pergunta nova, ainda não
testada de ponta a ponta.

**Reprodução:** `python main.py geometria` ·
`specs/048-h20-historico-estendido/`.

---

#### Atualização — o sinal confirmado não sobrevive ao backtest real: REPROVADA de novo (2026-09-03, spec 049)

Antes de qualquer avaliação operacional, auditoria de código encontrou
uma lacuna real: `avaliar_par` rotulava e treinava com o `tp_mult`/
`sl_mult` de `ParametrosBarreira`, mas o backtest simulado
(`ResultadoModelo.backtest`) nunca recebia esses multiplicadores —
sempre saía aos fixos de produção (3,0×ATR/1,5×ATR), independente da
geometria declarada. Invisível para H14 (default coincide com
produção); real para H20 (`tp=2,0`): o "sinal confirmado" de spec 048
era sobre rótulos futuros de preço, nunca testado contra uma posição
simulada que realmente sai a 2×ATR. Corrigido
(`specs/049-h20-backtest-real/`) — retrocompatível por construção,
regressão confirma H14/H17 byte a byte inalterados.

**Resultado (`python main.py geometria`, 2026-09-03, backtest real por
par, `tp=2,0` de fato simulado):**

| Par | Trades | Retorno | Drawdown | Profit factor | Veredito |
|---|---|---|---|---|---|
| BTC/USDT | 136 | −6,14% | 7,48% | 0,52 | reprovado |
| ETH/USDT | 78 | −2,72% | 4,07% | 0,67 | reprovado |
| SOL/USDT | 54 | −0,97% | 2,57% | 0,85 | reprovado |
| **LINK/USDT** | 51 | **+1,09%** | 1,96% | **1,23** | **aprovado** |
| BCH/USDT | 70 | −5,64% | 6,99% | 0,42 | reprovado |
| TRX/USDT | 268 | −5,36% | 5,56% | 0,61 | reprovado |
| XRP/USDT | 63 | −0,56% | 2,71% | 0,92 | reprovado |
| AVAX/USDT | 32 | −0,90% | 3,24% | 0,79 | reprovado |
| LTC/USDT | 68 | −2,71% | 4,11% | 0,59 | reprovado |
| DOT/USDT | 33 | −0,62% | 2,79% | 0,86 | reprovado |
| ADA/USDT | 34 | +0,51% | 1,64% | 1,11 | reprovado |
| ATOM/USDT | 53 | −0,01% | 1,82% | 1,00 | reprovado |

**11 de 12 pares reprovados; só LINK/USDT aprova.** 940 trades no
total, profit factor entre 0,42 e 1,23 — a maioria bem abaixo de 1,
apesar de a razão pooled decidida (0,8421) superar o empate (0,750)
com folga estatística robusta (z≈+3,50). **A confirmação estatística
de rótulo e a lucratividade real divergem.**

**Por que divergem — três candidatos, nenhum excludente.** (1) A
geometria `tp=2,0` tem payoff de 2:1,5 (≈1,33:1) contra 3:1,5 (2:1) de
`tp=3,0` — o mesmo custo fixo de execução (`BACKTEST_FEE_RATE`/
`BACKTEST_SLIPPAGE_PCT`) consome uma fração maior de um alvo mais
próximo. (2) O motor real usa **stop trailing** (sobe a cada novo
máximo), diferente da barreira estática usada para rotular — um trade
que "tocaria o alvo" na rotulagem pode ser fechado antes pelo trailing
no motor real. (3) A confirmação estatística é sobre a amostra
**pooled** (3.664 eventos); o backtest real roda **por par**, com
amostras dez vezes menores (32-268 trades) — mais suscetível a ruído
por par mesmo com o efeito agregado sendo real. Nenhuma das três foi
isolada nesta spec — ver "O que isto não decide" abaixo.

**Padrão já visto em H21 (lead-lag): sinal direcional real que o custo
de giro consome antes de virar retorno.** Aqui o mecanismo é análogo,
mas do lado da geometria de saída, não da frequência de sinal — mais
uma confirmação de que "há sinal estatístico" e "sobrevive à execução
real" são perguntas diferentes, e a segunda é a que decide aprovação.

**Veredito: REPROVADA (2ª reversão).** A trajetória completa de H20
agora tem três estágios: REPROVADA (2.000 candles, margem no empate) →
sinal confirmado (6.000 candles, spec 048, margem resolvida por
rótulo) → **REPROVADA de novo** (spec 049, o mesmo sinal não sobrevive
ao backtest real). Cada estágio testou uma pergunta genuinamente
diferente e nenhum invalida o anterior — a estatística de rótulo de
spec 048 continua correta, só não é suficiente para aprovação
operacional.

**O que isto não decide.** Não isola qual dos três mecanismos
candidatos (custo, trailing, amostra por par) domina — uma spec futura
poderia medir o backtest sem custo (`retorno_sem_custo_modelo`, já
propagado pela mesma correção) para isolar o efeito do custo de
execução isoladamente, mesmo padrão já usado em H21 (E6, custo de
giro). Não decide se `tp=2,5`/`tp=3,0` (também elegíveis nesta
rodada, tabela acima) teriam resultado melhor — a regra de spec 028
seleciona a menor `tp` elegível por desenho (evita otimizar sobre o
conjunto), então testá-las seria uma pergunta nova, não um ajuste desta.

**Reprodução:** `python main.py geometria` ·
`specs/049-h20-backtest-real/`.

---

#### Atualização — custo de execução isolado: é o mecanismo dominante (2026-09-03, spec 050)

Primeiro dos três candidatos de spec 049 testado — custo de execução —
reusando o método E6 já usado em H10/H21: reexecutar os mesmos sinais
com taxa e slippage zerados (`retorno_sem_custo_modelo`, já calculado
por `avaliar_par` a cada chamada) e comparar contra o resultado com
custo real de spec 049. Zero backtest novo.

**Resultado (`python main.py geometria`, 2026-09-03, mesmos 12 pares):**

| Par | Com custo | Sem custo | Vira positivo? |
|---|---|---|---|
| BTC/USDT | −6,14% | −1,82% | não |
| ETH/USDT | −2,72% | −0,03% | quase |
| SOL/USDT | −0,97% | **+0,54%** | **sim** |
| LINK/USDT | +1,09% | +2,88% | já era |
| BCH/USDT | −5,64% | −3,65% | não |
| TRX/USDT | −5,36% | **+2,39%** | **sim** |
| XRP/USDT | −0,56% | **+1,19%** | **sim** |
| AVAX/USDT | −0,90% | +0,04% | sim (marginal) |
| LTC/USDT | −2,71% | −0,80% | não |
| DOT/USDT | −0,62% | **+0,30%** | **sim** |
| ADA/USDT | +0,51% | +1,51% | já era |
| ATOM/USDT | −0,01% | **+1,46%** | **sim** |

**O custo de execução é o mecanismo dominante, não só um dos três
candidatos.** Sem custo, **8 de 12 pares têm retorno positivo** (contra
2 de 12 com custo) e **7 de 12 superam o buy-and-hold do próprio par**
(contra 1 aprovado em `evaluate_approval()` com custo, spec 049). Seis
pares — SOL, TRX, XRP, AVAX, DOT, ATOM — trocam de sinal (negativo para
positivo) só ao remover o custo. Os únicos três que continuam negativos
mesmo sem custo (BTC, BCH, LTC) são exatamente os de maior volume/liquidez
do universo — consistente com o payoff apertado (`tp=2,0`, 2:1,5) tornando
a estratégia sensível a custo em qualquer par, mas insuficiente para
explicar por si só os três que continuam negativos.

**Fecha o candidato #1 (payoff/custo) como explicação primária — não
descarta os outros dois, mas reduz sua prioridade.** A hipótese de
spec 049 de que o payoff mais apertado de `tp=2,0` tornaria o custo
fixo proporcionalmente mais pesado está diretamente confirmada pelos
números: a mesma estratégia, mesmos sinais, sem custo de execução,
teria sido lucrativa e batido o buy-and-hold na maioria dos pares. Os
candidatos #2 (trailing stop divergindo da barreira estática) e #3
(amostra por par) continuam sem teste, mas com prioridade reduzida —
a divergência já tem uma explicação dominante medida, não hipotética.

**Não aprova H20 nem reverte o veredito REPROVADA.** `evaluate_approval()`
mede o resultado com custo real, como deve ser — o bot nunca opera sem
pagar taxa e slippage. O achado é sobre MECANISMO, não sobre veredito:
o sinal estatístico de rótulo (spec 048) é real, a estratégia
resultante teria edge genuíno num mundo sem custo, mas o custo de
execução real consome a maior parte dessa vantagem antes dela virar
retorno — o mesmo padrão de H21, agora confirmado por medição direta em
vez de inferido por analogia.

**Reprodução:** `python main.py geometria` ·
`specs/050-h20-custo-de-execucao/`.

---

#### Atualização — custo decomposto: taxa domina, não slippage — fecha a via de execução mais barata (2026-09-03, spec 051)

`USE_LIMIT_ORDERS` (produção, `execution/order_manager.py`) não é
simulável com dados históricos — sem order book do passado, mesma
limitação que já força `REAL_SLIPPAGE_ENABLED=false` em `python main.py
replay`. O que é testável: decompor o custo já isolado em spec 050
(taxa e slippage juntos) nos dois componentes independentes, reusando
`simulate_backtest(fee_rate=..., slippage_pct=...)` já existente —
zero mecânica nova (`specs/051-h20-decomposicao-custo/`).

**Resultado (`python main.py geometria`, 2026-09-03, mesmos 12 pares):**

| Par | Com custo | Sem slippage | Sem taxa | Sem custo |
|---|---|---|---|---|
| BTC/USDT | −6,14% | −4,56% | −3,42% | −1,82% |
| ETH/USDT | −2,72% | −1,61% | −1,16% | −0,03% |
| SOL/USDT | −0,97% | −0,54% | +0,11% | +0,54% |
| LINK/USDT | +1,09% | +1,84% | +2,11% | +2,88% |
| BCH/USDT | −5,64% | −5,05% | −4,24% | −3,65% |
| TRX/USDT | −5,36% | −3,01% | −0,00% | +2,39% |
| XRP/USDT | −0,56% | −0,07% | +0,70% | +1,19% |
| AVAX/USDT | −0,90% | −0,62% | −0,26% | +0,04% |
| LTC/USDT | −2,71% | −2,15% | −1,35% | −0,80% |
| DOT/USDT | −0,62% | −0,36% | +0,04% | +0,30% |
| ADA/USDT | +0,51% | +0,83% | +1,20% | +1,51% |
| ATOM/USDT | −0,01% | +0,40% | +1,05% | +1,46% |

**Taxa domina slippage nos 12 de 12 pares, sem exceção.** Removendo só
o slippage, **3 de 12** pares ficam positivos (LINK, ADA, ATOM) —
praticamente o mesmo de com custo total (2/12). Removendo só a taxa,
**6 de 12** ficam positivos (SOL, LINK, XRP, DOT, ADA, ATOM), TRX
essencialmente no zero. Em todo par, o efeito de remover a taxa é maior
que o de remover o slippage — em TRX (268 trades, o par de maior giro)
por uma margem enorme (5,36pp contra 2,35pp), consistente com taxa
sendo cobrada por operação: mais giro, mais taxa acumulada.

**Fecha a via de execução mais barata como solução — e por um motivo
específico.** "Sem slippage" é o teto otimista do que `USE_LIMIT_ORDERS`
entregaria (ordens limit só afetam a ENTRADA em produção, nunca a
saída/stop, que precisa de execução imediata) — mesmo nesse cenário
generoso, só 3/12 pares aprovam. E a taxa (`BACKTEST_FEE_RATE`), o
componente que de fato domina, é cobrada pela corretora sobre o valor
da ordem — **não muda com o tipo de ordem** neste projeto (não há
desconto maker/taker modelado). Um método de execução mais barato não
resolveria H20 mesmo no melhor caso possível.

**Terceira e última atualização desta linha.** H20 termina com o
mecanismo totalmente diagnosticado: sinal de rótulo real (spec 048) →
não sobrevive ao backtest real (spec 049) → custo domina a divergência
(spec 050) → dentro do custo, taxa domina slippage, e nenhuma melhoria
de execução plausível resolveria (spec 051). Veredito continua
REPROVADA. Os candidatos #2 (trailing stop) e #3 (amostra por par) de
spec 049 seguem sem teste, agora com prioridade ainda mais baixa — o
mecanismo dominante já está totalmente explicado por custo, e dentro
de custo, por taxa especificamente.

**Reprodução:** `python main.py geometria` ·
`specs/051-h20-decomposicao-custo/`.

**Verificação final — `BACKTEST_FEE_RATE` contra a taxa real (2026-09-03).**
Confirmado via fee schedule oficial da Binance: contas padrão (VIP0,
sem pagar taxa em BNB) pagam 0,10% maker e taker no spot — exatamente
o valor já usado (`BACKTEST_FEE_RATE=0.001`). O desconto de 25% por
pagar em BNB (→0,075%) exigiria a opção ativada na conta; confirmado
com o usuário que **não está ativada** na conta real do bot. Nenhuma
mudança de código — a suposição de custo já era exata, não
conservadora nem otimista. Fecha definitivamente a hipótese de que o
valor de `BACKTEST_FEE_RATE` estivesse superestimando o custo real.

---

### 4.17 H21 — Lead-lag BTC para altcoins

**Origem.** Primeira hipótese deste registro originada de uma busca
deliberada por literatura acadêmica real (não intuição interna) — pedido
explícito do usuário após H14 fechar reprovada em risco de carteira
(spec 037): "faça deep search na internet e procure novas hipóteses".

**Tese.** O retorno do BTC no mesmo candle de 4h lidera o retorno de
altcoins menos líquidas — causalidade de Granger unidirecional
documentada em "Price Transmission from Bitcoin to Altcoins: High-Frequency
Evidence and Implications for Trading Strategy" (*Asia-Pacific Financial
Markets*, Springer 2026). Estruturalmente distinta de H7 (momentum do
próprio par) e do oposto de H10 (aposta em reversão, não continuação).

#### A defasagem foi medida — e um erro de formulação corrigido — antes de qualquer código

`research.md` da spec 038 registrou, sobre 2.000 candles reais de 4h e os
12 pares de `UNIVERSO_H11`, a correlação entre o retorno defasado do BTC
e o retorno futuro de cada altcoin, para 7 defasagens × 3 horizontes (21
combinações). A mais forte e mais consistente: retorno de BTC no mesmo
candle prevendo o candle seguinte da altcoin — correlação média **0,0445**,
positiva em **100%** dos 11 pares. Fraca em magnitude (explica bem menos
de 1% da variância), mas o sinal é robusto entre pares.

A primeira redação da spec descrevia a fórmula do sinal com uma defasagem
extra por engano (`close[t-1]/close[t-2]` em vez de `close[t]/close[t-1]`)
— capturado e corrigido em `research.md` (D1) antes de `/speckit-plan`
prosseguir, com um teste de regressão dedicado (`test_lead_lag.py`,
T004) para impedir que o erro voltasse silenciosamente.

#### Resultado: 0 de 11 aprovados

Sinal binário (BTC subiu no candle ou não, sem limiar de magnitude — D2),
saída por take-profit ATR + stop trailing (mesmo mecanismo genérico de
toda avaliação deste registro), 6.000 candles de 4h, `UNIVERSO_H11` menos
BTC/USDT:

| | Valor |
|---|---|
| Pares avaliados | 11 |
| Aprovados | **0** |
| Reprovados | **11** |
| Profit factor > 1,0 | **0 / 11** |
| Superam o próprio buy-and-hold | 6 / 11 |
| Trades por par | 692–743 |
| Retorno por par | −9,4% a −48,0% |

**O sinal dispara demais para o custo que carrega.** Com ~700 trades por
par sobre ~1.786 candles de teste, o sinal fica positivo (BTC em alta)
perto de 40% dos candles — a mesma frequência que a correlação fraca já
sugeria (0,0445 não filtra quase nada). Profit factor no melhor caso
(LINK/BCH/TRX, 0,82–0,83) já está abaixo de 1,0 antes de qualquer
critério de aprovação — o custo de giro (taxa + slippage) sobre centenas
de trades supera qualquer vantagem que a correlação carregava.

**"Superar o buy-and-hold" aqui não é sinal de força.** Em vários pares
(DOT −90%, ATOM −87%, AVAX −85%) o buy-and-hold caiu tanto que qualquer
estratégia com exposição parcial "supera" por perder menos numa queda
geral — mesmo padrão de leitura já registrado em H11 (4h/333 dias de
queda inflava a taxa de "supera buy-hold" sem indicar vantagem real).

**Veredito: REPROVADA.** A direção do efeito é real (correlação positiva
consistente em 100% dos pares, fundamentação acadêmica sólida) — mas na
frequência em que o sinal binário dispara, o custo de transação consome a
vantagem antes dela virar retorno. Diferente de H14, aqui não há uma
"barra estatística que quase se paga" — profit factor abaixo de 1,0 em
todos os 11 pares é reprovação limpa, não marginal.

**O que isso não decide.** Não é evidência de que o lead-lag BTC→altcoins
não existe — é evidência de que operá-lo com um sinal binário sem filtro
de magnitude, entrando a cada candle positivo do BTC, negocia rápido
demais para o efeito que carrega. Um filtro de magnitude (só entrar
quando o retorno do BTC excede um limiar, reduzindo a frequência de
trades) poderia mudar o resultado — mas exigiria sua própria medição
antes de declarar o limiar (mesmo princípio de D2), e seria uma hipótese
nova, não um ajuste desta.

**Reprodução:** `python main.py leadlag` · `specs/038-lead-lag-btc-altcoins/`.

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
| M14 | `evaluate_approval()` trata amostra abaixo do mínimo como motivo de reprovação, não como categoria própria | Medido em H10 (spec 039, 2026-09-02): validação com 6 trades (abaixo do mínimo de 10) devolveu `"reprovado"` — `"apenas 6 trades... "` listado ao lado de `"profit factor abaixo do mínimo"` como se fossem evidência do mesmo tipo. Confirmado por um segundo caso em H14/circuit breaker (spec 044, 2026-09-03): 6 trades e profit factor 0,36 juntos no mesmo `"reprovado"`. `classificar_avaliacao()` (`backtesting/modelo.py`, usada por H14) já resolve isso: devolve `"inconclusivo"` explicitamente quando `total_trades < EDGE_MIN_TRADES`, **antes** de avaliar profit factor ou drawdown — mas `evaluate_approval()` (`backtesting/approval.py`), compartilhada por `grid`/`carteira`/`leadlag`/`pairs`, não tinha essa distinção | **Corrigido** (2026-09-03) — checagem de amostra movida para antes de qualquer outro critério, retorno antecipado com `"inconclusivo"` e motivo único, mesmo padrão de `classificar_avaliacao()`. Auditoria de vereditos publicados afetados: ver nota abaixo |
| M15 | Contagem bruta de observações (`N ≥ 30`) tratada como amostra utilizável, sem checar se as observações passaram pelo próprio filtro de qualidade do instrumento | Medido em H15 (campanha real, 2026-09-03): 615 observações, `estado_agregado = "amostra suficiente"` (41 por combinação) — mas 607 (98,7%) vieram `latencia_alta`, porque a leitura das 6 corretoras é sequencial e só uma combinação (as duas adjacentes na ordem de leitura) fica abaixo do teto de 2.000ms. 14 de 15 combinações nunca tiveram uma comparação válida, e nunca teriam, não importa quantos ciclos rodassem — limitação estrutural do instrumento, não de tempo decorrido | **Corrigido** (2026-09-03, `specs/053-h15-leitura-paralela/`) — `medir_ciclo` lê as 6 corretoras via `ThreadPoolExecutor` em vez de sequencial. Validado com ciclo real: 6 de 15 combinações válidas (`sem_oportunidade`) num único ciclo, contra 1 de 15 em 615 observações antes da correção. Latência residual entre algumas corretoras específicas (`gate` consistentemente mais lenta) permanece — a correção elimina o viés estrutural da ordem de leitura, não garante latência zero |

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

**M14 é M9 outra vez, num lugar diferente do código.** M9 foi corrigido em
`classificar_status`/`classificar_avaliacao` (`backtesting/horizonte.py`/
`modelo.py`) — mas `evaluate_approval()` (`backtesting/approval.py`), a
função de aprovação mais usada do projeto, nunca recebeu a mesma correção.
O defeito ficou latente até H10 (spec 039) produzir uma validação com
amostra pequena o bastante para expor.

**Auditoria de vereditos publicados afetados (2026-09-03, mesmo dia da
correção).** Busca por toda menção a amostra abaixo do mínimo neste
registro: H10 (spec 039, E3 e a validação de 6 trades) já estava rotulada
`INCONCLUSIVA` no quadro-resumo (§4.1) e na narrativa (§4.11,
"Por que INCONCLUSIVA e não REPROVADA") — a leitura humana já havia
corrigido manualmente para o mesmo veredito que a função corrigida produz
agora, então nada muda no texto publicado. H17 (on-chain, primeira
execução) usa `classificar_avaliacao()`, não `evaluate_approval()` — já
tinha a distinção desde antes, também sem mudança. H18 (grid) e H21
(lead-lag) reprovam por profit factor/drawdown genuínos sobre amostras
grandes (centenas de trades), não por amostra insuficiente — fora do
alcance do defeito. **Único resultado publicado cujo texto mudou de fato:
H14/circuit breaker isolado (spec 044, §4.15)**, atualizado no mesmo
commit da correção.

**M12 tem procedência diferente das demais.** Não veio de confrontar resultado
com predição, e sim de um **teste de fumaça em dado real** rodado antes da
varredura. A guarda que o detectou (`FR-007`, buy-and-hold ancorado) tinha sido
escrita para outro propósito — verificar que as janelas cobriam o mesmo período
— e capturou uma causa que ninguém havia previsto. É argumento a favor de
guardas declaradas antes de existir suspeita: elas pegam o que não se pensou em
procurar.

**M15 é da mesma família de M12** — não veio de comparar resultado contra
predição, veio de rodar a campanha real e olhar os dados brutos em vez de
confiar só no rótulo agregado (`estado_agregado`) que o próprio código já
calculava. A contagem "suficiente" existia; a checagem de que a contagem
media a coisa certa não. Mesma lição: um número que passa no critério
declarado ainda merece ser olhado por dentro antes de virar conclusão.

---

## 6. Hipóteses não testadas

Fila de avaliação, ordenada por razão evidência-publicada / custo-de-implementação.

### 6.1 Prioridade alta

*(H10 avaliada em 2026-09-01 — ver seção 4.11. Status: inconclusiva, requer reavaliação com histórico mais longo.
Reavaliada em 2026-09-02 (`specs/039-reavaliar-h10-pairs-trading/`): seletor
corrigido (poder 20%→60%), mas segue **inconclusiva** — só 6 trades na
validação, abaixo do mínimo de 10 (achado M14, §5). Universo amplo testado em
2026-09-03 (`specs/052-h10-universo-amplo/`, 12→22 pares de histórico
completo): **refutado como causa** — validação continua com exatamente 6
trades nos dois universos. Diagnóstico direto (sem tocar parâmetro) mediu a
causa real: só 4 ciclos de reseleção em ~2.300 candles de validação, 6
oportunidades de entrada no total — o mesmo número dos trades. Reseleção
desacoplada da formação e testada a cada 120 candles (`meia_vida_max`,
`specs/054-h10-reselecao-frequente/`): validação foi para 10 trades, primeiro
veredito não bloqueado por amostra — **REPROVADA**, profit factor 0,15,
drawdown 16,61%. Status final.)*

*(H11 avaliada em 2026-09-01 — ver seção 4.12. Status: reprovada em 4h e 1d; inconclusiva em 1w por limitação estrutural de histórico. Reavaliada com histórico estendido em 2026-09-02
(`specs/036-historico-estendido/`): veredito mantido, fração inconclusiva cai de 27% para 2-8%.)*

*(H12 avaliada em 2026-09-01 — ver seção 4.13. Status: inconclusiva. **Movida
para 6.4**: depende de uma estratégia lucrativa existir antes.)*

*(H13 avaliada em 2026-09-01 — ver seção 4.14. Status: **reprovada**. 96
combinações, 1 melhora, abaixo do que o acaso produziria; efeito mediano
negativo em três de cada quatro combinações avaliadas.)*

*(H14 avaliada em 2026-09-01 — ver seção 4.15. Status original: **insuficiente**.
Reavaliada com histórico estendido em 2026-09-02 (`specs/036-historico-estendido/`):
o teste que definia `insuficiente` passou a responder **sim** — z = +7,97 contra
+0,50. Aprovação de carteira testada em 2026-09-02
(`specs/037-motor-carteira-h14/`): **reprovada** — drawdown de carteira 28,66%
(5x o maior drawdown isolado por par, 5,54%), profit factor 0,72. Sinal
estatístico continua real; não sobrevive a capital compartilhado entre os
12 pares. Linha de overlays de risco (specs 040-047, 2026-09-03): universo
amplo refutado; dimensionamento, correlação, circuit breaker (degenerado),
limite de drawdown diário e suas combinações medidos isolados e no teto —
melhor caso (vol+correlação+limite diário) 19,88% de drawdown, profit
factor 0,68, ainda reprovado por margem substancial. Linha fechada: o
problema é o profit factor por trade, não a composição de risco — ver
§4.15, atualização spec 047.)*

*(H20 avaliada em 2026-09-01 — ver seção 4.16. Status original: **reprovada**.
Tese refutada por medição; o sinal aterrissava no ponto de empate em duas
geometrias independentes. Revertida com histórico estendido em 2026-09-03
(`specs/048-h20-historico-estendido/`): mesma elevação de amostra que já
havia corrigido H14 (spec 036) — razão pooled decidida 0,7478→0,8421, razão
sobre empate 0,997→1,123, z=−0,07→+3,50, sinal de rótulo confirmado. Testada
contra o backtest real na mesma sessão (`specs/049-h20-backtest-real/`,
depois de corrigir uma lacuna real onde o backtest simulado nunca recebia a
geometria usada para rotular): **REPROVADA de novo** — 11/12 pares
reprovados, profit factor 0,42-1,23. O sinal de rótulo é real; não sobrevive
a custo de execução/trailing stop. Trajetória final: reprovada → sinal
confirmado → reprovada, cada estágio testando uma pergunta diferente.)*

**H15 — Arbitragem entre exchanges** — *campanha real rodada, achado de
instrumento encontrado (`specs/029-arbitragem-entre-corretoras/`,
2026-09-03)*

**Campanha real (2026-09-03, 14:52–15:32, 40 ciclos, `BTC/USDT`).** 615
observações, 41 por combinação de corretoras — `estado_agregado` =
"amostra suficiente" pela contagem bruta. Mas a contagem esconde um
problema real: **607 de 615 (98,7%) vieram classificadas
`latencia_alta`** (intervalo entre as duas leituras acima do teto de
2.000ms — média medida 11.431ms, até 30.324ms no pior caso) — a leitura
das seis corretoras é **sequencial**, então o intervalo entre ler a
primeira e a última corretora do ciclo já ultrapassa o teto sozinho.
Das 15 combinações de corretoras possíveis, **só uma (kucoin×okx)**
ficou abaixo do teto alguma vez — porque são as únicas duas adjacentes
na ordem fixa de leitura (`CORRETORAS = (binance, bybit, okx, kucoin,
gate, kraken)`). As outras 14 combinações nunca tiveram uma única
comparação válida em 615 tentativas, e **nunca teriam**, não importa
quantos ciclos rodassem — a limitação é estrutural do instrumento
(leitura sequencial), não de tempo decorrido.

**Os poucos dados válidos são negativos.** As 2 observações
`sem_oportunidade` (kucoin×okx, intervalo 1969-1981ms, dentro do teto)
tiveram diferencial líquido −0,0025% e −0,0024% — negativo, não perto
do empate. As 6 `profundidade_insuficiente` (kraken×gate, nas duas
direções) nunca chegaram nem a medir diferencial — o livro de ofertas
não comporta US$ 10.000 na profundidade necessária. **Zero
observações, entre as 615, classificaram `oportunidade`.**

**Achado de instrumento (M15, ver §5).** A campanha "completou" pela
contagem bruta declarada (`N ≥ 30` por combinação), mas 14 de 15
combinações nunca produziram uma comparação que a própria checagem de
latência considerasse confiável — o "amostra suficiente" do relatório é
tecnicamente correto e ao mesmo tempo enganoso, porque a amostra
utilizável de verdade é muito menor que 615. Corrigir exigiria ler as
seis corretoras **em paralelo** (ex.: `asyncio`/threads), não mais
ciclos sequenciais — mudança de instrumento, não mais tempo passando.

**Leitura honesta do que já dá para dizer.** Nos dados que passaram
pela checagem de latência (9 de 615, 1,5%), nunca houve oportunidade e
o diferencial foi consistentemente negativo — consistente com a medição
preliminar de um único ciclo (+0,0203% bruto, uma ordem de grandeza
abaixo do custo mínimo de 0,200%). Não é um veredito formal (a spec
declara que este instrumento nunca produz aprovado/reprovado, FR-010) —
mas a evidência disponível, ainda que pequena, aponta na mesma direção
que a medição preliminar já apontava.

**M15 corrigido no mesmo dia (`specs/053-h15-leitura-paralela/`).**
`medir_ciclo` passou a ler as seis corretoras em paralelo
(`ThreadPoolExecutor`, I/O de rede libera o GIL, threads bastam sem
`asyncio`). Validado com um ciclo real: **6 de 15 combinações válidas**
num único ciclo — antes, só 1 de 15 tinha ficado válida em 615
observações inteiras. A limitação estrutural (viés da ordem fixa de
leitura) está corrigida; latência residual específica de algumas
corretoras (`gate`, consistentemente mais lenta que as demais) persiste
e é uma característica real da rede, não um defeito de instrumento.
**Segunda campanha (2026-09-03, instrumento corrigido, 40 ciclos, 630
novas observações).** Salto real na taxa de validade: **42% válidas**
(266 de 630), contra 1,5% na primeira campanha (instrumento
sequencial). **6 das 15 combinações já passam de 30 observações
válidas**: kucoin×okx (43), binance×okx (42), kraken×kucoin (41),
kraken×okx (39), binance×kucoin (38), binance×kraken (35) — amostra
suficiente de verdade, não só pela contagem bruta.

**Mas 5 das 15 continuam em zero, mesmo com o instrumento corrigido**:
todas as que envolvem `gate` (exceto `gate×kraken`, 6 válidas, e
`bybit×gate`, 8) e `bybit×kucoin`/`bybit×kraken` — 83 tentativas cada,
zero válidas. Diferente do defeito original (viés estrutural da ORDEM
de leitura, já corrigido), isto é consistente com uma característica
real de rede: `gate` responde consistentemente mais devagar que as
outras cinco corretoras a partir desta VPS, e paralelizar reduz o
atraso RELATIVO entre corretoras rápidas entre si, mas não resolve uma
corretora que é lenta em termos absolutos — ela chega tarde não
importa com quem for comparada.

**Evidência agregada agora bem mais robusta: 268 observações válidas
no total (9→268), zero oportunidades, zero diferenciais positivos.**
Diferencial líquido variando de −0,0057% a −0,0018%, média −0,0035% —
consistentemente negativo em toda a amostra válida acumulada até
aqui, não mais um punhado de pontos. Ainda não é veredito formal (a
spec nunca calcula aprovado/reprovado, FR-010) — mas a base de
evidência real, não mais preliminar, aponta na mesma direção desde o
início: sem oportunidade de arbitragem líquida nas seis corretoras
públicas testadas.

*Diferente de H1–H14/H20: não é retrotestável.* Corretoras não publicam
histórico de livro de ofertas — o veredito exige uma campanha de amostragem
ao vivo, não uma única execução. `python main.py arbitragem [PAR]` mede um
ciclo (seis corretoras, `BTC/USDT`, US$ 10.000/perna) e persiste em
`data/arbitragem.jsonl`; o veredito aguarda `N ≥ 30` observações por
combinação de corretoras — tempo passando, não código.

**Medição preliminar registrada antes da campanha** (research.md da spec):
maior diferencial **bruto** medido +0,0203%, contra custo mínimo de execução
de 0,200% — uma ordem de grandeza abaixo. Não é o veredito, mas reformula o
que a campanha precisa encontrar: não um diferencial ligeiramente acima do
custo, e sim um **dez vezes maior** que o observado.

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

**H17 — Sinais on-chain** — *avaliada em 2026-09-02, status
**insuficiente*** (`specs/033-fonte-dados-onchain/`,
`specs/034-sinais-onchain/`, reavaliada com histórico estendido em
`specs/036-historico-estendido/`). Única das quatro hipóteses de
prioridade baixa em que infraestrutura era obstáculo removível —
construída (`data/onchain.py`, fonte pública `api.blockchain.info`, sem
chave, só Bitcoin). Atributo declarado antes de medir (D1, research.md da
spec 034): variação de 7 dias da MA7 de endereços únicos ativos
(`onchain_addr_growth_7d`). Colinearidade contra os 5 atributos de H14
medida e abaixo do limiar (máxima 0,304, `atr_ratio` — limiar 0,80): o
atributo sobrevive à checagem.

**Primeira execução (2000 candles, 333 dias): inconclusiva** — a linha de
base de regras teve só 7 operações na janela de teste, abaixo do mínimo de
10. Não era problema do atributo nem da amostra rotulada (1.951 eventos,
ordens de grandeza acima do mínimo de treino) — era a estratégia de regras
operando pouco nesse período específico de BTC-only.

**Reavaliada com histórico estendido** (6.000 candles de 4h, ~2,7 anos,
spec 036): linha de base de regras passou a ter amostra suficiente
(`n_treino`=4.142, `n_teste`=1.786 — 3x o anterior). Resultado
**conclusivo**: razão de chances no subconjunto decidido **0,372 sem
on-chain, 0,370 com on-chain** — diferença de 0,002, dentro do ruído.
Nenhuma das duas versões supera a razão de empate de 0,500 (mesmo critério
de H14) — estado `insuficiente` para as duas: sinal detectável (distinto
do embaralhado), mas que não paga a barreira. **O atributo on-chain não
mudou o resultado em nenhuma direção** — nem ajudou, nem atrapalhou.

**Comparação isolada BTC/USDT** (mesmo par, mesmo período, 5 atributos de
H14 vs 5 + on-chain; nunca comparado contra o resultado pooled de 12 pares
que H14 publicou) confirma, de forma limpa, que a variação de endereços
ativos não carrega informação adicional além do que os 5 atributos
técnicos já capturam — consistente com a leitura da literatura já
registrada (§6.3): sinal on-chain nascente, aqui medido como
indistinguível de ruído para este atributo específico.

**O que isso não decide.** Não é veredito sobre "sinais on-chain" em
geral — é sobre `onchain_addr_growth_7d` especificamente, o único atributo
declarado (FR-001, spec 034: um só, para não abrir busca de atributos).
Outro atributo on-chain (ex.: hash rate) seria uma hipótese nova, não uma
reinterpretação desta.

**H18 — Grid trading com gestão de cauda** — *avaliada em 2026-09-02, status
**reprovada*** (`specs/035-grid-trading/`). Primeira das quatro hipóteses de
prioridade baixa medida de verdade em vez de julgada só por raciocínio — a
objeção original ("sem gestão de cauda") foi incorporada como requisito
central, não descartada: a grade só abre em regime `"sideways"` (ADX já
calculado) e liquida tudo a mercado quando o regime vira `"trending"`.
Motor de métricas e critério de aprovação **reusados sem alteração**
(`Trade`/`BacktestResult`/`evaluate_approval`/`edge_score`, mesmos de
qualquer outra avaliação deste registro).

**Resultado sobre `UNIVERSO_H11`** (12 pares, 2000 candles de 4h): **0
aprovados, 12 reprovados**. Profit factor entre 0,08 e 0,35 em todos os
pares, drawdown convergindo para ~90% em todos — inclusive TRX/USDT, cujo
buy-and-hold no período foi de +0,32% (praticamente parado), a grade ainda
perdeu 13,40% com 89,75% de drawdown. A convergência do drawdown para a
mesma faixa independente do desempenho do par embaixo é o que aponta para
um mecanismo estrutural, não para "o mercado caiu".

**O mecanismo, isolado por par** (BTC/ETH/TRX): trades de round-trip normal
(`exit_reason="grid"`) têm PnL médio pequeno e ora positivo ora levemente
negativo (BTC +0,12, ETH +0,26, TRX −0,05, por trade de ~US$100) — a
captura de oscilação funciona, marginalmente. Mas as liquidações forçadas
por mudança de regime (`exit_reason="regime mudou para trending"`) têm PnL
médio **6 a 30 vezes pior** (BTC −3,85, ETH −3,32, TRX −1,60) e respondem
por ~25-30% de todos os trades. **A gestão de cauda existe e dispara — só
que tarde demais**: ADX é um indicador de confirmação de tendência já
formada (calculado sobre uma janela móvel), não de antecipação — no
momento em que cruza o limiar, o preço já se moveu o suficiente para que a
liquidação forçada aconteça com prejuízo maior que várias rodadas de lucro
normal já acumularam.

**O que isso não decide.** Não é evidência de que nenhuma gestão de cauda
funciona para grid — é evidência de que **esta gestão de cauda específica
(ADX, reativa)** chega tarde. Um filtro antecipatório (ex.: volatilidade
implícita, ou um stop de preço absoluto por nível em vez de por regime)
poderia mudar o resultado — mas isso seria uma hipótese nova, não um ajuste
de parâmetro sobre esta (o número de níveis e a fonte das bandas já estavam
declarados antes de medir, `research.md` da spec 035). Fica registrado
aqui, não reaberto como spec nova sem uma hipótese de mecanismo diferente
declarada primeiro.

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
