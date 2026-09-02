# Fase 1 — Modelo de dados: H15

## `LeituraLivro`

Uma consulta a um livro de ofertas, numa corretora, num instante.

| Campo | Tipo | Descrição |
|---|---|---|
| `corretora` | `str` | id ccxt (`binance`, `bybit`, `okx`, `kucoin`, `gate`, `kraken`) |
| `par` | `str` | símbolo unificado ccxt, ex. `BTC/USDT` |
| `instante` | `float` | `time.monotonic()` local no momento da resposta — **nunca** o timestamp que a corretora reporta (edge case "relógios dessincronizados": o intervalo entre leituras precisa do mesmo relógio) |
| `bids` / `asks` | `list[(float, float)]` | níveis normalizados `(preço, quantidade)` — ver `normalizar_niveis` |
| `erro` | `str \| None` | motivo da falha, quando a consulta não teve sucesso |

**`normalizar_niveis(raw: list) -> list[(float, float)]`**: kraken e okx
devolvem três campos por nível (preço, quantidade, instante do nível); as
demais corretoras devolvem dois (D1, achado de implementação). A normalização
descarta o terceiro campo quando presente — o `instante` de `LeituraLivro` já
é o que importa para o teto de latência (D4), e o instante por nível não é
usado em nenhum requisito.

Uma `LeituraLivro` com `erro` preenchido não participa de nenhuma
`Comparacao` — é como a corretora "não respondeu neste ciclo" (FR-011).

---

## `Comparacao`

Duas leituras do mesmo par, em corretoras distintas, com mesma moeda de
cotação (FR-003 — comparações de cotação diferente **nunca chegam a existir**
como `Comparacao`; são contadas à parte como recusadas).

| Campo | Descrição |
|---|---|
| `corretora_compra` / `corretora_venda` | Onde comprar (ask mais barato) / vender (bid mais caro) |
| `preco_medio_compra` / `preco_medio_venda` | Preço médio de execução sobre `volume_usdt` (FR-001), não o topo do livro |
| `volume_preenchido_usdt` | Quanto do `volume_usdt` pretendido o livro de fato comportava |
| `diferencial_bruto_pct` | `(preco_medio_venda - preco_medio_compra) / preco_medio_compra` |
| `custo_pct` | Taxa de tomador das duas pontas somada (D3) — `None` se alguma corretora não está em `TAXA_TOMADOR` |
| `diferencial_liquido_pct` | `diferencial_bruto_pct - custo_pct`, ou `None` se `custo_pct` é `None` |
| `intervalo_ms` | `abs(instante_venda - instante_compra) * 1000` — mesmo relógio local (edge case) |
| `estado` | Ver tabela de estados abaixo |
| `instante_registro` | Quando a `Comparacao` foi montada — vira a linha do tempo em `data/arbitragem.jsonl` |

### `preco_medio_execucao(niveis, volume_usdt) -> (preco_medio, volume_preenchido)`

Caminha os níveis a partir do melhor preço, igual em espírito a
`execution/liquidity.py::estimate_slippage_pct` mas **não é a mesma função**
(ver `plan.md`, Project Structure — duplicação deliberada entre pesquisa e
execução real). Se o livro inteiro não comporta `volume_usdt`,
`volume_preenchido < volume_usdt` e o preço médio reflete só o que foi
possível preencher — nunca extrapola além da profundidade real (mesmo
princípio do `None` em `estimate_slippage_pct`, adaptado: aqui o chamador
sempre recebe um preço, mas sabe exatamente sobre quanto volume ele é válido).

---

## Estados de `Comparacao`

**A ordem das checagens é a regra**, como em 024–027.

| # | Estado | Condição |
|---|---|---|
| 1 | `custo_desconhecido` | `custo_pct is None` — alguma corretora fora de `TAXA_TOMADOR` (FR-006) |
| 2 | `profundidade_insuficiente` | `volume_preenchido_usdt < volume_usdt` em qualquer perna (FR-007) |
| 3 | `latencia_alta` | `intervalo_ms > TETO_LATENCIA_MS` (2.000, D4) — FR-005 |
| 4 | `oportunidade` | `diferencial_liquido_pct > 0` |
| 5 | `sem_oportunidade` | `diferencial_liquido_pct <= 0` — caso esperado por D6/pesquisa preliminar |

Justificativa da ordem:

- **`custo_desconhecido` precede tudo**: sem custo conhecido não existe
  diferencial líquido para classificar — calcular qualquer estado abaixo
  disso seria tratar o custo desconhecido como zero pela porta dos fundos
  (o que FR-006 proíbe explicitamente).
