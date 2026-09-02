# Fase 1 — Modelo de dados: motor de carteira para H14

## `AvaliacaoH14.previsao_teste` (novo campo, `backtesting/modelo.py`)

| Campo | Tipo | Preenchido quando |
|---|---|---|
| `previsao_teste` | `Optional[pd.Series]` (índice = timestamp do candle, valor = probabilidade prevista) | `avaliar_par(..., retornar_previsao=True)` (D2) — `None` no caminho default, comportamento atual inalterado |

## `CarteiraH14` (novo, `backtesting/portfolio_h14.py`)

Estado da simulação — não persistido, só em memória durante
`simular_carteira()`.

| Campo | Descrição |
|---|---|
| `caixa` | Capital livre, único entre os 12 pares (D1: inicia em 1.000,0) |
| `posicoes` | `Dict[par, PosicaoCarteira]` — no máximo `MAX_POSITIONS` chaves ao mesmo tempo (FR-006) |
| `curva_capital` | Lista de `(timestamp, patrimonio)` — `caixa` + valor de posições abertas a preço de mercado, um ponto por candle da união de timelines (D3) |

## `PosicaoCarteira`

Espelha o estado por posição de `simulate_backtest`
(`backtesting/engine.py`), um por par aberto simultaneamente (D7).

| Campo | Descrição |
|---|---|
| `par` | Símbolo |
| `preco_entrada` | Preço de abertura |
| `quantidade` | `tamanho_usdt / preco_entrada` |
| `entry_atr` | ATR travado na entrada (não recalculado depois) |
| `preco_alvo` | `_take_profit_price(preco_entrada, entry_atr, ...)` — take-profit por ATR, calculado uma vez na abertura |
| `stop_price` | Trailing — inicia em `_stop_price(preco_entrada, entry_atr, ...)`, só sobe conforme `highest_price` avança (D7) |
| `highest_price` | Máxima desde a entrada, usada para atualizar `stop_price` |
| `instante_entrada` | Timestamp do candle de abertura |

## `Trade` (reusado, `backtesting/engine.py`, sem campo novo)

| Campo | Preenchido como |
|---|---|
| `entry_price` / `exit_price` | `preco_entrada` / preço de saída (`"Take Profit"`, `"Stop Loss"`, ou `close` no fim do histórico) |
| `quantity` | `PosicaoCarteira.quantidade` |
| `pnl` / `pnl_pct` | Mesma fórmula já usada pelo motor (`_close_trade`, reusada), com `BACKTEST_FEE_RATE`/`BACKTEST_SLIPPAGE_PCT` aplicados |
| `entry_time` / `exit_time` | Timestamps dos candles de abertura/fechamento |
| `exit_reason` | `"Take Profit"` / `"Stop Loss"` (mesmos rótulos de `simulate_backtest`, D7) ou `"Fim do periodo"` (posição aberta quando o histórico termina — mesmo rótulo do motor genérico) |

## `BacktestResult` (reusado, `backtesting/engine.py`, sem campo novo)

Montado por `simular_carteira()` a partir de `curva_capital`:

| Campo | Origem |
|---|---|
| `trades` | Lista de `Trade`, uma por posição fechada em qualquer par |
| `initial_capital`/`final_capital` | `1.000,0` (D1) / último ponto de `curva_capital` |
| `total_return_pct` | `(final - inicial) / inicial * 100` |
| `buy_hold_return_pct` | Retorno de uma carteira igualmente ponderada nos 12 pares, sem rebalanceamento (D5) |
| `max_drawdown_pct` | Pico-a-vale sobre `curva_capital` — o número central desta spec, primeira medição real de drawdown agregado de H14 |
| Demais campos | `_calculate_advanced_metrics(...)`, chamada sem modificação (D6) |

## `simular_carteira(pares=UNIVERSO_H11, capital_inicial=1000.0) -> BacktestResult`

1. `run_modelo_scan(pares, retornar_previsao=True internamente)` — reusa
   treino/purga global, obtém `previsao_teste` por par (D2).
2. Une os timestamps de teste de todos os pares (D3), avança
   cronologicamente.
3. A cada candle: fecha posições que tocaram take-profit ou stop trailing
   (D7, mesmo mecanismo do backtest publicado de H14), atualiza o
   trailing das que continuam abertas; abre novas posições para pares com
   `previsao_teste` acima
   do limiar de decisão, respeitando `MAX_POSITIONS` e o caixa disponível,
   com desempate por maior probabilidade (D4) e dimensionamento
   `min(MAX_ORDER_SIZE_USDT, (caixa/slots_livres_restantes)*0.95)`
   (`CLAUDE.md`, FR-005).
4. Ao fim do histórico, posições abertas fecham a mercado (`"fim do
   periodo"`).
5. Monta `BacktestResult` (acima), aplica `evaluate_approval()` — sem
   critério novo (FR-009).

## `cmd_carteira()` (CLI, `main.py`)

Chama `simular_carteira()`, imprime a curva de capital agregada e o
veredito de `evaluate_approval()`, lado a lado com o maior drawdown por
par já registrado em H14 (SC-003) — reusa `export_report` (padrão de
`modelo`/`grid`).
