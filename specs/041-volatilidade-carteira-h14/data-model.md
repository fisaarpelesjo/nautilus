# Fase 1 — Modelo de dados: dimensionamento por volatilidade na carteira

## `_simular_carteira_core(..., usar_dimensionamento_vol: bool = False)` (extensão, spec 037)

| Passo | Descrição |
|---|---|
| `order_size` (já existente) | `min(MAX_ORDER_SIZE_USDT, (caixa/slots_livres)*0,95)`, ajustado por caixa disponível |
| **Novo**: fator de volatilidade | Se `usar_dimensionamento_vol`, `order_size *= fator_volatilidade(row.get("atr_ratio"))` (D1) — `fator_volatilidade` já existente, `backtesting/volatilidade.py`, sem alteração |
| Default | `usar_dimensionamento_vol=False` reproduz o resultado já publicado (spec 037) byte a byte — regressão testada |

## `simular_carteira(..., usar_dimensionamento_vol: bool = False)` (extensão, spec 037)

Repassa o parâmetro para `_simular_carteira_core` — mesmo padrão de
`retornar_previsao` em `avaliar_par`/`run_modelo_scan` (H14, spec 034).

## `fator_volatilidade`/`ParametrosVolatilidade` (reusados, `backtesting/volatilidade.py`, spec 025, sem alteração)

Nenhum campo novo, nenhuma fórmula nova — consumidos exatamente como já
existem.

## `cmd_carteira_vol()` (CLI, `main.py`)

Chama `simular_carteira(usar_dimensionamento_vol=True)` sobre
`UNIVERSO_H11` (FR-005), imprime a curva de capital agregada, o veredito
de `evaluate_approval()`, e o drawdown já publicado sem dimensionamento
(28,66%, spec 037) lado a lado — mesmo padrão visual de
`cmd_carteira`/`cmd_carteira_ampla`. Reusa
`export_report("carteira_vol", ...)`.
