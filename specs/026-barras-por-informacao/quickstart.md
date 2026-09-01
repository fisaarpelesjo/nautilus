# Quickstart — validação de H13

Cenários executáveis que provam que a feature faz o que a spec pede. Cada um
declara o que observar e o que significa falhar.

## Pré-requisitos

```bash
cd C:\Users\filip\OneDrive\Documents\GitHub\itgr
.venv\Scripts\activate
```

Acesso de leitura à Binance (dados públicos). Nenhuma chave de API é necessária
para os cenários de pesquisa.

---

## Cenário 1 — Comparação pareada ancorada em calendário (US1, P1)

```bash
python main.py barras
```

**Esperado:** tabela onde cada linha traz observações das duas versões, o
intervalo de calendário comum, e as métricas de cada lado.

**Falha se:** o intervalo de calendário diferir entre as versões, ou o número de
observações não aparecer. Sem esses dois, a comparação pode estar medindo
tamanho de amostra em vez de esquema de amostragem — a restrição estrutural
desta hipótese.

---

## Cenário 2 — Menos participação não vira vantagem (US2, P1)

**O cenário mais importante da spec.**

Observar as combinações cuja versão de barras opera menos e cujo retorno melhora
apenas na proporção da menor participação.

**Esperado:** estado `sem vantagem`, nunca `melhora`. E combinação cuja versão de
tempo perde dinheiro recebe `confundido`, nunca `melhora`.

**Falha se:** alguma combinação com `dTiming <= 0` aparecer como `melhora`, ou
alguma com retorno de tempo negativo aparecer como `melhora`. Seria M7/M11 se
repetindo numa quarta forma, e o resultado entraria no registro como falso
positivo.

---

## Cenário 3 — Construção não usa futuro (US3, P1)

```bash
pytest tests/test_bars.py -k causalidade -v
```

**Esperado:** barras construídas incrementalmente, prefixo a prefixo, são
**exatamente iguais** às construídas sobre a série completa.

**Falha se:** houver qualquer diferença. Uma barra que conhece o próprio total
futuro produz o resultado mais convincente e mais falso possível — é a classe de
defeito de M2, que passou meses despercebida no projeto.

---

## Cenário 4 — Barra incompleta é descartada

```bash
pytest tests/test_bars.py -k incompleta -v
```

**Esperado:** a última barra, se não cruzou o limiar, não aparece na saída.

**Falha se:** ela aparecer. Seu `close` é o preço do instante em que os dados
acabaram, e tratá-lo como fechamento é transformar um instante arbitrário em
decisão.

---

## Cenário 5 — Reamostragem inerte é estado próprio

```bash
pytest tests/test_bars.py -k inerte -v
```

**Esperado:** limiar tão baixo que cada candle vira uma barra produz estado
`inerte`, não `piora`.

**Falha se:** aparecer como `piora`. Foi o defeito D2 de H12: 33 combinações
afirmando deterioração onde nada havia mudado.

---

## Cenário 6 — Aquecimento verificado em dias

```bash
pytest tests/test_barras_scan.py -k aquecimento -v
```

**Esperado:** combinação cujo aquecimento de 50 barras não cabe no histórico em
dias de calendário é `inconclusivo`.

**Falha se:** for avaliada normalmente. H11 tropeçou nisto: 50 candles semanais
eram 350 dias, quase um ano consumido antes da primeira decisão.

---

## Cenário 7 — Amostra insuficiente é inconclusiva

```bash
pytest tests/test_barras_scan.py -k amostra -v
```

**Esperado:** menos operações que `EDGE_MIN_TRADES` em **qualquer** das versões
produz `inconclusivo`, mesmo que as métricas pareçam ruins.

**Falha se:** produzir `piora`. Regra de H10, H11 e M9.

---

## Cenário 8 — Buy-and-hold ancorado

```bash
pytest tests/test_barras_scan.py -k buy_hold -v
```

**Esperado:** buy-and-hold idêntico entre as versões dentro de tolerância
numérica; divergência maior produz `erro`, não uma comparação silenciosa.

**Falha se:** a comparação prosseguir com referências diferentes. O buy-and-hold
é o único ponto fixo entre as duas amostragens; se ele se mover, nada é
comparável.

---

## Cenário 9 — Produção intacta (FR-015, SC-006)

```bash
git diff --stat <commit-inicial-da-spec>..HEAD -- risk/ execution/ trading/ data/fetcher.py
```

**Esperado:** saída vazia.

**Falha se:** houver qualquer alteração. O bot roda em modo paper no VPS 24/7;
uma mudança acidental num desses caminhos altera o comportamento de um processo
em execução.

---

## Cenário 10 — Suíte completa sem regressão

```bash
pytest tests/ -q
```

**Esperado:** contagem de testes maior que a anterior à feature, zero falhas.

**Falha se:** a contagem cair. Teste removido para fazer a suíte passar é o
oposto do que a Constituição III pede.

---

## Critério de conclusão

Os dez cenários passam, e o veredito de H13 está registrado em
`docs/research/registro-de-hipoteses.md` com evidência, procedência, declaração
de executabilidade operacional (D6) e o diagnóstico da reamostragem — que é o
que distingue "não houve vantagem" de "o instrumento não mediu nada".
