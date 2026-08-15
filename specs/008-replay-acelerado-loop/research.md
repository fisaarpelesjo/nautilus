# Research: Replay Acelerado do Loop Real

Fase 0 do `/speckit-plan`. Nenhum item do Technical Context ficou como `NEEDS CLARIFICATION`.

## Isolamento total de arquivos reais (US1, FR-002/FR-003)

- **Decision**: `trading/replay.py` implementa um context manager
  `_isolated_order_manager_environment()` que troca temporariamente, via `try/finally` (restaura
  mesmo em exceção), as seguintes ligações em `execution.order_manager`: `TRADING_MODE` → forçado
  `"paper"` (garante que `OrderManager` NUNCA entra no caminho `_live_buy`/`_live_sell`,
  independente do `.env` real — fecha FR-003); `load_state` → sempre retorna `{}` (estado limpo a
  cada replay); `save_state` → no-op; `log_trade` → coletor em memória (os trades resultantes SÃO o
  produto do replay, coletados aqui em vez de ir para `data/trades.csv`); `log_event` → no-op (evita
  poluir `logs/events-*.jsonl` reais com eventos de simulação); `send_telegram` → no-op (**crítico**:
  sem isso, cada trade simulado dispararia uma mensagem real no Telegram do operador, se configurado).
- **Rationale**: reusa exatamente o mesmo padrão de isolamento já usado extensivamente pela suíte de
  testes deste projeto (`monkeypatch.setattr(order_manager, "load_state", ...)` etc., presente em
  `tests/test_order_manager_safety.py`) — não inventa um mecanismo novo, só aplica fora do contexto
  de teste, em produção, dentro de um context manager que garante restauração mesmo em erro.
- **Alternatives considered**: adicionar um parâmetro `isolated: bool` a `OrderManager.__init__` —
  rejeitado por aumentar a superfície de `execution/order_manager.py` (arquivo de alto risco,
  usado pelo bot real) só para servir a uma ferramenta de análise; o monkeypatch scoped por context
  manager, vivendo inteiramente em `trading/replay.py`, mantém o arquivo de execução real inalterado.

## Motor de decisão real candle a candle (US1)

- **Decision**: `run_replay(symbol, timeframe, candle_limit)` busca histórico público
  (`fetch_ohlcv`, mesma função já usada por backtest/produção), itera com um índice crescente
  (mesmo padrão de `simulate_backtest` em `backtesting/engine.py`: `df.iloc[:i]` a cada ciclo,
  chamando `strategy.generate_signal(df.iloc[:i])`), e para cada ciclo chama diretamente
  `handle_entry_candidate`/`handle_open_position` (já existentes, `trading/position_lifecycle.py`)
  com o `OrderManager` isolado — não reimplementa a lógica de decisão, só o laço de iteração.
- **Rationale**: é o requisito central da spec (FR-001) — exercitar o código real de decisão, não
  uma segunda simulação simplificada. Reusar `handle_entry_candidate`/`handle_open_position`
  diretamente garante que qualquer bug/comportamento real do caminho de produção apareça no replay
  também, sem precisar manter duas implementações sincronizadas.
- **Limitação conhecida e documentada** (não é bug, é escopo): `manager.set_cooldown()`/
  `is_in_cooldown()` usam `datetime.now()` (relógio real), não o timestamp do candle histórico sendo
  processado. Num replay que roda em segundos, um cooldown ativado por um Stop Loss no início do
  histórico praticamente nunca expira relativo ao tempo real de execução do replay, then Tende a
  sub-negociar apos qualquer evento de cooldown dentro do mesmo replay. Corrigir isso exigiria
  injetar um "relógio simulado" em `execution/order_manager.py` (arquivo de alto risco) — fora de
  escopo desta spec; documentado no relatório final do replay como limitação explícita.
- **MTF durante o replay**: usa `mtf_confirmed()` já existente, que busca o timeframe de confirmação
  mais recente disponível (não um MTF point-in-time correto para o candle histórico sendo
  processado) — mesma limitação de escopo, documentada no `spec.md` Assumptions. Corrigir exigiria
  buscar e alinhar dois históricos por timestamp, uma complexidade maior não necessária para o valor
  já entregue pelo MVP (comparar divergência de decisão, não replicar 100% fielmente cada detalhe).

## Comparação replay vs backtest (US2)

- **Decision**: após o replay, roda `run_backtest(symbol, timeframe, strategy=EmaRsiStrategy())`
  (já existente, spec 006) sobre os mesmos dados, e compara número de trades e retorno total entre
  os dois, com uma lista de observações textuais fixas quando aplicável (ex: "replay teve menos
  trades — cooldown/MTF pode ter bloqueado entradas que o backtest simplificado não modela").
- **Rationale**: reusa a infraestrutura de backtest já validada (spec 006) em vez de duplicar
  simulação — a comparação é o valor analítico desta spec, não uma nova forma de simular.

## Superfície de configuração nova

Nenhuma — comando novo (`python main.py replay <PAR>`), sem novas variáveis de `.env`.
