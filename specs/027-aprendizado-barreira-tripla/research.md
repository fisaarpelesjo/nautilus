# Fase 0 — Pesquisa: H14, aprendizado supervisionado com barreira tripla

**Data:** 2026-09-01

Cinco decisões, todas resolvidas por medição sobre os 12 pares do universo
(4h × 2.000 candles, 23.412 eventos rotulados).

---

## D1 — Estimador

**Decisão:** regressão logística binária via `statsmodels`, alvo = "o preço toca
a barreira superior antes da inferior".

**Rationale.** `scikit-learn` está **ausente** do ambiente; `statsmodels` já é
dependência de desenvolvimento e já foi usado no portão ADF de H10. Não
introduzir dependência é FR-016.

Mas a razão principal não é ambiental, e sim metodológica. O risco dominante é
sobreajuste, e o registro já o quantificou: H13 testou 96 combinações e produziu
**uma** aprovação confirmada fora da amostra — abaixo do que o acaso produziria.
Um modelo de alta capacidade multiplicaria esse problema.

Com 5 atributos e intercepto são **6 parâmetros** para ~16.000 amostras de
treino: razão de 2.700 para 1. Sobreajuste por capacidade fica implausível **por
construção**, e o que sobrar de desempenho é atribuível aos dados.

**Alvo binário, não ternário.** O bot opera apenas comprado. A decisão que ele
precisa tomar é "entrar agora?", cuja resposta útil é a probabilidade de o alvo
ser atingido antes do stop. Colapsar `stop` e `tempo` numa classe negativa
mantém o alvo alinhado à decisão real e evita um terceiro conjunto de
coeficientes que ninguém consultaria.

**Alternativas rejeitadas.** Árvore ou ensemble: mais graus de liberdade,
exatamente o que a evidência acumulada desaconselha. Rede neural: idem, e
exigiria dependência nova.

---

## D2 — Barreiras e o limiar de sucesso

**Decisão:** reusar os multiplicadores que o bot já aplica — stop em
`1,5 × ATR`, alvo em `3,0 × ATR` — e limite de tempo de **24 velas** (4 dias em
4h).

**Medição** (12 pares, 23.412 eventos):

| Barreira tocada primeiro | Frequência |
|---|---|
| Alvo (`+3,0 ATR`) | **23,4%** |
| Stop (`−1,5 ATR`) | **62,8%** |
| Limite de tempo | 12,8% |

Horizonte mediano até uma barreira ser tocada: **8 velas** (32 horas).

### O achado que dá a H14 um critério quantitativo

Uma entrada em instante **aleatório** com essas barreiras tem expectativa:

```
E = 0,234 × 3,0 − 0,628 × 1,5 = −0,241 ATR
```

**Negativa.** O par de barreiras que o bot usa perde dinheiro se acionado ao
acaso — o stop está a metade da distância do alvo e é tocado 2,7 vezes mais.

Disso sai o limiar que o classificador precisa vencer, e ele é declarável antes
do teste:

| Grandeza | Valor |
|---|---|
| Razão de chances alvo/stop observada | 0,372 |
| Razão necessária para empatar | 0,500 |
| **Elevação relativa exigida do modelo** | **+34,3%** |

Este é um critério **melhor** que "superar buy-and-hold", porque é interno à
decisão que o modelo toma e não depende do regime do período. Fica registrado
aqui, antes da execução, para que a avaliação não possa ser reinterpretada
depois.

**Consequência para a leitura do resultado.** Um classificador que não eleve a
razão de chances acima de 0,5 no subconjunto em que decide entrar **não pode**
ser lucrativo com estas barreiras, por mais alta que seja sua acurácia. Acurácia
não é a métrica: prever sempre "stop" acerta 62,8% e nunca opera.

---

## D3 — Conjunto de atributos

**Decisão:** cinco atributos — `volume_ratio`, `atr_ratio`, `adx`,
`dist_ema_slow`, `macd`.

**O problema medido: colinearidade severa.** Dos nove candidatos derivados dos
indicadores existentes, vários são quase o mesmo número:

| Par de atributos | Correlação absoluta |
|---|---|
| `dist_ema_fast` ↔ `dist_ema_slow` | **0,959** |
| `dist_ema_trend` ↔ `dist_ema_slow` | **0,908** |
| `rsi` ↔ `dist_ema_slow` | **0,901** |
| `pos_bb` ↔ `dist_ema_slow` | **0,807** |
| `macd` ↔ `dist_ema_slow` | 0,699 |
| `volume_ratio` ↔ qualquer | 0,033 |

Correlação de 0,96 entre atributos torna a estimação de máxima verossimilhança
instável: os coeficientes ficam mal determinados e o modelo pode não convergir.
É exatamente o caminho de falha que FR-012 antecipou.

**Seleção gulosa em ordem declarada.** A ordem é por **distinção conceitual** —
liquidez, volatilidade, força de tendência, posição relativa, momento — e não
por desempenho preditivo. Nenhuma métrica de acerto participa da seleção; caso
contrário isso seria busca de atributos, proibida por FR-003.

| Ordem | Atributo | Correlação máxima com os já mantidos | Decisão |
|---|---|---|---|
| 1 | `volume_ratio` | — | mantém |
| 2 | `atr_ratio` | 0,009 | mantém |
| 3 | `adx` | 0,382 | mantém |
| 4 | `dist_ema_slow` | 0,281 | mantém |
| 5 | `rsi` | 0,901 | **descarta** |
| 6 | `pos_bb` | 0,807 | **descarta** |
| 7 | `macd` | 0,699 | mantém |
| 8 | `dist_ema_fast` | 0,959 | **descarta** |
| 9 | `dist_ema_trend` | 0,908 | **descarta** |

