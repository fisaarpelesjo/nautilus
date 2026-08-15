# Research: Observabilidade Operacional

Fase 0 do `/speckit-plan`. Nenhum item do Technical Context ficou como `NEEDS CLARIFICATION`.

## Patrimônio operacional compartilhado (US1)

- **Decision**: novo `trading/portfolio.py`, função `compute_portfolio_snapshot(manager: OrderManager)
  -> PortfolioSnapshot` — caixa livre (`manager.paper_balance_usdt` em paper, `fetch_balance()` em
  live, mesma bifurcação já usada em `_current_balance`/`_reference_balance`), valor em posições
  (soma de `quantity × preço_atual` via `fetch_ticker`, `None` por posição se o preço não puder ser
  buscado — nunca `0.0` silencioso), patrimônio total (caixa + posições conhecidas), PnL realizado
  (`manager.realized_pnl`, já existente), PnL não realizado (soma de `(preço_atual - entry_price) ×
  quantity` por posição), PnL total (realizado + não realizado conhecido). Reusado por `status` e
  `painel` — cálculo escrito uma vez só.
- **Rationale**: `cmd_status()` hoje mistura `paper_balance_usdt` (caixa livre) com "saldo", e calcula
  PnL como `balance - 1000.0` (hardcoded, mesmo padrão de bug já corrigido em `is_daily_limit_hit()`
  na spec 005 — número fixo em vez do estado real). Centralizar o cálculo evita repetir esse erro em
  `painel`.
- **Alternatives considered**: calcular patrimônio inline em cada comando que precisa dele —
  rejeitado, seria repetir a mesma lógica (e o mesmo risco de bug) em `status` e `painel`.

## Contexto explícito no edge (US2)

- **Decision**: `backtesting/validation.py` `run_edge_report()` ganha uma chamada a uma nova
  `_print_simulation_context(symbol, timeframe, df, initial_capital)` (em `utils/display.py`, mesmo
  padrão de outras funções de exibição já existentes) antes de `print_report()` — mostra modo
  ("backtest simulado"), par, timeframe, período testado (primeiro/último timestamp do `df`) e
  capital inicial, com aviso de que não reflete `data/state.json`.
- **Rationale**: mudança isolada a `run_edge_report()` (não a `print_report()` compartilhado com
  `backtest`/`scan`/`multibacktest`/`compare`) — evita alterar a saída desses outros comandos, que
  já têm contexto suficiente pelo próprio nome do comando rodado.

## Painel local (US3)

- **Decision**: novo `main.py` `cmd_painel()` → novo `trading/panel.py` `print_panel()` — agrega
  `compute_portfolio_snapshot()` (US1), leitura tolerante de `data/trades.csv` (últimas N via novo
  leitor em `data/trade_store.py`, mesmo padrão de `_load_decisions()` em
  `data/decisions_analysis.py`: `Path.exists()` → lista vazia, não erro), leitura tolerante
  equivalente de `data/signals.csv` (últimos sinais), e `analyze_decisions()` já existente (spec 004,
  bloqueios mais frequentes). Comando novo `python main.py painel`.
- **Rationale**: nenhuma informação nova — só agregação do que já existe em CSVs e no `state.json`,
  reusando leitores/analisadores já validados em vez de duplicar parsing de CSV pela terceira vez.
- **Alternatives considered**: painel web (Dash), já usado para o gráfico de candles — rejeitado
  para esta primeira versão; painel de terminal (mesmo padrão Rich já usado em `status`) é suficiente
  e não introduz um segundo servidor local rodando.

## Modo debug da estratégia (US4)

- **Decision**: `strategy/diagnostics.py` ganha `full_diagnosis(symbol, indicators, previous,
  current_price, strategy, mtf_ok, regime, cooldown_active) -> dict` — reusa `signal_checks()` já
  existente e adiciona os checks que faltam nele (MTF, regime, volatilidade, cooldown), retornando
  TODOS os valores (não só os 3 primeiros bloqueios, como `hold_diagnosis()` trunca hoje). Novo
  `main.py cmd_debug()` (`python main.py debug <PAR>`) busca candles reais, calcula indicadores,
  chama `mtf_confirmed()` (já existente em `trading/position_lifecycle.py`) e `full_diagnosis()`, e
  imprime cada condição com seu valor e se passou ou não.
- **Rationale**: reusa `signal_checks()` em vez de duplicar a lógica de condições — extensão, não
  substituição. `hold_diagnosis()` (usado no terminal do bot rodando) continua truncado a 3 motivos
  de proposito (espaço limitado na tabela ao vivo); o modo debug é uma visualização completa
  separada, sob demanda.
- **Cooldown**: `full_diagnosis` recebe `cooldown_active: bool` já calculado pelo chamador
  (`manager.is_in_cooldown(symbol)`, método já existente em `OrderManager`) — não duplica essa
  lógica.

## Gráficos de performance (US5)

- **Decision**: `utils/chart.py` ganha uma segunda camada de marcadores lidos de `data/trades.csv`
  (entrada/saída REAIS, distintos visualmente dos marcadores teóricos de sinal já existentes,
  calculados por `precompute_signals`). Novo `backtesting/performance_charts.py` (curva de capital,
  drawdown, PnL por par), reusando `plotly` (mesma lib já em uso, sem dependência nova) a partir de
  uma lista de `Trade` (já existente em `backtesting/engine.py`) ou de `data/trades.csv` lido via o
  mesmo leitor tolerante de US3.
- **Rationale**: reusa a mesma stack de visualização já validada (`plotly`/`dash`) em vez de
  introduzir uma biblioteca nova; distinguir marcador real vs teórico no chart existente evita
  confundir "o que a estratégia sinalizaria hoje" com "o que o bot realmente fez".
- **Alternatives considered**: unificar os dois tipos de marcador (teórico e real) num só —
  rejeitado, são informações diferentes (uma é o sinal recalculado com os parâmetros atuais, a outra
  é o que de fato foi executado, possivelmente com parâmetros antigos ou bloqueios que não existem
  mais nos dados históricos).

## Superfície de configuração nova

Nenhuma — todas as capacidades desta spec são comandos/funções novas ou extensões de comandos já
existentes, sem novo comportamento configurável via `.env`.
