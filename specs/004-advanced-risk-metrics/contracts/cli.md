# CLI Contract: Comandos Afetados

Fase 1 do `/speckit-plan`.

## `python main.py backtest`, `backtest --validate`, `backtest --montecarlo`, `multibacktest`, `scan`, `edge`, `optimize [--validate|--walk-forward]`

- **Input**: sem mudança — nenhuma flag nova para US1/US2.
- **Efeito**: todo relatório que já mostra o Sharpe simplificado passa a mostrar também Sortino,
  Calmar, retorno anualizado e retorno por tempo exposto — são campos do `BacktestResult` já
  compartilhado por todos esses comandos (`print_report()`, `backtesting/engine.py`).
- **Output (stdout)**: quatro linhas novas no bloco de métricas já existente (mesmo formato das já
  presentes, ex: "Sharpe simplif."). `return_per_exposure_pct == None` exibido como "n/a" em vez de um
  número.
- **Efeito colateral observável**: nenhum — comandos de leitura, não persistem nem alteram
  comportamento de decisão (FR-010).

## `python main.py decisions` (novo comando; alias `decisoes`)

- **Input**: nenhum argumento obrigatório.
- **Efeito**: lê `data/decisions.csv` (se existir) e resume: total de ciclos, contagem de sinais por
  tipo, entradas bloqueadas, bloqueios mais frequentes ranqueados.
- **Output (stdout)**: tabela/resumo com as contagens acima. Quando `data/decisions.csv` não existe ou
  está vazio, imprime uma mensagem clara ("nenhum dado para analisar ainda — rode o bot para gerar
  `data/decisions.csv`") em vez de erro.
- **Efeito colateral observável**: nenhum — comando de leitura, não persiste nem envia alerta.