Limiar de 0,80, declarado. `macd` entra a 0,699 — é o mais próximo do limiar e
isso fica registrado.

**Todos os atributos são adimensionais ou normalizados pelo preço**, para serem
comparáveis entre pares de preços muito diferentes. É pré-condição de D4.

---

## D4 — Purga, embargo e o agrupamento entre pares

**Decisão:** treinar um modelo único sobre os 12 pares agrupados, com purga e
embargo aplicados **no eixo do tempo, simultaneamente a todos os pares**.

**Custo da purga é desprezível.** Horizonte mediano de 8 velas contra 16.388
amostras de treino: a purga remove ~8 amostras na fronteira e o embargo outras
~8. Restam **100,0%** do treino ingênuo (arredondado). A preocupação registrada
na spec — de que purga e embargo pudessem esvaziar a amostra — **não se
materializa** nesta configuração, e isso é resultado da medição, não suposição.

**Mas o agrupamento cria um vazamento que a purga por par não cobriria.** Este é
o ponto não óbvio desta fase.

Agrupar 12 pares dá 23.412 amostras em vez de 1.951 — necessário para que 6
parâmetros sejam estimados com folga. Só que criptoativos são fortemente
correlacionados: **H9 mediu correlação de 0,71** entre os pares do universo, e
foi por isso que aquela hipótese reprovou.

Se a purga fosse aplicada par a par, a amostra de treino de BTC no instante `t`
permaneceria no treino enquanto a amostra de ETH em `t` estivesse no teste. Como
os dois se movem juntos, o modelo veria, pelo BTC, o desfecho que deveria prever
para o ETH. **A purga tem de ser temporal e global**: qualquer amostra, de
qualquer par, cujo horizonte alcance a janela de teste sai do treino.

Sem essa decisão, H14 produziria desempenho excelente e inteiramente artificial —
é o análogo, em dados agrupados, do achado M2.

**Embargo = horizonte máximo (24 velas).** Não o mediano: o embargo protege
contra a cauda, e usar a mediana deixaria metade dos casos descobertos.

---

## D5 — Ponto de integração

**Decisão:** o modelo produz o sinal e o restante do caminho de avaliação
permanece inalterado — mesmo motor, mesma bateria, mesmas guardas.

**Rationale.** As specs 024, 025 e 026 estabeleceram o padrão: reusar
`preparar`, `_simular`, `split_train_validation`, `evaluate_approval` e as
guardas de exposição. Um motor próprio criaria duas implementações da mesma
lógica de execução, que é o defeito M1.

A comparação pareada reusa a estrutura de `backtesting/barras.py`, que já
resolveu rodar duas versões da mesma série com as guardas M7/M11 e a confirmação
fora da amostra.

---

## D6 — Executabilidade operacional (FR-017)

**Decisão:** seria **parcialmente executável**, e a ressalva é maior que a de
H13.

Avaliar o modelo a cada ciclo é barato: são cinco atributos e um produto
interno, sobre indicadores que o bot já calcula.

**Ressalva de primeira ordem: não existe mecanismo de retreino.** Um modelo
ajustado sobre 333 dias de histórico carrega o regime desse período. Diferente
do limiar de H13 — que também precisaria de recalibração, mas cuja degradação
seria gradual e observável na contagem de barras —, aqui a degradação é
silenciosa: o modelo continua emitindo probabilidades com aparência normal
enquanto a relação que ele aprendeu deixa de valer.

Operar isto exigiria retreino periódico **e** um mecanismo de detecção de
degradação. Nenhum dos dois existe, e esta spec não os implementa.

---

## Resumo das decisões

| # | Decisão | Efeito |
|---|---|---|
| D1 | Logística binária, 6 parâmetros | 2.700 amostras por parâmetro; sobreajuste implausível por construção |
| D2 | Barreiras do próprio bot, limite 24 velas | Limiar declarado: elevar a razão de chances em **+34,3%** |
| D3 | 5 atributos por seleção gulosa em ordem declarada | Evita colinearidade de 0,96 que impediria a estimação |
| D4 | Agrupar pares, purgar no tempo globalmente | Sem isso, correlação de 0,71 entre pares vazaria desfecho |
| D5 | Sinal do modelo no caminho existente | Motor, guardas e critérios inalterados |
| D6 | Parcialmente executável | Sem retreino nem detecção de degradação |

**Expectativa registrada antes da execução.** O padrão do registro (§6.3-b) é
que toda hipótese direcional falhou, e a medição de D2 mostra que a barreira a
vencer é alta: +34,3% na razão de chances. O resultado mais provável é que o
modelo não se distinga do modelo de rótulos embaralhados. Se for esse o caso,
H14 fecha a família direcional com catorze hipóteses de suporte, e a fila deve
migrar para a família relativa e não-preditiva, como §6.3-b já antecipou.

Se o modelo **se distinguir** do embaralhado mas ainda assim não atingir a razão
de 0,5, o resultado correto é reportar **sinal detectável porém insuficiente** —
categoria que o registro ainda não tem e que seria o achado desta spec.

## Fontes

- Medição própria, 2026-09-01: 12 pares × 2.000 candles de 4h, 23.412 eventos.
- `config/settings.py`: `ATR_SL_MULTIPLIER = 1.5`, `ATR_TP_MULTIPLIER = 3.0`.
- `docs/research/registro-de-hipoteses.md` §4.10 (H9, correlação 0,71), §4.14
  (H13, 1 aprovação em 96), §5 (M1, M2, M7, M10, M11, M12), §6.3-b.
- López de Prado, *Advances in Financial Machine Learning*, cap. 3 (barreira
  tripla) e cap. 7 (purga e embargo).
