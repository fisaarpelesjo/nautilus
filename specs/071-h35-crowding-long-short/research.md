# Research: H35 — Crowding via long/short ratio e open interest (Binance)

## D1 — o que conta como "crowded short": decil mais baixo do próprio par

Decil mais baixo (10º percentil, `PERCENTIL_EXTREMO = 0.10`, mesmo valor de
H26) da distribuição de `longShortRatio` do PRÓPRIO par — não um valor
absoluto compartilhado entre pares, pelo mesmo motivo de H26: pares
diferentes têm distribuições de posicionamento com escalas distintas, um
limiar absoluto privilegiaria o par de maior volatilidade de ratio por
construção, não por sinal real. Calculado apenas sobre a fatia de treino
(D5), antes de olhar qualquer resultado.

## D2 — confirmação por open interest: acima da mediana de treino

Um evento só conta se, no mesmo instante, `openInterestValue` (capital
comprometido em USD, não a quantidade em unidades do ativo) estiver acima
da MEDIANA da própria janela de treino do par. Sem essa confirmação, um
long/short ratio extremo com poucas contas ativas e pouco capital
comprometido seria indistinguível de ruído estatístico de baixa liquidez —
a fundamentação da hipótese exige "capital real comprometido", não só a
proporção de contas. Mediana escolhida (não média) por ser robusta a picos
pontuais de open interest que não representam o regime típico do par.

## D3 — mecânica do trade: só o lado long

Ratio no decil mais baixo (crowded short — minoria de contas compradas)
interpretado como sinal contrário de squeeze, dispara um evento de entrada
COMPRADA, avaliado pela mesma barreira tripla de H14/H26 (`stop 1,5×ATR`,
`alvo 3,0×ATR`, `24 velas`, `ParametrosBarreira` padrão, sem alteração). O
lado espelhado (ratio no decil mais alto → contrário seria vender/short)
não é testado: o bot é long-only por restrição de produção (`CLAUDE.md`),
mesma limitação declarada de H8/H24/H26.

## D4 — alinhamento causal e descarte de candles sem histórico real

Long/short ratio e open interest são alinhados ao candle por
forward-fill causal (`pd.Series.reindex(..., method="ffill")`, mesmo
mecanismo de D3 de H26) — cada candle herda a última leitura publicada até
aquele instante, nunca uma leitura futura. Diferença deliberada em relação
a H26: candles ANTERIORES ao primeiro timestamp real disponível de cada
série são DESCARTADOS do universo avaliável, nunca preenchidos
retroativamente a partir do primeiro valor existente — extrapolar o
primeiro valor real 300 dias para trás fingiria conhecer o posicionamento
de um período em que o dado simplesmente não existe (achado empírico de
D6 torna esse cuidado necessário aqui, diferente de H26 onde funding tinha
histórico completo).

## D5 — disciplina estatística: calibrar só no treino, medir só na validação, agregar entre pares

Limiar do decil (D1) calculado exclusivamente sobre a fatia de treino
(`1 - DEFAULT_VALIDATION_RATIO` = 70% da janela realmente disponível — ver
D6, não os 2.000 candles de H26) e aplicado sem reajuste à fatia de
validação. A mediana de open interest (D2) segue a mesma regra: calculada
só no treino. Significância avaliada via `supera_empate_com_confianca`
(Wilson CI, `backtesting/modelo.py`, sem alteração) sobre a contagem
agregada (pooled) entre os pares de `UNIVERSO_H11` — um único par
raramente acumula amostra suficiente, ainda mais aqui dado D6.

## D6 — retenção real do endpoint, medida empiricamente (não presumida)

Probe real via `ccxt` nesta sessão (2026-09-06, símbolo `BTC/USDT:USDT`,
`fetch_long_short_ratio_history`/`fetch_open_interest_history`, timeframes
4h e 1d, `limit=500`): os dois endpoints devolveram exatamente ~31 dias de
histórico (186 candles de 4h; 31 candles de 1d) — teto do próprio endpoint
público da Binance (dados de "estatísticas de mercado" têm retenção curta
por desenho, diferente de funding rate que é histórico completo), não do
parâmetro `limit`/paginação. **Isso é ~11x menor que os 2.000 candles
(~333 dias) que H8/H14/H26 usam com funding rate.**

Consequência direta no desenho: com 186 candles por par, um split
treino/validação por par no padrão `MIN_WINDOW_CANDLES=150` do harness
comum (`backtesting/bateria_hipotese.py`) é inviável (186 < 2×150=300) —
por isso esta hipótese usa a mesma arquitetura de H26 (evento pooled +
barreira tripla), não o harness E1-E6. O plano MUST medir a retenção real
por par (pode variar por símbolo) em vez de presumir os ~31 dias do probe
de BTC/USDT para todo o universo — `avaliar_par` descarta um par cuja
retenção real não permita nem calibrar treino, sem abortar os demais
(FR-008).

## Hipótese declarada antes de medir

**Expectativa honesta: REPROVADA (ou INCONCLUSIVA por amostra, dado D6) é
o resultado mais provável.** Base histórica: 22 hipóteses direcionais
anteriores neste registro (H34 incluída), nenhuma sobreviveu a confirmação
fora da amostra — H35 usa uma fonte de dado genuinamente nova
(posicionamento, não custo de posição, nem preço), mas continua na mesma
família estrutural (aposta contrária direcional). Diferente de H34
(proxy só de OHLCV), aqui o risco adicional e já esperado é de amostra:
a retenção curta do endpoint (D6) pode não deixar eventos suficientes
mesmo agregados entre 12 pares — se assim for, o veredito correto é
INCONCLUSIVA por amostra, não REPROVADA, mesma distinção que M9/M14 já
estabeleceram neste registro (amostra insuficiente nunca é lida como
reprovação).

## Reprodução

`python main.py crowding` · `reports/crowding_*.json`.

(Resultado real preenchido após a execução — ver
`docs/research/registro-de-hipoteses.md` §6.1 para o número medido.)
