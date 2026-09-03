# Research: H30 — fator de tamanho/iliquidez (cross-sectional, sem timing)

## D1 — universo: reusa o subconjunto já corrigido de H10

`UNIVERSO_AMPLO_HISTORICO_COMPLETO` (`backtesting/pairs_trading.py`, 22
pares) — subconjunto de `UNIVERSO_AMPLO` (34 pares) já filtrado para
ter histórico completo de 6.000 candles, corrigindo o bug de colapso de
índice comum descoberto em H10 (spec 052): `split_treino_validacao`
usa a interseção do índice de tempo de TODOS os pares recebidos —
incluir um par com histórico curto colapsa a janela inteira para o
tamanho do mais curto. Não escolhido para este teste especificamente —
já existe, já corrigido.

## D2 — construção da cesta: N=7, rebalance a cada 180 candles

N = 7 (≈ 22/3, terço inferior/superior por volume). Rebalanceamento a
cada 180 candles de 4h (30 dias) — mesma ordem de grandeza de
rebalanceamento mensal usada em fundos de fator reais. Ambos declarados
antes de qualquer medição, não ajustados depois de ver o resultado.

## D3 — baseline: mesma construção sobre o terço de maior volume

Isola o efeito de TAMANHO/LIQUIDEZ, não "uma cesta de altcoins subiu
nesse período" — a cesta líquida usa exatamente a mesma mecânica
(igualmente ponderada, mesmo intervalo de rebalanceamento, mesmo custo)
sobre os 7 pares de MAIOR volume médio. Qualquer diferença de retorno
entre as duas cestas isola o fator de tamanho, não o mercado geral.

## D4 — custo: sensibilidade declarada, não medição pontual

Backtest histórico não tem acesso a order book do passado — o mesmo
motivo já documentado em `CLAUDE.md` para por que `REAL_SLIPPAGE_ENABLED`
só funciona em paper/live, nunca em backtest. Fingir uma medição real de
slippage por liquidez seria falso. Em vez disso, mede sob três
multiplicadores do slippage padrão do projeto (`BACKTEST_SLIPPAGE_PCT`,
0,05%): 1x, 3x e 5x — testa diretamente se um "prêmio" aparente é
robusto a assumir execução pior que o padrão (esperado para nomes menos
líquidos) ou se desaparece com um custo levemente mais realista.

## D5 — disciplina fora da amostra

Mesmo corte compartilhado de tempo de H10 (`split_treino_validacao`) —
divide os 22 pares numa única linha do tempo comum, treino (70%) e
validação (30%). O excesso de retorno ilíquida-líquida é reportado
separadamente para os dois cortes: só é lido como achado real se
aparecer em ambos, não só no treino (mesmo padrão "só na busca" que já
reprovou H5).

## Hipótese declarada antes de medir

**Principal:** a cesta ilíquida supera a líquida em retorno, com o
excesso presente tanto em treino quanto em validação, mesmo sob o
multiplicador de slippage mais severo (5x).

**Alternativa, com igual peso:** o excesso aparente desaparece (ou
inverte de sinal) ao subir o multiplicador de slippage, ou não se repete
entre treino e validação — refutando o fator como um tilt operável
mesmo que a literatura o documente em dados sem custo de execução real.

## Reprodução

`python main.py fator_tamanho` · `reports/fator_tamanho_*.json`.

(Resultado real preenchido após a execução — ver
`docs/research/registro-de-hipoteses.md` §6.1 para o número medido.)
