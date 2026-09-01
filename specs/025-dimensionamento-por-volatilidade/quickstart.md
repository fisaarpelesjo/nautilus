# Quickstart — H12: validar o dimensionamento por volatilidade

Cenários executáveis que provam a feature de ponta a ponta.

## Pré-requisitos

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
```

Sem chave de API: OHLCV é endpoint público.

---

## Cenário 1 — Comparação pareada (US1, P1)

```bash
python main.py volatilidade
```

**Esperado:** por combinação, drawdown e retorno nas duas versões com os deltas,
mais o status. Relatório em `reports/volatilidade_*`.

**Falha se:** o relatório mostrar apenas a versão dimensionada, impossibilitando
a comparação — H12 não pergunta se a versão dimensionada é boa, pergunta se é
melhor que a mesma estratégia sem dimensionamento.

---

## Cenário 2 — Redução de exposição não vira melhoria (US2, P1)

Inspecionar uma combinação cujo drawdown caiu e cujo ganho de timing não subiu.

**Esperado:** status `sem vantagem`, com o delta de exposição visível.

**Falha se:** essa combinação aparecer como `melhora`. Seria o achado M7
repetido: dimensionar por volatilidade reduz exposição por construção — ~10% em
média, medido em `research.md` — e num mercado em queda isso sozinho melhora o
retorno relativo sem qualquer capacidade de seleção.

**Por que este cenário é o mais importante:** se ele falhar, H12 passa
trivialmente e a aprovação não significa nada.

---

## Cenário 3 — Separar mecanismo de custo de giro (US3, P2)

**Esperado:** número de operações e custo de execução de cada versão, mais o
resultado sem custo, permitindo verificar se a diferença persiste com custo
zerado.

**Falha se:** apenas o retorno líquido for reportado.

---

## Cenário 4 — O fator nunca amplia a posição

```bash
python main.py volatilidade 0.5
```

Alvo absurdamente alto, muito acima de qualquer `atr_ratio` observado (p99 =
0,0474).

**Esperado:** fator médio exatamente `1,000` e resultado **idêntico** à linha de
base, combinação por combinação.

**Falha se:** qualquer fator exceder 1,0, ou o resultado divergir da base. FR-003
e a proibição de alavancagem da constituição dependem do teto na fórmula.

---

## Cenário 5 — Volatilidade indisponível recai no tamanho vigente

Série com `atr_ratio` nulo ou ausente.

**Esperado:** fator 1,0, tamanho igual ao que o sistema já calcularia.

**Falha se:** produzir divisão por zero, posição infinita, ou entrada suprimida.
Dado desconhecido não vira decisão silenciosa.

---

## Cenário 6 — Amostra insuficiente é inconclusiva

Combinação em que uma das versões produz menos operações que o mínimo.

**Esperado:** `inconclusivo`, com a contagem das duas versões declarada.

**Falha se:** aparecer como `piora`. Comparar 30 operações contra 4 não mede
dimensionamento, mede diferença de amostra.

---

## Cenário 7 — Produção intacta (FR-013, SC-006)

```bash
git diff --stat risk/manager.py     # antes e depois da execução
python main.py volatilidade
git diff --stat risk/manager.py
```

**Esperado:** sem alteração. O arquivo está sob o princípio Safety First da
constituição.

**Falha se:** houver qualquer diferença.

---

## Cenário 8 — Regressão do motor

O parâmetro de dimensionamento tem default que preserva o comportamento atual.

**Esperado:** `simulate_backtest` sem o parâmetro produz resultado idêntico ao
de antes desta feature, verificado pela suíte existente.

**Falha se:** a contagem de testes que passam diminuir.

---

## Suíte automatizada

```bash
pytest tests/test_volatilidade.py -q
pytest -q
```

---

## Critério de conclusão

A feature está pronta quando os oito cenários passam **e** o veredito de H12
consta de `docs/research/registro-de-hipoteses.md` com evidência e procedência —
favorável ou não. O registro do resultado negativo é parte da entrega.
