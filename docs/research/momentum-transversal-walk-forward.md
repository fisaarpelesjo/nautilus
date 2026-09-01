# Momentum transversal — do +29pp ao ganho de timing negativo

**Data:** 2026-09-01
**Pergunta:** o resultado promissor do momentum transversal se sustenta?
**Resposta:** não. Em walk-forward, o ganho de timing médio é **−1,37pp**.

## O que parecia

Uma configuração (lookback 30, top_k 3, rebalance 12) mediu, numa janela de
confirmação out-of-sample:

- retorno **+28,97%** contra buy-and-hold **−0,32%** → edge **+29,29pp**
- profit factor 1,96
- reprovada apenas por drawdown: 11,76% contra o teto de 10%

Foi o primeiro resultado desta investigação que falhou **no limite de risco** em
vez de falhar por não ter vantagem. Justificava explorar.

## O que o walk-forward mostrou

Cinco janelas contíguas e não sobrepostas de 400 candles (~67 dias cada), sem
selecionar configuração — um conjunto fixo de variantes, cada uma com hipótese
declarada, medido em regimes diferentes.

| Variante | Ret. médio | Pior janela | Janelas positivas | DD máx |
|---|---|---|---|---|
| base | −11,85% | −31,80% | 1 de 5 | 35,19% |
| diluida (top_k 6) | −8,70% | −24,28% | 1 de 5 | 26,30% |
| exigente (min_mom 10%) | −8,11% | −18,38% | 1 de 5 | 18,63% |
| lenta (lookback 90) | −8,77% | −26,61% | 1 de 5 | 30,23% |
| exigente+ | **−3,49%** | **−9,52%** | 2 de 5 | **9,66%** |

**Nenhuma aprovada em nenhuma janela.** O +29pp não replicou.

## O teste que separou habilidade de ausência

Uma estratégia que fica em caixa num mercado em queda parece habilidosa sem ser.
A referência correta não é o buy-and-hold cheio, é o buy-and-hold **mantido na
mesma fração de capital**:

```
ganho de timing = retorno da estratégia − (buy-and-hold × exposição)
```

No período completo de 333 dias, esse teste separou as variantes:

| Variante | Exposição | Retorno | Passivo equivalente | Ganho de timing |
|---|---|---|---|---|
| exig 20% | 13,2% | −6,54% | −7,26% | **+0,72pp** |
| exigente+ | 55,8% | −17,42% | −30,70% | +13,27pp |
| exig lenta | 92,7% | −7,22% | −51,00% | **+43,78pp** |

`exig 20%` parecia a melhor pelo retorno bruto (−6,54% num mercado que caiu 55%)
e é a pior pelo timing: quase todo o resultado é não ter estado lá.

`exig lenta` parecia genuína — 92,7% de exposição, +43,78pp de timing.

## E então o walk-forward matou `exig lenta` também

| Janela | Regime | B&H | Estratégia | Exposição | Ganho de timing |
|---|---|---|---|---|---|
| 1 | baixa | −35,1% | −1,42% | 17,3% | +4,65pp |
| 2 | baixa | −27,3% | −4,98% | 78,2% | +16,38pp |
| 3 | lado | +0,2% | −9,81% | 91,7% | **−9,99pp** |
| 4 | baixa | −26,8% | −0,10% | 12,0% | +3,11pp |
| 5 | **alta** | **+24,8%** | **+3,78%** | **100,0%** | **−21,01pp** |

**Média: −1,37pp. Três janelas positivas de cinco.**

A janela 5 é a que encerra o assunto: **100% investida numa alta de 24,8%, e
capturou 3,78%**. Isso não é reduzir exposição — é escolher os ativos errados.

Os ganhos das janelas 1 e 4 vêm com exposição de 17% e 12%: são o efeito de
ausência outra vez, não seleção.

## Conclusão

O momentum transversal, nas configurações testadas, **não tem habilidade de
seleção**. O que ele tem é exposição variável, que ajuda em queda e custa caro
em alta. O +43,78pp do período completo era o resultado de um período que caiu
55% — a ordem de composição favorecendo quem estava menos presente.

O +29pp inicial era uma janela, não uma estratégia.

## O que fica

`walk_forward()` e `WalkForwardFold.ganho_de_timing_pp` em
`backtesting/cross_sectional.py`. As duas coisas que faltavam ao projeto:

1. **Múltiplas janelas em vez de uma.** Uma janela de confirmação não distingue
   vantagem de sorte de regime. Foi o que quase aprovou esta estratégia.
2. **Descontar a exposição.** Sem isso, "perdi 6% enquanto o mercado caiu 55%"
   é lido como habilidade quando pode ser apenas ausência.

Ambas são reutilizáveis por qualquer estratégia de carteira futura, e ambas
nasceram de um falso positivo que teria sido enviado com o teste anterior.
