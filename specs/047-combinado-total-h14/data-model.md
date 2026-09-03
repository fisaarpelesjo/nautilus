# Fase 1 — Modelo de dados: combinação total (teto)

## `simular_carteira(pares=UNIVERSO_H11, usar_dimensionamento_vol=True, usar_gate_correlacao=True, usar_limite_drawdown_diario=True)`

Nenhum campo novo. Ordem de aplicação já declarada (specs 041/042/045),
inalterada: limite diário → circuit breaker (desligado) → gate de
correlação → dimensionamento base → fator de volatilidade.

## `cmd_carteira_teto()` (CLI, `main.py`)

Chama `simular_carteira` com os três parâmetros. Imprime a curva de
capital agregada, o veredito de `evaluate_approval()`, e os sete
resultados já publicados (sem overlay 28,66%/931; só volatilidade
23,04%/763; só correlação 20,74%/595; vol+correlação 20,24%/595;
circuit breaker 0,57%/6; limite diário 22,17%/762; correlação+diário
20,38%/594) lado a lado. Marca explicitamente se o resultado ficou
perto do gate de correlação sozinho (confirmando a expectativa
declarada) ou divergiu. Reusa `export_report("carteira_teto", ...)`.
