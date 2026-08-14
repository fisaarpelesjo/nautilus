# Research: Otimização Sem Overfitting

Fase 0 do `/speckit-plan`. Nenhum item do Technical Context ficou como `NEEDS CLARIFICATION`. As
decisões abaixo resolvem as três alternativas deixadas em aberto no `Assumptions` do `spec.md`.

## Split treino/validação no grid search (US1)

- **Decision**: para cada símbolo, `split_train_validation()` (spec 001) roda uma vez sobre o df já
  com indicadores calculados, produzindo `train_df`/`validation_df`. O grid search (`_optimize_multi`)
  passa a rodar `simulate_backtest` só sobre `train_df` para pontuar e escolher os `top_n`
  candidatos (mesmo algoritmo/critério de hoje, `_score()`, só que sobre uma fatia menor). Depois de
  escolhidos, cada um dos `top_n` (não só o #1) é reavaliado contra `validation_df` de cada símbolo,
  e o relatório mostra as duas métricas lado a lado por candidato.
- **Rationale**: reavaliar todos os `top_n` (hoje 15) contra a validação, em vez de só o vencedor,
  tem custo desprezível (15 `simulate_backtest` extras por símbolo, contra as centenas já rodadas na
  busca em grade) e entrega mais informação: pode revelar que o #3 do treino generaliza melhor que o
  #1, o que só o vencedor isolado nunca mostraria.
- **Alternatives considered**: rodar walk-forward já dentro do grid search (uma otimização por
  janela) — rejeitado por ser exponencialmente mais caro (K janelas × centenas de combinações × N
  pares) e por ser exatamente o escopo da User Story 2, não da 1; validar só o #1 — rejeitado pelo
  motivo acima (custo desprezível de validar todos os `top_n`).

## Quando a validação não é possível (US1, Edge Case)

- **Decision**: reusa o mecanismo que `split_train_validation()` já tem — quando uma fatia fica menor
  que `MIN_WINDOW_CANDLES` (150, spec 001), a função já retorna `(df, None)`. Um símbolo com
  `validation_df is None` é marcado como "sem validação possível" no relatório e simplesmente não
  contribui pontos para a média de validação entre símbolos (mas continua contribuindo para a média de
  treino, como hoje).
- **Rationale**: reusa uma decisão já tomada e testada na spec 001 em vez de inventar um segundo
  critério de "histórico insuficiente" com número diferente.
- **Alternatives considered**: excluir o símbolo inteiro (também do treino) quando a validação não é
  possível — rejeitado por reduzir sem necessidade a base de dados do treino, que não tem esse
  requisito de tamanho mínimo por si só.

## Walk-forward: janelas fixas sobre o conjunto já vencedor, não uma nova otimização por janela (US2)

- **Decision**: `walk_forward_validate(df, strategy_params, min_windows=3)` em
  `backtesting/robustness.py` divide o df (já com indicadores) em `min_windows` fatias contíguas e
  não sobrepostas (mesmo espírito do split simples da spec 001, generalizado de 2 para N fatias) e
  roda `simulate_backtest` com os `strategy_params` já escolhidos (pelo grid search da US1, ou
  informados diretamente) em cada uma. Não reotimiza parâmetros por janela.
- **Rationale**: a spec pede confirmar que *o conjunto de parâmetros escolhido* se sustenta em
  diferentes regimes de mercado — não pede descobrir um conjunto de parâmetros diferente por regime
  (isso seria uma forma de overfitting por regime, o oposto do objetivo desta spec). Reotimizar por
  janela também multiplicaria o custo computacional por `min_windows`, incompatível com o non-goal de
  manter o motor de busca em grade como está.
- **Alternatives considered**: reotimizar por janela (walk-forward "clássico" da literatura de
  trading quantitativo) — rejeitado pelo motivo acima; janelas com sobreposição (rolling window) —
  rejeitado por complicar a interpretação de "pior janela" (janelas sobrepostas compartilham dados,
  então uma sequência ruim de trades pode aparecer em várias janelas ao mesmo tempo, inflando a
  aparência de fragilidade); mantido como candidato de evolução futura se `min_windows` fixo e
  contíguo se provar insuficiente em uso real.

## Menos de `min_windows` janelas possíveis (US2, Edge Case)

- **Decision**: mesmo padrão de `split_train_validation()` — se o histórico não render pelo menos
  `min_windows` janelas de tamanho mínimo (`MIN_WINDOW_CANDLES=150` reusado, spec 001), a função
  retorna um resultado indicando "dados insuficientes" em vez de rodar com menos janelas.
- **Rationale**: FR-006 exige isso explicitamente — rodar com menos janelas sem avisar esconderia que
  a evidência é mais fraca que o mínimo definido como aceitável.
- **Alternatives considered**: reduzir automaticamente `min_windows` para o que couber — rejeitado
  por definição (o próprio requisito proíbe isso).

## Análise Monte Carlo: bootstrap com reposição sobre a ordem dos trades (US3)

- **Decision**: `monte_carlo_resample(trades: List[Trade], n_simulations=1000, seed=None)` em
  `backtesting/robustness.py`. Cada simulação reamostra a lista de PnLs dos trades **com reposição**
  (bootstrap clássico), reconstrói a curva de equity na ordem reamostrada e calcula o drawdown máximo
  e a maior sequência de perdas dessa simulação. Ao final, agrega percentis (mediana, p95) de
  drawdown máximo entre as `n_simulations` execuções.
- **Rationale**: bootstrap com reposição é o método padrão para estimar a distribuição de uma
  estatística (aqui, drawdown máximo) a partir de uma amostra pequena — sem reposição, com poucos
  trades (< 20, típico deste bot) o número de permutações possíveis é limitado e a distribuição
  resultante seria artificialmente estreita. `n_simulations=1000` é o valor típico da literatura para
  estabilidade dos percentis sem custo perceptível (milissegundos para dezenas de trades).
- **Alternatives considered**: reamostrar sem reposição (permutação pura da ordem observada) —
  rejeitado por sub-representar sequências de perdas piores que a já observada, que é exatamente o
  que a análise existe para estimar; simular trades sintéticos a partir de uma distribuição paramétrica
  ajustada aos PnLs — rejeitado por adicionar uma suposição de distribuição (normal, etc.) que os
  retornos de trading tipicamente não satisfazem; mais complexo sem ganho claro para o escopo desta
  spec.

## Confiança baixa com amostra pequena (US3, Edge Case)

- **Decision**: reusa `EDGE_MIN_TRADES` (`config/settings.py`, spec 002 — default `10`) como limiar:
  menos trades que isso no resultado de entrada faz o relatório marcar a estimativa como "confiança
  baixa", sem deixar de calcular — os números continuam aparecendo, só com o aviso.
- **Rationale**: evita um quarto número "mínimo de trades" divergente no projeto (depois de
  `MAX_CONSECUTIVE_LOSSES`, `EDGE_MIN_TRADES` e `MIN_TRADES_FOR_RANKING`, cada um com uma razão de
  existir documentada) — `EDGE_MIN_TRADES` já é especificamente "abaixo disso a conclusão não é
  confiável", que é exatamente o caso aqui.
- **Alternatives considered**: novo limiar dedicado a Monte Carlo — rejeitado por criar mais uma
  constante para o operador acompanhar sem diferença conceitual clara da já existente.

## Superfície de CLI (US1/US2/US3)

- **Decision**: `python main.py optimize --validate` habilita US1 (split treino/validação);
  `python main.py optimize --walk-forward` habilita US2 (implica `--validate`, já que walk-forward
  precisa de um conjunto de parâmetros vencedor escolhido via treino primeiro); `python main.py
  backtest --montecarlo` habilita US3 sobre o backtest de janela única já existente (reusa a lista de
  `Trade` que `simulate_backtest` já produz, sem rodar nada nova rede).
- **Rationale**: mesmo padrão já estabelecido em `backtest --validate` (spec 001) — flag opcional,
  comportamento default inalterado (FR-009). Colocar Monte Carlo em `backtest` (não em `optimize`) é
  consistente com a Assumption do `spec.md` de que US3 "não depende tecnicamente" das outras duas —
  reusa o comando mais simples que já produz uma lista de trades.
- **Alternatives considered**: subcomando dedicado (`python main.py montecarlo`) — rejeitado por
  introduzir mais um comando de topo quando uma flag já resolve, inconsistente com o padrão
  `backtest --validate` já em uso.
