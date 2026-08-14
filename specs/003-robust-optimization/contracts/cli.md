# CLI Contract: Comandos Afetados

Fase 1 do `/speckit-plan`. Todas as flags são opcionais e aditivas — `python main.py optimize` e
`python main.py backtest` sem flag continuam com o comportamento de hoje (FR-009).

## `python main.py optimize --validate`

- **Input**: flag opcional `--validate` no comando `optimize` já existente.
- **Efeito**: para cada símbolo, divide o histórico em treino/validação (`split_train_validation()`,
  spec 001) antes do grid search; a busca em grade escolhe os `top_n` candidatos usando só a fatia de
  treino; cada candidato é reavaliado contra a fatia de validação.
- **Output (stdout)**: a tabela de resultados já existente ganha colunas de validação
  (`retorno validação`, `drawdown validação`) ao lado das colunas de treino já existentes; símbolos
  sem validação possível para um candidato aparecem listados separadamente (não silenciosamente
  ausentes da média).
- **Efeito colateral observável**: nenhum — comando de leitura.

## `python main.py optimize --walk-forward`

- **Input**: flag opcional `--walk-forward` (implica `--validate`, já que precisa de um conjunto de
  parâmetros vencedor escolhido via treino antes de testá-lo nas janelas).
- **Efeito**: o conjunto de parâmetros vencedor (após `--validate`) é avaliado em ≥3 janelas
  deslizantes não sobrepostas por símbolo (`min_windows=3` default).
- **Output (stdout)**: nova seção "VALIDAÇÃO WALK-FORWARD" após a tabela principal — uma linha por
  janela (período, retorno, drawdown) mais um resumo (retorno médio, pior janela). Quando o histórico
  não cobre `min_windows` janelas, a seção mostra "dados insuficientes para walk-forward" em vez de
  rodar com menos janelas.
- **Efeito colateral observável**: nenhum.

## `python main.py backtest --montecarlo`

- **Input**: flag opcional `--montecarlo` no comando `backtest` já existente (par único,
  `PAIRS[0]`/`TIMEFRAME`, mesma janela do `backtest` sem flag — não interage com `--validate`, que já
  é outro fluxo).
- **Efeito**: reamostra (bootstrap com reposição, 1000 simulações) a ordem da lista de trades
  produzida pelo backtest, estimando a distribuição de drawdown máximo e maior sequência de perdas.
- **Output (stdout)**: relatório de backtest já existente (inalterado), seguido de uma seção nova
  "ANÁLISE MONTE CARLO": drawdown máximo (mediana e p95 entre as simulações), maior sequência de
  perdas esperada (mediana), e aviso de confiança baixa quando o número de trades de entrada for
  menor que `EDGE_MIN_TRADES`.
- **Efeito colateral observável**: nenhum.
