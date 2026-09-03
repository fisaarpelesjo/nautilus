# Fase 1 — Modelo de dados: gate de correlação na carteira

## `_correlacionado_com_posicao_aberta(par_candidato, preparados, posicoes_abertas, t, lookback=CORRELATION_LOOKBACK, limiar=MAX_POSITION_CORRELATION) -> Optional[str]`

| Passo | Descrição |
|---|---|
| Sem posições abertas | Devolve `None` (nada para comparar, D1/FR-004) |
| Série do candidato | `preparados[par_candidato]["close"].loc[:t].pct_change().dropna().tail(lookback)` |
| Amostra insuficiente do candidato | `< lookback // 2` → devolve `None` (falha aberta, FR-004) |
| Para cada par já aberto | Mesma série, mesmo corte; interseção de tamanho com o candidato; `< lookback // 2` → pula esse par (comparação individual, FR-004) |
| Correlação | `Series.corr()` sobre as duas séries alinhadas por posição (`reset_index(drop=True)`) |
| Bloqueio | Primeira correlação `>= limiar` encontrada → devolve o símbolo do par já aberto (FR-003) |
| Nenhuma correlação alta | Devolve `None` |

## `_simular_carteira_core(..., usar_gate_correlacao: bool = False)` (extensão, spec 037/041)

| Passo | Descrição |
|---|---|
| Candidatos a abrir (já existente) | Ordenados por maior probabilidade (D4, spec 037) |
| **Novo**: filtro de correlação | Se `usar_gate_correlacao`, antes de dimensionar, chama `_correlacionado_com_posicao_aberta(par, preparados, carteira.posicoes.keys(), t)` — se devolver um símbolo, pula esse candidato (não abre, tenta o próximo) |
| Default | `usar_gate_correlacao=False` reproduz o resultado já publicado (spec 037) byte a byte |

## `simular_carteira(..., usar_gate_correlacao: bool = False)` (extensão, spec 037/041)

Repassa o parâmetro para `_simular_carteira_core` — mesmo padrão de
`usar_dimensionamento_vol` (spec 041).

## `cmd_carteira_corr()` (CLI, `main.py`)

Chama `simular_carteira(pares=UNIVERSO_H11, usar_gate_correlacao=True)`,
imprime a curva de capital agregada, o veredito de `evaluate_approval()`,
e o drawdown já publicado sem o gate (28,66%, spec 037) lado a lado —
mesmo padrão visual de `cmd_carteira`/`cmd_carteira_vol`. Reusa
`export_report("carteira_corr", ...)`.
