# Research: H37 — Mean reversion em par de stablecoin (USDC/USDT)

## D1 — estratégia: H3 inalterada, único par avaliado

`strategy/mean_reversion.py::MeanReversionStrategy` (Bollinger 20/2.0, RSI
14/30/70, sem filtro ADX — mesmos defaults já usados quando H3 foi testada
originalmente em BTC/SOL/ETH) roda sem nenhuma alteração de código sobre
`USDC/USDT`. Diferente de H34/H35, não há universo — a hipótese é sobre um
símbolo específico (mecanismo de reversão determinística de uma
stablecoin), não uma família de pares. Reajustar parâmetros para este par
especificamente seria otimizar até passar, o problema que a disciplina
deste registro existe para impedir.

## D2 — janela de dados

2.000 candles de 4h confirmados disponíveis para `USDC/USDT` na Binance
(2025-10-08 a 2026-09-06, ~11 meses) — mesma ordem de grandeza usada por
outras hipóteses recentes da bateria, verificado por fetch real nesta
sessão antes de dimensionar o teste.

## D3 — por que o horizonte de 4h pode não capturar nada (obstáculo declarado)

A própria literatura citada na fundamentação descreve a janela de
arbitragem de stablecoin como durando segundos, dominada por bots MEV —
mesma limitação estrutural que já zerou H15 (latência) e H22 (arbitragem
triangular). O motor de backtest deste projeto opera em candles de 4h; se
a reversão real dura segundos, um candle de 4h não tem resolução para
capturar entrada e saída dentro da mesma janela de reversão. A estratégia
BB+RSI de H3 não foi desenhada para esse horizonte — a expectativa honesta
é que o resultado seja indistinguível de ruído em torno de um preço
estruturalmente estável (~1,0000), não uma vantagem real.

## Nota de instrumentação — segunda hipótese sobre o harness comum

H37 roda pela mesma bateria E1-E6 (`backtesting/bateria_hipotese.py`) já
usada por H34 — o teste de sanidade (E1) usa uma série sintética de preço
CONSTANTE (sem volatilidade), garantindo que a estratégia de reversão
nunca encontre uma banda inferior para tocar nessa série, isolando defeito
de motor de resultado de estratégia real.

## Hipótese declarada antes de medir

**Principal:** a estratégia de reversão à média (H3, inalterada) produz
retorno positivo e consistente sobre `USDC/USDT` quando avaliada pela
bateria completa.

**Alternativa, com peso igual:** o resultado é indistinguível de ruído —
nem positivo nem negativo de forma consistente — porque o horizonte de 4h
não tem resolução para capturar uma reversão que a própria literatura
descreve como durando segundos (D3). Diferente de H3 nos outros pares
(que teve win rate ruim mas mensurável, 20-31%), aqui a expectativa é de
uma amostra pequena demais ou sem sinal capturável, não necessariamente
um sinal capturável e ruim.

## Reprodução

`python main.py stablecoin`.

(Resultado real preenchido após a execução — ver
`docs/research/registro-de-hipoteses.md` §6.1 para o veredito medido, com
comparação explícita contra o resultado original de H3.)
