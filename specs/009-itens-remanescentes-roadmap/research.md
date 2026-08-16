# Research: Itens Remanescentes do ROADMAP

Fase 0 do `/speckit-plan`. Nenhum item do Technical Context ficou como `NEEDS CLARIFICATION`.

## Exportação de relatórios (US1)

- **Decision**: novo `utils/report_export.py`, `export_report(name: str, params: dict, result,
  ranking: Optional[list] = None) -> None` — serializa `dataclasses.asdict(result)` (funciona
  direto para `BacktestResult`/`MultiResult`/`ScanResult`, já dataclasses) em JSON
  (`json.dump`), CSV (uma linha, `csv.DictWriter`) e Markdown (tabela simples), salvos em
  `reports/{name}_{timestamp}.{ext}`. Chamado a partir de `cmd_backtest`/`cmd_scan`/
  `cmd_multibacktest`/`cmd_otimizar` em `main.py`.
- **Rationale**: reusa as dataclasses de resultado já existentes via `dataclasses.asdict()` — não
  inventa um schema de relatório paralelo que precisaria ser mantido sincronizado manualmente toda
  vez que um campo novo for adicionado a `BacktestResult` (como aconteceu repetidas vezes nas specs
  002-004).
- **Alternatives considered**: um formato de relatório customizado (schema próprio, não espelhando
  as dataclasses) — rejeitado, cria uma segunda fonte de verdade sobre "quais campos o resultado
  tem" que diverge silenciosamente cada vez que uma spec futura adicionar uma métrica nova.

## Diagnóstico agressivo (US2)

- **Decision**: `diagnose_profile()` (`backtesting/approval.py`) ganha uma segunda checagem:
  `is_aggressive = result.max_drawdown_pct > MAX_ACCEPTABLE_DRAWDOWN_PCT and result.total_return_pct
  > result.buy_hold_return_pct * 1.5` (retorno significativamente acima, não só "um pouco acima" --
  evita marcar como "agressivo" um caso que já seria aprovado normalmente). Reusa
  `MAX_ACCEPTABLE_DRAWDOWN_PCT` já definido, mesmo princípio do perfil defensivo.
- **Rationale**: mesmo padrão já estabelecido pelo perfil defensivo — reusar o limiar existente em
  vez de um número novo evita dois "o que é drawdown alto" divergentes no mesmo módulo.
- **Alternatives considered**: limiar de "retorno bem acima" fixo em vez de multiplicador do
  buy-hold — rejeitado, um multiplicador escala melhor entre pares/períodos diferentes que um
  número absoluto fixo (ex: "+50 pontos percentuais" não faz sentido igual para um período de 1 mês
  vs 1 ano).

## Out-of-sample no relatório de edge (US3)

- **Decision**: `run_edge_report(symbol, timeframe, initial_capital, candle_limit, validate:
  bool = False)` -- quando `validate=True`, reusa `split_train_validation`/`simulate_backtest` (o
  mesmo caminho já usado por `run_backtest_with_validation`) e calcula `evaluate_approval` sobre o
  resultado de validação, não o resultado de janela única. Exibe treino e validação lado a lado
  (mesmo formato visual de `_print_validation_report`, já existente).
- **Rationale**: `backtesting/validation.py` já tem toda a lógica necessária
  (`split_train_validation`, `simulate_backtest` com `precomputed_signals` fatiado corretamente na
  fronteira) — US3 é literalmente reusar essas peças já validadas com uma saída de
  `evaluate_approval` diferente (sobre validação, não sobre o resultado inteiro).
- **Alternatives considered**: duplicar a lógica de split dentro de `run_edge_report` -- rejeitado,
  `run_backtest_with_validation` já existe exatamente para isso.

## Indicadores médios por decisão (US4)

- **Decision**: `DecisionRecord` (`data/decisions_analysis.py`) ganha campo `rsi: Optional[float]`
  (e opcionalmente `volume_ratio`/`atr_pct`/`trend_gap_pct`, mesma extensão). `analyze_decisions()`
  agrupa por `signal` e calcula média de cada indicador presente (ignora linhas onde o indicador
  está ausente/vazio, não quebra o cálculo). Novo campo `DecisionsAnalysisResult.avg_indicators_by_signal:
  Dict[str, Dict[str, float]]`.
- **Rationale**: `data/decision_store.py` `DECISION_HEADERS` já inclui essas colunas (gravadas desde
  a spec 001) — a informação já existe no CSV, só falta agregá-la. Não exige mudança em
  `trading/decision_logger.py`.
- **Alternatives considered**: calcular médias de todos os indicadores numéricos genericamente (sem
  listar campos específicos) — considerado, mas começar por RSI (exemplo explícito do `spec.md`)
  mantém a mudança pequena e testável; extensão para os demais indicadores fica trivial (mesmo
  padrão) se o valor for confirmado em uso.

## Superfície de configuração nova

Nenhuma — todas as capacidades são extensões de comandos/funções já existentes.
