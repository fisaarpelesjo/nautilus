# Roadmap

Este roteiro registra melhorias identificadas ao comparar este bot com projetos maduros de negociação cripto de código aberto, como Freqtrade, Jesse, Hummingbot, VibeTrading e Wisp. Priorize mudanças que melhorem validação, observabilidade e qualidade de decisão antes de adicionar automações avançadas.

## Prioridade Alta

- [x] Métricas avançadas de teste histórico: adicionar fator de lucro, expectativa, média de ganho/perda, maior ganho/perda, maior sequência de perdas, Sharpe simplificado, exposição e retorno por par/período gráfico.
- [x] Comando de análise: adicionar `python main.py analisar` para ler `data/trades.csv` e gerar um resumo local de desempenho após sessões em simulado ou real.
- [x] Otimização de parâmetros: adicionar `python main.py otimizar` para testar faixas de EMA, RSI, ATR, volume e Bollinger Bands.
- [x] Lista permitida dinâmica: selecionar pares negociáveis automaticamente usando volume, diferença entre compra e venda, volatilidade, tendência e resultados recentes de teste histórico.
- [x] Lista bloqueada de pares: suportar `BLACKLIST_PAIRS` e ignorar moedas estáveis, pares com baixa liquidez ou ativos problemáticos.

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

## Notas de Implementação

Mantenha cada item pequeno o suficiente para ter seu próprio commit e etapa de validação. Prefira testes determinísticos antes de mudanças de comportamento. Qualquer funcionalidade que possa afetar negociação real deve preservar `TRADING_MODE=paper` como padrão e manter salvaguardas explícitas para o modo real.

Para avaliação da estratégia atual, resultados locais e próximos experimentos de validação, consulte `STRATEGY_REVIEW.md`.
