# Quickstart — H11: validar a avaliação de horizonte temporal

Cenários executáveis que provam a feature de ponta a ponta. Não contém código de
implementação; ver `tasks.md` para isso.

## Pré-requisitos

```bash
python -m venv .venv && .venv\Scripts\activate    # Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

Nenhuma chave de API necessária: OHLCV é endpoint público. Conectividade com a
Binance é o único requisito externo.

---

## Cenário 1 — Execução completa (User Story 1, P1)

```bash
python main.py horizonte
```

**Esperado:**

- Uma seção por horizonte (4h, 1d, 1w).
- Cada seção abre com o contexto de dado, depois a contagem de avaliadas /
  confirmadas / inconclusivas, e só então a tabela.
- Nenhuma combinação com menos operações que o mínimo aparece como `reprovado`.
- Relatório gravado em `reports/horizonte_*.json`, `.csv` e `.md`.

**Falha se:** uma combinação com 3 operações aparecer como `reprovado` em vez de
`inconclusivo`; ou a contagem vier depois da tabela.

---

## Cenário 2 — Horizonte semanal é inconclusivo por amostra (Edge case)

```bash
python main.py horizonte 1w
```

**Esperado:** todas as combinações em `inconclusivo`, com motivo declarando
amostra insuficiente. Pela medição de `research.md`, o horizonte semanal entrega
de 261 a 423 candles utilizáveis; o split 70/30 produz janela de validação de 78
a 127, abaixo do mínimo de 150.

**Falha se:** alguma combinação semanal aparecer como `reprovado` ou
`confirmado` — nos dois casos o dimensionamento das janelas está errado.

**Por que este cenário importa:** é a distinção que salvou H10 de uma reprovação
indevida. Se ela não funcionar aqui, não funciona em lugar nenhum.

---

## Cenário 3 — Separar vantagem preditiva de economia de custo (User Story 2, P2)

```bash
python main.py horizonte 4h 1d
```

**Esperado:** para cada combinação, retorno com custo real e sem custo, mais o
impacto em pontos percentuais. Se uma combinação em 1d superar a mesma
estratégia em 4h, o relatório deve permitir verificar se a diferença persiste
com custo zerado.

**Falha se:** o relatório apresentar apenas o retorno líquido, impossibilitando
a distinção.

---

## Cenário 4 — Marcação de histórico curto (User Story 3, P3)

```bash
python main.py horizonte 1w
```

**Esperado:** AVAX, DOT e SOL marcados como histórico curto (311, 316 e 317
candles contra mediana de 414). BTC e ETH, que definem o teto do horizonte, não
marcados.

**Falha se:** os 12 pares aparecerem marcados — indica comparação contra o valor
solicitado em vez da mediana do horizonte, e o alerta perde função.

---

## Cenário 5 — Janela vazia reportada como vazia (FR-006)

Inspecionar o walk-forward de qualquer combinação de baixa frequência de sinal.

**Esperado:** fold sem operação marcado como vazio, excluído da contagem de
janelas positivas e da média de ganho de timing.

**Falha se:** um fold vazio contar como janela neutra — dilui tanto resultado
bom quanto ruim e distorce a média.

---

## Cenário 6 — O horizonte de produção não muda (FR-012, SC-006)

```bash
grep '^TIMEFRAME=' .env          # antes
python main.py horizonte
grep '^TIMEFRAME=' .env          # depois
```

**Esperado:** valor idêntico. O comando lê `TIMEFRAME` apenas para exibir a
linha de base.

**Falha se:** houver qualquer diferença. Mudar o horizonte operacional por
resultado de backtest é precisamente o que a metodologia existe para impedir.

---

## Cenário 7 — Falha isolada não derruba a varredura

Incluir um símbolo inexistente no universo e executar.

**Esperado:** entrada de erro para o símbolo inválido; todos os demais avaliados
normalmente.

**Falha se:** a varredura abortar. Uma varredura de 144 combinações que morre na
terceira é inútil.

---

## Suíte automatizada

```bash
pytest tests/test_horizonte.py -q     # cobertura da feature
pytest -q                             # suíte completa, sem regressão
```

**Esperado:** todos passam, e a contagem total da suíte não diminui em relação
ao commit anterior.

---

## Critério de conclusão

A feature está pronta quando os sete cenários passam **e** o veredito de H11
consta de `docs/research/registro-de-hipoteses.md` com evidência e procedência —
favorável ou não. O registro do resultado negativo é parte da entrega, não
consequência dela.
