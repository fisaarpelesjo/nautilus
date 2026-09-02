# Fase 0 — Pesquisa: H15, arbitragem entre corretoras

**Data:** 2026-09-01

---

## Correção de um número que entrou na spec errado

A spec cita latência de **2,0 a 6,1 segundos** por consulta de livro. Esse
número veio de uma medição preliminar que incluía `load_markets()` e conexão
fria. A latência **quente** — que é a que importa, porque um processo de
arbitragem mantém as conexões abertas — é de **272 a 1.082 ms, mediana 342 ms**.

A correção enfraquece o argumento de US3 em uma ordem de grandeza, e por isso
está aqui em vez de ser silenciosamente ajustada. O argumento **sobrevive**, mas
por menos: uma arbitragem exige duas leituras e duas ordens, algo em torno de
**1,4 s** no melhor caso — ainda muito para um diferencial de topo de livro.

---

## D1 — Conjunto de corretoras

**Decisão:** `binance`, `bybit`, `okx`, `kucoin`, `gate`, `kraken`.

**Medição** (`BTC/USDT`, livro de 100 níveis):

| Corretora | Taxa tomador | Latência fria | Latência quente | Profundidade mín. | Slippage a $10k |
|---|---|---|---|---|---|
| binance | **0,100%** | 2.660 ms | 272 ms | 0,50 M | 0,0000% |
| bybit | **0,100%** | 4.715 ms | 351 ms | 0,42 M | 0,0000% |
| kucoin | **0,100%** | 2.125 ms | 336 ms | 0,26 M | 0,0000% |
| okx | 0,150% | 2.406 ms | 347 ms | 1,97 M | 0,0000% |
| gate | 0,200% | 10.364 ms | 282 ms | 0,37 M | 0,0000% |
| kraken | 0,400% | 1.338 ms | 1.082 ms | 1,08 M | 0,0018% |

**Rationale.** Selecionadas por **acessibilidade pública e liquidez**, nunca por
diferencial observado — a restrição está em Assumptions da spec. Todas expõem
livro sem chave de API e têm `BTC/USDT`.

Kraken entra apesar da taxa de 0,400% e da latência de 1.082 ms: excluí-la por
ser cara seria selecionar pelo resultado esperado, que é precisamente o que a
restrição proíbe. Ela participa e o relatório mostrará que suas combinações são
as piores.

**Formato do livro difere entre corretoras.** Kraken e OKX devolvem três campos
por nível (preço, quantidade, instante); as demais, dois. Uma implementação que
assuma dois falha nas duas — aconteceu na primeira medição desta fase.

---

## D2 — Volume de referência

**Decisão:** **US$ 10.000** por perna.

**Rationale.** O slippage medido a $10k é **0,0000%** em cinco das seis
corretoras e 0,0018% na Kraken. Nesse volume, o topo do livro descreve bem o
preço de execução, e o diferencial medido não é artefato de profundidade.

É também a ordem de grandeza plausível para este projeto. Volumes muito maiores
mediriam um obstáculo que o projeto não enfrentaria; muito menores tornariam o
custo fixo dominante.

**A profundidade não é o gargalo aqui**, e registrar isso importa: a hipótese
poderia falhar por livro raso, e não é o caso.

---

## D3 — Custo de execução

**Decisão:** taxa pública de **tomador de liquidez nos dois lados**, sem
desconto por volume.

| Combinação | Custo de ida e volta |
|---|---|
| Melhor caso (binance / bybit / kucoin) | **0,200%** |
| Mediano | 0,250% |
| Pior caso (kraken em um lado) | 0,500% |

**Por que tomador nos dois lados.** Arbitragem exige execução **imediata** — o
diferencial some. Uma ordem limite que espera não é arbitragem; é especulação
direcional com passos extras. Assumir taxa de provedor de liquidez seria assumir
que a ordem repousa no livro, o que contradiz a tese.

---

## D4 — Teto de latência

**Decisão:** **2.000 ms** entre a primeira e a última leitura de uma comparação.

**Rationale.** Duas leituras a 342 ms medianos somam ~700 ms; o teto dá folga de
quase três vezes para variação de rede. Acima disso, as duas pontas descrevem
instantes distantes demais e o diferencial calculado entre elas não existiu
simultaneamente em lugar nenhum.

