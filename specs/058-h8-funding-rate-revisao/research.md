# Research: H8 — arbitragem de funding rate, revisão com universo amplo e eficiência de capital

## D1 — taxas de custo atuais (verificadas 2026-09-03, não as de 0,04% originais)

Busca realizada em 2026-09-03: Binance VIP0 —

- **Spot taker**: 0,10% (`BACKTEST_FEE_RATE = 0.001`, já verificado
  contra a taxa real para H20 na mesma sessão, mesmo valor reusado
  aqui).
- **Futuros USDT-M taker**: 0,05% (`FUTURES_TAKER_FEE = 0.0005`, novo
  para este módulo).

A medição original de H8 (2026-09-01) usou 0,04% para as duas pernas —
subestimava o lado spot (0,04% vs. 0,10% real) e superestimava
ligeiramente o lado futuros (0,04% vs. 0,05% real). Líquido: custo real
de abertura+fechamento é 2×(0,0010+0,0005) = **0,30%**, contra os
0,16% (4×0,04%) originais — quase o dobro, mas ainda um evento **único**
por posição mantida um ano inteiro, não um custo recorrente (D2).

## D2 — custo é evento único, anualizado na mesma base que o bruto

Round-trip (abre spot + abre perp no início, fecha os dois no fim) é um
custo **único** por posição — não se repete a cada período de funding
(8h). Anualizado multiplicando por `365/dias_cobertos`, a mesma base do
retorno bruto, para os dois ficarem comparáveis: um histórico mais curto
que um ano faz o custo pesar proporcionalmente mais quando anualizado
(correto — reflete que o custo fixo é amortizado sobre menos tempo).

## D3 — eficiência de capital: a correção central desta revisão

**A medição original reportou retorno sobre o NOCIONAL da posição — não
sobre o capital realmente implantado.** Uma posição delta-neutra (long
spot + short perpétuo, mesmo nocional) **sem alavancagem** — a única
configuração que praticamente elimina risco de liquidação, porque a
margem da perna perpétua cobre o nocional inteiro — exige:

```
capital implantado = nocional (perna spot, comprada à vista)
                    + margem (perna perpétua, ≈ nocional a 1x)
                    = 2 × nocional
```

O retorno real sobre capital implantado é, portanto, **aproximadamente
metade** do retorno sobre nocional que a medição original reportou. Isso
não é uma correção neutra — só piora a leitura já desfavorável da
medição original (BTC +3,21% a.a. sobre nocional → ~+1,5-1,6% a.a. sobre
capital implantado, antes mesmo de comparar contra qualquer benchmark).

**Por que não modelar alavancagem maior.** Alavancar a perna perpétua
(ex.: 3x) reduziria a margem necessária e aumentaria o retorno sobre
capital, mas introduz risco de liquidação real por divergência de base
(spot vs. perpétuo) — um risco que este módulo **não quantifica**
(exigiria dados de book/mark-price fora do escopo de histórico de
funding). Fica como limitação declarada, não como suposição otimista
não testada.

## D4 — benchmark de custo de oportunidade

Busca realizada em 2026-09-03: produtos de empréstimo de USDT em
plataformas estabelecidas (Binance Earn, Aave) — faixa observada
**5-8% a.a.** em condições normais de mercado, com produtos CeFi
alcançando até 8,5% a.a. Usado o **piso conservador da faixa, 5% a.a.**
— não o número mais favorável à hipótese, seguindo o mesmo princípio de
`BACKTEST_SLIPPAGE_PCT` como piso conservador no resto do projeto.

## D5 — universo: mais amplo que os 4 pares originais, sem cherry-pick

`UNIVERSO_AMPLO` (`backtesting/portfolio_h14.py`, 34 pares) — já
existe, já foi filtrado por liquidez de spot para outra pesquisa (spec
040), **não escolhido especificamente para este teste**. Intersectado
programaticamente (não manualmente) com pares que têm mercado perpétuo
ativo na Binance E pelo menos 90 dias de histórico de funding — piso de
qualidade de dado (`MIN_DIAS_COBERTURA`), não um filtro de resultado.
Pares sem perpétuo (ex.: listagens só-spot, memecoins muito recentes)
são excluídos automaticamente (`fetch_funding_rate_history` devolve
DataFrame vazio em `ccxt.BadSymbol`), nunca contados como zero.

## Hipótese declarada antes de medir

**Principal:** com a correção de capital aplicada, a maioria dos pares
do universo ampliado continua abaixo do benchmark de 5% a.a. sobre
capital implantado — reforçando o veredito REPROVADA original, agora
com mais rigor metodológico.

**Alternativa, com igual peso:** algum subconjunto do universo (pares
de alta volatilidade idiossincrática, historicamente associados a
funding mais alto por viés de posição comprada do varejo) supera o
benchmark mesmo sobre capital implantado — justificando uma spec nova
de infraestrutura de execução (permissão de futuros, gestão de margem)
como próximo passo, fora do escopo desta.

## Reprodução

`python main.py funding` · `reports/funding_*.json`.

(Resultado real preenchido após a execução — ver
`docs/research/registro-de-hipoteses.md` §4.9 para o número medido.)
