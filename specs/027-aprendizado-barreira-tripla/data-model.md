# Fase 1 — Modelo de dados: H14

## `ParametrosBarreira`

Governa a rotulagem. Reusa os multiplicadores do bot (D2), sem parâmetro novo de
risco.

| Campo | Tipo | Padrão | Descrição |
|---|---|---|---|
| `sl_mult` | `float` | `ATR_SL_MULTIPLIER` (1,5) | Distância do stop, em múltiplos de ATR |
| `tp_mult` | `float` | `ATR_TP_MULTIPLIER` (3,0) | Distância do alvo |
| `limite_velas` | `int` | `24` | Terceira barreira: limite de tempo |

**Invariantes:** `sl_mult > 0`, `tp_mult > 0`, `limite_velas >= 1`. Valores não
positivos produziriam barreiras degeneradas — tocadas imediatamente ou nunca.

**Razão de empate declarada:** `sl_mult / tp_mult = 0,500`. É a razão de chances
alvo/stop que o modelo precisa atingir para não perder dinheiro (D2). Observada
ao acaso: 0,372.

---

## `EventoRotulado`

Uma linha do conjunto de treino.

| Campo | Descrição |
|---|---|
| `instante` | Momento do evento |
| `par` | Símbolo de origem — necessário porque os pares são agrupados (D4) |
| `rotulo` | `1` se o alvo foi tocado primeiro, `0` caso contrário |
| `rotulo_bruto` | `+1` alvo, `−1` stop, `0` tempo — preservado para o relatório |
| `fim_horizonte` | Instante em que a barreira foi tocada, **ou** o limite de tempo |
| *atributos* | Os cinco de D3 |

**`fim_horizonte` é o campo que torna a purga possível.** Sem ele não há como
saber quais amostras de treino se sobrepõem à janela de teste, e a purga vira
uma aproximação por distância fixa. O rótulo em `t` só é conhecido em
`fim_horizonte`, e é essa a informação que não pode vazar.

**`rotulo` é binário** (D1): o bot só opera comprado, então `stop` e `tempo`
colapsam na classe negativa. `rotulo_bruto` sobrevive para o relatório poder
exibir as três frequências, que é o que revela desbalanceamento.

---

## `ConjuntoAtributos`

Lista **declarada** e fixa (D3, FR-003):

| Atributo | Natureza | Correlação máxima com os demais mantidos |
|---|---|---|
| `volume_ratio` | Liquidez relativa | 0,000 |
| `atr_ratio` | Volatilidade relativa | 0,009 |
| `adx` | Força de tendência | 0,382 |
| `dist_ema_slow` | Posição relativa à tendência | 0,281 |
| `macd` | Momento | 0,699 |

Todos adimensionais ou normalizados pelo preço — pré-condição para agrupar
pares de preços muito diferentes.

**Descartados por colinearidade**, com o valor medido: `rsi` (0,901),
`pos_bb` (0,807), `dist_ema_fast` (0,959), `dist_ema_trend` (0,908). Todos
contra `dist_ema_slow`.

---

## `DivisaoPurgada`

Um par de janelas treino/teste com o vazamento removido.

| Campo | Descrição |
|---|---|
| `inicio_teste` / `fim_teste` | Fronteiras temporais da janela de teste |
| `indices_treino` | Amostras que sobreviveram à purga e ao embargo |
| `n_purgadas` | Quantas saíram por sobreposição de horizonte |
| `n_embargadas` | Quantas saíram pelo embargo |
| `embargo_velas` | `24` — o horizonte **máximo**, não o mediano (D4) |

**Regra de purga (a definição operacional):** uma amostra de treino é removida
se `fim_horizonte >= inicio_teste` e `instante <= fim_teste`. Em português: se o
desfecho dela só se conhece depois que a janela de teste começou, ela carrega
informação da janela de teste.

**A purga é temporal e global, não por par.** Consequência de agrupar 12 pares
correlacionados a 0,71 (medido em H9). Purgar par a par deixaria a amostra de
BTC em `t` no treino enquanto a de ETH em `t` está no teste — e, movendo-se
juntos, o modelo veria pelo BTC o desfecho que deve prever para o ETH.

---

## `ResultadoModelo`

Saída de uma execução do classificador.

| Campo | Descrição |
|---|---|
| `convergiu` | Se a estimação convergiu |
| `coeficientes` | Um por atributo, mais intercepto |
| `n_treino` / `n_teste` | Tamanhos efetivos após purga |
| `dist_classes` | Frequência de alvo, stop e tempo |
| `razao_chances_geral` | Alvo/stop em toda a amostra de teste |
| `razao_chances_decidido` | Alvo/stop **apenas onde o modelo decide entrar** |
| `backtest` | Resultado da simulação com o sinal do modelo |

