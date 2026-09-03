# Fase 1 — Modelo de dados: carteira sobre universo amplo

## `UNIVERSO_AMPLO` (constante, `backtesting/portfolio_h14.py`)

Lista fixa de 34 símbolos (D1, `research.md`) — mesmo formato de
`UNIVERSO_H11` (`backtesting/horizonte.py`).

## `simular_carteira(pares=UNIVERSO_AMPLO)` (reusado, spec 037, sem alteração)

| Diferença vs. spec 037 | Descrição |
|---|---|
| `pares` | `UNIVERSO_AMPLO` (34) em vez de `UNIVERSO_H11` (12) |
| Tudo o resto | Idêntico — `MAX_POSITIONS`, capital inicial, dimensionamento, mecanismo de saída (D7 de spec 037), buy-and-hold igualmente ponderado (D5 de spec 037, agora sobre 34 pares em vez de 12) |

## `comparar_drawdown(resultado_carteira, avaliacoes)` (reusado, spec 037, sem alteração)

Usado duas vezes nesta spec: uma vez internamente (carteira ampla vs.
maior drawdown isolado por par, já existente), e o resultado do
`BacktestResult` de carteira ampla é reportado ao lado do já publicado
sobre 12 pares (FR-004) — comparação manual no texto do registro, não
uma função nova.

## `cmd_carteira_ampla()` (CLI, `main.py`)

Chama `simular_carteira(pares=UNIVERSO_AMPLO)`, imprime a curva de
capital agregada (patrimônio final, retorno, drawdown, buy-hold, profit
factor), o veredito de `evaluate_approval()`, e o drawdown já publicado
sobre 12 pares (28,66%, spec 037) lado a lado para comparação direta —
mesmo padrão visual de `cmd_carteira`. Reusa `export_report("carteira_ampla", ...)`.
