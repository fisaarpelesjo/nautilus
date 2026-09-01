# Fase 1 — Modelo de dados: H11

Três entidades. Nenhuma persiste em banco: a saída é relatório em `reports/` e
uma entrada em `docs/research/registro-de-hipoteses.md`.

---

## `DisponibilidadeHistorico`

Registro do que a fonte de dados efetivamente entregou, por combinação de par e
horizonte. Existe para satisfazer FR-009, FR-010 e FR-011 — a limitação de dado
precisa ser um dado, não uma nota de rodapé.

| Campo | Tipo | Significado |
|---|---|---|
| `par` | str | Símbolo avaliado |
| `horizonte` | str | Escala temporal |
| `solicitado` | int | Candles pedidos |
| `obtido` | int | Candles recebidos |
| `aquecimento` | int | Candles consumidos antes do primeiro sinal possível |
| `utilizaveis` | int | `obtido − aquecimento`, nunca negativo |
| `dias_cobertos` | float | Extensão temporal real do histórico |
| `historico_curto` | bool | Marca relativa à mediana do horizonte (ver research D3) |
| `erro` | str \| None | Falha na busca; a combinação não é avaliada |

**Regras de validação**

- `utilizaveis = max(0, obtido − aquecimento)`.
- `historico_curto` é verdadeiro quando `obtido` fica materialmente abaixo da
  mediana **do próprio horizonte** — não abaixo de `solicitado`. Comparar com o
  solicitado marcaria 12 de 12 pares em escala semanal e o alerta perderia
  função.
- `erro` preenchido implica combinação não avaliada, e **não** avaliada com
  resultado zero.

---

## `CombinacaoAvaliada`

Unidade de análise: uma estratégia, em um horizonte, sobre um par. Carrega o
resultado de cada etapa da bateria e o veredito consolidado.

| Campo | Tipo | Significado |
|---|---|---|
| `estrategia` | str | Nome da estratégia |
| `horizonte` | str | Escala temporal |
| `par` | str | Símbolo |
| `disponibilidade` | `DisponibilidadeHistorico` | Contexto de dado |
| `resultado_janela_unica` | `BacktestResult` \| None | E2 |
| `veredito_janela_unica` | `ApprovalVerdict` \| None | E2 |
| `resultado_busca` | `BacktestResult` \| None | E3, fatia de descoberta |
| `resultado_confirmacao` | `BacktestResult` \| None | E3, fatia reservada |
| `folds` | `list[WalkForwardFold]` | E4 e E5 |
| `retorno_sem_custo_pct` | float \| None | E6 |
| `status` | str | Veredito consolidado |
| `motivo` | str | Por que este status |

**Estados de `status`**

| Estado | Condição |
|---|---|
| `confirmado` | Aprovado em E2 **e** na fatia de confirmação de E3 |
| `so_na_busca` | Aprovado na descoberta, não sustentado na confirmação. **Não é aprovação** |
| `reprovado` | Falha em critério da bateria com amostra suficiente |
| `inconclusivo` | Amostra insuficiente para julgar |
| `erro` | Falha ao obter dados |

**Regra central (FR-003)**

`inconclusivo` tem precedência sobre `reprovado`. Uma combinação com menos
operações que o mínimo exigido, ou sem janela de confirmação válida, ou com
menos janelas de walk-forward que o mínimo, é **inconclusiva** — mesmo que suas
métricas pareçam ruins. Ausência de amostra não é evidência de ausência de
vantagem.

**Regra de janela vazia (FR-006)**

Fold sem operação alguma é marcado vazio e **excluído** da contagem de janelas
positivas e da média de ganho de timing. Contá-lo como neutro diluiria tanto o
resultado bom quanto o ruim.

---

## `RelatorioHorizonte`

Agregação das combinações de um mesmo horizonte, permitindo compará-los.

| Campo | Tipo | Significado |
|---|---|---|
| `horizonte` | str | Escala |
| `combinacoes` | `list[CombinacaoAvaliada]` | Todas as avaliadas |
| `n_confirmadas` | int | Quantas passaram fora da amostra |
| `n_inconclusivas` | int | Quantas ficaram sem amostra |
| `candles_medianos` | int | Mediana de candles obtidos |
| `aquecimento_dias` | float | Custo do aquecimento em dias |

**Invariante de leitura**

`n_confirmadas` só é interpretável ao lado do total avaliado. Uma confirmação
entre 144 tentativas tem peso estatístico distinto de uma entre 3 — a exibição
deve apresentar os dois números juntos, como já faz `multimarket`.

---

## Relações

```
RelatorioHorizonte 1 ── N CombinacaoAvaliada 1 ── 1 DisponibilidadeHistorico
                                            1 ── N WalkForwardFold  (reusado)
                                            1 ── 1 BacktestResult   (reusado)
                                            1 ── 1 ApprovalVerdict  (reusado)
```

`BacktestResult`, `ApprovalVerdict` e `WalkForwardFold` são reusados sem
alteração de `backtesting/engine.py`, `approval.py` e `cross_sectional.py`.
Estender qualquer um deles para acomodar H11 acoplaria a hipótese ao motor.
