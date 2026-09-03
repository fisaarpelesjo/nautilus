# Research: H24 — diferencial de funding rate entre corretoras (perp × perp)

## D1 — corretoras qualificadas (verificado 2026-09-03, testes reais via ccxt)

Das seis corretoras já lidas por H15 (`binance`, `bybit`, `okx`,
`kucoin`, `gate`, `kraken`), testadas via `ccxt` com chamada real
(`fetch_funding_rate_history('BTC/USDT:USDT', limit=1)` e o
equivalente ETH):

| Corretora | Classe ccxt | Suporta `fetchFundingRateHistory`? | BTC/USDT:USDT | ETH/USDT:USDT |
|---|---|---|---|---|
| Binance | `binance` (defaultType=future) | Sim | OK | OK |
| Bybit | `bybit` | Sim | OK | OK |
| OKX | `okx` | Sim | OK | OK |
| KuCoin | `kucoinfutures` | Sim | OK | OK |
| Gate | `gate` (defaultType=swap) | Sim | OK | OK |
| Kraken | `krakenfutures` | Sim (tecnicamente) | **BadSymbol** | não testado |

**Kraken excluído.** `krakenfutures` não tem `BTC/USDT:USDT` -- só
oferece `BTC/USD:BTC` (inverso, margeado em BTC) e `BTC/USD:USD`
(margeado em USD), nunca um perpétuo linear margeado em USDT como as
outras cinco. Misturar isso numa comparação de diferencial de funding
exigiria converter denominação de margem (USD/BTC vs. USDT), um passo
metodológico à parte que muda o que está sendo medido -- fora do
escopo desta spec (FR-005). **Cinco corretoras qualificadas**:
Binance, Bybit, OKX, KuCoin, Gate -- 10 pares de corretoras (C(5,2))
por ativo.

**Cadência de funding confirmada igual (verificado, 4 registros por
corretora):** todas as cinco liquidam a cada 8h, no mesmo horário
cheio (00:00/08:00/16:00 UTC) -- Gate com poucos segundos de jitter
(observado: 1-3s de desvio), as demais exatas. Alinhamento por hora
arredondada (FR-002) resolve esse jitter sem perder precisão material.

## D2 — taxas reais por corretora (verificadas 2026-09-03, busca)

| Corretora | Taxa de tomador (futuros, tier base) |
|---|---|
| Binance | 0,05% (já verificado nesta sessão, spec 058) |
| Bybit | 0,055% |
| OKX | 0,05% |
| KuCoin | 0,06% |
| Gate | 0,05% |

Custo de um par de corretoras (A, B): abre A + abre B + fecha A +
fecha B = `2 × (taxa_A + taxa_B)` -- mesma estrutura de "evento único,
anualizado pela mesma base do bruto" de H8/H23 (`fator_anual`).

## D3 — eficiência de capital: investigada, não presumida (achado central)

**Hipótese de entrada:** sem perna à vista, H24 seria mais eficiente em
capital que H8 (que exige nocional + margem = 2×).

**Investigação:** cada corretora gerencia margem de forma
independente. Não existe margem cruzada entre contas de varejo em
corretoras diferentes -- abrir uma posição vendida na corretora A e
comprada na corretora B exige margem própria em CADA corretora,
dimensionada para cobrir o nocional da perna ali (mesma lógica "sem
alavancagem, margem ≈ nocional" de H8, D3).

**Conclusão: a exigência de capital NÃO é menor que H8 -- é
igual (2× o nocional, uma vez por perna), com um risco adicional que
H8 não tem:** capital precisa estar PRÉ-POSICIONADO em duas corretoras
diferentes (não uma), e a posição está sujeita a risco de base entre
duas contas de margem independentes -- se uma corretora sofrer um
evento de liquidação em cascata (funding extremo, book raso) e a outra
não, a divergência entre as duas pernas não se corrige automaticamente
como aconteceria numa margem cruzada de conta única. A hipótese de
entrada estava errada: não há vantagem de capital aqui, só uma
vantagem potencial de TAMANHO do diferencial (D-principal), à custa de
mais risco operacional que H8.

## D4 — universo de ativos

BTC/USDT e ETH/USDT -- mesmos de H23 (`specs/059-h23-futuros-trimestrais/`),
para comparabilidade entre as três variantes de carry medidas nesta
sessão (H8 spot×perp, H23 spot×futuro-trimestral, H24 perp×perp
cross-exchange).

## D5 — benchmark

Reusa `BENCHMARK_RENDA_FIXA_AA` (5% a.a.) de
`backtesting/funding_carry.py` sem alteração -- mesma pergunta de
custo de oportunidade em todas as três variantes de carry.

## Reprodução

`python main.py funding_cross` · `reports/funding_cross_*.json`.

(Resultado real preenchido após a execução -- ver
`docs/research/registro-de-hipoteses.md` §6.2/§4.9 para o número medido.)
