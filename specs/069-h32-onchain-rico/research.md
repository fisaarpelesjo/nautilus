# Research: H32 — on-chain mais rico

## D1 — viabilidade de fonte de dado (verificado 2026-09-03, chamadas reais)

H17 testou só `n-unique-addresses` (crescimento de rede) via
`api.blockchain.info/charts`, a mesma fonte já integrada
(`data/onchain.py`). Testado nesta spec, com chamadas reais (30 dias,
`sampled=false`):

| Métrica | Status | Registros (30d) | Categoria |
|---|---|---|---|
| `trade-volume` | OK | 31 | Volume de negociação em corretoras |
| `estimated-transaction-volume-usd` | OK | 30 | Valor movimentado on-chain (USD) |
| `transaction-fees-usd` | OK | 23 | Congestionamento de rede |
| `miners-revenue` | OK | 23 | Receita de mineradores |
| `my-wallet-n-users` | OK | 720 | Usuários do app Blockchain.com |
| `output-volume` | OK | 30 | Volume de saídas de transação (BTC) |
| `mvrv` | **404** | — | Não disponível nesta API |
| `nvt` | **404** | — | Não disponível nesta API |
| `exchange-net-flow` | **404** | — | Não disponível nesta API |

**Achado: existe atributo novo e gratuito, na MESMA fonte já
integrada — nenhuma dependência nova, nenhuma chave de API.**
`mvrv`/`nvt`/`exchange-net-flow` (as métricas de posicionamento mais
citadas na literatura de whale-tracking) não existem nesta API
gratuita — confirma a parte do obstáculo já esperada (essas exigem
provedor pago, Glassnode/Nansen/CryptoQuant). Mas `estimated-transaction
-volume-usd` (valor transacionado on-chain, em USD) é um atributo
genuinamente disponível e qualitativamente diferente do já testado.

## D2 — atributo declarado: valor transacionado on-chain, não contagem de rede

`n-unique-addresses` (H17) mede QUANTOS endereços estão ativos —
atividade de rede. `estimated-transaction-volume-usd` mede QUANTO valor
está se movendo — magnitude, não contagem. Um dia com poucos endereços
mas transações grandes (movimento de posições concentradas) teria sinal
oposto nos dois atributos — categoricamente diferente, não uma
reformulação do mesmo dado.

**Descartado nesta rodada:** `trade-volume` (redundante com o volume de
OHLCV da própria Binance, já um dos 5 atributos de H14 —
`volume_ratio`); `my-wallet-n-users` (dataset proprietário do app
Blockchain.com, proxy fraco e ruidoso da rede inteira, atualização
diária mas com viés de usuário de varejo de uma única carteira);
`miners-revenue`/`transaction-fees-usd` (interessantes para uma
hipótese de "capitulação de minerador", mas isso é uma pergunta
diferente de "positioning" — fica registrado como candidato futuro, não
testado aqui, para não abrir busca sobre múltiplos atributos ao mesmo
tempo).

## D3 — transformação: mesma técnica de H17, para comparabilidade direta

`onchain_txn_volume_growth_7d(serie) = (MA7 atual − MA7 há 7 dias) /
MA7 há 7 dias` — exatamente a mesma fórmula de
`onchain_addr_growth_7d` (H17), só trocando a série de entrada. Reusar a
técnica em vez de inventar uma nova isola a variável testada (o
atributo), não o método de transformação.

## D4 — universo e período

BTC/USDT, mesmo par único de H17 (a fonte é Bitcoin-only), 6.000
candles de 4h (`fetch_ohlcv`, mesmo histórico estendido de spec 036).
Comparação isolada par-a-par contra o modelo original de H14, nunca
contra o resultado pooled de 12 pares (mesma regra FR-005 de H17).

## D5 — checagem de colinearidade obrigatória antes de qualquer leitura de desempenho

Limiar de 0,80 (mesmo de H17) contra os 5 atributos de H14 **e** contra
`onchain_addr_growth_7d` (H17), já que os dois vêm da mesma fonte e
podem covariar. Se colinear, o atributo é descartado sem medir
desempenho — carregaria a mesma informação que já está sendo usada.

## Reprodução

`python main.py onchain_volume` · `specs/069-h32-onchain-rico/`.

(Resultado real preenchido após a execução — ver
`docs/research/registro-de-hipoteses.md` §6.2/§6.3 para o número
medido.)
