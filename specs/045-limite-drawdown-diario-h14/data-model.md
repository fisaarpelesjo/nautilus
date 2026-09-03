# Fase 1 — Modelo de dados: limite de drawdown diário

## `_simular_carteira_core(..., usar_limite_drawdown_diario: bool = False)` (`backtesting/portfolio_h14.py`)

Novo estado local, escopo da simulação (não persistido):

- `dia_referencia: Optional[date] = None` — dia de calendário do saldo
  de referência atual.
- `saldo_referencia_diario: float = capital_inicial` — patrimônio
  capturado no primeiro candle do dia corrente.

**Ordem de aplicação** (estende specs 043/044 — este roda antes do
circuit breaker, mesmo critério de "mais barato e mais binário primeiro"):

1. Fecha posições que tocaram take-profit/stop trailing.
2. Monta a fila de candidatos.
3. **Limite de drawdown diário** (spec 045, novo): se
   `usar_limite_drawdown_diario=True`:
   a. Calcula `patrimonio_atual` (caixa + posições abertas a mercado,
      preço de fechamento deste candle) — mesma fórmula do cálculo de
      patrimônio já existente no passo final de cada candle.
   b. Se `t.date() != dia_referencia`: `dia_referencia = t.date()`,
      `saldo_referencia_diario = patrimonio_atual` (reset
      incondicional, independente de resultado).
   c. Se `patrimonio_atual < saldo_referencia_diario × (1 -
      DAILY_DRAWDOWN_LIMIT)`: nenhum candidato novo abre neste passo.
4. Circuit breaker (spec 044, se ligado).
5. Gate de correlação (spec 042, se ligado).
6. Dimensionamento base.
7. Fator de volatilidade (spec 041, se ligado).

Passo 3 roda por candle inteiro (carteira, não candidato a candidato) —
mesmo padrão do circuit breaker (spec 044): quando bloqueia, pula a
iteração de abertura inteira.

## `simular_carteira(..., usar_limite_drawdown_diario: bool = False)`

Wrapper real, passa o parâmetro adiante sem lógica própria — mesmo
padrão dos parâmetros anteriores.

## `cmd_carteira_dd_diario()` (CLI, `main.py`)

Chama `simular_carteira(pares=UNIVERSO_H11,
usar_limite_drawdown_diario=True)` — isolado, sem os outros três
mecanismos (FR-005). Imprime a curva de capital agregada, o veredito de
`evaluate_approval()`, e os cinco resultados já publicados (sem overlay
28,66%/931 trades; só volatilidade 23,04%/763; só correlação
20,74%/595; combinado 20,24%/595; circuit breaker 0,57%/6) lado a
lado — `total_trades` em destaque, é o número que decide se este
mecanismo repete o colapso amostral do circuit breaker ou não. Reusa
`export_report("carteira_dd_diario", ...)`.
