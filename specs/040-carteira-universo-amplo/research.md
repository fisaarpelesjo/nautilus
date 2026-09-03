# Fase 0 — Pesquisa: carteira de H14 sobre universo amplo

**Data:** 2026-09-03

---

## D1 — Universo de 34 pares (medido, não escolhido)

**Decisão:** lista fixa de 34 pares (snapshot 2026-09-03), reusada sem
recálculo entre execuções.

**Medição** (`market/selector.py::_filter_tickers`, dados reais de
tickers da Binance, 2026-09-03): aplicando os limiares de liquidez **já
declarados** do projeto — `MIN_VOLUME_USDT` (10.000.000) e
`MAX_SPREAD_PCT` (0,003) — 39 pares USDT passam. Inspecionados
manualmente, 5 não são altcoins no sentido que a hipótese testa:

| Símbolo | Motivo da exclusão |
|---|---|
| USD1/USDT | Stablecoin pareada a USD — filtro `STABLECOINS` de `market/selector.py` não cobre |
| RLUSD/USDT | Stablecoin da Ripple — mesmo motivo |
| EUR/USDT | Par fiat (EUR), não cripto |
| XAUT/USDT | Token lastreado em ouro — perfil de volatilidade não é o de uma altcoin |
| PAXG/USDT | Token lastreado em ouro — mesmo motivo |

Resultado: **34 pares** (lista completa abaixo). Não é 40-80 (faixa
usada pela estratégia comunitária mais popular do Freqtrade,
NostalgiaForInfinity, que motivou esta spec) — é o que o piso de liquidez
já em produção devolve, honestamente, sem forçar um número.

```
BTC/USDT, ETH/USDT, SOL/USDT, XRP/USDT, ZEC/USDT, UNI/USDT, BNB/USDT,
DOGE/USDT, SUI/USDT, HEMI/USDT, ARB/USDT, ENA/USDT, U/USDT, TRUMP/USDT,
LINK/USDT, AAVE/USDT, TRX/USDT, NEAR/USDT, BMT/USDT, SNDKB/USDT,
PUMP/USDT, ADA/USDT, FIL/USDT, PROM/USDT, LTC/USDT, T/USDT, PEPE/USDT,
WLD/USDT, ASTER/USDT, CRCLB/USDT, TUT/USDT, MUBARAK/USDT, TAO/USDT,
AVAX/USDT
```

**Histórico heterogêneo, esperado e tratado sem mecanismo novo.** Vários
destes pares (ex.: PUMP, MUBARAK, ASTER, TRUMP, HEMI, BMT, SNDKB, CRCLB,
T, TUT) são listagens recentes, sem os ~2,7 anos que `UNIVERSO_H11` tem.
`run_modelo_scan`/`avaliar_par` já isolam falha por par sem abortar a
varredura (R7) — o mesmo tratamento de H11 para "histórico curto".
Nenhum ajuste novo necessário.

**Rationale contra usar `select_dynamic_pairs()` inteira.** Essa função
(já existente) filtra e RANQUEIA por `backtest_return_pct`/`trend_pct` —
usar o resultado dela construiria um universo enviesado por desempenho
recente (viés de sobrevivência: só entrariam pares que já estavam
subindo). Reusar só `_filter_tickers` (liquidez/spread, sem componente de
desempenho) evita esse viés — o universo é definido por **tradabilidade**,
não por já ter dado certo.

---

## D2 — `MAX_POSITIONS` permanece fixo

**Decisão:** o teto de posições simultâneas não muda junto com o
universo — continua o valor de produção (`MAX_POSITIONS`, config).

**Rationale.** A tese é "mais opções de pares reduz a correlação entre as
posições que DE FATO abrem, para o mesmo número de posições simultâneas"
— não "mais posições simultâneas reduz risco por si só" (isso seria uma
variável diferente, confundiria o resultado). Mudar as duas ao mesmo
tempo tornaria impossível saber qual delas produziu qualquer efeito
observado.

---

## Resumo

| # | Decisão | Efeito |
|---|---|---|
| D1 | Universo de 34 pares, medido via limiares de liquidez já existentes, pegged assets excluídos | Testa a tese sem viés de sobrevivência nem número arbitrário |
| D2 | `MAX_POSITIONS` fixo no valor de produção | Isola pool size como a única variável em teste |

## Fontes

- `docs/research/registro-de-hipoteses.md` §4.15 (H14, spec 037) —
  achado que motivou esta spec: drawdown de carteira 5x o maior isolado
  por par, mecanismo provável (correlação) explicitamente não coberto
  ali (FR-007 daquela spec).
- Medição própria, 2026-09-03: `market/selector.py::_filter_tickers`
  sobre tickers reais da Binance.
- Pesquisa sobre bots de código aberto (conversa desta sessão): NFI
  (Freqtrade), estratégia comunitária mais usada, opera 40-80 pares —
  motivou a pergunta, não define o número usado aqui.
