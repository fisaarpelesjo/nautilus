# Fase 1 — Modelo de dados: combinação vol + correlação

## `simular_carteira(pares=UNIVERSO_H11, usar_dimensionamento_vol=True, usar_gate_correlacao=True)` (chamada, sem alteração de `backtesting/portfolio_h14.py`)

Nenhum campo novo. A ordem de aplicação dentro de
`_simular_carteira_core` (já existente, inalterada nesta spec) é:

1. Fecha posições que tocaram take-profit/stop trailing.
2. Monta a fila de candidatos (previsão acima do limiar, maior
   probabilidade primeiro).
3. **Gate de correlação** (spec 042): candidato correlacionado com
   posição já aberta é pulado antes de qualquer dimensionamento.
4. Dimensionamento base (teto por ordem, reserva de caixa).
5. **Fator de volatilidade** (spec 041): aplicado por último, só reduz.

O gate de correlação roda primeiro porque é um filtro **binário**
(abre/não abre); o dimensionamento por volatilidade só faz sentido
depois de decidido que a posição vai abrir.

## `cmd_carteira_combo()` (CLI, `main.py`)

Chama `simular_carteira(pares=UNIVERSO_H11, usar_dimensionamento_vol=True,
usar_gate_correlacao=True)`, imprime a curva de capital agregada, o
veredito de `evaluate_approval()`, e os três drawdowns já publicados
(sem overlay 28,66%; só volatilidade 23,04%; só correlação 20,74%) lado
a lado. Reusa `export_report("carteira_combo", ...)`.
