# Fase 1 — Modelo de dados: H20 backtest real

## `avaliar_par(..., params: Optional[ParametrosBarreira] = None, ...)` (`backtesting/modelo.py`)

Nas duas chamadas de `_resultado_modelo(...)` (loop `for nome, y in
(("modelo", ...), ("embaralhado", ...))`), adiciona
`atr_tp_multiplier=p.tp_mult, atr_sl_multiplier=p.sl_mult` aos
argumentos — `_resultado_modelo` já repassa `**kwargs` para
`_simular_com_sinais`, que já repassa para `simulate_backtest`
(`backtesting/engine.py`), que já aceita `atr_tp_multiplier`/
`atr_sl_multiplier` como parâmetros nomeados.

**Efeito quando `params=None`**: `p = params or ParametrosBarreira()`
(linha já existente) — `ParametrosBarreira()` tem
`tp_mult=ATR_TP_MULTIPLIER`, `sl_mult=ATR_SL_MULTIPLIER` como default,
os MESMOS valores que `simulate_backtest` já usava sem receber os
kwargs. Byte a byte idêntico.

**Efeito quando `params=ParametrosBarreira(tp_mult=2.0)`**: o backtest
real agora sai a `2×ATR`, a mesma geometria usada para rotular e
treinar — antes saía a `3×ATR` (produção), uma estratégia diferente da
rotulada.

## `cmd_geometria()` (CLI, `main.py` — extensão de spec 048)

Depois de imprimir o resumo estatístico (já existente), roda
`avaliar_par` por par sobre `UNIVERSO_H11` com o `ParametrosBarreira`
da geometria selecionada (já construído para `run_modelo_scan`) e
imprime, por par: `total_trades`, `total_return_pct`,
`max_drawdown_pct`, `profit_factor` do `ResultadoModelo.backtest` —
sem agregar (drawdown não é agregável entre pares independentes, mesma
razão já documentada em `resumo_agregado`). Compara contra os números
por-par já publicados de H14 (`tp=3,0`) onde disponíveis, sem inventar
critério de aprovação novo — `evaluate_approval`/`diagnose_profile`
já existentes, reusados por par.
