# Data Model: Decisão de Aprovação Multi-Par

Fase 1 do `/speckit-plan`. Todas as entidades abaixo são transientes — existem só durante a execução
de um comando de relatório (`multibacktest`/`scan`/`edge`), nunca persistidas em disco. Nenhum
`state.json`/CSV novo, nenhuma mudança de schema de dado gravado.

## Veredito de aprovação (generalização de `ValidationVerdict` da spec 001)

Renomeado para `ApprovalVerdict` em `backtesting/approval.py` (ver `research.md`); aplicável a
qualquer `BacktestResult`, com ou sem split treino/validação.

| Campo | Tipo | Regras |
|---|---|---|
| `status` | enum(`aprovado`, `reprovado`, `inconclusivo`) | `inconclusivo` quando o resultado de entrada é `None` (ex: janela sem dados) ou amostra abaixo de `min_trades`; `aprovado` só quando retorno > buy-and-hold **e** profit factor > mínimo **e** drawdown ≤ máximo **e** amostra ≥ mínimo; `reprovado` nos demais casos. |
| `reasons` | lista de string | Motivos textuais curtos do status; vazia só quando `status=aprovado`. |
| `diagnosis` | string ou `None` | Preenchido só quando `status=reprovado` e o padrão "defensivo" é detectado (ver `research.md`); `None` nos demais casos — campo aditivo, não substitui `reasons`. |

## Resultado com veredito (extensão de `MultiResult`/`ScanResult` existentes)

Campos novos adicionados às dataclasses já existentes em `backtesting/multi.py` e
`backtesting/scanner.py` — não substituem os campos atuais (`trades`, `win_rate`, `retorno_pct`,
`drawdown_pct`, `capital_final` continuam existindo, inalterados).

| Campo | Tipo | Regras |
|---|---|---|
| `profit_factor` | float | Copiado do `BacktestResult` subjacente; hoje descartado silenciosamente ao construir `MultiResult`/`ScanResult`. |
| `buy_hold_return_pct` | float | Idem — necessário para o veredito e para exibição lado a lado com `retorno_pct`. |
| `edge_score` | float | Usado como critério de ranking (ver `research.md`); substitui o `.score` ad hoc de `ScanResult`. |
| `edge_score_band` | string | Faixa legível (`Forte`/`Médio`/`Fraco`/`Reprovado`) derivada de `edge_score`. |
| `verdict` | `ApprovalVerdict` ou `None` | `None` só na linha de erro (par que falhou ao buscar dados/rodar backtest) — ver entidade abaixo. |

## Linha de erro (novo — hoje o par simplesmente desaparece da tabela)

| Campo | Tipo | Regras |
|---|---|---|
| `pair` | string | Par que falhou. |
| `error` | string | Mensagem curta do erro (já capturada pelo `except Exception as e` existente, só passa a ser exibida). |

Não é um `MultiResult`/`ScanResult` completo — é uma entidade separada e mais simples, já que nenhuma
métrica de backtest existe para um par que falhou antes de completar.

## Relatório de edge com veredito (novo — `python main.py edge` hoje não calcula nada disso)

Substitui o comportamento atual de `cmd_edge` (que hoje só chama `run_backtest`, idêntico a
`cmd_backtest`).

| Campo | Tipo | Regras |
|---|---|---|
| `result` | `BacktestResult` (já existente) | Backtest de janela única, sem split treino/validação (diferente do fluxo de `backtest --validate`, spec 001 US3). |
| `verdict` | `ApprovalVerdict` | Calculado sobre `result` inteiro (não há `train`/`validation` separados aqui). |
