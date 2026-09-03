# Fase 0 — Pesquisa: reseleção de pares desacoplada da formação

## D1 — Diagnóstico direto da janela de validação, sem tocar em parâmetro algum

**Método.** Script de investigação (não faz parte do código do
projeto) reproduzindo o loop de `run_pairs_backtest` sobre a mesma
janela de validação de spec 052 (22 pares,
`UNIVERSO_AMPLO_HISTORICO_COMPLETO`, `formacao=500`), registrando:
quantos ciclos de reseleção ocorrem, quantos pares ficam elegíveis em
cada um, quantas vezes o z-score de um par elegível cruza o limiar de
entrada, e quantos candles têm slot livre (`max_pares` não esgotado)
sem nenhuma oportunidade entre os pares selecionados no momento.

**Medido (2026-09-03, janela de validação real, 2.300 candles,
2025-08-16 a 2026-09-03):**

| # | Instante | Pares elegíveis |
|---|---|---|
| 1 | i=500 (2025-11-07) | 2 — (BNB,PROM), (BTC,PROM) |
| 2 | i=1000 (2026-01-30) | 3 — (NEAR,FIL), (BTC,BNB), (XRP,FIL) |
| 3 | i=1500 (2026-04-23) | 3 — (DOGE,T), (BNB,LTC), (BTC,LTC) |
| 4 | i=2000 (2026-07-15) | 1 — (SUI,FIL) |

- **4 ciclos de reseleção** em toda a validação (`reselecionar_a_cada
  = formacao = 500`, amarrados).
- **9 pares distintos** elegíveis ao todo (união dos 4 ciclos).
- **6 oportunidades de entrada** (candles em que o z-score de algum
  par elegível cruzou `-entrada_z`) em toda a janela — o mesmo número
  exato dos 6 trades já publicados em specs 039/052.
- **1.794 de 2.300 candles** (78%) têm slot livre (`max_pares=3` não
  esgotado) e **zero** oportunidade entre os pares selecionados no
  momento.

**Conclusão do diagnóstico.** `max_pares` está descartado como
gargalo — a capacidade sobra quase o tempo todo. O número de trades já
publicado (6) não é uma coincidência de execução: é literalmente o
número de vezes que uma oportunidade de entrada existiu, dado só 4
checkpoints de reseleção ao longo de 2.300 candles.

## D2 — `reselecionar_a_cada` desacoplado de `formacao`, sem perda de poder de detecção

**Decisão.** `run_pairs_scan` ganha `reselecionar_a_cada:
Optional[int] = None`, repassado a `run_pairs_backtest` (que já aceita
esse parâmetro independentemente, default 250 — só `run_pairs_scan`
nunca o expôs, sempre chamando com `reselecionar_a_cada=p.formacao`).

**Por que isso não é "olhar menos candles" (perder poder de
detecção).** `selecionar_pares(precos, p, ate=i)` sempre usa
`ini = max(0, i - p.formacao)` — a janela de LOOKBACK é sempre
`p.formacao` (500), não importa a cadência de chamadas. Reselecionar a
cada 120 candles em vez de a cada 500 não encolhe a janela testada em
cada reseleção — só aumenta QUANTAS VEZES uma janela de 500 candles é
reavaliada ao longo do período, capturando relações que se formaram e
se desfizeram entre um checkpoint de 500 e o próximo.

## D3 — Valor testado: `reselecionar_a_cada = 120` (`meia_vida_max`)

**Decisão.** Testa `reselecionar_a_cada=120` — o valor de
`PairsParams.meia_vida_max`, já declarado em spec 028/039 (teto de
meia-vida ainda considerada negociável).

**Rationale.** `meia_vida_max` é o ciclo de reversão mais LENTO que a
própria regra de seleção ainda aceita como elegível. Reselecionar mais
devagar que esse ciclo arrisca perder pares cuja relação já completou
uma reversão inteira e mudou de caráter entre um checkpoint e outro —
o intervalo de reseleção deveria, no mínimo, acompanhar o ciclo mais
lento que o próprio critério de elegibilidade define. `120` é o maior
intervalo que ainda garante isso — não um número escolhido por
produzir mais trades (não medido antes desta declaração).

**Alternativa considerada e rejeitada.** Reselecionar a cada candle
(intervalo=1) — daria o máximo de checkpoints, mas multiplicaria o
custo computacional por 500x sem justificativa declarada além de
"mais é melhor"; sem um critério mecânico para o valor, seria a mesma
varredura disfarçada que motivou D3 aqui ter uma âncora declarada.
