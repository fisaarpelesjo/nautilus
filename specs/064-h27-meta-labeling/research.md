# Research: H27 — meta-labeling, pré-condição sobre o sinal primário

## D1 — a pergunta e o critério, declarados antes de medir

Meta-labeling (López de Prado) treina um modelo SECUNDÁRIO para decidir
se um sinal PRIMÁRIO já existente deve ser executado. O sinal primário
candidato é o crossover/pullback EMA/RSI de produção
(`strategy/ema_rsi.py`, `backtesting/engine.py::precompute_signals`).

**Risco declarado antes de qualquer código:** H1 (o mesmo sinal EMA/RSI,
backtestado com o mecanismo de saída real de produção) foi REPROVADO
isoladamente — 0/20 combinações confirmadas fora da amostra (registro,
§4.2). Se o sinal primário não carrega nenhuma informação real nos
próprios eventos de entrada, um modelo secundário estaria filtrando
ruído, não sinal — mesma armadilha estrutural que bloqueou H12 (§6.4:
"dimensionamento decide QUANTO, nunca SE").

**Critério de pré-condição, declarado antes de medir:** os eventos de
entrada do EMA/RSI (`Signal.BUY` via `precompute_signals`), rotulados
pela barreira tripla de H14 (`rotular`, mesmos parâmetros —
`ATR_SL_MULTIPLIER`/`ATR_TP_MULTIPLIER`), precisam superar o ponto de
empate COM CONFIANÇA (`supera_empate_com_confianca`, Wilson CI — nunca a
razão pontual isolada, mesma disciplina de H14/M9/M13). Se não superarem,
a pré-condição não está atendida e a spec se encerra aqui, sem treinar
nenhum modelo secundário.

## D2 — diagnóstico ad-hoc, resultado real

Script fora do repositório (mesmo padrão de diagnóstico usado em H8/H10
antes de comprometer código), pooled sobre `UNIVERSO_H11`, 6.000 candles
por par:

```
empate: 0.5000
  BTC/USDT: 76 eventos de entrada EMA/RSI, 5951 candles rotulaveis
  ETH/USDT: 48 eventos
  SOL/USDT: 58 eventos
  LINK/USDT: 63 eventos
  BCH/USDT: 74 eventos
  TRX/USDT: 86 eventos
  XRP/USDT: 69 eventos
  AVAX/USDT: 45 eventos
  LTC/USDT: 77 eventos
  DOT/USDT: 48 eventos
  ADA/USDT: 47 eventos
  ATOM/USDT: 49 eventos

todos os candles (baseline): n=71412 alvo=18706 stop=42683 tempo=10023
  razao=0.4383 supera_empate_ci95=False
eventos de entrada EMA/RSI (sinal primario): n=740 alvo=227 stop=453
  tempo=60 razao=0.5011 supera_empate_ci95=False
```

**Leitura honesta.** A razão de chances dos eventos de entrada (0,5011)
fica bem mais perto do empate (0,5000) que o baseline geral (0,4383) —
o sinal primário claramente DESLOCA a probabilidade na direção certa,
não é aleatório em relação ao baseline. Mas 0,5011 não supera 0,5000 com
confiança (n=740, 453 stops — intervalo de Wilson ainda cruza o empate).
**A pré-condição declarada em D1 NÃO é atendida.**

**Por que isso encerra a linha aqui, e não é uma leitura arbitrária.**
O critério foi declarado ANTES de rodar o diagnóstico (D1) — não foi
ajustado depois de ver 0,5011 ficar tão perto de 0,5000. A tentação de
ler "quase lá" como "praticamente atendida" é exatamente o padrão que
`supera_empate_com_confianca` existe para impedir (M9/M13, mesma lição
usada em toda avaliação de H14 em diante neste registro): um número que
parece bom porque a régua não tem tolerância não é evidência.

## D3 — o que isso decide, e o que não decide

**Decide:** filtrar apostas do EMA/RSI de produção especificamente, com
meta-labeling, não é testável hoje — o sinal primário não tem informação
suficiente comprovada para um modelo secundário separar entradas boas de
ruins.

**Não decide:** meta-labeling como TÉCNICA continua válida — se um sinal
primário diferente (não o EMA/RSI de produção) mostrar informação real
em seus próprios eventos, a mesma pré-condição poderia ser reaplicada e
passar. Isso seria uma hipótese nova (sinal primário diferente), não uma
continuação desta spec.

## Reprodução

`python main.py meta_labeling` · `reports/meta_labeling_*.json`.
