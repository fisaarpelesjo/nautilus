# Fase 0 — Pesquisa: H13, barras dirigidas por informação

**Data:** 2026-09-01

A spec deixou quatro decisões para esta fase. Todas resolvidas por medição sobre
os 12 pares do universo já usado nas avaliações anteriores.

---

## D1 — Granularidade de base

**Decisão:** candles de **1h**, 8.000 por par.

### O problema declarado na spec

Barras dirigidas por informação canônicas se constroem a partir de negociações
individuais. O projeto consome candles agregados, então uma barra só pode ser
uma união de candles **inteiros** — a granularidade mínima é um candle, e as
barras resultantes são sempre mais grossas que a série de origem. Construídas
sobre 4h, seriam grossas demais para significar alguma coisa.

### Medição

Quanto histórico a corretora entrega por granularidade:

| Timeframe | Candles | Dias cobertos |
|---|---|---|
| 4h | 2.000 | 333,2 |
| 1h | 2.000 | 83,3 |
| 15m | 2.000 | 20,8 |

À primeira vista, granularidade fina custa janela de calendário — e comparar 21
dias contra 333 não responderia nada. **Mas `fetch_ohlcv` pagina:**

| Timeframe | Candles | Dias cobertos |
|---|---|---|
| 1h | 4.000 | 166,6 |
| **1h** | **8.000** | **333,3** |

`1h × 8.000 = 333,3 dias` é **a mesma janela de calendário** de `4h × 2.000 =
333,2 dias`, que é a janela de todas as doze hipóteses já avaliadas.

**Rationale.** Isto resolve simultaneamente a restrição 1 (granularidade) e a
restrição 4 (âncora de calendário): a comparação passa a ser entre dois
esquemas de amostragem sobre exatamente o mesmo período, com o mesmo
buy-and-hold, contra o mesmo universo das avaliações anteriores.

**Perda declarada em relação a dados de negociação.** Fronteiras de barra só
caem em marcas de hora. Com mediana de 4 candles por barra (ver D3), o erro de
posicionamento da fronteira é de até ±0,5h numa barra de ~4h, ou seja **~12%**
da largura típica. É aproximação, e está quantificada. Não é equivalente a
dados de tick, e o veredito deve dizê-lo.

**Alternativa considerada.** 15m × 32.000 daria resolução de ±7,5min. Rejeitada:
são 4× mais requisições por par, e o ganho de resolução não muda a conclusão
qualitativa sobre uma barra que agrupa 16 candles de 15m em vez de 4 de 1h. Fica
registrado como caminho caso o veredito seja inconclusivo por resolução.

---

## D2 — Calibração do limiar

**Decisão:** limiar calibrado por iteração de Newton sobre a **contagem de
barras**, até ficar a 5% da contagem de barras de tempo, máximo 6 iterações.

### Por que o limiar não pode ser arbitrário

Restrição 2 da spec: barras dirigidas produzem uma quantidade diferente de
observações sobre o mesmo período. Comparar 1.532 barras contra 2.000 candles é
comparar tamanhos de amostra, não esquemas de amostragem.

Limiar ingênuo `total / 2000` não acerta o alvo, porque a barra fecha **ao
cruzar** o limiar e o candle que cruza costuma passar bastante do ponto:

| Par | Contagem por iteração | Erro final |
|---|---|---|
| BTC/USDT | 1615 → 1925 | 3,8% |
| BCH/USDT | 1366 → 1815 → 1944 | 2,8% |
| LTC/USDT | 1485 → 1870 → 1957 | 2,1% |

O passo `limiar ← limiar × contagem / alvo` converge em 2–3 iterações.

**Rationale, e por que isto não é varredura.** A calibração consulta
**exclusivamente a contagem de barras**. Nenhuma métrica de retorno, drawdown ou
profit factor participa. É calibração de **escala**, exatamente como o alvo de
volatilidade de H12 foi fixado pela mediana de `atr_ratio` — e pela mesma razão:
o mecanismo precisa ser neutro em escala para que o que se meça seja o
posicionamento das barras, não a quantidade delas.

**Declaração honesta:** a calibração usa o mesmo período que será avaliado.
Calibração dentro da amostra, portanto — mas de escala, não de desempenho. A
alternativa (limiar fixo em dólares para todos os pares) produziria 200 barras
em TRX e 8.000 em BTC, e aí a comparação mediria liquidez do par.

---

## D3 — Variantes de construção

**Decisão:** duas variantes — **valor negociado acumulado** (dollar bars) e
**desvio acumulado** (CUSUM).

### Medição (12 pares, base 1h × 8.000, alvo 2.000 barras)

| Variante | Barras (mediana) | Candles/barra (mediana) | p90 | Máx | % de barras com 1 candle |
|---|---|---|---|---|---|
| Dollar | 1.532 | 4,0 | ~10 | 21–64 | **9,4%** |
| CUSUM | 1.152 | 5,0 | ~15 | 39–78 | **10,7%** |

**O número que decide a viabilidade é o último.** Se a maioria das barras
fosse de um candle só, a reamostragem seria inerte e H13 mediria nada — foi
exatamente o que aconteceu com 37 das 48 combinações de H12, e o registro tem o
estado `inerte` por causa disso.

Com 9–11%, a reamostragem **atua de fato**: a largura varia de 1 a 78 candles.
Períodos parados se comprimem em barras largas, períodos agitados se abrem em
barras finas. É o que a hipótese postula.

