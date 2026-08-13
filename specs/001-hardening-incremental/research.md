# Research: Hardening Incremental do Bot de Daytrade

Fase 0 do `/speckit-plan`. Nenhum item do Technical Context ficou como `NEEDS CLARIFICATION` — o
projeto já existe e sua stack já está decidida — mas as decisões técnicas específicas de cada User
Story ainda precisavam de escolha e justificativa. Registradas abaixo.

## clientOrderId (US1)

- **Decision**: gerar um ID curto por ordem combinando um prefixo fixo (ex: `bot-`), os primeiros 8
  caracteres de um `uuid4` e o timestamp Unix em segundos, ex: `bot-3f2a9c1e-1755100000`.
- **Rationale**: a Binance aceita `clientOrderId`/`newClientOrderId` com até 36 caracteres via
  `ccxt`; um uuid4 truncado + timestamp é suficientemente único para o volume de ordens deste bot
  (poucas por dia) sem exigir um contador persistido central nem coordenação entre processos.
- **Alternatives considered**: contador incremental persistido em `state.json` — rejeitado por
  exigir lock/coordenação se dois processos rodarem por engano (mais uma forma de estado para
  divergir); hash do sinal (par+timestamp+direção) — rejeitado porque dois sinais idênticos no mesmo
  segundo colidiriam.

## Reconciliação (US1)

- **Decision**: reconciliação roda (a) uma vez na inicialização do bot e (b) a cada N ciclos dentro
  do loop existente de 60s em `trading/runner.py` (não um processo/thread separado). Compara posições
  abertas em `state.json` com `fetch_positions`/`fetch_open_orders` via `ccxt`. Divergência → evento
  JSONL + alerta Telegram; sem correção automática.
- **Rationale**: reusar o loop existente evita introduzir concorrência (threads/async) numa base de
  código hoje síncrona — consistente com o non-goal de não migrar para asyncio nesta fase. Não
  corrigir automaticamente é uma escolha de segurança: uma correção automática errada poderia
  amplificar um problema já existente sem supervisão humana.
- **Alternatives considered**: reconciliação em processo separado (cron/thread) — rejeitada por
  complexidade desproporcional ao volume de operações; correção automática da divergência —
  rejeitada por risco (ver Rationale).

## Circuit breaker de perdas consecutivas (US2)

- **Decision**: contador global (não por par) persistido em `state.json`, incrementado a cada trade
  fechado com `pnl < 0`, resetado a qualquer trade com `pnl > 0`. Limite configurável via
  `MAX_CONSECUTIVE_LOSSES` (sugestão de default: 3, a validar/ajustar durante o uso em paper mode).
- **Rationale**: um contador global é mais simples e mais conservador que por-par — perdas
  consecutivas em pares diferentes ainda podem indicar que a estratégia/regime de mercado piorou de
  forma geral, não só naquele par. Consistente com `MAX_ENTRIES_PER_CYCLE=1`, que já trata entradas
  como um recurso compartilhado entre pares.
- **Alternatives considered**: contador por par — mais granular, mas adiado; pode virar uma
  iteração futura se o global se mostrar bloqueando pares saudáveis por causa de um par ruim.

## Kill switch (US2)

- **Decision**: flag booleana persistida em `state.json` (reaproveita o arquivo de estado já
  existente, em vez de um arquivo novo), lida a cada ciclo do `runner.py`. Dois novos subcomandos em
  `main.py`: `kill` (seta a flag) e `resume` (limpa a flag).
- **Rationale**: reaproveitar `state.json` evita mais um arquivo de estado para reconciliar/perder
  sincronia; os subcomandos são consistentes com o padrão já existente de `main.py` (`bot`, `status`,
  etc.).
- **Alternatives considered**: arquivo de flag separado (`data/killswitch.flag`) — mais simples de
  inspecionar manualmente, mas foi descartado por criar uma segunda fonte de estado.

## Split out-of-sample no backtest (US3)

- **Decision**: dividir o DataFrame de candles em duas fatias contíguas por índice (ex: 70%
  treino/otimização, 30% validação), sem embaralhar (dado é série temporal). Rodar
  `simulate_backtest`/`run_backtest` já existentes em cada fatia e reportar as duas métricas lado a
  lado.
- **Rationale**: reusa o motor de backtest existente (`backtesting/engine.py`) sem reescrevê-lo —
  consistente com o non-goal de não trocar de motor de backtest. Split simples por índice é
  suficiente para a US3 (walk-forward com múltiplas janelas rolantes fica como evolução futura, não
  bloqueante para o objetivo desta spec de "mostrar in-sample vs out-of-sample").
- **Alternatives considered**: walk-forward com múltiplas janelas rolantes — mais robusto
  estatisticamente, mas maior escopo; adiado para uma iteração futura do `ROADMAP.md` depois que o
  split simples provar valor.

## Eventos de observabilidade (todas as User Stories)

- **Decision**: reusar o pipeline já existente (`utils/logger.py` grava JSONL em
  `logs/events-YYYY-MM-DD.jsonl`; `utils/notifier.py` envia Telegram). Três novos tipos de evento:
  `reconciliation_mismatch`, `circuit_breaker_triggered`, `killswitch_toggled`.
- **Rationale**: constitution (Observability Mandatory) exige explicitamente não introduzir um
  pipeline paralelo.
- **Alternatives considered**: nenhuma — a constitution já decide isso.
