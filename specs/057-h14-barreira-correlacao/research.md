# Research: H14 — saída por barreira tripla + gate de correlação

## D1 — por que as duas combinações anteriores dominaram, e por que esta pode ser diferente

Duas combinações de dois mecanismos de risco já foram medidas sobre a
carteira de H14:

- **Spec 043** (dimensionamento por volatilidade + gate de correlação):
  `total_trades` do combinado (595) idêntico ao do gate sozinho (595).
  O dimensionamento só reduz o TAMANHO de uma entrada que o gate já
  decidiu permitir — nunca muda QUAIS entradas abrem.
- **Spec 046** (gate de correlação + limite de drawdown diário):
  `total_trades` do combinado (594) praticamente idêntico ao do gate
  sozinho (595). O limite diário só dispara depois de uma perda agregada
  grande, e boa parte dessas perdas vêm exatamente de posições
  correlacionadas quebrando juntas — o gate já remove a causa raiz antes
  do limite diário ter chance de agir.

**O padrão comum às duas: o segundo mecanismo só reajusta a MESMA
decisão de entrada que o gate de correlação já filtra** (tamanho ou
pausa temporal) — nenhum dos dois muda como uma posição já aberta
termina.

**Saída por barreira (spec 056) não se encaixa nesse padrão.** Não
decide quando ou quanto abrir — decide como uma posição JÁ ABERTA sai
(stop fixo em vez de trailing, limite de tempo). O gate de correlação
decide quais posições abrem; a saída por barreira decide como as
posições que abriram terminam. São estágios diferentes do ciclo de vida
da posição, não a mesma decisão vista de dois ângulos — a razão
estrutural para a dominância nas duas combinações anteriores não se
aplica aqui.

## D2 — hipótese declarada antes de medir

**Principal (aditividade):** o drawdown combinado fica **abaixo** dos
dois isolados (barreira: 22,25%; correlação: 20,74%) — os dois efeitos
se somam, ao menos parcialmente, porque atacam pontos diferentes.

**Alternativa (dominância), com igual peso:** se a amostra de trades que
sobrevive ao gate de correlação já é, em grande parte, a mesma amostra
que se beneficia da saída por barreira (sobreposição, não
independência), o resultado combinado fica perto de um dos dois
isolados — repetindo o padrão das specs 043/046 apesar da diferença
estrutural.

Nenhuma das duas é considerada mais provável a priori — a estrutura
diferente (payoff de saída vs. filtro de entrada) é evidência a favor
de aditividade, mas as duas combinações anteriores também pareciam
"dimensões ortogonais" antes de medir (spec 046 dizia isso
explicitamente) e dominaram mesmo assim.

## D3 — comparação declarada

| | Sem overlay (037) | Só barreira (056) | Só correlação (042) | Combinado (057) |
|---|---|---|---|---|
| Trades | 931 | 543 | 595 | ? |
| Drawdown | 28,66% | 22,25% | 20,74% | ? |
| Profit factor | 0,72 | 0,78 | 0,68 | ? |

Se `total_trades` do combinado ficar perto de 543 (barreira) ou de 595
(correlação) isoladamente, é dominância. Se ficar significativamente
diferente dos dois (esperado: menor que ambos, já que o gate reduz
entradas E a barreira muda a saída de cada uma), é evidência de
composição real.

## Reprodução

`python main.py carteira_barreira_corr` · `reports/carteira_barreira_corr_*.json`.

(Resultado real preenchido após a execução — ver
`docs/research/registro-de-hipoteses.md` §4.15 para o número medido.)
