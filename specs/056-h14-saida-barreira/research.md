# Research: H14 — saída por barreira tripla em vez de trailing stop

## D1 — o descasamento nunca foi medido, só declarado (D7 de spec 037)

`specs/037-motor-carteira-h14/research.md` (D7) já registrou, de forma
explícita e correta para o objetivo daquela spec, que a carteira usa
take-profit por ATR + stop **trailing** (mecanismo real de produção) e
**não** a barreira tripla fixa que rotulou o alvo de treino do
classificador — "medir com as barreiras de rotulagem mediria uma
estratégia diferente de H14 com o mesmo nome". Essa decisão estava certa
para o objetivo de "medir H14 tal como foi publicado", mas deixou uma
pergunta genuinamente diferente sem resposta: será que avaliar a
previsão do classificador sob um mecanismo de saída **diferente**
daquele que ela foi medida contra é, em si, uma causa do profit factor
baixo (nunca acima de 0,75 em nenhuma das nove specs de H14 até aqui)?

## D2 — a expectativa em unidades de ATR, sob a própria barreira do classificador

Sobre o subconjunto já decidido em produção (spec 055,
`python main.py calibracao`, corte real 0,3333): alvo=968, stop=1.378,
tempo=140 (n=2.486). Em unidades de ATR, sob a definição da própria
barreira (alvo = +3×ATR, stop = −1,5×ATR, ignorando o peso exato do
timeout, cujo desfecho real depende de onde o preço estava no candle do
limite):

```
EV ≈ p_alvo × 3 − p_stop × 1,5
   = (968/2486)×3 − (1378/2486)×1,5
   = 0,3894×3 − 0,5543×1,5
   = 1,168 − 0,831
   = +0,337 ATR por trade
```

Positivo, e nada marginal. A carteira, sob o mecanismo real (trailing),
nunca chegou perto disso — profit factor 0,68-0,75 em todas as
configurações de risco testadas (specs 037-047). A pergunta desta spec:
o gap entre "+0,337 ATR esperado sob a barreira" e "profit factor <1 sob
trailing" é explicado, ao menos em parte, pelo mecanismo de saída ser
diferente do que a previsão modela?

## D3 — hipótese e alternativa, declaradas antes de qualquer medição de carteira

**Hipótese principal:** saída por barreira produz profit factor mais
próximo de — ou acima de — 1,0, mesmo que ainda não aprove H14 sozinha
(drawdown de carteira permanece uma pergunta distinta).

**Hipótese alternativa, com igual peso:** profit factor continua baixo
mesmo sob a barreira própria do classificador — o problema não é
descasamento de saída, é que a previsão não se traduz em capital real
quando executada como sequência de trades (custo de execução, ordem de
prioridade entre candidatos concorrentes, concorrência de capital
compartilhado) mesmo dentro da própria definição de sucesso que ela usa.

## D4 — escopo mínimo, mesma disciplina de uma-variável-por-vez

Testado **isolado** — sem dimensionamento (spec 041), gate de correlação
(spec 042), circuit breaker (spec 044) ou limite diário (spec 045).
Comparado apenas contra o baseline sem overlay (spec 037: 931 trades,
drawdown 28,66%, PF 0,72), mesmo par de comparação usado por cada uma
das cinco specs de mecanismo isolado anteriores.

## Reprodução

`python main.py carteira_barreira` · `reports/carteira_barreira_*.json`.

(Resultado real preenchido após a execução — ver
`docs/research/registro-de-hipoteses.md` §4.15 para o número medido.)
