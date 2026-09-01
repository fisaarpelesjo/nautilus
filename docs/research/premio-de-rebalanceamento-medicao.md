# Prêmio de rebalanceamento — a matemática está certa, os insumos não

**Data:** 2026-09-01
**Pergunta:** dá para extrair retorno da volatilidade sem prever nada?
**Resposta:** a matemática é real. A pré-condição dela **não é atendida** por
cripto contra cripto.

## A ideia

O prêmio de rebalanceamento (demônio de Shannon, *volatility pumping*) é a única
ideia desta investigação que é literalmente aritmética, não teoria de mercado.
Rebalançar periodicamente entre ativos voláteis e **descorrelacionados** extrai
retorno da própria volatilidade: você vende automaticamente o que subiu e compra
o que caiu, e a média geométrica da carteira supera a média dos ativos.

Não prevê nada. Não depende de regime. É consequência da desigualdade entre
média aritmética e geométrica.

**A condição:** os ativos precisam ser voláteis **e** pouco ou negativamente
correlacionados. Sem isso não há o que rebalancear — vender o que subiu para
comprar o que caiu não significa nada quando os dois sobem e caem juntos.

## Condição 1: correlação — reprovado

12 pares, 2000 candles de 4h, correlação de retornos:

| | |
|---|---|
| Mediana | **0,71** |
| Mínima | 0,34 |
| Máxima | 0,89 |
| Pares com correlação < 0,3 | **0 de 72** |
| Pares com correlação < 0,0 | **0 de 72** |

Nenhum par do universo chega perto do necessário. O altcoin mais "independente"
ainda anda 34% junto com os outros.

## Condição 2: o prêmio aparece? — reprovado

**Carteira igualmente ponderada de 12 pares:**

| Rebalanceamento | Retorno | Drawdown |
|---|---|---|
| a cada 6 candles | −56,53% | −67,00% |
| a cada 42 candles | −56,33% | −66,96% |
| a cada 180 candles | −56,70% | −67,05% |
| **nunca (buy & hold)** | **−54,87%** | −64,82% |

**Rebalancear piorou o resultado.** Sem correlação baixa não há prêmio, e o
custo de giro é real — sobra só o custo.

**BTC + caixa:**

| Alocação em BTC | rebal 6c | rebal 42c | rebal 180c |
|---|---|---|---|
| 100% | −35,25% | −35,25% | −35,25% |
| 50% | −17,84% | −17,17% | −17,26% |
| 25% | −8,89% | −8,35% | −8,44% |

50% em BTC dá −17,8%, que é exatamente −35,25% × 0,5. **Escalonamento puro de
exposição, prêmio zero.** A frequência de rebalanceamento quase não altera o
resultado (−17,84% contra −17,26%), que é a assinatura de prêmio inexistente.

Por que zero: o prêmio exige os **dois** ativos voláteis. Caixa tem volatilidade
zero, então não há oscilação para capturar do lado dele.

## Conclusão

A matemática do demônio de Shannon está correta. Ela simplesmente não se aplica
a um universo onde tudo tem correlação 0,71 — e a única coisa realmente
descorrelacionada disponível (caixa) não é volátil.

Para o prêmio existir seria preciso um ativo volátil e descorrelacionado de
cripto. Isso não está dentro de cripto.

## Registro do argumento

Este documento existe porque a pergunta foi feita na forma "isso é matemática,
então dá para lucrar". A resposta honesta é que **sim, é matemática, e a
matemática diz que não dá — com estes insumos**. A fórmula não foi refutada; a
pré-condição dela foi medida e reprovada.
