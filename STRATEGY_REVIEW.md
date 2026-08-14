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

## Validacao Out-of-Sample (2026-08-14)

Primeiro resultado real de `python main.py backtest --validate` (US3 de
`specs/001-hardening-incremental`), rodado sobre `PAIRS[0]`/`TIMEFRAME` configurados no `.env` do
operador: `LUNC/USDT` `4h` (demais parametros no default do `config/settings.py`:
`RSI_OVERBOUGHT=70`, `VOLUME_MIN_RATIO=1.0`, `PULLBACK_ENTRY_ENABLED=true`; note que isso diverge do
`TIMEFRAME=1h` citado em "Preset operacional atual" acima — o preset documentado nao corresponde ao
default atual do codigo, vale revisar qual dos dois esta desatualizado). Split 70% treino / 30%
validacao, `CANDLE_LIMIT=2000` candles buscados.

```text
                    TREINO         VALIDACAO (out-of-sample)
retorno total       -0.44%         +0.00%
total de trades      3              0
win rate             33.3%          0.0%
profit factor         0.58           0.00
max drawdown          1.24%          0.00%
buy & hold           +57.17%        -20.74%
edge vs buy&hold     -57.61%        +20.74%

VEREDITO: REPROVADO
  - apenas 0 trades na validacao (minimo 10)
  - profit factor 0.00 abaixo do minimo 1.2
```

Leitura: a janela de validacao nao gerou nenhuma entrada — filtros conservadores (RSI/volume/MTF/BB)
bloquearam tudo naquele periodo, entao o veredito REPROVADO aqui e por falta total de amostra, nao por
prejuizo. Na janela de treino a estrategia perdeu (3 trades, profit factor 0.58) enquanto
buy-and-hold subiu forte (+57%) — o mesmo padrao ja visto no resultado local anterior (`## Resultado
Local`): a estrategia preserva capital mas nao acompanha altas fortes.

Confirmacao com um segundo par/execucao (mesma data, `ENSO/USDT` `4h`, config default do repositorio
sem `.env`): treino 3 trades/-1.35%, validacao 9 trades/+1.38% (profit factor 1.76, mas ainda
REPROVADO por ficar abaixo do minimo de 10 trades e nao superar buy-and-hold +27.63%). Os dois pares
reprovaram, mas por motivos diferentes (amostra zero vs amostra insuficiente) — nenhum dos dois chegou
perto de um veredito aprovado.

Amostra pequena demais em ambos os pares para qualquer conclusao estatistica sobre a estrategia em si
— o resultado principal desta rodada e confirmar que o pipeline de validacao (split, criterios,
veredito) funciona ponta a ponta com dados reais, nao decidir se a estrategia tem vantagem. Proximo
passo antes de repetir esse experimento com mais confianca: rodar sobre um periodo mais longo
(`candle_limit` maior) e/ou `multibacktest`/`scan` para varios pares de uma vez, ja que o split 70/30
exige pelo menos ~500 candles totais para cada janela passar de `MIN_WINDOW_CANDLES=150`.

## Decisão Multi-Par (2026-08-14, spec 002-multi-pair-approval)

Primeira rodada real de `python main.py multibacktest`, `scan` e `edge` com veredito/ranking
agregado (US1-US3 da spec `002-multi-pair-approval`), sobre a config real do `.env` do operador
(`LUNC/USDT` como `PAIRS[0]`) e o scan padrão (top 30 pares por volume, `4h`).

**`multibacktest`** (5 pares fixos × 3 timeframes = 15 combinações): 2/15 resultados positivos
(`BNB/USDT` `1d` +0.73%, 1 trade; `BNB/USDT` `4h` +0.08%, 9 trades). **Nenhum aprovado** — todos os
15 reprovados, a maioria por amostra insuficiente (a maior parte das combinações tem menos de 10
trades no período testado) ou por não superar buy-and-hold. Confirma visualmente o que a proteção de
`MIN_TRADES_FOR_RANKING=3` faz: no grupo `1d`, três pares com 0-2 trades mostraram `edge_score`
positivo alto (SOL +16.3, XRP +22.0, BNB +72.2) mas ficaram no fim do ranking do grupo mesmo assim,
por trás de pares com amostra maior — o número bruto não domina a ordenação quando a amostra é
minúscula.

**`scan`** (top 30 pares por volume 24h): 7/30 resultados positivos. **Primeiro veredito APROVADO
real encontrado**: `DOGE/USDT` `4h` — 11 trades, win rate 45%, retorno +0.58%, drawdown 1.11%,
`edge_score +28.3 (Forte)`. Passou nos quatro critérios simultaneamente (amostra ≥ 10, retorno >
buy-and-hold, profit factor > 1.2, drawdown ≤ 10%) — o primeiro caso, entre todas as execuções
registradas neste documento, em que a estratégia bate a régua completa num par real. Achado
qualitativo interessante: `TUT/USDT` teve o maior retorno bruto da lista (+3.35%) mas o pior
`edge_score` (-210.7, Reprovado) — o ativo subiu tanto no período que bater buy-and-hold ficou muito
mais difícil ali, ilustrando por que `edge_score` (retorno relativo) é o critério certo para ranquear,
não retorno absoluto.

**`edge`** (`PAIRS[0]` = `LUNC/USDT` `4h`): reprovado — 3 trades (abaixo do mínimo), retorno +0.06%
não supera buy-and-hold +27.02%, profit factor 1.11 abaixo do mínimo. Diagnóstico "perfil defensivo"
corretamente disparado (drawdown baixo, expectativa positiva, mas capturou pouco da alta) —
`edge_score -40.92 (Reprovado)`.

