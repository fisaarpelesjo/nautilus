# Roadmap

Este roteiro organiza as proximas melhorias do bot por impacto na chance de lucro real e reducao de risco. A prioridade nao e adicionar mais sinais rapidamente; e criar um processo confiavel para provar se uma estrategia tem vantagem antes de considerar `TRADING_MODE=live`.

O projeto ja possui uma base importante: backtest com taxas e slippage, metricas como profit factor/drawdown/Sharpe, otimizador de parametros, analise de `data/trades.csv`, selecao dinamica de pares, blacklist, paper mode, persistencia de estado e limites basicos de risco. Os itens abaixo focam no que ainda falta para transformar esses recursos em um fluxo de validacao mais rigoroso.

## Principios de Execucao

- Cada item deve ser pequeno o suficiente para ter teste, commit e validacao propria.
- Mudancas de estrategia devem ser validadas primeiro em backtest, depois em paper mode, antes de qualquer uso em live.
- Qualquer funcionalidade que afete execucao real deve preservar `TRADING_MODE=paper` como padrao e exigir salvaguardas explicitas para live.
- Resultados de experimentos e decisoes sobre parametros devem ser registrados em `STRATEGY_REVIEW.md`.
- Runtime artifacts como CSVs locais, logs, cache, estado e relatorios gerados nao devem ser commitados.

## Fase 1 - Medir se a estrategia realmente vence alternativas simples

Objetivo: evitar otimizar no escuro. Antes de mexer muito na estrategia, o bot precisa responder se ele supera uma referencia simples como comprar e segurar o mesmo ativo.

1. [x] **Benchmark buy-and-hold no backtest**
   - Implementar retorno buy-and-hold por par e timeframe usando o mesmo periodo do backtest.
   - Exibir retorno da estrategia, retorno buy-and-hold, diferenca e vencedor.
   - Por que melhora: lucro isolado nao basta. Se a estrategia rende +5% enquanto buy-and-hold rende +25%, ela destruiu oportunidade apesar de parecer positiva.

2. [ ] **Criterios automaticos de aprovacao**
   - Criar uma funcao de avaliacao que marque estrategia/par como aprovado, reprovado ou inconclusivo.
   - Criterios iniciais: retorno acima do buy-and-hold, profit factor > 1.2, expectativa positiva, drawdown maximo aceitavel e numero minimo de trades.
   - Por que melhora: reduz decisao subjetiva e evita escolher parametros por impressao visual ou por um unico backtest bom.

3. [ ] **Ranking de pares por qualidade**
   - Ordenar pares por profit factor, expectativa, drawdown, numero de trades, consistencia e diferenca contra buy-and-hold.
   - Integrar o ranking aos comandos de backtest multipar e scanner.
   - Por que melhora: em cripto, a estrategia pode funcionar em alguns ativos e falhar em outros. O ranking ajuda a escolher onde operar e onde bloquear.

4. [ ] **Exportacao de relatorios em `reports/`**
   - Salvar resultados de backtest, scan, otimizacao e analise nos formatos JSON, CSV e Markdown.
   - Incluir parametros usados, periodo testado, custos, slippage, metricas e ranking.
   - Por que melhora: cria historico auditavel. Sem relatorios versionados por execucao local, fica dificil comparar experimentos e evitar repetir testes.

## Fase 1.1 - Evoluir o relatorio de edge

Objetivo: transformar o `python main.py edge` de um painel de metricas em uma decisao operacional clara. O comando ja mostra retorno, expectativa, payoff, buy-and-hold, edge vs benchmark e score inicial; agora precisa explicar a qualidade desses numeros e onde eles devem ser usados.

1. [ ] **Classificacao automatica do edge**
   - Mostrar status final como `APROVADO`, `REPROVADO` ou `INCONCLUSIVO`.
   - Usar criterios como minimo de trades, profit factor > 1.2, expectativa positiva, edge vs buy-and-hold positivo e drawdown aceitavel.
   - Por que melhora: evita interpretar numeros manualmente toda vez e reduz risco de operar uma estrategia que parece boa em uma metrica isolada.

