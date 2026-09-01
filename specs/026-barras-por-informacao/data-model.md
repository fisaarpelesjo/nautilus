# Fase 1 — Modelo de dados: H13

## `TipoBarra`

Variante de construção. Duas, decididas em D3.

| Valor | Fecha a barra quando |
|---|---|
| `dollar` | O valor negociado acumulado (Σ close × volume) cruza o limiar |
| `cusum` | O desvio acumulado de retornos, positivo ou negativo, cruza o limiar |

Volume bars foram descartadas em D3: quase colineares com `dollar` em cripto, e
uma terceira variante adicionaria combinações à varredura — mais combinações
significam mais aprovações por acaso — sem responder nada novo.

---

## `ParametrosBarra`

Governa uma construção. **Limiar declarado, nunca varrido** (FR-014).

| Campo | Tipo | Padrão | Descrição |
|---|---|---|---|
| `tipo` | `TipoBarra` | `dollar` | Variante de construção |
| `limiar` | `float` | — | Valor de corte; calibrado por D2, nunca escolhido por desempenho |
| `barras_alvo` | `int` | `2000` | Contagem-alvo, igual à contagem de barras de tempo |
| `tolerancia` | `float` | `0.05` | Erro relativo aceito na calibração |
| `max_iteracoes` | `int` | `6` | Teto do Newton; medido convergindo em 2–3 |

**Invariante:** `limiar > 0`. Limiar não positivo produziria uma barra por
candle (reamostragem inerte) ou divisão degenerada.

---

## `SerieReamostrada`

Resultado da construção. É um DataFrame com **o mesmo contrato de colunas** de
uma série de candles — `open`, `high`, `low`, `close`, `volume`, índice temporal
— para que indicadores, motor, walk-forward e validação funcionem sem saber que
a amostragem mudou (D5).

Colunas adicionais, usadas só no relatório:

| Coluna | Descrição |
|---|---|
| `candles_origem` | Quantos candles de base compõem a barra |
| `duracao_horas` | Extensão em horas de calendário da barra |

**Regras de agregação** — cada barra é a união de candles inteiros:

| Campo | Valor |
|---|---|
| `open` | `open` do primeiro candle do grupo |
| `high` | máximo dos `high` do grupo |
| `low` | mínimo dos `low` do grupo |
| `close` | `close` do último candle do grupo |
| `volume` | soma dos `volume` do grupo |
| índice | instante do **último** candle do grupo |

**O índice é o instante de fechamento, não o de abertura.** É o instante em que
a barra passa a existir e em que uma decisão poderia ser tomada sobre ela.
Indexar pela abertura dataria a barra num momento em que seu conteúdo ainda era
desconhecido — vazamento de futuro por convenção de índice (FR-003).

**A última barra é descartada** quando não cruzou o limiar (FR-004). Uma barra
incompleta tem `close` arbitrário — o preço do momento em que os dados
acabaram — e avaliá-la como fechada é tratar um instante arbitrário como
decisão.

---

## `ComparacaoBarras`

Uma estratégia sobre um par, nas duas versões de amostragem. Espelha
`ComparacaoPareada` da spec 025, com o que muda aqui.

| Campo | Tipo | Descrição |
|---|---|---|
| `estrategia` | `str` | Nome da estratégia |
| `par` | `str` | Símbolo |
| `tipo` | `TipoBarra` | Variante avaliada |
| `tempo` | `BacktestResult?` | Versão amostrada por tempo |
| `barras` | `BacktestResult?` | Versão amostrada por informação |
| `n_tempo` | `int` | Observações da versão de tempo |
| `n_barras` | `int` | Observações da versão de barras |
| `inicio` / `fim` | datetime | Intervalo de calendário **comum** |
| `aquecimento_dias_tempo` | `float` | Dias consumidos pelo aquecimento |
| `aquecimento_dias_barras` | `float` | idem, na versão de barras |
| `limiar_calibrado` | `float` | Limiar após D2 |
| `pct_barras_1_candle` | `float` | Fração de barras de um candle só |
| `validacao_tempo` / `validacao_barras` | `BacktestResult?` | Fatia fora da amostra |
| `retorno_sem_custo_tempo` / `_barras` | `float?` | Reexecução com custo zerado |
| `status` | `str` | Veredito |
| `motivo` | `str` | Justificativa legível |

### Grandezas derivadas

| Propriedade | Definição |
|---|---|
| `delta_retorno` | `barras − tempo`, em pontos percentuais |
| `delta_drawdown` | `barras − tempo`; negativo é melhor |
| `delta_exposicao` | Exposição de **tempo** (D4), `barras − tempo` |
| `delta_operacoes` | `barras − tempo` |
| `delta_timing` | `ganho_de_timing(barras) − ganho_de_timing(tempo)`, descontada a exposição de tempo |
| `delta_timing_validacao` | O mesmo, na fatia fora da amostra |
| `delta_custo` | Parcela da diferença atribuível a taxa e slippage |
| `razao_observacoes` | `n_barras / n_tempo` |
| `buy_hold_divergente` | Verdadeiro se os buy-and-hold diferirem além da tolerância |

**`delta_timing` usa exposição de TEMPO aqui, não de capital.** É a diferença
para a spec 025 e está justificada em D4: mudar a amostragem muda *quando* as
decisões acontecem, então a exposição de tempo responde. Em H12 ela era
invariante por construção e por isso M10 exigiu a medida de capital.

---

## Estados de `ComparacaoBarras`

**A ordem das checagens é a regra**, como em 024 e 025.

| # | Estado | Condição |
|---|---|---|
| 1 | `erro` | Uma das versões não produziu resultado, ou a série não pôde ser construída |
| 2 | `erro` | `buy_hold_divergente` — comparação desancorada (FR-007) |
| 3 | `inerte` | `razao_observacoes` ≈ 1 e a reamostragem não agrupou nada |
| 4 | `inconclusivo` | Aquecimento não cabe no histórico, em dias (FR-010) |
| 5 | `inconclusivo` | Operações abaixo do mínimo em **qualquer** versão (FR-011) |
| 6 | `piora` | `delta_drawdown > 0` |
| 7 | `sem_vantagem` | `delta_drawdown == 0` |
| 8 | `sem_vantagem` | `delta_timing <= 0` |
| 9 | `confundido` | Retorno da versão de tempo ≤ 0 (guarda M11) |
| 10 | `inconclusivo` | Sem janela de validação válida |
| 11 | `so_na_busca` | `delta_timing_validacao <= 0` |
| 12 | `melhora` | Todas as anteriores superadas |

Justificativas herdadas do registro:

- **`inerte` precede tudo** (H12): se as duas versões são a mesma série, não há
  comparação a julgar — nem por amostra, nem por métrica.
- **`inconclusivo` precede métrica** (H10, H11, M9): comparar 30 operações
  contra 4 mede diferença de amostra.
- **`confundido`** (M11): sobre base perdedora, operar menos aproxima de zero e a
  métrica registra ganho; o limite da lógica é não operar.
- **`so_na_busca`** (H10): sem confirmação, `melhora` significa apenas "melhorou
  onde foi medido".

---

## `RelatorioBarras`

Agregado da varredura.

| Campo | Descrição |
|---|---|
| `comparacoes` | Lista de `ComparacaoBarras` |
| `parametros` | Tipo, alvo de barras, tolerância, base e quantidade de candles |
| `contagem_por_estado` | Quantas em cada estado |
| `executavel_em_producao` | Declaração de D6, com a ressalva de recalibração |

A contagem aparece **antes** da tabela na exibição: quem lê 96 linhas forma a
impressão pelas primeiras que vê, e o agregado é o resultado.
