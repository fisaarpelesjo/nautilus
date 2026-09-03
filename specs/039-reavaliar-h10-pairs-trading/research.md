# Fase 0 — Pesquisa: reavaliar H10 com histórico estendido

**Data:** 2026-09-02

Diferente das demais specs deste registro, as decisões centrais aqui já
estavam declaradas e medidas em `docs/research/registro-de-hipoteses.md`
§4.11 **antes** desta spec — esta Fase 0 consolida, não decide de novo.

---

## D1 — Formação de 500 candles (já medida)

**Decisão:** `PairsParams(formacao=500)` com `reselecionar_a_cada=500`
(parâmetro próprio de `run_pairs_backtest`, não campo de `PairsParams`),
em vez
de 250 (valor original).

**Medição já publicada** (§4.11, poder de detecção do seletor sobre par
cointegrado **construído**, 30 sementes):

| Meia-vida construída | Janela de formação | Detecção |
|---|---|---|
| 20 | 250 | **20%** |
| 20 | 500 | **60%** |

Com 250 candles, o seletor perde 80% dos pares de reversão lenta — o
resultado negativo de E3/E4 não distinguia "sem vantagem" de "sem
detecção". 500 candles é o próximo ponto já medido nessa tabela, não um
valor novo escolhido para esta spec. Testar formações maiores (750, 1000)
resolveria mais poder ainda, mas exigiria nova medição de detecção antes
de declarar — fora do escopo desta correção pontual.

---

## D2 — Split treino/validação com aquecimento causal

**Decisão:** corte de tempo único, compartilhado entre os 12 pares
(70% treino / 30% validação, `DEFAULT_VALIDATION_RATIO`,
`backtesting/validation.py`). A fatia de validação recebe os `formacao`
candles finais do treino como aquecimento — sem eles, o seletor
começaria "frio" nos primeiros 500 candles da validação, desperdiçando a
janela mais cara de conseguir (out-of-sample).

**Rationale.** `run_pairs_backtest` já pula os primeiros `p.formacao`
candles do `dados` recebido (`range(p.formacao, len(precos))`) e ancora
`period_start` exatamente nesse ponto — passar
`treino[-formacao:] + validação` como o `dados` da chamada de validação
faz o aquecimento interno already existente alinhar exatamente com o
início real da validação, sem duplicar lógica de warmup nem tocar
`run_pairs_backtest`.

**Por que resolve o segundo problema de §4.11.** "0 a 7 operações contra
o mínimo de 10" nas janelas de walk-forward veio de janelas curtas demais
em relação à formação (250 candles de formação sobre janelas de teste de
tamanho comparável). Com 6.000 candles totais, formação de 500 e split
70/30, a validação sozinha tem ~1.650 candles — mais de 3x a formação —
dando espaço real para operações se acumularem.

---

## Resumo

| # | Decisão | Efeito |
|---|---|---|
| D1 | `formacao=500` (medido: 60% de detecção, era 20% a 250) | Seletor deixa de perder 80% dos pares de reversão lenta |
| D2 | Split 70/30 com aquecimento causal prepostos | Validação tem ~1.650 candles, resolve a escassez de operações já diagnosticada |

## Fontes

- `docs/research/registro-de-hipoteses.md` §4.11 (H10) — poder do
  seletor, contagem de operações por janela, recomendação explícita de
  reavaliação com histórico mais longo.
- `backtesting/pairs_trading.py::run_pairs_backtest` — mecânica de
  warmup interno (`range(p.formacao, len(precos))`), reusada sem
  alteração.
- `backtesting/validation.py::DEFAULT_VALIDATION_RATIO` (0,3) — mesma
  proporção de split já usada em toda avaliação do projeto com divisão
  treino/validação.