2. [ ] **Motivos da classificacao**
   - Exibir lista curta com os principais motivos do status.
   - Exemplo: `Reprovado: perdeu para buy-and-hold por -70.76%`, `Amostra baixa: 7 trades`, `Ponto positivo: drawdown baixo`.
   - Por que melhora: explica a decisao e mostra exatamente qual gargalo precisa ser atacado.

3. [ ] **Alerta de amostra insuficiente**
   - Destacar quando o numero de trades for baixo demais para conclusao confiavel.
   - Comecar com minimo configuravel, por exemplo 30 trades.
   - Por que melhora: 5 ou 10 trades podem gerar profit factor alto por acaso. O relatorio precisa impedir conclusoes fortes com pouca evidencia.

4. [ ] **Diagnostico defensivo vs agressivo**
   - Classificar casos em que a estrategia tem baixo drawdown e expectativa positiva, mas perde muito para buy-and-hold.
   - Exemplo: `Perfil defensivo: preservou capital, mas capturou pouco da alta`.
   - Por que melhora: diferencia uma estrategia ruim de uma estrategia conservadora que talvez sirva para mercados laterais ou de queda, mas nao para bull market.

5. [ ] **Edge por par e timeframe**
   - Levar as metricas de edge para `multibacktest`, `scan` e selecao dinamica.
   - Mostrar quais pares/timeframes passam, falham ou ficam inconclusivos.
   - Por que melhora: um unico par pode enganar. A chance de lucro real depende de consistencia em varios ativos e janelas.

6. [ ] **Edge anualizado e retorno por exposicao**
   - Calcular retorno anualizado da estrategia, buy-and-hold anualizado e retorno por tempo exposto.
   - Por que melhora: uma estrategia exposta apenas 7% do tempo precisa ser julgada tambem pela eficiencia do capital, nao so pelo retorno bruto.

7. [ ] **Out-of-sample no relatorio de edge**
   - Mostrar edge separado entre periodo de treino e periodo de teste quando o backtest vier do otimizador ou de validacao walk-forward.
   - Por que melhora: edge em dados usados para escolher parametros pode ser overfitting. O dado fora da amostra e o que mais importa.

8. [ ] **Refinar o `edge_score`**
   - Transformar o score atual em escala interpretavel, por exemplo 0-100 ou faixas `Forte`, `Medio`, `Fraco`, `Reprovado`.
   - Documentar pesos e penalidades: benchmark, profit factor, expectativa, drawdown, amostra e exposicao.
   - Por que melhora: o score atual e util como primeira heuristica, mas ainda nao e facil de comparar entre pares, timeframes e versoes da estrategia.

## Fase 2 - Reduzir overfitting

Objetivo: separar o que funcionou por vantagem real do que funcionou por ajuste excessivo ao passado.

1. [ ] **Split treino/teste no otimizador**
   - Otimizar parametros em uma parte dos candles e validar o resultado em periodo posterior nao usado na escolha.
   - Mostrar metricas separadas de treino e teste.
   - Por que melhora: parametros podem parecer otimos porque foram escolhidos para aquele recorte historico. O teste fora da amostra mede se eles sobrevivem em dados novos.

2. [ ] **Walk-forward validation**
   - Substituir ou complementar o split unico por janelas deslizantes com no minimo 3 periodos out-of-sample.
   - Agregar resultado medio e pior janela.
   - Por que melhora: mercado muda de regime. Uma unica divisao treino/teste pode esconder fragilidade em periodos laterais, quedas fortes ou euforia.

3. [ ] **Analise Monte Carlo**
   - Reamostrar sequencias de trades e simular variacoes de ordem dos resultados.
   - Estimar probabilidade de drawdown extremo, sequencia de perdas e risco de ruina.
   - Por que melhora: mesmo uma estrategia lucrativa pode quebrar emocional ou financeiramente se a distribuicao de perdas for ruim.

## Fase 3 - Melhorar metricas de risco

Objetivo: medir qualidade do retorno, nao apenas retorno bruto.

