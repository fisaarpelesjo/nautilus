# Data Model: Itens Remanescentes do ROADMAP

Fase 1 do `/speckit-plan`. Uma persistência nova (`reports/`), sem mudança de schema em CSVs
já existentes (US4 só adiciona leitura de colunas já gravadas).

## Arquivo de relatório (`reports/`, novo)

| Campo | Tipo | Regras |
|---|---|---|
| `name` | string | Nome do comando/execução (ex: `backtest`, `scan`). |
| `timestamp` | string | Usado no nome do arquivo, evita sobrescrita entre execuções. |
| `params` | dict | Parâmetros usados (par, timeframe, custos, slippage). |
| `result` | dict | `dataclasses.asdict()` do resultado (`BacktestResult`/`MultiResult`/`ScanResult`). |
| `ranking` | Optional[list] | Presente só em comandos multi-par (`scan`/`multibacktest`/`optimize`). |

## Diagnóstico de perfil (extensão de `backtesting/approval.py`)

Sem entidade nova — `diagnose_profile()` continua retornando `Optional[str]`, só com um segundo
padrão de texto possível ("perfil agressivo: ...").

## Relatório de edge com validação (extensão de `backtesting/validation.py`)

Reusa `Tuple[BacktestResult, Optional[BacktestResult], ValidationVerdict]`, já o tipo de retorno de
`run_backtest_with_validation()` — `run_edge_report(..., validate=True)` passa a retornar o mesmo
formato em vez de `Tuple[BacktestResult, ApprovalVerdict]`.

## Indicadores médios por decisão (extensão de `data/decisions_analysis.py`)

| Campo novo | Tipo | Regras |
|---|---|---|
| `DecisionRecord.rsi` | Optional[float] | `None` quando ausente/vazio na linha do CSV. |
| `DecisionsAnalysisResult.avg_indicators_by_signal` | Dict[str, Dict[str, float]] | Chave externa = sinal (`HOLD`/`BUY`/`SELL`), interna = nome do indicador (`rsi`). |
