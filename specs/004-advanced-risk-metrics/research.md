# Research: Métricas de Risco Avançadas

Fase 0 do `/speckit-plan`. Nenhum item do Technical Context ficou como `NEEDS CLARIFICATION`. As
decisões abaixo resolvem as alternativas deixadas em aberto no `Assumptions` do `spec.md`.

## Sortino Ratio (US1)

- **Decision**: mesma fórmula/padrão já usado por `_simplified_sharpe()` (`backtesting/engine.py`),
  trocando o desvio padrão geral pelo desvio padrão só dos retornos negativos (`trade_returns`
  filtrados por `< 0`), com `ddof=1` (mesma convenção do Sharpe existente). Requer ≥2 trades com
  prejuízo para o desvio ser calculável; menos que isso (ou nenhum trade com prejuízo) retorna
  `float("inf")` se a média de retornos for positiva, `0.0` caso contrário — mesma convenção já usada
  por `profit_factor`/`payoff_ratio` quando o denominador é zero.
- **Rationale**: reusa a mesma base estatística (`pd.Series.std`) e a mesma convenção de "sem dado no
  denominador" já estabelecida no código, em vez de introduzir uma segunda convenção divergente.
- **Alternatives considered**: usar retornos abaixo de uma MAR (minimum acceptable return, ex: 0%) em
  vez de simplesmente negativos — rejeitado por adicionar um parâmetro configurável sem pedido
  explícito na spec; `trade_returns < 0` já é a definição padrão de "downside" para uma estratégia que
  não tem retorno-alvo declarado.

## Calmar Ratio (US1)

- **Decision**: `annualized_return_pct / max_drawdown_pct` quando `max_drawdown_pct > 0`; `inf` se
  `annualized_return_pct > 0` e drawdown zero, `0.0` caso contrário. Depende do retorno anualizado
  (User Story 2) já estar calculado — implementado na mesma função (`_calculate_advanced_metrics`),
  não numa segunda passada.
- **Rationale**: Calmar é definido pela literatura como retorno anualizado sobre drawdown máximo — usar
  o `max_drawdown_pct` já calculado por `simulate_backtest` (não um novo cálculo de drawdown) evita
  duas fontes de verdade para a mesma métrica.
- **Alternatives considered**: Calmar sobre retorno total (não anualizado) — rejeitado por não ser a
  definição padrão da métrica e por tornar a comparação entre backtests de durações diferentes
  enganosa.

## Base de anualização: 365 dias (US2)

- **Decision**: `annualized_return_pct = ((1 + total_return_pct/100) ** (365 / period_days) - 1) * 100`
  (juros compostos, não escala linear), usando `period_days` derivado de `period_start`/`period_end`
  já calculados para `_exposure_pct`. `period_days <= 0` (menos de 1 dia de histórico) retorna `0.0`
  em vez de uma potência com expoente extremo.
- **Rationale**: cripto opera 24/7 (sem fins de semana/feriados como mercados tradicionais), então
  365 dias é a base de anualização padrão do setor — diferente de ações (geralmente ~252 dias úteis).
  Juros compostos (não escala linear simples) é a convenção correta para anualizar retorno percentual
  — escalar linearmente superestimaria retornos compostos ao longo de períodos longos.
- **Alternatives considered**: escala linear (`total_return_pct * 365 / period_days`) — rejeitada por
  distorcer sistematicamente para períodos != 1 ano (ex: um retorno de 10% em 30 dias viraria "120%
  anualizado" linear, quando o composto correto é maior ainda, ~3400%, mas a distorção linear tende a
  *subestimar* retornos altos e é a fórmula tecnicamente incorreta para "anualizado").

## Retorno por tempo exposto (US2)

- **Decision**: `return_per_exposure_pct = total_return_pct / (exposure_pct / 100)` quando
  `exposure_pct > 0`; `None` (não `0.0` nem `inf`) quando `exposure_pct == 0` — campo
  `Optional[float]`, exibido como "não aplicável" no relatório em vez de um número.
- **Rationale**: ao contrário de Sortino/Calmar (onde `inf`/`0.0` já são convenções estabelecidas no
  projeto para "sem denominador, mas com significado direcional"), aqui exposição zero significa
  literalmente "a estratégia nunca operou" — não há retorno por tempo exposto para calcular, positivo
  ou negativo. `None` explícito (FR-006) é mais honesto que forçar um `0.0`/`inf` sem sentido.
- **Alternatives considered**: `inf`/`0.0` como as outras métricas — rejeitado porque, diferente de
  "zero perdas" (que é um resultado real e informativo), "zero exposição" é ausência de dado, uma
  categoria diferente.

## Novo comando `decisions` para análise de `data/decisions.csv` (US3)

- **Decision**: novo módulo `data/decisions_analysis.py`, espelhando a estrutura de
  `backtesting/analysis.py` (dataclass de registro + `_load_*` + `analyze_*` + `print_*` + `run()`).
  Novo comando `python main.py decisions` (alias `decisoes`), mesmo padrão de nomeação de
  `analyze`/`analisar`, `optimize`/`otimizar`.
- **Rationale**: `decisions.csv` já tem uma leitura companheira natural (`data/decision_store.py`
  escreve, este módulo lê) — replicar a estrutura já validada de `analysis.py` em vez de inventar um
  padrão novo mantém os dois comandos de análise (`analyze` para trades fechados, `decisions` para
  ciclos/sinais) consistentes entre si e fáceis de manter juntos.
- **Alternatives considered**: adicionar a análise como uma flag de `python main.py analyze` — rejeitado
  porque opera sobre um arquivo e um domínio de dado completamente diferente (ciclos/sinais/bloqueios,
  não trades fechados); misturaria dois relatórios não relacionados sob o mesmo comando.

## Resiliência a schema antigo em `decisions.csv` (US3, Edge Case)

- **Decision**: leitura via `csv.DictReader` (não `pandas.read_csv` com schema fixo) — colunas
  ausentes numa linha específica viram `None`/chave ausente no dict daquela linha, sem quebrar as
  demais. Contagens/agregações que dependem de uma coluna específica (ex: `blockers`) tratam ausência
  como "sem bloqueio registrado" em vez de propagar uma exceção.
- **Rationale**: `DECISION_HEADERS` já mudou de forma aditiva antes nesta base de código (ex: spec 001
  adicionou `client_order_id` a outros CSVs via `ensure_csv`/migração de header) — um `decisions.csv`
  girado ao longo de várias sessões de bot pode legitimamente ter linhas de antes de uma coluna nova
  existir. `DictReader` já lida com isso nativamente (linhas mais curtas que o header viram `None` nas
  colunas faltantes), sem precisar de tratamento manual extra.
- **Alternatives considered**: exigir migração de schema antes de analisar (como `ensure_csv` faz para
  escrita) — rejeitado por ser desproporcional para um comando de leitura/diagnóstico; a leitura
  tolerante já resolve o requisito (FR-009) sem exigir migrar dados históricos do operador.