Leitura: com visão agregada (35 execuções entre os três comandos nesta rodada), a estratégia aprovou
em 1 de 35 casos — não é evidência de vantagem consistente, mas é a primeira confirmação de que o
critério de aprovação *consegue* aprovar um caso real quando os números realmente sustentam (não é um
veredito sempre-reprovado por construção). Próximo experimento natural: revisitar os pares/timeframes
que mais se aproximaram do veredito aprovado (`UNI/USDT` scan, +18.5 Médio; `BNB/USDT` 4h
multibacktest) com um histórico mais longo, já que amostra insuficiente foi o motivo de reprovação
mais comum nesta rodada.

## Otimização Sem Overfitting (2026-08-14, spec 003-robust-optimization)

Primeira rodada real de `python main.py optimize --walk-forward` (implica `--validate`) — grid search
completo (648 combinações válidas × `OPTIMIZE_PAIRS`, 5 pares: BTC, ETH, BNB, SOL, XRP, `4h`) com
split treino/validação (US1) e o vencedor testado em 3 janelas walk-forward por par (US2).

**Achado central — a divergência treino vs validação que esta spec existe para expor**: o candidato
#1 (`EMA 7/21, RSI<70, vol 1.2x, BB 2.0, ATR 2.0/2.4`) teve **retorno médio de treino +0.28%** (score
5.77, o melhor da busca) mas **retorno de validação -0.87%** — sinal claro de que o conjunto que
parecia melhor no histórico usado para escolher não se sustentou no período reservado. Todos os 5
primeiros colocados do treino mostraram o mesmo padrão (treino sempre positivo ~+0.27-0.29%, validação
sempre negativa entre -0.54% e -0.88%) — não é um caso isolado do #1, é sistemático nesta rodada.

**Walk-forward do vencedor** (3 janelas de ~54 dias cada, por par): resultado consistente com o achado
acima — **4 dos 5 pares fecharam a janela mais recente (jan. 3, 2026-06-23 a 2026-08-14) no negativo**
(BTC -1.20%, BNB -0.54%, SOL -0.59%, XRP -1.68%; só ETH ficou positivo, +0.19% de média geral). `SOL`
foi o pior par em quase todas as janelas (única exceção: janela 1, onde `BTC` foi pior). Média geral
por par: BTC -0.17%, ETH +0.19%, BNB -0.06%, SOL -0.29%, XRP -0.55% — só `ETH` teve média positiva
entre as 3 janelas.

**`backtest --montecarlo`** (`PAIRS[0]` = `LUNC/USDT` `4h`, 1000 simulações sobre os 3 trades do
backtest simples): drawdown máximo mediana 0.52%, p95 1.08%; maior sequência de perdas esperada
(mediana) 2. Confiança marcada como baixa (3 trades, abaixo do mínimo de 10) — números direcionais,
não conclusivos, exatamente o comportamento que FR-008/SC-004 pedem.

Leitura: esta é a primeira evidência concreta e sistemática (não anedótica) de que a busca em grade
estava overfitando ao histórico completo — exatamente o gap que motivou a spec `001` item parcial e a
spec `003` inteira. O conjunto "vencedor" do treino não é confiável sem essa checagem; nenhum dos 5
primeiros colocados bateria o critério de aprovação da spec `002` (`evaluate_approval`) se aplicado à
validação. Próximo experimento natural: repetir com um grid mais restrito ao redor dos parâmetros que
menos divergiram (candidatos #3/#5, retorno de validação -0.54/-0.55%, os "menos piores"), e considerar
se `SOL/USDT` deveria sair da lista `OPTIMIZE_PAIRS` dado seu desempenho consistentemente fraco nas 3
janelas.

## Métricas de Risco Avançadas (2026-08-14, spec 004-advanced-risk-metrics)

Primeira rodada real de `python main.py backtest` (Sortino/Calmar/anualizado/por-exposição — US1/US2
da spec `004-advanced-risk-metrics`) sobre `LUNC/USDT` `4h` (`PAIRS[0]` do `.env` do operador):

```text
Retorno total       +0.06%
Max drawdown         0.62%
Exposicao             2.0%
Retorno anualiz.     +0.15%
Retorno/exposicao    +2.95%
Sharpe simplif.       0.06
Sortino               0.10
Calmar                0.25
```

Leitura: Sortino (0.10) e Sharpe (0.06) próximos nesta amostra específica (3 trades, 1 prejuízo só) —
esperado, já que com um único trade de prejuízo o desvio "downside" e o desvio geral não divergem
muito. Calmar 0.25 (retorno anualizado bem menor que o drawdown máximo) confirma quantitativamente o
mesmo diagnóstico "perfil defensivo" já visto na spec `002` para este par: a estratégia mal cobre o
próprio drawdown quando anualizada. `Retorno/exposição +2.95%` mostra que, no tempo em que esteve
de fato posicionada (2% do período), a eficiência de capital não é desprezível — mas isso não
compensa ficar 98% do tempo fora do mercado durante um período de alta forte (buy-and-hold +26.75%
no mesmo período). Nenhuma das quatro métricas novas produziu erro em nenhuma das execuções (SC-002
confirmado com dados reais, não só nos testes sintéticos de fronteira).

`python main.py decisions` (US3): validado só com fixture sintética nesta sessão — este ambiente não
tem `data/decisions.csv` real, já que o bot nunca rodou continuamente aqui (mesma limitação documentada
no `Assumptions` da spec). Fica pendente do operador rodar `python main.py bot` por um período e então
`python main.py decisions` para um diagnóstico real de bloqueios mais frequentes.

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