- **`profundidade_insuficiente` precede `latencia_alta`**: um preço médio
  calculado sobre volume parcial já é uma medição degradada; classificá-la
  como oportunidade ou não-oportunidade antes de sinalizar isso esconderia
  por que o número saiu do jeito que saiu.
- **`latencia_alta` precede a classificação de oportunidade**: um
  diferencial calculado entre leituras separadas por mais de 2 segundos não
  descreve um instante que existiu em lugar nenhum (spec, US3) — reportá-lo
  como "oportunidade" seria descrever algo inexecutável como se fosse real.
- **`oportunidade` / `sem_oportunidade` são mutuamente exclusivos** e só se
  aplicam quando as três checagens anteriores passam — é a leitura "limpa".

Uma `Comparacao` sempre tem os campos numéricos preenchidos (nunca `None`
silencioso, exceto `custo_pct`/`diferencial_liquido_pct` no estado
`custo_desconhecido`) — o estado é uma **classificação sobre** o número, não
uma substituição dele. Mesmo `profundidade_insuficiente` e `latencia_alta`
carregam o diferencial calculado, só que marcado como não-confiável.

---

## `ObservacaoPersistida`

Uma `Comparacao` depois de gravada em `data/arbitragem.jsonl` — mesmos campos,
serializados como uma linha JSON. `data/arbitragem_store.py` não adiciona
campo nenhum além do que `Comparacao` já tem; é uma camada de I/O, não de
modelo.

**Persistência é por acréscimo, nunca reescrita** (D5): cada execução de
`python main.py arbitragem` abre o arquivo em modo `a`, escreve uma linha por
`Comparacao` gerada no ciclo, fecha. Uma execução interrompida no meio deixa
no máximo uma linha parcial no fim do arquivo; a leitura descarta qualquer
linha que não faça `json.loads` com sucesso, sem abortar a leitura das
demais.

---

## `RelatorioH15`

Saída de uma execução: as comparações do ciclo atual **mais** o agregado de
tudo que já foi persistido.

| Campo | Descrição |
|---|---|
| `comparacoes_ciclo` | `list[Comparacao]` geradas nesta execução |
| `corretoras_indisponiveis` | Quais corretoras falharam neste ciclo (FR-011) — a medição continua sem elas |
| `pares_recusados` | Combinações descartadas por cotação diferente, com o motivo (FR-003) — vazio quando só `BTC/USDT` é medido, mas o campo existe para quando a spec crescer para múltiplos pares |
| `periodo_coberto` | `(primeira_observacao, ultima_observacao)` de **todo** `data/arbitragem.jsonl`, não só do ciclo — FR-009 |
| `n_observacoes_total` | Linhas válidas acumuladas em `data/arbitragem.jsonl` |
| `n_observacoes_por_combinacao` | `dict[(corretora_a, corretora_b), int]` |
| `estado_agregado` | `"inconclusivo"` ou `"amostra_suficiente"` — ver abaixo |
| `executavel_em_producao` | Declaração estática de D6, sempre `False`, com o motivo (capital pré-posicionado, chaves múltiplas, execução simultânea) — FR-015 |

### `estado_agregado` e o limite desta spec

`MIN_OBSERVACOES_AGREGACAO = 30` **por combinação de corretoras**, declarado
em `backtesting/arbitragem.py`. É o tamanho de amostra convencional a partir
do qual uma média deixa de ser dominada por um único ponto extremo (regra
prática, não derivada dos dados) — o mesmo espírito de `MIN_DESFECHOS` em
`backtesting/geometria.py`, um número declarado antes de qualquer resultado,
não ajustado a ele.

`estado_agregado = "amostra_suficiente"` quando a combinação mais medida
atinge `MIN_OBSERVACOES_AGREGACAO`. **Isto não é um veredito de
aprovação/reprovação** — `RelatorioH15` não tem esse campo. A spec.md declara
explicitamente que o veredito "virá quando a amostra existir" (Assumptions);
esta fase entrega o instrumento e o descritivo (média, mediana e % de ciclos
com `diferencial_liquido_pct > 0` por combinação), nunca uma classificação
aprovada/reprovada. Calcular isso aqui seria a spec prometer o que ela mesma
declara que não pode entregar ainda — a mesma armadilha que a "Iteração 1" do
checklist já corrigiu uma vez (spec original prometia veredito).

Enquanto `estado_agregado == "inconclusivo"`, o relatório declara `N` e
quanto falta — nunca "reprovado" (FR-010).
