# Arbitragem de funding rate — medição própria

**Data:** 2026-09-01
**Pergunta:** vale construir execução de futuros para capturar funding rate?
**Resposta curta:** não. Medido, rende 2–3% ao ano em BTC/ETH e **negativo** em SOL.

## Por que a pergunta apareceu

Depois de quatro medições independentes mostrarem que a estratégia direcional
(EMA + RSI) não tem vantagem preditiva, a busca virou para categorias que **não
dependem de prever preço**. Arbitragem de funding é a principal delas: compra no
spot e vende o mesmo nocional no perpétuo, as duas pontas se cancelam, e a
receita vem da taxa que os comprados alavancados pagam aos vendidos a cada 8 h.

A literatura comercial promete **10–30% ao ano**, com firmas profissionais
reportando 19,26% em 2025.

## O que foi medido

12 meses de histórico público de funding da Binance (2025-09-01 a 2026-09-01),
1.095 pagamentos por símbolo, posição delta-neutra sem alavancagem. Custo de
0,04% por ponta em quatro pontas (abre spot, abre perp, fecha spot, fecha perp).

| Símbolo | Pagamentos | % negativos | Bruto a.a. | Custo | **Líquido a.a.** |
|---|---|---|---|---|---|
| BTC | 1.095 | 23,7% | 3,37% | 0,16% | **+3,21%** |
| ETH | 1.095 | 27,4% | 2,43% | 0,16% | **+2,27%** |
| SOL | 1.095 | 46,6% | −1,68% | 0,16% | **−1,84%** |
| XRP | 1.095 | 44,7% | 0,36% | 0,16% | **+0,20%** |

### O risco que a média esconde

| Símbolo | Pior janela de 30 dias | Janelas negativas |
|---|---|---|
| BTC | −0,173% | 3 de 13 |
| ETH | −0,288% | 3 de 13 |
| SOL | −1,064% | 7 de 13 |
| XRP | −0,555% | 5 de 13 |

## De onde vem a diferença para os 10–30% prometidos

A conta dos blogs parte de uma taxa "típica" de 0,01% a cada 8 h, que dá 10,95%
ao ano. Mas 0,01% é o valor de referência da Binance, não a média realizada.
Entre 24% e 47% dos pagamentos foram **negativos** no período — nesses momentos
quem paga é você. A média de 12 meses fica bem abaixo do valor nominal.

Não encontrei erro na aritmética dos blogs; encontrei uma premissa que o dado
não sustenta.

## Por que isso encerra a linha

Construir isso exigiria:

1. **Permissão de futuros nas chaves da Binance** — hoje são spot-only. Futuros
   significam alavancagem e risco de liquidação, uma classe de falha que o bot
   nunca teve. Os limites de drawdown e o circuit breaker atuais não protegem
   contra liquidação.
2. **Posição de duas pernas** no `state.json`, que hoje modela uma posição spot
   por símbolo. Delta-neutro precisa do par spot+perp e do delta entre eles.
3. **Monitoramento de margem** e re-hedge quando o delta desvia, cada
   rebalanceamento pagando taxa.
4. **Fonte de funding rate** no `data/fetcher.py`, hoje só OHLCV.

Tudo isso para capturar, em BTC, **3,21% ao ano** — menos que renda fixa, com
risco de liquidação, risco de execução e risco de exchange somados.

O número não justifica a obra. E a medição custou uma consulta a dado público,
antes de qualquer linha de execução ser escrita, que é exatamente a ordem certa.

## Ressalvas honestas

- Alavancagem multiplicaria o retorno **e** o risco de liquidação. A 2x, BTC
  daria ~6,4% ao ano com exposição real a liquidação.
- Não inclui slippage nem custo de re-hedge, então **3,21% é teto, não chegada**.
- Um estudo acadêmico (MDPI, *The Two-Tiered Structure of Cryptocurrency Funding
  Rate Markets*) relata que 95% das oportunidades terminam em saída forçada
  antes do previsto.
- O período medido pode não ser representativo. Em bull market forte o funding
  sobe muito. Mas apostar nisso é apostar em regime — exatamente o que a
  estratégia direcional já fazia.

## Fontes

- Histórico de funding: `ccxt.binance.fetch_funding_rate_history`, dado público
- [The Two-Tiered Structure of Cryptocurrency Funding Rate Markets — MDPI](https://www.mdpi.com/2227-7390/14/2/346)
- [Crypto Funding Rate Arbitrage: A Delta-Neutral Guide](https://arbitragescanner.io/blog/crypto-funding-rate-arbitrage-guide)
- [Funding Rate Arbitrage in 2026: Complete Guide](https://arbitrageghost.medium.com/funding-rate-arbitrage-in-2026-the-complete-guide-with-real-calculations-40e6cf341e52)
