# Fase 0 — Pesquisa: lead-lag BTC para altcoins (H21)

**Data:** 2026-09-02

---

## D1 — Defasagem e fórmula exata do sinal

**Decisão:** N=1 candle de 4h, **sem deslocamento extra**:
`retorno_btc[t] = close_btc[t] / close_btc[t-1] - 1`, usado como sinal
para a MESMA linha `t` da altcoin (entrada ao fechamento do candle `t` da
altcoin, apostando no candle `t+1`).

**Medição** (`data/fetcher.py::fetch_ohlcv`, 2000 candles de 4h, 12 pares
de `UNIVERSO_H11`, 2026-09-02): correlação entre `close_btc.pct_change(N)`
e `close_alt.pct_change(M).shift(-M)`, para N ∈ {1,2,3,4,6,8,12} e
M ∈ {1,2,3}, sobre os 11 pares excluindo BTC:

| N (defasagem BTC) | M (horizonte alt) | Correlação média | Correlação mediana | % pares positivos |
|---|---|---|---|---|
| **1** | **1** | **0,0445** | 0,0443 | **100%** |
| 4 | 1 | 0,0225 | 0,0258 | 100% |
| 8 | 1 | 0,0201 | 0,0195 | 90,9% |
| 1 | 3 | 0,0169 | 0,0207 | 90,9% |

N=1/M=1 tem a maior correlação média **e** empata no topo em consistência
(100% dos pares, com N=4/M=1) — critério de desempate: a defasagem mais
curta e mais simples de justificar mecanicamente (o candle que acabou de
fechar, não um agregado de 4 candles).

**Por que não há *lookahead*.** `df` é indexado pelo horário de ABERTURA
de cada candle; `close[t]` só é conhecido no fechamento, `index[t]+4h`. O
retorno de BTC em `t` (`close_btc[t]/close_btc[t-1]-1`) fica conhecido
exatamente em `index[t]+4h` — o MESMO instante em que a altcoin fecha seu
próprio candle `t` (grade de 4h alinhada entre pares na mesma exchange).
Decidir a entrada da altcoin usando seu próprio fechamento nesse instante,
informada pelo retorno de BTC que acabou de ficar disponível no mesmo
instante, não usa nenhuma informação futura — é a mesma convenção de
"negociar no fechamento" que `simulate_backtest` já usa para toda
estratégia deste projeto.

**Erro capturado antes de qualquer código:** a primeira redação desta
spec descrevia o sinal como `close[t-1]/close[t-2]-1` (o retorno do
candle ANTERIOR ao candle `t-1` da altcoin) — uma defasagem a mais do que
a medida acima, testando N=2 implicitamente em vez de N=1. Corrigido em
`spec.md` antes de `/speckit-plan` continuar.

---

## D2 — Sinal binário, não magnitude

**Decisão:** BUY quando `retorno_btc[t] > 0`; HOLD em qualquer outro caso
(incluindo exatamente zero e `NaN`).

**Rationale.** A medição em D1 testa a CORRELAÇÃO (sinal linear), não uma
magnitude de corte. Introduzir um limiar (ex.: "BTC subiu mais que X%")
exigiria uma medição própria antes de declarar X — sem ela, seria a mesma
falha que o registro já corrigiu (M13, `docs/research/registro-de-hipoteses.md`
§ tabela de correções): comparar contra um número não testado. `NaN`
(candle ausente de BTC ou início da série) mapeia para HOLD naturalmente
em Python (`float('nan') > 0` é `False`), sem tratamento especial — mesmo
espírito de FR-008.

---

## D3 — Universo: 11 pares, sem BTC/USDT

**Decisão:** `UNIVERSO_H11` menos `"BTC/USDT"` (11 pares).

**Rationale.** BTC é a variável explicativa (o "líder"), não um alvo de
operação nesta hipótese — testar "BTC prevê o próprio retorno futuro de
BTC" seria uma reformulação de H1/H7 (momentum do próprio ativo), não
lead-lag. Mesmo universo-base de H11/H14/H17/H37, sem escolher pares por
resultado.

---

## D4 — Reuso do motor: `_simular_com_sinais`, nenhum motor novo

**Decisão:** o sinal (`pd.Series` de `Signal.BUY`/`Signal.HOLD`) alimenta
`backtesting.modelo._simular_com_sinais(prep, estrategia, sinais)` —
função já existente e testada, que envolve `simulate_backtest` com
`precomputed_signals`. `estrategia` (`EmaRsiStrategy`) é usada só para
`calculate_indicators` (ATR, necessário para o take-profit/stop trailing)
— o sinal de compra da EMA/RSI nunca é consultado, porque
`precomputed_signals` o substitui inteiramente.

**Rationale.** É exatamente o padrão já usado por H14
(`_resultado_modelo`/`_sinais_do_modelo`) para transformar uma
probabilidade externa num `BacktestResult` — reusar a função em vez de
chamar `simulate_backtest` diretamente evita duplicar a lógica de
"simular com sinal pré-computado", que já existe, já é testada, e já é
consumida por um caminho crítico deste registro (H14).

---

## Resumo

| # | Decisão | Efeito |
|---|---|---|
| D1 | N=1, `close[t]/close[t-1]-1`, sem deslocamento extra, medido em 2000 candles reais | Maior correlação (0,0445) e 100% de consistência entre 11 pares; corrige um erro de defasagem pego antes do código |
| D2 | Sinal binário sobre o sinal do retorno, não magnitude | Evita limiar não testado (mesma classe de erro que M13) |
| D3 | `UNIVERSO_H11` menos BTC/USDT (11 pares) | BTC é variável explicativa, não alvo — evita confundir com H1/H7 |
| D4 | Reusa `_simular_com_sinais` (já existente, já testada) | Sem motor de backtest novo — mesmo padrão de H14 |

## Fontes

- Medição própria, 2026-09-02: `data/fetcher.py::fetch_ohlcv` sobre os 12
  pares de `UNIVERSO_H11`, 2000 candles de 4h.
- "Price Transmission from Bitcoin to Altcoins: High-Frequency Evidence
  and Implications for Trading Strategy," *Asia-Pacific Financial
  Markets* (Springer, 2026) — causalidade de Granger unidirecional
  BTC→altcoins, fundamentação da tese.
- `backtesting/modelo.py::_simular_com_sinais`/`_sinais_do_modelo` —
  padrão já estabelecido de sinal externo → `BacktestResult`, reusado sem
  alteração (H14, specs 027/034/037).
