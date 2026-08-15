# CLI Contract: Comportamento Afetado

Fase 1 do `/speckit-plan`. Dois comandos novos (`painel`, `debug`); demais mudanças são extensões
de comandos já existentes.

## `python main.py status` (existente, comportamento estendido)

- **Efeito**: além do já exibido hoje, mostra caixa livre, valor em posições, patrimônio total, PnL
  realizado, PnL não realizado e PnL total como valores distintos.
- **Retrocompatibilidade**: nenhum campo removido, só adicionados.

## `python main.py edge` (existente, comportamento estendido)

- **Efeito**: antes do relatório já existente, exibe modo ("backtest simulado"), par, timeframe,
  período testado e capital inicial, com aviso de que não reflete `data/state.json`.

## `python main.py painel` (novo)

- **Input**: sem argumentos.
- **Efeito**: imprime patrimônio (via `status`), posições abertas, últimas operações
  (`data/trades.csv`), últimos sinais (`data/signals.csv`) e bloqueios recentes
  (`data/decisions.csv`), cada seção com estado vazio explícito se não houver dado.

## `python main.py debug <PAR>` (novo)

- **Input**: símbolo do par (ex: `BTC/USDT`).
- **Efeito**: busca candles reais, calcula indicadores, avalia MTF, e imprime cada condição de
  entrada (EMA, RSI, volume, MTF, Bollinger, regime, volatilidade, cooldown) com seu valor e se
  passou ou não.

## `python main.py chart` (existente, comportamento estendido)

- **Efeito**: além dos marcadores teóricos de sinal já existentes (onde a estratégia sinalizaria
  hoje), uma segunda camada de marcadores mostra trades REALMENTE executados (de
  `data/trades.csv`), visualmente distintos dos teóricos.

## `python main.py performance` (novo, alias `desempenho`)

- **Input**: sem argumentos.
- **Efeito**: lê `data/trades.csv` (leitor tolerante de US3), gera 3 gráficos Plotly (curva de
  capital, drawdown ao longo do tempo, PnL por par) num único HTML combinado, salvo localmente e
  aberto no navegador (mesmo padrão de abertura de `utils/chart.py`, sem precisar rodar um segundo
  servidor Dash). Estado vazio explícito (mensagem, não erro/gráfico em branco) se
  `data/trades.csv` não existir ou estiver vazio.
