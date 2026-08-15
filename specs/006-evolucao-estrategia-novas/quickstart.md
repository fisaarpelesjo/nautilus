# Quickstart: Validando a Evolução da Estratégia

Fase 1 do `/speckit-plan`. Toda validação usa dados públicos da Binance via backtest — nenhum passo
exige credenciais ou `TRADING_MODE=live`, conforme FR-011.

Pré-requisitos: ambiente Python configurado (`.venv`), dependências instaladas.

## US1 — Regime de mercado via ADX

1. `python main.py backtest` com `REGIME_FILTER_ENABLED=false` (default) — confirmar que o resultado
   é idêntico ao já validado antes desta spec (nenhuma regressão).
2. `REGIME_FILTER_ENABLED=true python main.py backtest` no mesmo par/período — comparar número de
   trades e retorno contra o passo 1.
3. Rodar `python main.py decisions` e confirmar que a coluna `regime` aparece com valores
   `trending`/`sideways`/`indefinido`.

## US2 — Volatilidade elevada

1. `HIGH_VOLATILITY_FILTER_ENABLED=true python main.py backtest` no mesmo par/período do baseline —
   confirmar que candles com `ATR_ratio` acima do limiar tiveram a entrada bloqueada (verificável via
   `data/decisions.csv`, motivo `"volatilidade elevada"`).

## US3 — Bollinger adaptativo

1. `ADAPTIVE_BOLLINGER_ENABLED=true python main.py backtest` no mesmo par/período do baseline —
   comparar contra o filtro fixo atual (`ADAPTIVE_BOLLINGER_ENABLED=false`).

## US4 — `strategy/breakout.py`

1. Rodar um backtest isolado de `BreakoutStrategy` (script ad-hoc ou teste de integração) num par com
   histórico suficiente para janela de 200 períodos, confirmando relatório completo (mesmas métricas
   de qualquer outra estratégia) sem erros.
2. Testar as 3 janelas citadas na spec (50, 150, 200) e comparar resultado.

## US5 — Comando de comparação

1. `python main.py compare` — confirmar que o relatório mostra pelo menos EMA/RSI padrão e
   `BreakoutStrategy` (alguma janela) lado a lado, com veredito de aprovação em cada linha.

## Checklist final

- [ ] Suíte de testes completa passa sem alteração de comportamento com todos os `*_ENABLED` no
  default (`false`) — confirma FR-010/SC-004.
- [ ] Nenhum passo acima exigiu `.env` com credenciais reais ou `TRADING_MODE=live` — confirma
  FR-011.
