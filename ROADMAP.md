# Roadmap

Este roteiro registra melhorias identificadas ao comparar este bot com projetos maduros de negociação cripto de código aberto, como Freqtrade, Jesse, Hummingbot, VibeTrading e Wisp. Priorize mudanças que melhorem validação, observabilidade e qualidade de decisão antes de adicionar automações avançadas.

## Prioridade Alta

- [x] Métricas avançadas de teste histórico: adicionar fator de lucro, expectativa, média de ganho/perda, maior ganho/perda, maior sequência de perdas, Sharpe simplificado, exposição e retorno por par/período gráfico.
- [x] Comando de análise: adicionar `python main.py analisar` para ler `data/trades.csv` e gerar um resumo local de desempenho após sessões em simulado ou real.
- [x] Otimização de parâmetros: adicionar `python main.py otimizar` para testar faixas de EMA, RSI, ATR, volume e Bollinger Bands.
- [x] Lista permitida dinâmica: selecionar pares negociáveis automaticamente usando volume, diferença entre compra e venda, volatilidade, tendência e resultados recentes de teste histórico.
- [x] Lista bloqueada de pares: suportar `BLACKLIST_PAIRS` e ignorar moedas estáveis, pares com baixa liquidez ou ativos problemáticos.

## Validacao da Estrategia

Checklist baseado em `STRATEGY_REVIEW.md`, com foco em provar se a estrategia atual tem vantagem real antes de operar live.

- [ ] Criar benchmark formal contra buy-and-hold por par e timeframe.
- [ ] Adicionar comparativo no relatório de backtest: retorno da estratégia, retorno buy-and-hold, diferença e vencedor.
- [ ] Separar treino/teste no otimizador para reduzir overfitting.
- [ ] Adicionar ranking de pares por profit factor, expectativa, drawdown, número de trades e consistência.
- [ ] Testar preset menos restritivo com `VOLUME_MIN_RATIO=1.0`.
- [ ] Testar preset menos restritivo com `RSI_OVERBOUGHT=70`.
- [ ] Testar modo sem filtro Bollinger quando a tendência estiver forte.
- [ ] Testar entrada por pullback em tendência, além de crossover.
- [ ] Registrar resultados dos experimentos em `STRATEGY_REVIEW.md`.
- [ ] Definir critérios automáticos de aprovação: retorno acima de buy-and-hold, profit factor acima de 1.2, expectativa positiva, drawdown controlado e número mínimo de trades.

## Prioridade Média

- [ ] Painel local: adicionar `python main.py painel` para mostrar saldo, posições abertas, PnL, últimas operações, últimos sinais e status dos pares.
- [ ] Modo debug da estratégia: explicar por que cada par está em `BUY`, `SELL` ou `HOLD`, incluindo EMA, RSI, volume, MTF e filtros de Bollinger.
- [ ] Comparativo de estratégias: comparar múltiplas estratégias, predefinições, pares e períodos gráficos em um único comando.
- [ ] Exportação de relatórios: salvar resultados de teste histórico e análise em `reports/` nos formatos JSON, CSV e Markdown.
- [ ] Gráficos: gerar curva de capital, rebaixamento, PnL por par e candles com marcações de operações.

## Prioridade Baixa / Avançado

- [ ] Análise Monte Carlo: testar sequências de operações e variações de candles para estimar robustez e risco de sobreajuste.
- [ ] Filtro de sinal com aprendizado de máquina: coletar características rotuladas em testes históricos e opcionalmente filtrar entradas por confiança do modelo.
- [ ] Múltiplas corretoras: generalizar a configuração de corretora além da Binance usando a base existente com `ccxt`.
- [ ] Execução inteligente de ordens: adicionar ordens limit/stop, reconciliação de ordens, rastreamento de preenchimento parcial e controles mais seguros para live.

## Melhorias baseadas em Pesquisa Acadêmica

Itens derivados da análise de compatibilidade entre o projeto e os artigos em `docs/research/`. Foco em fechar gaps com evidência empírica de alpha real.

### Alta Prioridade

- [ ] **Trading Range Breakout (50/150/200 períodos):** Implementar `strategy/breakout.py` herdando `BaseStrategy`. Sinal BUY quando `price > MAX(close, n)`, SELL quando `price < MIN(close, n)`. Backtestear contra EMA atual nos mesmos pares e períodos. Fonte: Gerritsen et al. e Svogun & Bazán — melhor regra isolada em 2 dos 4 estudos de TA.
- [ ] **Regime Detection (trending vs. sideways):** Calcular ADX(14) em `strategy/ema_rsi.py`. ADX > 25 = trending (relaxar RSI threshold, manter crossover); ADX < 20 = sideways (aumentar filtros ou suspender entradas). Registrar regime no `data/decisions.csv` para análise posterior.

### Média Prioridade

- [ ] **Sortino Ratio e Calmar Ratio no backtest:** Adicionar em `backtesting/analysis.py`. Sortino = retorno médio / desvio-padrão dos retornos negativos. Calmar = retorno anual / max drawdown. Estudos usam essas métricas como benchmark primário; Sharpe sozinho não captura risco de cauda.
- [ ] **Walk-forward validation no otimizador:** Substituir split único por janela deslizante em `backtesting/optimizer.py`. Mínimo 3 janelas out-of-sample. Reduz data-snooping — pesquisa mostra que parâmetros otimizados em sample falham out-of-sample em Bitcoin especificamente.
- [ ] **Detecção de volatilidade elevada (modo bolha):** Calcular `ATR_ratio = ATR14 / price`. Se `ATR_ratio > threshold` (ex: 0.05), ativar modo volatility-aware: aumentar TP multiplier, manter SL apertado. Fonte: Svogun & Bazán — períodos de bolha geram +1.5-3x retorno para ETH/XRP/LTC quando estratégia adapta alvos.

## Notas de Implementação

Mantenha cada item pequeno o suficiente para ter seu próprio commit e etapa de validação. Prefira testes determinísticos antes de mudanças de comportamento. Qualquer funcionalidade que possa afetar negociação real deve preservar `TRADING_MODE=paper` como padrão e manter salvaguardas explícitas para o modo real.

Para avaliação da estratégia atual, resultados locais e próximos experimentos de validação, consulte `STRATEGY_REVIEW.md`.