Comparações acima do teto recebem estado próprio (FR-005) e não contam como
oportunidade.

---

## D5 — Persistência

**Decisão:** um arquivo por linha (JSONL) em `data/arbitragem.jsonl`.

**Rationale.** A amostra cresce por acréscimo, execução após execução, e nunca
é reescrita. JSONL é o formato que o projeto já usa para eventos estruturados
(`logs/events-*.jsonl`), suporta acréscimo sem ler o arquivo inteiro, e sobrevive
a uma execução interrompida no meio — a última linha parcial se descarta e o
resto permanece.

CSV exigiria cabeçalho fixo e dificultaria acrescentar campos; um banco seria
infraestrutura nova para um volume que não a justifica.

---

## D6 — Executabilidade operacional

**Decisão:** **inexecutável com a infraestrutura atual**, e o motivo não é a
latência.

1. **Capital pré-posicionado.** Arbitragem sem transferência exige saldo nas
   duas corretoras simultaneamente. O bot opera numa. Isto é decisão de alocação
   de capital do usuário, não de engenharia.
2. **Chaves de API em múltiplas corretoras**, cada uma com permissão de
   negociação. A constituição do projeto restringe permissões e proíbe saque;
   ampliar para N corretaras multiplica a superfície de risco.
3. **Execução simultânea nas duas pernas.** Executar uma e falhar na outra
   deixa posição direcional aberta — exatamente o que a arbitragem existe para
   evitar. Não há mecanismo para isso.

**Nenhum dos três está no escopo desta spec**, que mede se a oportunidade
existe. Se não existir, os três se tornam irrelevantes — e é essa a ordem certa
de investigar.

---

## Medição preliminar do diferencial

Instantâneo único, seis corretoras, mesma moeda de cotação:

| Grandeza | Valor |
|---|---|
| Maior diferencial **bruto** | **+0,0203%** (compra `gate`, vende `kucoin`) |
| Custo dos dois lados nessa combinação | 0,300% |
| Diferencial **líquido** | **−0,2797%** |
| Custo mínimo possível (melhor par de taxas) | 0,200% |

**O diferencial bruto é dez vezes menor que o custo mínimo possível.**

Isto **não é o veredito** — é um instantâneo, e a spec declara que o veredito
exige campanha de amostragem. Mas reformula o que a campanha precisa encontrar:
não se trata de o diferencial ficar ligeiramente acima ou abaixo do custo. Para
H15 ser viável, ele precisaria ser **uma ordem de grandeza maior** do que o
observado.

Registrar isso agora, antes da campanha, impede que o resultado seja apresentado
como surpresa — e impede a mim mesmo procurar razões para descartá-lo depois.

---

## Resumo das decisões

| # | Decisão | Efeito |
|---|---|---|
| D1 | Seis corretoras, por liquidez e acesso | Kraken incluída apesar de cara: excluí-la seria selecionar pelo resultado |
| D2 | US$ 10.000 por perna | Slippage 0,0000% em 5 de 6: profundidade não é o gargalo |
| D3 | Tomador nos dois lados | Custo mínimo 0,200%; limite não é ajustável sem contradizer a tese |
| D4 | Teto de 2.000 ms | ~3× a soma de duas leituras medianas |
| D5 | JSONL por acréscimo | Amostra cresce entre execuções; formato já usado no projeto |
| D6 | Inexecutável hoje | Capital pré-posicionado, chaves múltiplas, execução simultânea |

**Expectativa registrada antes da campanha.** Com diferencial bruto uma ordem de
grandeza abaixo do custo, o resultado provável é que H15 seja reprovada por
margem — não por amostra. Se a campanha mostrar diferenciais líquidos positivos
recorrentes, a explicação mais provável **não** é oportunidade: é liquidez
fantasma, retirada suspensa em alguma das pontas, ou par com cotação que só
parece equivalente.

## Fontes

- Medição própria, 2026-09-01: seis corretoras via ccxt 4.5.73, `BTC/USDT`,
  livro de 100 níveis, três leituras por corretora.
- `docs/research/registro-de-hipoteses.md` §6.3-b (frentes direcionais
  esgotadas), §4.15 e §4.16.
