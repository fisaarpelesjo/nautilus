# Revisao da Estrategia

Este documento registra a avaliacao atual da estrategia do bot e os proximos experimentos para validar se ela tem vantagem real. Ele complementa o `ROADMAP.md`: aqui ficam hipoteses, resultados e diagnosticos; no roadmap ficam features e tarefas.

## Estrategia Atual

A estrategia usa EMA crossover 9/21, entrada adicional por pullback em tendencia, filtro de tendencia EMA50, RSI, volume minimo, confirmacao multi-timeframe, Bollinger Bands e gestao de risco por ATR. A ideia e operar apenas compras em contexto de tendencia, evitando entradas quando o preco parece sobreestendido ou sem volume suficiente.

Preset operacional atual:

```text
TIMEFRAME=1h
EMA_FAST=9
EMA_SLOW=21
EMA_TREND=50
RSI_OVERBOUGHT=70
VOLUME_MIN_RATIO=1.0
PULLBACK_ENTRY_ENABLED=true
PULLBACK_RSI_MIN=45
PULLBACK_MAX_DISTANCE_PCT=0.01
MTF_TIMEFRAME=1d
```

Regras de entrada atuais:

- Crossover: EMA9 cruza acima EMA21, preco acima EMA50, RSI abaixo de 70, volume pelo menos igual a media, preco abaixo/igual a banda superior de Bollinger e MTF confirmado.
- Pullback: EMA9 > EMA21 > EMA50, preco acima da EMA50, RSI entre 45 e 70, candle toca perto da EMA21, fecha acima da EMA9 e fecha positivo, com volume e Bollinger validos.

## Evidencia Externa

Pesquisas sobre analise tecnica em cripto mostram resultado misto. Regras tecnicas podem superar buy-and-hold em certos periodos, ativos e regimes de mercado, mas medias moveis simples nao funcionam de forma universal. Estudos tambem destacam que custos de transacao, bolhas, volatilidade e escolha do ativo mudam bastante o resultado.

Referencias consultadas:

- Freqtrade Backtesting: https://www.freqtrade.io/en/latest/backtesting/
- Technical analysis in cryptocurrency markets, 2022: https://www.sciencedirect.com/science/article/pii/S1042443122000816
- Profitability of technical trading rules among cryptocurrencies, 2020: https://www.sciencedirect.com/science/article/pii/S1544612320300829
- Bitcoin technical analysis study, SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4332884

## Leitura Por Componente

**EMA / medias moveis:** usadas para identificar tendencia, mas sao indicadores atrasados. Crossovers tendem a funcionar melhor em tendencia e pior em mercado lateral, onde podem gerar sinais falsos. O filtro de EMA50 ajuda a reduzir entradas contra tendencia, mas tambem pode atrasar entradas.

**RSI:** mede momentum e sobrecompra/sobrevenda. O teto foi afrouxado de `RSI < 65` para `RSI < 70` para permitir entradas em tendencias fortes, quando o RSI permanece alto por varios candles. Isso deve aumentar frequencia, mas tambem pode aceitar compras mais esticadas.

**Bollinger Bands:** ajudam a medir volatilidade e preco sobreestendido. O filtro que evita comprar acima da banda superior e conservador, mas pode impedir entrada em rompimentos fortes. Estudos indicam que Bollinger depende bastante do regime: lateralizacao, breakout, acumulacao ou queda.

**ATR:** e uma parte forte da estrategia. Stop e alvo baseados em ATR se ajustam a volatilidade do ativo, o que e mais adequado para cripto do que usar apenas percentuais fixos. Os multiplicadores `1.5x` para stop e `3.0x` para alvo sao razoaveis, mas precisam ser testados por par e timeframe.

**Volume:** filtra sinais fracos. O default foi afrouxado de `VOLUME_MIN_RATIO=1.2` para `1.0`, exigindo volume pelo menos igual a media. Isso deve aumentar frequencia, mas reduz a protecao contra sinais com volume apenas moderado.

**Pullback em tendencia:** adiciona uma segunda forma de entrada quando a tendencia ja esta alinhada e o preco volta para perto da EMA21 antes de recuperar a EMA9. A ideia e capturar continuacoes de tendencia que o crossover original perdia por depender do cruzamento exato no candle atual.

**Conjunto da estrategia:** a combinacao continua mais robusta do que usar um indicador isolado, mas agora esta menos restritiva. A expectativa e aumentar numero de trades e capturar mais continuacoes de tendencia, com risco maior de sinais falsos em mercado lateral.

## Resultado Local

Amostra local anterior, antes da entrada por pullback e antes do preset mais ativo, com candles `4h`, ultimos ~450 candles, em 30 pares salvos:

```text
media estrategia: +0.01%
media buy-and-hold: -0.54%
pares lucrativos: 12/30
bateu buy-and-hold: 17/30
```

Leitura: a estrategia antiga ainda nao demonstrou lucro forte, mas preservou capital melhor que buy-and-hold em varios pares ruins. Ela tambem perdeu movimentos fortes em alguns ativos porque entrava pouco.

Resultado local atualizado ainda precisa ser medido com o preset atual (`TIMEFRAME=1h`, pullback ativo, RSI 70 e volume 1.0). O novo arquivo `data/decisions.csv` registra cada ciclo por par e deve ser usado para analisar bloqueios, frequencia de sinais, ocorrencias de pullback e filtros mais restritivos.

## Diagnostico

O desenho anterior era conservador demais. A versao atual reduz restricoes com RSI 70, volume 1.0 e entrada por pullback, entao deve gerar mais operacoes. O risco principal agora e aumentar entradas em consolidacao ou em pullbacks que viram reversao.

O numero de trades por par ainda e baixo, entao a amostra nao e estatisticamente forte. Antes de operar live, a estrategia precisa ser validada em mais periodos, com taxas, slippage, comparacao contra buy-and-hold e separacao entre treino e teste.

## Experimentos Recomendados

- Benchmark formal contra buy-and-hold por par e timeframe.
- Otimizacao com separacao treino/teste para reduzir overfitting.
- Validar `VOLUME_MIN_RATIO=1.0` em backtest e paper trading.
- Validar `RSI_OVERBOUGHT=70` em backtest e paper trading.
- Testar entrada sem filtro Bollinger quando a tendencia estiver forte.
- Validar entrada por pullback em tendencia, nao apenas crossover.
- Ranking de pares por profit factor, expectativa e consistencia.
- Criar analise automatica de `data/decisions.csv` para medir filtros que mais bloqueiam entradas.

## Criterios Para Considerar Boa

- Retorno medio maior que buy-and-hold em varios pares.
- Profit factor acima de 1.2.
- Expectativa positiva por trade.
- Drawdown controlado em periodos ruins.
- Resultado positivo fora do periodo usado para otimizar parametros.
- Numero suficiente de trades para evitar conclusao por acaso.
