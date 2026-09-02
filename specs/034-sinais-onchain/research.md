# Fase 0 — Pesquisa: H17, sinais on-chain

**Data:** 2026-09-02

---

## D1 — Atributo on-chain declarado

**Decisão:** `onchain_addr_growth_7d` — variação percentual de 7 dias da
média móvel de 7 dias de `n-unique-addresses` (endereços únicos ativos):

```
ma7[d]     = média(endereços ativos, dias d-6..d)
growth7d[d] = (ma7[d] - ma7[d-7]) / ma7[d-7]
```

**Rationale.** Suaviza ruído diário (dado bruto tem variação de dia da
semana visível) e mede crescimento semana-sobre-semana, unidade
adimensional (percentual), consistente com os 5 atributos existentes
(nenhum é nível bruto). Escolhida por precedência na literatura já
registrada no projeto (Assumptions da spec), **antes** de qualquer medição
de correlação ou desempenho.

---

## D2 — Colinearidade contra os 5 atributos existentes

**Decisão:** `onchain_addr_growth_7d` **não é colinear** — sobrevive à
checagem (FR-002).

**Medição** (BTC/USDT, 2000 candles de 4h, 2025-10-04 a 2026-09-02, 1951
linhas completas):

| Atributo existente | Correlação com `onchain_addr_growth_7d` |
|---|---|
| `atr_ratio` | 0,304 |
| `adx` | 0,257 |
| `dist_ema_slow` | −0,123 |
| `macd` | 0,060 |
| `volume_ratio` | −0,016 |

Maior correlação absoluta: **0,304** (`atr_ratio`) — bem abaixo do limiar
de 0,80 já estabelecido por `strategy/barreira_tripla.py` (mesmo limiar
que descartou `rsi`, `pos_bb`, `dist_ema_fast`, `dist_ema_trend` na
declaração original dos 5). O atributo entra no conjunto ampliado.

---

## D3 — Amostra BTC-only é suficiente

**Decisão:** prosseguir para a avaliação com modelo — amostra folgadamente
acima dos mínimos já estabelecidos.

**Medição** (mesma base de 2000 candles):

| Grandeza | Valor | Mínimo exigido |
|---|---|---|
| Eventos rotulados totais | 1.951 | — |
| `n_treino` pós-purga | **1.342** | `MIN_TREINO` = 200 |
| `n_teste` | **586** | `EDGE_MIN_TRADES` = 10 |
| Purgadas / embargadas | 3 / 20 | — |
| Distribuição treino (alvo) | 27,2% | — |

**Rationale.** BTC-only (1.951 eventos) é comparável à média por par do
pool original de H14 (23.412 eventos / 12 pares ≈ 1.951/par) — quase
idêntico por coincidência, não por ajuste. `n_treino`/`n_teste` superam os
mínimos por uma ordem de grandeza; a restrição estrutural (spec 033,
BTC-only) não estrangula a amostra na prática, ao contrário do que se
poderia supor antes de medir.

---

## D4 — Extensão de `backtesting/modelo.py`

**Decisão:** `avaliar_par()` ganha dois parâmetros opcionais —
`atributos: list[str] = ATRIBUTOS` e `extrair_atributos_fn: Callable =
extrair_atributos` — com default idêntico ao comportamento atual.
`estimar`/`prever` já são genéricos (recebem `DataFrame` de atributos, sem
hardcode). H17 chama:

```python
avaliar_par(
    "BTC/USDT",
    atributos=ATRIBUTOS + ["onchain_addr_growth_7d"],
    extrair_atributos_fn=construir_extrator_onchain(serie_growth7d),
)
```

Sem passar `eventos_globais` (H17 é par único — a purga global entre 12
pares não se aplica, `base_purga = eventos` já é o caminho existente
quando `eventos_globais is None`).

**Rationale.** `ATRIBUTOS`/`extrair_atributos` de H14 são resultado já
publicado (`docs/research/registro-de-hipoteses.md` §4.15) — não podem
mudar. Duplicar `avaliar_par()` inteira (~100 linhas) para trocar 5 pontos
de uso de uma constante seria a abstração errada na direção oposta:
copy-paste de lógica de purga/embargo/ajuste que já é a mesma. O default
dos dois parâmetros novos garante que `run_modelo_scan()` (sem passar
nada) produz **exatamente** o resultado de H14 hoje — mesmo padrão de
indireção com default preservando comportamento já usado em `as_of=None`
(spec 020), `_now()` (spec 032, planejada) e os módulos desta sessão.

**Alternativas consideradas:**
- **Duplicar `avaliar_par` numa função `avaliar_par_onchain`**: rejeitada
  — ~90% do código seria idêntico (purga, embargo, três linhas de base,
  classificação), risco real de uma correção futura em `avaliar_par` (ex.
  spec 019/020) ser aplicada numa cópia e esquecida na outra.
- **Mudar `ATRIBUTOS` para incluir o on-chain permanentemente**: rejeitada
  — mudaria o resultado publicado de H14 (12 pares), que não usa dado
  on-chain e deve continuar reproduzível como está.

---

## D5 — Merge causal (mecânica)

**Decisão:** para um candle no dia calendário `D` (UTC), o valor de
`onchain_addr_growth_7d` usado é o do dia `D-1` completo — nunca `D`.
Implementado como: `serie[serie.index <= (D - 1 dia)].iloc[-1]` (leva
adiante o último dia disponível, FR-009).

**Medição de cobertura**: das 1.951 linhas completas dos 5 atributos
existentes, **100%** (1.951/1.951) tiveram um valor on-chain causal
disponível — a série on-chain (início em 2023, D5/spec033) cobre com folga
o período de candles disponível (início em 2025-10-04).

**Rationale.** Mesma classe de correção que a spec 020 aplicou ao MTF —
um candle não pode ver o dia em que ele mesmo está, porque esse dia ainda
está sendo acumulado pela fonte (spec 033, D1: dado de um dia só fecha
quando o dia termina).

---

## Resumo das decisões

| # | Decisão | Efeito |
|---|---|---|
| D1 | `onchain_addr_growth_7d` (variação 7d da MA7 de endereços ativos) | Declarado antes de medir, adimensional |
| D2 | Colinearidade máxima 0,304 — sobrevive ao limiar 0,80 | Atributo entra no conjunto ampliado |
| D3 | `n_treino=1.342`, `n_teste=586`, ambos >> mínimos | Amostra BTC-only não é o gargalo |
| D4 | `avaliar_par(atributos=, extrair_atributos_fn=)`, defaults preservam H14 | Zero mudança no resultado publicado de H14 |
| D5 | Candle no dia D usa dado on-chain do dia D-1; cobertura 100% medida | Nenhum lookahead, mesma classe de correção da spec 020 |

## Fontes

- Medição própria, 2026-09-02: BTC/USDT, 2000 candles 4h via
  `data/fetcher.py::fetch_ohlcv`; `data/onchain.py::fetch_onchain_series`
  (spec 033).
- `strategy/barreira_tripla.py` (limiar de colinearidade 0,80, já
  estabelecido para os 5 atributos originais).
- `backtesting/modelo.py::avaliar_par`, `backtesting/purga.py` (código
  existente, lido antes de propor a extensão).
