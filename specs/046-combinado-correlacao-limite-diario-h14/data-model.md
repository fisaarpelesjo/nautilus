# Fase 1 — Modelo de dados: combinação correlação + limite diário

## `simular_carteira(pares=UNIVERSO_H11, usar_gate_correlacao=True, usar_limite_drawdown_diario=True)` (chamada, sem alteração de `backtesting/portfolio_h14.py`)

Nenhum campo novo. A ordem de aplicação dentro de
`_simular_carteira_core` (já existente, inalterada nesta spec, declarada
em `specs/045-limite-drawdown-diario-h14/data-model.md`) é:

1. Fecha posições que tocaram take-profit/stop trailing.
2. Monta a fila de candidatos.
3. **Limite de drawdown diário** (spec 045): se o patrimônio do dia caiu
   abaixo do limite, nenhum candidato abre.
4. Circuit breaker (spec 044) — desligado nesta spec (`False`).
5. **Gate de correlação** (spec 042): candidato correlacionado com
   posição já aberta é pulado.
6. Dimensionamento base — desligado nesta spec (`False`).
7. Fator de volatilidade (spec 041) — desligado nesta spec (`False`).

O limite diário roda antes do gate de correlação porque é um filtro de
carteira inteira (todos os candidatos ou nenhum); o gate de correlação
roda candidato a candidato, só faz sentido depois de saber que a
carteira está autorizada a abrir alguma coisa naquele instante.

## `cmd_carteira_combo2()` (CLI, `main.py`)

Chama `simular_carteira(pares=UNIVERSO_H11, usar_gate_correlacao=True,
usar_limite_drawdown_diario=True)`, imprime a curva de capital
agregada, o veredito de `evaluate_approval()`, e os seis resultados já
publicados (sem overlay 28,66%/931; só volatilidade 23,04%/763; só
correlação 20,74%/595; combinado vol+correlação 20,24%/595; circuit
breaker 0,57%/6; limite diário 22,17%/762) lado a lado — drawdown,
`total_trades` e profit factor em destaque. Reusa
`export_report("carteira_combo2", ...)`.