1. [ ] **Sortino Ratio no backtest e analise**
   - Calcular retorno ajustado apenas pela volatilidade negativa.
   - Por que melhora: Sharpe penaliza volatilidade positiva e negativa igualmente. Para trading, perdas e quedas importam mais.

2. [ ] **Calmar Ratio no backtest e analise**
   - Calcular retorno anualizado dividido pelo max drawdown.
   - Por que melhora: mostra se o retorno compensa o pior rebaixamento sofrido. E uma metrica pratica para estrategias com cauda de risco.

3. [ ] **Tempo em posicao e retorno anualizado**
   - Medir exposicao ao mercado, retorno anualizado e retorno por tempo exposto.
   - Por que melhora: uma estrategia que fica pouco tempo comprada precisa ser comparada de forma justa contra buy-and-hold e contra risco de ficar fora de grandes altas.

4. [ ] **Analise automatica de `data/decisions.csv`**
   - Criar comando para resumir sinais, decisoes finais, bloqueios, filtros que mais impediram entrada e indicadores medios por decisao.
   - Por que melhora: mostra se o bot esta parado por excesso de filtro, entrando em contexto ruim ou bloqueando bons sinais por uma regra especifica.

## Fase 4 - Validar e evoluir a estrategia atual

Objetivo: testar hipoteses de melhoria com evidencia, sem transformar a estrategia em um conjunto de regras impossivel de explicar.

1. [ ] **Validar preset operacional atual**
   - Rodar backtests e paper trading com `TIMEFRAME=1h`, `RSI_OVERBOUGHT=70`, `VOLUME_MIN_RATIO=1.0` e pullback ativo.
   - Registrar resultado em `STRATEGY_REVIEW.md`.
   - Por que melhora: o preset atual foi desenhado para aumentar frequencia de trades, mas ainda precisa provar que nao aumentou falsos sinais demais.

2. [ ] **Testar filtro Bollinger adaptativo**
   - Permitir entrada acima da banda superior somente quando tendencia e volume estiverem fortes.
   - Comparar contra o filtro fixo atual.
   - Por que melhora: o filtro atual evita compra esticada, mas tambem pode bloquear rompimentos fortes que sao comuns em cripto.

3. [ ] **Regime detection com ADX**
   - Calcular ADX(14) e classificar mercado como trending, sideways ou indefinido.
   - Em tendencia, permitir regras mais flexiveis; em lateralizacao, suspender ou endurecer entradas.
   - Registrar regime em `data/decisions.csv`.
   - Por que melhora: EMA crossover costuma perder dinheiro em mercado lateral. Detectar regime reduz trades onde a estrategia tem menor vantagem.

4. [ ] **Deteccao de volatilidade elevada**
   - Calcular `ATR_ratio = ATR14 / close`.
   - Quando volatilidade estiver alta, testar alvos/stops adaptados e bloqueios de entrada em candles extremos.
   - Por que melhora: cripto muda rapidamente de volatilidade. Stop e alvo fixos por regime podem ser apertados demais em explosoes e largos demais em consolidacao.

5. [ ] **Trading Range Breakout**
   - Implementar `strategy/breakout.py` herdando `BaseStrategy`.
   - Testar janelas 50/150/200 periodos e comparar contra EMA/RSI nos mesmos pares, custos e timeframes.
   - Por que melhora: estudos de analise tecnica em cripto indicam que regras de rompimento podem superar medias moveis em alguns ativos e periodos.

6. [ ] **Comparativo de estrategias e presets**
   - Criar comando para comparar EMA/RSI, breakout e presets diferentes em uma unica execucao.
   - Usar as mesmas metricas, benchmark e criterios de aprovacao.
   - Por que melhora: impede comparar resultados gerados em condicoes diferentes e ajuda a escolher a estrategia mais robusta, nao a mais recente.

## Fase 5 - Forward test e observabilidade operacional

Objetivo: aproximar o paper mode da realidade operacional antes de qualquer live.

1. [ ] **Forward test formal em paper mode**
   - Registrar carteira paper, trades, decisoes e metricas por periodo como uma avaliacao continua.
   - Comparar performance paper contra backtest do mesmo intervalo.
   - Por que melhora: backtest nao captura todos os problemas de execucao, latencia, dados incompletos e comportamento real do loop.

