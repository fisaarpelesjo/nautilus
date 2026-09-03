# Fase 0 (retroativa) — correção descoberta durante T003

**Data:** 2026-09-03, durante a execução real (T003) — não antes, porque
o problema só apareceu ao rodar contra dados reais.

## D1 — `UNIVERSO_AMPLO` bruto não é compatível com `split_treino_validacao`

**O que aconteceu.** Primeira execução real de `cmd_pairs_amplo()`
devolveu **0 trades em treino E validação** — pior que o já publicado
(6 trades), não melhor. Resultado anômalo o bastante para investigar
antes de registrar, em vez de aceitar como "H10 piorou".

**Causa raiz, confirmada por diagnóstico direto.** `UNIVERSO_AMPLO` (34
pares, spec 040) foi medido para **liquidez**, não para **profundidade
de histórico** — inclui listagens recentes (`SNDKB/USDT`, `CRCLB/USDT`:
504 candles; `U/USDT`: 1.400; `ASTER/USDT`: 1.993; outras entre 2.000 e
5.300). `split_treino_validacao` (`backtesting/pairs_trading.py`)
calcula `indice_comum` como a **interseção** dos índices de tempo de
**todos** os pares recebidos — o par de histórico mais curto do
universo inteiro determina a janela comum de todo mundo. Com
`SNDKB`/`CRCLB` limitando a interseção a ~504 candles, `len(precos) <=
p.formacao + 10` (510) falha em ambas as fatias, e `run_pairs_backtest`
devolve `_resultado_vazio` para as duas.

**Por que isso não apareceu em spec 040.** `backtesting/portfolio_h14.py`
(a carteira de H14) alinha cada par **independentemente** por candle —
nunca exige um índice comum entre todos os 34 pares simultaneamente.
`selecionar_pares`/`split_treino_validacao` (H10) exigem, por desenho,
porque a seleção de pares cointegrados precisa comparar séries na MESMA
janela de tempo. É uma incompatibilidade estrutural entre como os dois
motores usam a mesma lista de pares, não um bug em nenhum dos dois.

**Correção declarada, não ajuste até o resultado melhorar.** Filtra
`UNIVERSO_AMPLO` para os pares com os 6.000 candles completos — critério
mecânico e verificável (quantidade de candles retornada por
`fetch_ohlcv`), não escolhido por produzir resultado favorável. Medido
nesta mesma sessão: **22 de 34** pares têm histórico completo:

```
BTC/USDT, ETH/USDT, SOL/USDT, XRP/USDT, ZEC/USDT, UNI/USDT, BNB/USDT,
DOGE/USDT, SUI/USDT, ARB/USDT, LINK/USDT, AAVE/USDT, TRX/USDT,
NEAR/USDT, ADA/USDT, FIL/USDT, PROM/USDT, LTC/USDT, T/USDT, PEPE/USDT,
WLD/USDT, AVAX/USDT
```

Ainda **quase o dobro** de `UNIVERSO_H11` (12 pares) — C(22,2)=231
combinações contra 66, não os 561 originalmente esperados, mas ainda
uma ampliação real do espaço de busca.

**Consequência para o FR-001 original.** A spec declarava "chama
`run_pairs_scan(pares=UNIVERSO_AMPLO)` — nenhum parâmetro novo". Isso
muda: o universo candidato passa a ser o subconjunto de histórico
completo, não `UNIVERSO_AMPLO` bruto. `cmd_pairs_amplo()` atualizado
para filtrar antes de chamar `run_pairs_scan`.
