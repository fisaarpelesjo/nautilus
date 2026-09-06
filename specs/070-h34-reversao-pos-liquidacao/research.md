# Research: H34 — Reversão pós-liquidação (padrão de vela: pavio + pico de volume)

## D1 — proxy do padrão: pavio ≥ 50% do range + fechamento de recuperação

Sem dado de liquidação real (Binance não publica histórico livre de
`forceOrder`), o padrão é aproximado inteiramente a partir de OHLCV: pavio
inferior (`min(open, close) - low`) igual ou maior que 50% do range do
candle (`high - low`) **e** fechamento de recuperação (`close > open`).
50% é o ponto em que o pavio domina o corpo do candle — abaixo disso o
candle seria majoritariamente corpo, não "preço ultrapassou e voltou" como
a literatura descreve a cascata. Declarado antes de qualquer medição, não
ajustado depois de ver o resultado.

## D2 — proxy do pico de volume: ≥ 3x a média móvel de 20 candles

Volume do candle igual ou maior que 3× a média móvel simples dos últimos 20
candles. `ADAPTIVE_RSI_VOLUME_RATIO` (produção, `config/settings.py`) usa
2,0x como "volume confirma um pico real" para um propósito mais permissivo
(liberar uma entrada já filtrada por tendência); aqui o volume é o próprio
gatilho do sinal, não um confirmador adicional, então o limiar é mais
rigoroso (3x) para reduzir a chance de ler um pico de volume comum como
cascata de liquidação. A janela de 20 candles é declarada como constante
própria do módulo de pesquisa, não acoplada a `VOLUME_MA_PERIOD` de
produção — mudar o padrão de produção não deve silenciosamente mudar o
resultado já medido desta hipótese.

## D3 — universo: `UNIVERSO_H11`

Mesmos 12 pares já usados por H26 (`backtesting/horizonte.py::UNIVERSO_H11`)
— família direcional já estabelecida neste registro (S6.3-b), evita
declarar um universo novo ad hoc para mais uma hipótese da mesma família de
resultado historicamente fraco (22 hipóteses direcionais consecutivas sem
sobreviver à confirmação, por trás da qual esta entra como a 23ª).

## D4 — timeframe e janela: 4h, 2000 candles por par

Mesmo `TIMEFRAME` padrão do projeto e mesma ordem de grandeza de histórico
(~333 dias) já usada por H26/H14 antes do histórico estendido — por
tratabilidade de tempo de execução da bateria completa (E1-E6, ~9
simulações por par) sobre 12 pares.

## Nota de instrumentação — primeira hipótese sobre o harness comum

H34 é a primeira hipótese a rodar inteiramente através de
`backtesting/bateria_hipotese.py::rodar_bateria` (E1-E6), em vez de
reimplementar a orquestração como H8-H33 fizeram cada uma por conta própria
— ver o comentário correspondente em
`docs/research/registro-de-hipoteses.md` §7.1. Qualquer defeito do harness
em si (não do sinal desta hipótese) apareceria aqui primeiro; por isso E1
(sanidade) usa uma série sintética construída para nunca produzir o padrão
declarado em D1/D2, isolando defeito de motor de resultado de estratégia.

## Hipótese declarada antes de medir

**Principal:** um candle que bate o proxy (D1 + D2) antecede retorno
positivo acima do baseline, e esse excesso sobrevive tanto à divisão
treino/validação quanto ao walk-forward, mesmo sem custo reduzido (E6).

**Alternativa, com peso igual:** o proxy captura o mesmo ruído estatístico
já testado por H3 (reversão à média via Bollinger+RSI, reprovada, win rate
20-31%), e qualquer resultado positivo aparente não sobrevive à validação
fora da amostra nem ao walk-forward — resultado tão válido quanto o
positivo, dado que o objetivo desta rodada é decidir a família de mecanismo
(liquidação forçada via proxy), não confirmar a tese antes de medir.

## Reprodução

`python main.py liquidacao`.

(Resultado real preenchido após a execução — ver
`docs/research/registro-de-hipoteses.md` §6.1 para o veredito medido, com
comparação explícita contra H3.)
