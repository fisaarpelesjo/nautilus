# Data Model: Hardening Incremental do Bot de Daytrade

Fase 1 do `/speckit-plan`. Entidades novas ou alteradas por esta feature — todas persistidas nos
mecanismos já existentes (`state.json`, `data/trade_store.py`), nenhum banco novo introduzido.

## Ordem rastreável (extensão de entidade existente)

Campo novo em cada ordem registrada (paper ou live), tanto em `state.json` quanto no CSV de
`data/trade_store.py`:

| Campo | Tipo | Regras |
|---|---|---|
| `client_order_id` | string | Único por ordem; gerado no momento do envio (ver `research.md`); obrigatório em toda ordem nova, mesmo em paper mode (para manter paridade paper/live). |

## Relatório de reconciliação (nova, transiente)

Não persistido como histórico — só existe durante a checagem e vira um evento se houver divergência.

| Campo | Tipo | Regras |
|---|---|---|
| `status` | enum(`ok`, `mismatch`) | `mismatch` dispara evento + alerta. |
| `local_positions` | lista | Posições segundo `state.json` no momento da checagem. |
| `remote_positions` | lista | Posições segundo a conta real da Binance (`ccxt`). |
| `diffs` | lista | Pares/campos que divergem entre local e remoto; vazio quando `status=ok`. |
| `checked_at` | timestamp | Momento da checagem. |

## Contador de perdas consecutivas (novo, persistido em `state.json`)

| Campo | Tipo | Regras |
|---|---|---|
| `consecutive_losses` | inteiro ≥ 0 | Incrementa em trade fechado com `pnl < 0`; reseta para 0 em trade fechado com `pnl > 0`. |
| `circuit_breaker_active` | booleano | `true` quando `consecutive_losses >= MAX_CONSECUTIVE_LOSSES`; volta a `false` quando o contador reseta. |

**Transições de estado**:

```text
consecutive_losses = 0, circuit_breaker_active = false   (estado inicial)
  --[trade fecha com prejuízo]--> consecutive_losses += 1
  --[consecutive_losses >= limite]--> circuit_breaker_active = true (bloqueia novas entradas)
  --[trade fecha com lucro, a qualquer momento]--> consecutive_losses = 0, circuit_breaker_active = false
```

## Kill switch (novo, persistido em `data/killswitch.json` — não em `state.json`, ver `research.md`)

| Campo | Tipo | Regras |
|---|---|---|
| `active` | booleano | Setado por `python main.py kill`, limpo por `python main.py resume`. Bloqueia novas entradas quando `true`, independente de qualquer outro limite de risco. Não afeta gestão de posições já abertas. Lido do disco a cada ciclo de `trading/runner.py` (não fica em memória) para refletir uma ativação externa sem exigir restart. |
| `toggled_at` | string (ISO) | Timestamp da última mudança, para auditoria/exibição em `python main.py status`. |

## Janela de validação out-of-sample (nova, transiente — só no relatório de backtest)

| Campo | Tipo | Regras |
|---|---|---|
| `train_window` | intervalo de datas | Fatia usada para treino/otimização de parâmetros. |
| `validation_window` | intervalo de datas | Fatia usada para validar out-of-sample; não sobrepõe `train_window`. |
| `train_metrics` | métricas de backtest (já existentes: retorno, profit factor, drawdown, etc.) | Calculadas sobre `train_window`. |
| `validation_metrics` | métricas de backtest (mesmo formato) | Calculadas sobre `validation_window`; é o valor usado pelos critérios de aprovação automática (FR-008). |
| `approved` | enum(`aprovado`, `reprovado`, `inconclusivo`) | Resultado da função de aprovação automática aplicada a `validation_metrics`. |
