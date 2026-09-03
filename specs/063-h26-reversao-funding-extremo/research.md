# Research: H26 — reversão contra funding extremo (crowding/liquidação)

## D1 — o que conta como "funding extremo"

Decil mais negativo (10º percentil, `PERCENTIL_EXTREMO = 0.10`) da
distribuição de funding do PRÓPRIO par — não um valor absoluto fixo
compartilhado entre pares. Justificativa: pares diferentes têm
distribuições de funding com escalas distintas (ativos mais
especulativos tendem a funding mais volátil); um limiar absoluto
compartilhado privilegiaria os pares de maior volatilidade de funding
por construção, não por sinal real. O decil é relativo à própria
história do par, calculado **antes** de olhar qualquer resultado.

**Por que 10%, não outro número.** Decil é o ponto de corte mais comum
na literatura de "crowding" via funding (ex.: métricas de sentimento de
mercado de derivativos) — um valor redondo, defensável, não ajustado
para produzir um resultado específico. Não foi testado contra
alternativas (5%, 15%, 20%) antes de escolher — isso seria variar até
achar um que "passa", o problema de testes múltiplos que a metodologia
deste registro existe para impedir (`docs/research/
registro-de-hipoteses.md`, protocolo E1-E6).

## D2 — mecânica do trade: só o lado long

Funding extremamente **negativo** (abaixo do decil calibrado) —
interpretado como posição majoritariamente vendida (shorts pagando para
manter a posição, indicador de crowding vendido) — dispara um evento de
entrada **comprada**, avaliado pela barreira tripla já existente de H14
(`stop 1,5×ATR`, `alvo 3,0×ATR`, `24 velas`, `ParametrosBarreira`
padrão, sem alteração).

O lado espelhado (funding extremamente positivo → contrário seria
vender/short) **não é testado**: o bot é long-only por restrição de
produção (`CLAUDE.md`), e abrir posição curta exigiria a mesma
infraestrutura de futuros que H8 (spec 058) e H24 nunca construíram
para produção real — permissão de API, gestão de margem, risco de
liquidação. Fica como limitação declarada, não como parte do escopo
desta spec.

## D3 — alinhamento causal funding → candle

Funding é publicado a cada 8h; `TIMEFRAME` do bot é 4h (`config/
settings.py`). Cada candle de 4h herda a última leitura de funding
publicada **até aquele instante** (`pd.Series.reindex(..., method="ffill")`)
— nunca uma leitura futura. Isso significa que dois candles consecutivos
de 4h podem compartilhar a mesma leitura de funding (a que ainda não
"virou") — comportamento esperado e correto, não um defeito de
alinhamento.

## D4 — disciplina estatística: calibrar só no treino, medir só na validação

Diferente de simplesmente rodar o decil sobre a série inteira (o que
vazaria informação da validação para dentro do critério de entrada), o
limiar de extremo é calculado **exclusivamente** sobre a fatia de
treino (primeiros `1 - DEFAULT_VALIDATION_RATIO` = 70% da série,
`backtesting/validation.py`, constante já existente, reusada sem
alteração) e aplicado **sem reajuste** à fatia de validação. A razão de
chances alvo/stop reportada é **só da validação** — nunca do treino, e
nunca da série inteira.

Significância avaliada via `supera_empate_com_confianca` (Wilson CI,
`backtesting/modelo.py`, já usado por H14/H20/H55) sobre as contagens
**agregadas (pooled) entre pares** — mesma lição de M9/M13: um par
isolado raramente acumula amostra suficiente para uma leitura confiável
de intervalo de confiança; o agregado é a unidade que tem poder
estatístico, mesmo padrão de H14 (`docs/research/
registro-de-hipoteses.md` §4.15).

## D5 — janela de dados

2.000 candles de 4h (~333 dias) por par — a mesma janela do H14
pré-"histórico estendido" (spec 036), escolhida por tratabilidade de
tempo de execução (esta spec busca preço E funding para até 12 pares,
mais chamadas de rede que uma avaliação só de preço). Funding buscado
com folga (`DIAS_FUNDING = 340`) para cobrir a janela de candles
inteira sem faltar dado no início da série. **Limitação declarada**:
uma janela maior (6.000 candles, ~2,7 anos, como a "histórico
estendido" de H14/H20) teria mais poder estatístico — não usada aqui
por custo de execução, não por escolha metodológica; se o resultado
desta spec vier `insuficiente`, ampliar a janela é o próximo passo
natural, mesmo padrão que já resolveu H14 (spec 036).

## Hipótese declarada antes de medir

**Expectativa honesta: REPROVADA é o resultado mais provável.** Base
histórica: 21 hipóteses direcionais anteriores neste registro, nenhuma
sobreviveu a custo de execução e confirmação fora da amostra (§6.3-b).
H26 usa um sinal diferente (funding extremo, não indicador técnico),
mas continua na mesma família estrutural (previsão de direção). Esta
spec não busca confirmar uma crença de que H26 vai funcionar — busca
medir com o mesmo rigor de qualquer outra hipótese e reportar o que
sair, positivo ou negativo.

## Reprodução

`python main.py funding_extremo` · `reports/funding_extremo_*.json`.

(Resultado real preenchido após a execução — ver
`docs/research/registro-de-hipoteses.md` §6.3 para o número medido.)
