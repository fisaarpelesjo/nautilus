# Research: H36 — Hash Ribbons: capitulação de mineradores (BTC-only)

## D1 — definição do cruzamento: médias móveis simples de 30/60 dias, sem suavização

Cruzamento de alta: média de 30 dias do hashrate cruza de baixo para cima
da média de 60 dias (`ma30.shift(1) <= ma60.shift(1)` e `ma30 > ma60` no
dia seguinte). Cruzamento de baixa: o inverso. Sem suavização adicional
sobre o hashrate bruto da fonte pública — definição fixada antes de medir
qualquer desempenho.

**Achado empírico (probe real, 2026-09-06).** Sobre a série real
(`fetch_onchain_series("hash-rate", timespan="3years")`, 1085 pontos
diários, 2023-09-07 a 2026-09-05): 16 cruzamentos de alta e 16 de baixa —
mais frequente que os "~14 sinais em 13 anos" da literatura original
(Charles Edwards/Capriole). Hipótese mais provável: a série pública do
blockchain.info é mais ruidosa que o indicador original, possivelmente já
suavizado por médias adicionais ou tratamento de outliers na fonte
original. **Não ajustado**: a definição do cruzamento já estava fixada
antes deste probe ser rodado; a frequência observada é reportada como
contexto, não motivo para redesenhar a definição.

## D2 — mecânica do trade: entrada e saída pelo próprio indicador

BUY no cruzamento de alta (recuperação após capitulação), SELL no
cruzamento de baixa simétrico — sem SL/TP artificial novo. O
SL/TP/trailing por ATR já genérico de `simulate_backtest` permanece ativo
sem alteração (mesmo comportamento que a produção teria com qualquer
sinal). Diferença deliberada em relação a H26/H35 (que também usam
barreira tripla/ATR para todo trade): aqui o próprio indicador já define
quando sair, então o ATR do motor funciona como proteção adicional
sobreposta, não como o único mecanismo de saída.

**Risco declarado.** O holding médio histórico do sinal original (~253
dias) é muito mais longo que qualquer horizonte já medido neste registro.
Se o stop por ATR (1,5×ATR, `ATR_SL_MULTIPLIER`) interromper a posição
antes do cruzamento de saída, isso é esperado e não deve ser "corrigido"
desativando o SL/TP — desativar o SL/TP misrepresentaria como o bot
realmente operaria esse sinal em produção. O resultado, seja qual for,
mede a interação real entre o sinal e a infraestrutura de risco existente.

## D3 — alinhamento causal e descarte de candles sem histórico real

Mesmo helper já existente `backtesting.onchain_hipotese._merge_causal`
(usado por H17/H32, sem alteração): candle do dia D usa o valor completo
do dia D-1, nunca o dia corrente (ainda incompleto na fonte). Diferente de
H26 (funding, retenção completa) e igual a H35 (D4): candles anteriores
ao primeiro dia com hashrate disponível são DESCARTADOS do universo
avaliável, nunca um cruzamento presumido antes de existir dado real.

## D4 — universo e janela de dados

Somente `BTC/USDT` — hashrate é métrica exclusiva da rede Bitcoin, sem
equivalente para os demais pares do bot (mesma limitação estrutural já
declarada por H17/H32/H36 na fundamentação). Candles buscados com margem
suficiente para cobrir toda a janela real de hashrate disponível
(2023-09-07 em diante): confirmado por probe real que 7.000 candles de 4h
alcançam 2023-06-28, antes do início do hashrate — margem suficiente sem
custo de rede desnecessário.

## D5 — disciplina estatística: mesma bateria E1-E6, mesmo risco de amostra de H34

Amostra esperada pequena por construção (16 cruzamentos de alta possíveis
no máximo, distribuídos por busca/confirmação/walk-forward) — mesma
categoria de risco de H34 (proxy raro) e H10 antes da correção de spec
054. `rodar_bateria` já trata amostra insuficiente como `inconclusivo` em
cada etapa (nunca aprovado por omissão de dado), então o resultado
esperado mais provável, declarado antes de medir, é `inconclusivo`, não
necessariamente `reprovado`.

## Hipótese declarada antes de medir

**Principal:** o cruzamento de alta das médias de 30/60 dias do hashrate
antecede retorno positivo em BTC/USDT acima do baseline, mesmo com o
SL/TP por ATR do motor ativo sem alteração.

**Alternativa, com peso igual:** a amostra disponível no histórico de
candles (limitada pela retenção do hashrate, D4) é pequena demais para
qualquer leitura ter peso, ou o SL/TP por ATR interrompe sistematicamente
o hold antes do sinal completar seu ciclo histórico — ambos resultados
igualmente informativos, dado que o objetivo desta rodada é medir a
interação real entre um sinal de OFERTA (mecanismo nunca testado antes) e
a infraestrutura de risco existente, não confirmar a tese antes de medir.

## Comparação planejada com H17/H32

Mesma fonte de dado (`data/onchain.py`), mecanismo de sinal categoricamente
diferente: H17/H32 usam a métrica on-chain como ATRIBUTO de um classificador
supervisionado (barreira tripla); H36 usa o hashrate como sinal de
entrada/saída DIRETO, sem modelo intermediário. O registro final compara
os dois resultados explicitamente — mesma fonte, mecanismos diferentes,
vereditos que podem legitimamente divergir sem contradição.

## Reprodução

`python main.py hashribbons`.

(Resultado real preenchido após a execução — ver
`docs/research/registro-de-hipoteses.md` §6.1 para o veredito medido, com
comparação explícita contra H17/H32.)