**`razao_chances_decidido` é a métrica central.** A geral é propriedade dos
dados; a do subconjunto decidido é o que o modelo produziu. Se ela não superar
`0,500`, o modelo não pode ser lucrativo com estas barreiras — independentemente
da acurácia, que é enganosa aqui: prever sempre "stop" acerta 62,8% e nunca
opera.

---

## `AvaliacaoH14`

A unidade de análise: um par, com as três linhas de base.

| Campo | Descrição |
|---|---|
| `par` | Símbolo |
| `modelo` | `ResultadoModelo` com rótulos reais |
| `embaralhado` | `ResultadoModelo` com rótulos permutados |
| `regras` | Resultado da estratégia de regras sobre a mesma série e período |
| `retorno_sem_custo_*` | Reexecução com custo zerado |
| `status` / `motivo` | Veredito |

### Grandezas derivadas

| Propriedade | Definição |
|---|---|
| `delta_retorno` | `modelo − regras` |
| `delta_drawdown` | `modelo − regras` |
| `delta_exposicao` | Exposição de tempo, `modelo − regras` |
| `delta_timing` | Ganho descontada a exposição, `modelo − regras` |
| `delta_vs_embaralhado` | `modelo − embaralhado`, em ganho de timing |
| `delta_operacoes` | `modelo − regras` |
| `delta_custo` | Parcela atribuível a taxa e slippage |
| `supera_empate` | `razao_chances_decidido > 0,500` |

**`delta_vs_embaralhado` é a grandeza que decide.** As demais respondem "o
modelo é melhor que as regras?"; só esta responde "o que o modelo achou está nos
dados ou na capacidade dele?".

---

## Estados de `AvaliacaoH14`

**A ordem das checagens é a regra**, como em 024, 025 e 026.

| # | Estado | Condição |
|---|---|---|
| 1 | `erro` | Falha ao obter dados ou rotular |
| 2 | `nao_convergiu` | A estimação não convergiu (FR-012) |
| 3 | `classe_unica` | Todos os eventos na mesma classe — nada a classificar |
| 4 | `inconclusivo` | Amostra de treino ou teste abaixo do mínimo após purga |
| 5 | `inconclusivo` | Operações abaixo do mínimo em **qualquer** versão (FR-011) |
| 6 | `sem_sinal` | Desempenho não se distingue do embaralhado (FR-008) |
| 7 | `insuficiente` | Distingue-se do embaralhado, mas `razao_chances_decidido <= 0,500` |
| 8 | `piora` | `delta_drawdown > 0` |
| 9 | `sem_vantagem` | `delta_timing <= 0` |
| 10 | `confundido` | Retorno das regras `<= 0` (guarda M11) |
| 11 | `inconclusivo` | Sem janela de validação válida |
| 12 | `so_na_busca` | Vantagem não se sustenta fora da amostra |
| 13 | `melhora` | Todas as anteriores superadas |

Justificativas herdadas do registro:

- **`nao_convergiu` e `classe_unica` precedem tudo** (FR-012): sem modelo
  estimado não há o que julgar, e métricas calculadas sobre uma estimação que
  falhou seriam silenciosamente inválidas.
- **`sem_sinal` precede qualquer métrica de desempenho**: se o embaralhado
  empata, tudo o que vier depois é ruído bem ajustado.
- **`insuficiente` é estado novo neste registro.** Distingue "não há sinal" de
  "há sinal, e ele não paga as barreiras". A segunda é informação real, e
  colapsá-la em reprovação perderia o único achado positivo possível de H14.
- **`confundido`** (M11), **`so_na_busca`** (H10), **regra de amostra** (M9):
  reusados sem alteração.

---

## `RelatorioH14`

| Campo | Descrição |
|---|---|
| `avaliacoes` | Lista de `AvaliacaoH14` |
| `atributos` | Os cinco declarados, exibidos na saída (FR-003) |
| `parametros_barreira` | Multiplicadores e limite |
| `razao_empate` | `0,500`, declarada |
| `contagem_por_estado` | Quantas em cada estado |
| `executavel_em_producao` | Declaração de D6, com a ressalva de retreino |

A contagem aparece **antes** da tabela: o agregado é o resultado, e quem lê uma
tabela longa forma a impressão pelas primeiras linhas.
