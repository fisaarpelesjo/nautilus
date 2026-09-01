# Fase 0 — Pesquisa: H11, horizonte temporal superior

**Data:** 2026-09-01

Nenhum marcador `NEEDS CLARIFICATION` restou da spec. Esta fase resolve as três
incógnitas técnicas que a spec deixou para verificação em execução, todas
medidas antes de escrever código.

---

## D1 — Disponibilidade real de histórico por horizonte

**Decisão:** avaliar 4h, 1d e 1w, sabendo de antemão que 1w não comporta a
bateria completa e será reportado como inconclusivo por construção.

**Medição** (12 pares, solicitação de 2000 candles, executada 2026-09-01):

| Horizonte | Candles obtidos | Cobertura | Aquecimento | Utilizáveis |
|---|---|---|---|---|
| 4h | 2000 (todos) | 333 dias | 8 dias | 1950 |
| **1d** | **2000 (todos)** | **2000 dias (5,5 anos)** | 50 dias | 1950 |
| 1w | **311 a 473** | 2177–3311 dias | **350 dias (0,96 ano)** | 261–423 |

Detalhe do horizonte semanal, por par:

| Par | Candles | Utilizáveis | Par | Candles | Utilizáveis |
|---|---|---|---|---|---|
| BTC | 473 | 423 | XRP | 436 | 386 |
| ETH | 473 | 423 | TRX | 430 | 380 |
| LTC | 456 | 406 | LINK | 399 | 349 |
| ADA | 438 | 388 | ATOM | 384 | 334 |
| BCH | 354 | 304 | SOL | 317 | 267 |
| DOT | 316 | 266 | AVAX | 311 | 261 |

**Rationale:** 1d é o achado favorável — entrega 5,5 anos de histórico contra
333 dias do horizonte atual, cobrindo múltiplos regimes de mercado. É onde a
hipótese tem chance real de ser respondida.

**Alternativas consideradas:** avaliar apenas 1d, descartando 1w por
insuficiência. Rejeitada porque a literatura citada (Liu & Tsyvinski 2021)
documenta o efeito em horizonte de **uma a quatro semanas**, e omitir a escala
semanal deixaria a hipótese parcialmente não testada. Avaliar 1w e **declarar
inconclusivo** é mais honesto que não avaliar.

---

## D2 — Consequência do tamanho amostral sobre a bateria

**Decisão:** dimensionar as janelas em função do histórico utilizável de cada
combinação, e emitir inconclusivo quando o dimensionamento não couber.

**Cálculo, com as constantes vigentes** (`MIN_WINDOW_CANDLES = 150`,
`DEFAULT_VALIDATION_RATIO = 0,3`, `EDGE_MIN_TRADES = 10`):

| Horizonte | Utilizáveis | Split 70/30 → validação | Cabe em E3? |
|---|---|---|---|
| 4h | 1950 | 585 | sim |
| 1d | 1950 | 585 | sim |
| 1w (BTC, melhor caso) | 423 | 127 | **não** (< 150) |
| 1w (AVAX, pior caso) | 261 | 78 | **não** |

**Nenhum par comporta E3 em horizonte semanal.** `split_train_validation` já
trata isso: quando a fatia fica abaixo de `MIN_WINDOW_CANDLES`, o split é
considerado inválido e o dataframe inteiro volta como treino, sem janela de
validação. O comportamento correto é reportar **inconclusivo**, não reprovado.

Para E4 (walk-forward), o número de janelas passa a ser derivado, não fixo:

```
n_janelas = min(5, utilizáveis // MIN_WINDOW_CANDLES)
```

Em 1w isso resulta em 1 ou 2 janelas — abaixo do mínimo de 3 exigido pelo
critério de E4, portanto também inconclusivo. Em 4h e 1d resulta em 5.

**Rationale:** essa é a lição direta de H10, onde uma janela de walk-forward
teve zero operações e o resultado quase foi lido como reprovação. A distinção
entre "não há vantagem" e "não há amostra" é o requisito FR-003 da spec.

