# Fase 1 — Modelo de dados: H12

Duas entidades. Nenhuma persiste em banco: a saída é relatório em `reports/` e
uma entrada em `docs/research/registro-de-hipoteses.md`.

---

## `ParametrosVolatilidade`

Configuração do dimensionamento. Fixa para toda a avaliação (ver research D3).

| Campo | Tipo | Significado |
|---|---|---|
| `alvo` | float | Volatilidade-alvo. `0,02`, próximo à mediana observada |
| `fator_minimo` | float | Piso do fator, evita posição irrelevante |

**Invariantes**

- O fator resultante nunca excede `1,0`. Não é validação, é a fórmula: o `min`
  está no código. FR-003 e a proibição de alavancagem da constituição dependem
  disso, e nenhum valor de `alvo` pode violá-lo.
- `alvo` e `fator_minimo` são únicos para toda a execução. Variá-los por par ou
  estratégia reintroduziria testes múltiplos.

---

## `ComparacaoPareada`

Uma estratégia, sobre um par, avaliada nas duas versões. É a unidade de análise:
H12 não pergunta "a versão dimensionada é boa?", pergunta "ela é melhor que a
mesma estratégia sem dimensionamento?".

| Campo | Tipo | Significado |
|---|---|---|
| `estrategia` | str | Nome |
| `par` | str | Símbolo |
| `sem_dimensionamento` | `BacktestResult` | Linha de base |
| `com_dimensionamento` | `BacktestResult` | Versão avaliada |
| `folds_base` | `list[WalkForwardFold]` | Walk-forward da linha de base |
| `folds_dim` | `list[WalkForwardFold]` | Walk-forward da versão dimensionada |
| `retorno_sem_custo_base` | float \| None | E6, linha de base |
| `retorno_sem_custo_dim` | float \| None | E6, dimensionada |
| `fator_medio` | float | Fator médio aplicado, para auditoria |
| `status` | str | Veredito da comparação |
| `motivo` | str | Justificativa |

### Grandezas derivadas

| Grandeza | Definição | Requisito |
|---|---|---|
| `delta_drawdown` | drawdown dimensionado − base | FR-006 |
| `delta_retorno` | retorno dimensionado − base | FR-006 |
| `delta_exposicao` | exposição dimensionada − base | FR-007 |
| `delta_timing` | ganho de timing dimensionado − base | FR-007, FR-008 |
| `delta_operacoes` | operações dimensionada − base | FR-009 |
| `delta_custo` | custo dimensionado − base | FR-009 |

### Estados de `status`

| Estado | Condição |
|---|---|
| `melhora` | Drawdown cai **e** `delta_timing` > 0 |
| `sem_vantagem` | Drawdown cai mas `delta_timing` ≤ 0 — o ganho era exposição |
| `piora` | Drawdown não cai, ou retorno cai desproporcionalmente |
| `inconclusivo` | Amostra insuficiente em qualquer das versões |
| `erro` | Falha ao obter dados ou simular |

**A regra central (FR-008)**

`sem_vantagem` existe como estado próprio, distinto de `melhora` e de `piora`.
Dimensionar por volatilidade reduz exposição por construção — pela medição de
research D3, cerca de 10% em média. Num mercado em queda, isso sozinho melhora o
retorno relativo ao buy-and-hold sem qualquer capacidade de seleção.

Uma combinação cujo drawdown cai e cujo `delta_timing` é nulo ou negativo **não
melhorou**: ela apenas participou menos. Colapsar esse caso em `melhora` faria
H12 passar trivialmente, e a aprovação não significaria nada.

**Precedência de `inconclusivo` (FR-011)**

Vale a regra já estabelecida em H10 e H11: amostra abaixo do mínimo em qualquer
das duas versões torna a comparação inconclusiva, **antes** de avaliar qualquer
métrica. Comparar uma versão com 30 operações contra outra com 4 não mede
dimensionamento — mede a diferença de amostra.

---

## Relações

```
ParametrosVolatilidade  1 ── N  ComparacaoPareada
                                   ├── 2 × BacktestResult    (reusado)
                                   └── 2 × list[WalkForwardFold] (reusado)
```

`BacktestResult` e `WalkForwardFold` são reusados sem alteração. Estender
qualquer um para acomodar H12 acoplaria a hipótese ao motor — o mesmo raciocínio
aplicado em H11.
