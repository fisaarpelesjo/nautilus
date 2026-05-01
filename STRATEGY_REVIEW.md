# Revisao da Estrategia

Este documento registra a avaliacao atual da estrategia do bot e os proximos experimentos para validar se ela tem vantagem real. Ele complementa o `ROADMAP.md`: aqui ficam hipoteses, resultados e diagnosticos; no roadmap ficam features e tarefas.

## Estrategia Atual

A estrategia usa EMA crossover 9/21, filtro de tendencia EMA50, RSI, volume minimo, confirmacao multi-timeframe, Bollinger Bands e gestao de risco por ATR. A ideia e operar apenas compras em contexto de tendencia, evitando entradas quando o preco parece sobreestendido ou sem volume suficiente.

## Evidencia Externa

Pesquisas sobre analise tecnica em cripto mostram resultado misto. Regras tecnicas podem superar buy-and-hold em certos periodos, ativos e regimes de mercado, mas medias moveis simples nao funcionam de forma universal. Estudos tambem destacam que custos de transacao, bolhas, volatilidade e escolha do ativo mudam bastante o resultado.

Referencias consultadas:

- Freqtrade Backtesting: https://www.freqtrade.io/en/latest/backtesting/
- Technical analysis in cryptocurrency markets, 2022: https://www.sciencedirect.com/science/article/pii/S1042443122000816
- Profitability of technical trading rules among cryptocurrencies, 2020: https://www.sciencedirect.com/science/article/pii/S1544612320300829
- Bitcoin technical analysis study, SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4332884

## Leitura Por Componente

**EMA / medias moveis:** usadas para identificar tendencia, mas sao indicadores atrasados. Crossovers tendem a funcionar melhor em tendencia e pior em mercado lateral, onde podem gerar sinais falsos. O filtro de EMA50 ajuda a reduzir entradas contra tendencia, mas tambem pode atrasar entradas.

**RSI:** mede momentum e sobrecompra/sobrevenda. Usar `RSI < 65` evita comprar muito esticado, mas pode bloquear entradas em tendencias fortes, quando o RSI permanece alto por varios candles.

**Bollinger Bands:** ajudam a medir volatilidade e preco sobreestendido. O filtro que evita comprar acima da banda superior e conservador, mas pode impedir entrada em rompimentos fortes. Estudos indicam que Bollinger depende bastante do regime: lateralizacao, breakout, acumulacao ou queda.

**ATR:** e uma parte forte da estrategia. Stop e alvo baseados em ATR se ajustam a volatilidade do ativo, o que e mais adequado para cripto do que usar apenas percentuais fixos. Os multiplicadores `1.5x` para stop e `3.0x` para alvo sao razoaveis, mas precisam ser testados por par e timeframe.

**Volume:** filtra sinais fracos, mas `VOLUME_MIN_RATIO=1.2` pode deixar a estrategia exigente demais. Reduz entradas ruins, mas tambem pode reduzir demais o numero de trades.

**Conjunto da estrategia:** a combinacao e mais robusta do que usar um indicador isolado, mas tambem pode ficar restritiva. A estrategia atual parece melhor em preservar capital e evitar mercados ruins do que em capturar altas fortes.

## Resultado Local

Amostra local com candles `4h`, ultimos ~450 candles, em 30 pares salvos:

```text
media estrategia: +0.01%
media buy-and-hold: -0.54%
pares lucrativos: 12/30
bateu buy-and-hold: 17/30
```

Leitura: a estrategia ainda nao demonstrou lucro forte, mas preservou capital melhor que buy-and-hold em varios pares ruins. Ela tambem perdeu movimentos fortes em alguns ativos porque entra pouco.

## Diagnostico

O desenho atual e conservador e defensavel, mas provavelmente restritivo demais. A combinacao de EMA cross, preco acima da EMA50, RSI abaixo de 65, volume acima de 1.2x a media, confirmacao MTF e Bollinger reduz entradas ruins, mas tambem filtra movimentos bons.

O numero de trades por par ainda e baixo, entao a amostra nao e estatisticamente forte. Antes de operar live, a estrategia precisa ser validada em mais periodos, com taxas, slippage, comparacao contra buy-and-hold e separacao entre treino e teste.

## Experimentos Recomendados

- Benchmark formal contra buy-and-hold por par e timeframe.
- Otimizacao com separacao treino/teste para reduzir overfitting.
- Testar `VOLUME_MIN_RATIO=1.0`.
- Testar `RSI_OVERBOUGHT=70`.
- Testar entrada sem filtro Bollinger quando a tendencia estiver forte.
- Testar entrada por pullback em tendencia, nao apenas crossover.
- Ranking de pares por profit factor, expectativa e consistencia.

## Criterios Para Considerar Boa

- Retorno medio maior que buy-and-hold em varios pares.
- Profit factor acima de 1.2.
- Expectativa positiva por trade.
- Drawdown controlado em periodos ruins.
- Resultado positivo fora do periodo usado para otimizar parametros.
- Numero suficiente de trades para evitar conclusao por acaso.