**Alternativas consideradas:** reduzir `MIN_WINDOW_CANDLES` para acomodar 1w.
**Rejeitada** — alterar o limiar para fazer uma hipótese passar é seleção sobre
o próprio critério, exatamente o que a metodologia proíbe.

---

## D3 — Marcação de histórico curto sem gerar ruído

**Decisão:** distinguir **par listado recentemente** de **horizonte que limita
estruturalmente o histórico**.

**Problema medido:** a marcação ingênua (obtido < 50% do solicitado) sinalizou
**os 12 pares** em horizonte semanal. Isso é falso positivo por construção: 2000
candles semanais equivalem a 38 anos, e a Binance não existe há tanto tempo.
Uma marcação que dispara para todos não informa nada.

**Critério adotado:** um par é marcado como histórico curto quando seu total de
candles fica materialmente abaixo da **mediana do próprio horizonte**, não
abaixo do valor solicitado. Aplicado à medição:

- Em 1w a mediana é 414 candles. AVAX (311), DOT (316) e SOL (317) ficam ~25%
  abaixo — esses são listagens recentes de verdade e merecem marca.
- BTC e ETH (473) definem o teto do que o horizonte permite.

Independentemente da marca, o relatório **sempre declara** solicitado, obtido e
lacuna por combinação (FR-009), para que a limitação seja visível mesmo quando
não dispara alerta.

**Rationale:** o objetivo de FR-011 é impedir avaliação silenciosa sobre amostra
menor. Um alerta que dispara sempre é equivalente a alerta nenhum — o operador
aprende a ignorá-lo.

**Alternativas consideradas:** comparar contra um teto teórico por horizonte
(data de listagem do par). Rejeitada por exigir consulta adicional à exchange
para um ganho marginal sobre a mediana observada.

---

## D4 — Aquecimento dos indicadores

**Decisão:** declarar o aquecimento em candles **e** em dias, por horizonte.

**Medição:** o aquecimento dominante é `EMA_TREND = 50` candles.

| Horizonte | 50 candles equivalem a | % do histórico utilizável |
|---|---|---|
| 4h | 8 dias | 2,5% |
| 1d | 50 dias | 2,5% |
| **1w** | **350 dias (0,96 ano)** | **11% a 16%** |

**Rationale:** em escala semanal o aquecimento consome quase um ano antes do
primeiro sinal possível — fato invisível se declarado apenas em candles. FR-010
exige a declaração; expressá-la em dias é o que a torna interpretável.

**Verificação exigida:** a implementação deve confirmar que o aquecimento não
excede a janela de teste. Nas medições atuais não excede em nenhum caso, mas o
guard precisa existir para pares futuros de histórico ainda menor.

---

## Resumo das decisões

| # | Decisão | Efeito na implementação |
|---|---|---|
| D1 | Avaliar 4h, 1d e 1w | 3 horizontes × 4 estratégias × 12 pares = 144 combinações |
| D2 | Janelas derivadas do histórico | `n_janelas = min(5, utilizáveis // MIN_WINDOW_CANDLES)`; inconclusivo quando < 3 |
| D3 | Marca relativa à mediana do horizonte | Evita marcar 12 de 12 pares em 1w |
| D4 | Aquecimento em candles e dias | Guard contra aquecimento maior que a janela de teste |

**Expectativa registrada antes da execução:** 1d é onde a hipótese pode ser
respondida; 1w tende a inconclusivo por amostra. Registrar a expectativa antes
do resultado é o que permite distinguir, depois, previsão de racionalização.

## Fontes

- Liu, Y., Tsyvinski, A. (2021). *Risks and Returns of Cryptocurrency* —
  momentum de série temporal em horizonte de uma a quatro semanas.
- Medição própria de disponibilidade, 2026-09-01, 12 pares × 3 horizontes,
  `data/fetcher.py` com paginação (removida a limitação de 1000 candles em
  2026-08-31).
- `docs/research/registro-de-hipoteses.md` §7.1 — definição da bateria E1–E6.