2. [ ] **Painel local**
   - Adicionar `python main.py painel` para mostrar saldo, posicoes abertas, PnL, ultimas operacoes, ultimos sinais, status dos pares e bloqueios recentes.
   - Por que melhora: reduz operacao as cegas. O operador precisa saber rapidamente se o bot esta saudavel, parado, exposto ou repetindo erros.

3. [ ] **Modo debug da estrategia**
   - Explicar por que cada par esta em `BUY`, `SELL` ou `HOLD`, incluindo EMA, RSI, volume, MTF, Bollinger, regime e cooldown.
   - Por que melhora: facilita diagnosticar sinais ausentes e evita mexer em parametros sem entender qual filtro esta dominando.

4. [ ] **Graficos de performance**
   - Gerar curva de capital, drawdown, PnL por par e candles com marcacoes de entrada/saida.
   - Por que melhora: algumas falhas aparecem melhor visualmente, como lucros concentrados em poucos trades, drawdown longo ou entradas logo antes de reversoes.

## Fase 6 - Protecoes para live

Objetivo: se um dia o bot for para dinheiro real, reduzir a chance de erro operacional ou perda fora do planejado.

1. [ ] **Confirmacao explicita para live**
   - Exigir confirmacao manual clara ao iniciar com `TRADING_MODE=live`.
   - Mostrar pares, saldo, tamanho maximo por ordem, maximo de posicoes e limite de drawdown antes de operar.
   - Por que melhora: impede ligar live por engano ou com `.env` mal configurado.

2. [ ] **Kill switch operacional**
   - Criar mecanismo para suspender novas entradas e/ou fechar posicoes conforme configuracao.
   - Pode ser arquivo local, variavel de ambiente ou comando dedicado.
   - Por que melhora: em falha de mercado, bug ou comportamento inesperado, a resposta precisa ser simples e rapida.

3. [ ] **Checagem de liquidez e spread antes da ordem**
   - Validar order book, spread maximo, volume minimo e tamanho da ordem antes de comprar.
   - Por que melhora: slippage real pode destruir expectativa positiva, principalmente em pares menores.

4. [ ] **Execucao inteligente de ordens**
   - Adicionar ordens limit/stop, reconciliacao de ordens, rastreamento de preenchimento parcial e verificacao de estado na corretora.
   - Por que melhora: ordem a mercado e estado local simples sao suficientes para paper, mas live exige reconciliar o que a corretora realmente executou.

5. [ ] **Limites de perda por dia, semana e mes**
   - Expandir o limite diario atual para limites semanais/mensais e bloqueio automatico apos sequencia ruim.
   - Por que melhora: protege contra degradacao gradual da estrategia e contra periodos em que o mercado deixou de favorecer o modelo.

## Fase 7 - Avancado

Objetivo: explorar melhorias maiores somente depois que validacao, risco e operacao estiverem maduros.

1. [ ] **Filtro de sinal com aprendizado de maquina**
   - Coletar caracteristicas rotuladas em backtests e paper mode para opcionalmente filtrar entradas por probabilidade.
   - Por que melhora: pode reduzir falsos positivos, mas tem alto risco de overfitting. So deve vir depois de walk-forward e relatorios solidos.

2. [ ] **Multiplas corretoras**
   - Generalizar configuracao de corretora alem da Binance usando a base existente com `ccxt`.
   - Por que melhora: permite comparar liquidez/custos e reduz dependencia operacional, mas aumenta complexidade de execucao.

## Referencias Internas

- `STRATEGY_REVIEW.md`: hipoteses, resultados locais e diagnostico da estrategia.
- `docs/research/`: artigos e notas sobre analise tecnica, custos, drawdown, out-of-sample e comparacao com buy-and-hold.
- `backtesting/engine.py`: simulacao historica, custos, slippage e metricas atuais.
- `backtesting/optimizer.py`: busca de parametros atual, ponto de partida para split treino/teste e walk-forward.
