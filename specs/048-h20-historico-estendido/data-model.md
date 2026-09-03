# Fase 1 — Modelo de dados: H20 com histórico estendido

## `run_geometria_scan()` (`backtesting/geometria.py`)

Único campo alterado: a chamada `fetch_ohlcv(par, TIMEFRAME, 2000)`
(linha 204) passa a `fetch_ohlcv(par, TIMEFRAME, 6000)`. Nenhuma
mudança de assinatura, nenhum campo novo em `PerfilGeometria`/
`RelatorioGeometria`.

## `cmd_geometria()` (CLI, `main.py` — H20 nunca teve comando)

1. `relatorio = run_geometria_scan()` — mede os perfis sobre 6.000
   candles e aplica a regra de seleção já declarada (spec 028,
   inalterada).
2. Se `relatorio.selecionada` for `None`: reporta "nenhuma geometria
   elegível" — desfecho legítimo já previsto por `selecionar()`
   (FR-006 de spec 028), sem forçar avaliação.
3. Se houver selecionada: monta
   `ParametrosBarreira(tp_mult=selecionada.tp_mult,
   sl_mult=selecionada.sl_mult, limite_velas=selecionada.limite_velas)`
   e chama `run_modelo_scan(params=params)` seguido de
   `resumo_agregado(avaliacoes, params)` (`backtesting/modelo.py`, já
   existentes, já migrados para 6.000 candles por spec 036).
4. Imprime, por geometria candidata: `tp_mult`, razão base, elegível
   sim/não. Para a selecionada: razão pooled (`resumo_agregado()["
   modelo"]["razao"]`), ponto de empate (`razao_empate`),
   `supera_empate` (bool, teste com banda de incerteza — Wilson CI,
   já corrigido por M13) e `supera_empate_pontual` (bool, comparação
   por ponto único, só para contexto/comparação, nunca usado como
   veredito).
5. Compara explicitamente contra os números já publicados (2.000
   candles): razão base 0,6223 em tp=2,0, razão pooled 0,7478 no
   subconjunto decidido, `z=-0,07`/`p=0,535` (não superava o empate).
6. Reusa `export_report("geometria_estendida", ...)`.
