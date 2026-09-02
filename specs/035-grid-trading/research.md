# Fase 0 — Pesquisa: H18, grid trading com gestão de cauda

**Data:** 2026-09-02

---

## D1 — Número de níveis

**Decisão:** `N = 10` níveis, igualmente espaçados entre `bb_lower` e
`bb_upper` do candle em que a grade abre.

**Rationale.** Número redondo, default comum de bots de grid comerciais
(faixa típica 5-50), escolhido por convenção — não ajustado a nenhum
resultado (FR-004). Suficiente para várias transações por episódio sem
fragmentar o capital em fatias irrelevantes.

---

## D2 — Capital por nível

**Decisão:** `capital_por_nivel = capital_inicial / N`, fixo por episódio
(não recompõe entre round-trips dentro do mesmo episódio).

**Rationale.** Mesmo princípio de simplicidade declarada antes de medir.
Recompor capital dentro de um episódio introduziria um efeito de
alavancagem implícita que a spec não se propõe a medir.

---

## D3 — Mecânica de preenchimento

**Decisão:** por candle, com a grade ativa:

1. **Vendas primeiro.** Para cada nível ocupado cujo `preco_venda` (o
   nível imediatamente acima) esteja dentro de `[low, high]` do candle:
   fecha o round-trip, libera capital.
2. **Compras depois.** Para cada nível vazio cujo `preco_compra` esteja
   dentro de `[low, high]` do candle: abre posição, com o capital já
   liberado no passo 1 disponível.

**Rationale.** Processar vendas antes de compras no mesmo candle evita
que uma compra fique bloqueada por capital que só seria liberado depois
dela na mesma iteração — ordem declarada, não arbitrária.

**Preço de preenchimento**: o preço do próprio nível (não o `close` do
candle) — mesmo princípio de uma ordem limite já posicionada, ajustado por
`BACKTEST_SLIPPAGE_PCT` (compra paga um pouco acima do nível, venda recebe
um pouco abaixo — sempre contra o executor, nunca a favor, mesmo critério
conservador já usado em `backtesting/engine.py`).

---

## D4 — Liquidação forçada (gestão de cauda)

**Decisão:** quando o regime do candle é `"trending"` e a grade tem
níveis ocupados, todos são liquidados ao **preço de fechamento** desse
candle (não ao melhor preço possível dentro dele) — FR-003.

**Rationale.** Fechamento a mercado no primeiro candle em que o regime
muda é a definição operacional de "gestão de cauda" desta spec (Contexto).
Usar o `close` (não o `high`, que seria otimista) é o mesmo critério
conservador de preenchimento de ordem a mercado já usado no motor
existente.

---

## D5 — Reabertura

**Decisão:** após uma liquidação forçada, a grade fica inativa até o
regime voltar a `"sideways"`; quando volta, uma grade **nova** é aberta
com `bb_lower`/`bb_upper` do candle de reabertura (não as bandas antigas).

**Rationale.** As bandas são recalculadas a cada candle pelo indicador já
existente — usar valores antigos exigiria guardá-los sem motivo, quando o
dado atual já está disponível.

---

## D6 — Montagem do `BacktestResult` (reuso do motor existente)

**Decisão:** cada round-trip de nível (D3) e cada liquidação forçada (D4)
vira um `Trade` (`backtesting/engine.py`, campos já existentes —
`exit_reason="grid"` ou `"regime mudou para trending"`). `max_drawdown_pct`
é calculado pela mesma lógica de pico-a-vale sobre a curva de capital que
`simulate_backtest()` já usa. O resto —
`profit_factor`, `sharpe`, `sortino`, `calmar`, `edge_score`, etc. — vem de
`_calculate_advanced_metrics(trades, total_return_pct, buy_hold_return_pct,
max_drawdown_pct, period_start, period_end)`, chamada sem modificação.

**Rationale (FR-006).** Zero duplicação de fórmula de métrica. O
`BacktestResult` produzido passa por `evaluate_approval()` exatamente como
o de qualquer outra estratégia — nenhum critério de aprovação novo.

---

## D7 — Universo e período

**Decisão:** `UNIVERSO_H11` (12 pares, `backtesting/horizonte.py`), 2000
candles no `TIMEFRAME` de produção — mesmo teto já usado por H14/H17/H20.

**Rationale.** Mesmo universo que toda avaliação recente deste registro já
usa — evita escolher pares favoráveis à hipótese.

---

## Resumo das decisões

| # | Decisão | Efeito |
|---|---|---|
| D1 | N=10 níveis | Convenção declarada, não ajustada a resultado |
| D2 | Capital/nível fixo, sem recompor | Sem alavancagem implícita |
| D3 | Vendas antes de compras no mesmo candle; preço do nível, não o close | Mecânica declarada, capital nunca "trava" |
| D4 | Liquidação forçada ao `close` do candle em que regime vira trending | Gestão de cauda, conservador (não otimista) |
| D5 | Reabertura recalcula bandas no candle atual | Sem estado obsoleto |
| D6 | `Trade`/`BacktestResult`/`_calculate_advanced_metrics` reusados sem alteração | Zero critério de aprovação novo (FR-006) |
| D7 | `UNIVERSO_H11`, 2000 candles | Mesma amostra de H14/H17/H20 |

## Fontes

- `backtesting/engine.py` (leitura de código): `Trade`, `BacktestResult`,
  `_calculate_advanced_metrics`, `edge_score`, lógica de drawdown de
  `simulate_backtest`.
- `strategy/ema_rsi.py::_classify_regime`/Bollinger Bands (já existentes).
- `backtesting/horizonte.py::UNIVERSO_H11`.
- `backtesting/approval.py::evaluate_approval` (critério já existente).
