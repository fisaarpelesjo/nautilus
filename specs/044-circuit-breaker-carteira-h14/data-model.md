# Fase 1 — Modelo de dados: circuit breaker de perdas consecutivas

## `_simular_carteira_core(..., usar_circuit_breaker: bool = False)` (`backtesting/portfolio_h14.py`)

Novo estado local, escopo da simulação (não persistido, não um campo de
`CarteiraH14`/`PosicaoCarteira`):

- `perdas_consecutivas: int = 0` — inicializado antes do loop principal.

**Ordem de aplicação** (estende a ordem já declarada em spec 043,
`usar_circuit_breaker` entra antes do gate de correlação — é o filtro
mais barato e mais binário dos três, roda primeiro):

1. Fecha posições que tocaram take-profit/stop trailing. A cada
   fechamento: se `pnl < 0`, `perdas_consecutivas += 1`; se `pnl > 0`,
   `perdas_consecutivas = 0`. (`pnl == 0`, caso de borda raro, não altera
   o contador — nem reforça nem reseta uma sequência de perdas.)
2. Monta a fila de candidatos.
3. **Circuit breaker** (spec 044, novo): se `usar_circuit_breaker=True`
   e `perdas_consecutivas >= MAX_CONSECUTIVE_LOSSES`, nenhum candidato
   novo abre neste passo — `continue` para o próximo instante sem
   consumir a fila.
4. Gate de correlação (spec 042): candidato correlacionado com posição
   já aberta é pulado.
5. Dimensionamento base.
6. Fator de volatilidade (spec 041).

Passo 3 roda **antes** do loop sobre candidatos individuais (é uma
condição de carteira inteira, não por candidato) — quando ativo, pula
a iteração de abertura inteira, não candidato a candidato.

## `simular_carteira(..., usar_circuit_breaker: bool = False)`

Wrapper real, passa o parâmetro adiante sem lógica própria — mesmo
padrão de `usar_dimensionamento_vol`/`usar_gate_correlacao`.

## `cmd_carteira_breaker()` (CLI, `main.py`)

Chama `simular_carteira(pares=UNIVERSO_H11, usar_circuit_breaker=True)`
— isolado, sem os outros dois mecanismos (FR-005). Imprime a curva de
capital agregada, o veredito de `evaluate_approval()`, e os quatro
resultados já publicados (sem overlay 28,66%; só volatilidade 23,04%;
só correlação 20,74%; combinado 20,24%) lado a lado. Reusa
`export_report("carteira_breaker", ...)`.