**Volume bars foram descartadas.** Sobre cripto, volume em unidades do ativo e
valor em dólar carregam quase a mesma informação, e o valor é comparável entre
pares de preços muito diferentes. Uma terceira variante quase colinear
adicionaria combinações à varredura — e mais combinações significam mais
aprovações por acaso — sem responder nada que as duas primeiras não respondam.

---

## D4 — Qual medida de exposição descontar

**Decisão:** exposição em **tempo** (`ganho_de_timing_pp`, a métrica original de
M7), **somada** à guarda de base perdedora de M11.

### O raciocínio, e por que difere de H12

A spec pergunta se a amostragem exige uma quarta forma da família M7/M10/M11.
Analisando o que cada mecanismo move:

| Hipótese | O mecanismo varia | Medida certa |
|---|---|---|
| H7 | tempo em mercado | tempo (M7) |
| H12 | capital por operação | capital (M10) |
| **H13** | **quando os sinais ocorrem** | **tempo (M7)** |

Mudar a amostragem muda **onde as decisões acontecem no calendário**, e portanto
os instantes de entrada e saída. Diferente de H12 — onde o mecanismo alterava só
o tamanho e a exposição de tempo era invariante por construção — aqui a
exposição de tempo **responde**. A medida original serve.

**M11 também se aplica, e por conta própria.** Barras mais grossas produzem
menos operações. Sobre estratégia de expectativa negativa, operar menos aproxima
o resultado de zero e qualquer métrica de melhora registra ganho. A guarda
`confundido` de H12 é reusada sem alteração.

**Predição registrada:** espera-se `delta_exposicao_tempo` **diferente de zero**.
Se vier zero como em H12, a premissa acima está errada, e essa é a descoberta —
seria a quarta forma da família que a spec previu como achado principal
possível.

---

## D5 — Ponto de integração

**Decisão:** função de reamostragem aplicada ao DataFrame **entre a busca de
dados e o cálculo de indicadores**, sem tocar motor nem estratégias.

**Rationale.** `horizonte.preparar(df, estrategia)` já é o ponto onde os
indicadores são calculados uma vez sobre a série. Reamostrar antes dele entrega
uma série com o mesmo contrato de colunas, e todo o resto — indicadores, motor,
walk-forward, validação — funciona sem saber que a amostragem mudou.

As alternativas foram rejeitadas pelas mesmas razões de sempre:

1. **Motor próprio para barras.** Rejeitada: duas implementações da mesma lógica
   de execução é o defeito M1.
2. **Alterar `data/fetcher.py`.** Rejeitada: o caminho de busca é compartilhado
   com produção, e FR-015 exige que o bot não mude.

A comparação pareada reusa a estrutura de `backtesting/volatilidade.py`, que já
resolveu o problema de rodar a mesma estratégia em duas versões da mesma série.

---

## D6 — Executabilidade operacional (FR-017)

**Decisão:** seria **executável**, com uma ressalva declarada.

O bot busca candles periodicamente e decide a cada ciclo. Construir barras
dirigidas ao vivo significaria acumular valor negociado dos candles de 1h desde
o fechamento da última barra e emitir a decisão quando cruzasse o limiar. Isso
não exige infraestrutura nova: é aritmética sobre dados que o bot já busca.

**Ressalva:** o limiar é calibrado sobre histórico, e regimes de volume mudam.
Um limiar de 2025 aplicado em 2027 produziria barras sistematicamente mais
largas ou mais finas do que o pretendido. Operar isto exigiria recalibração
periódica — mecanismo que não existe e que **esta spec não implementa**.

Registrar isto agora importa porque aprovar algo inexecutável é pior que
reprovar, e a decisão sobre a ressalva pertence ao usuário, não à avaliação.

---

## Resumo das decisões

| # | Decisão | Efeito |
|---|---|---|
| D1 | Base 1h × 8.000 | 333,3 dias, mesma janela do 4h × 2.000; erro de fronteira ~12% |
| D2 | Limiar por Newton sobre contagem | N pareado a 5%; consulta só contagem, nunca retorno |
| D3 | Dollar + CUSUM | 9–11% de barras de 1 candle: reamostragem atua, não é inerte |
| D4 | Exposição em tempo + guarda M11 | Reusa M7 e `confundido`; sem métrica nova |
| D5 | Reamostragem antes de `preparar()` | Motor, estratégias e produção intactos |
| D6 | Executável com ressalva | Limiar precisaria de recalibração periódica |

**Expectativa registrada antes da execução:** as doze hipóteses anteriores
reprovaram sobre amostragem por tempo. Se a amostragem fosse a causa, esperar-se-ia
melhora ampla e consistente ao trocá-la. O resultado mais provável, dado o
histórico do registro, é que a amostragem mude os números sem mudar o veredito —
e nesse caso H13 encerra a suspeita de que as reprovações anteriores mediram o
relógio em vez da estratégia. Registrar a previsão antes permite distinguir,
depois, previsão de racionalização.

## Fontes

- Medição própria, 2026-09-01: 12 pares × 8.000 candles de 1h.
- Lopez de Prado, *Advances in Financial Machine Learning*, cap. 2 (barras
  dirigidas por informação).
- `docs/research/registro-de-hipoteses.md` §4.13 (H12, estado `inerte`), §5
  (M1, M2, M7, M10, M11).
