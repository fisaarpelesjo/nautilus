# CLI Contract: Comportamento Afetado

Fase 1 do `/speckit-plan`. Nenhum comando novo — extensões de comandos já existentes.

## `python main.py backtest` / `scan` / `multibacktest` / `optimize` (existentes, estendidos)

- **Efeito novo**: além do já exibido, salva o resultado em `reports/{comando}_{timestamp}.json`,
  `.csv` e `.md`, criando `reports/` se ainda não existir.
- **Retrocompatibilidade**: nenhuma saída de terminal existente é removida.

## `python main.py edge --validate` (flag nova em comando existente)

- **Input**: flag opcional `--validate`.
- **Efeito**: em vez do backtest de janela única atual, roda `split_train_validation` +
  `simulate_backtest` (mesmo caminho de `backtest --validate`), calcula o veredito de aprovação
  sobre a fatia de validação (out-of-sample), mostra treino e validação lado a lado.
- **Sem a flag**: comportamento idêntico ao já existente hoje.

## `python main.py decisions` (existente, estendido)

- **Efeito novo**: além do já exibido (contagem de sinais, bloqueios mais frequentes), mostra RSI
  médio (e demais indicadores já registrados) agrupado por sinal.
