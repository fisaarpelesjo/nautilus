# Quickstart: Validando a Observabilidade Operacional

Fase 1 do `/speckit-plan`. Toda validação usa dados públicos de backtest ou fixtures sintéticas —
nenhum passo exige histórico real de paper mode rodando por um período (FR-010).

Pré-requisitos: ambiente Python configurado (`.venv`), dependências instaladas.

## US1 — Caixa/posições/patrimônio no status

1. Em paper mode com uma posição simulada aberta (`state.json` sintético ou real), rodar
   `python main.py status` e confirmar que caixa livre + valor em posições = patrimônio total, e que
   PnL realizado + não realizado = PnL total.
2. Sem nenhuma posição aberta, confirmar que patrimônio total = caixa livre e PnL não realizado = 0.

## US2 — Contexto explícito no edge

1. `python main.py edge` para qualquer par e confirmar que modo, par, timeframe, período e capital
   inicial aparecem explicitamente, com o aviso de que não é o estado real do bot.

## US3 — Painel local

1. `python main.py painel` com `data/trades.csv`/`data/signals.csv`/`data/decisions.csv`
   sintéticos (ou reais, se existirem) e confirmar que todas as seções aparecem sem erro.
2. `python main.py painel` numa instalação sem nenhum desses arquivos e confirmar estado vazio
   claro em cada seção, não erro.

## US4 — Modo debug da estratégia

1. `python main.py debug BTC/USDT` (ou outro par configurado) e confirmar que cada condição de
   entrada (EMA, RSI, volume, MTF, Bollinger, regime, volatilidade, cooldown) aparece com seu valor.
2. Comparar o motivo apontado pelo modo debug contra o `blockers`/`decision` já registrado em
   `data/decisions.csv` para o mesmo par no ciclo mais recente, confirmando consistência (SC-004).

## US5 — Gráficos de performance

1. `python main.py performance` com `data/trades.csv` sintético (via fixture de teste) e confirmar
   que os 3 gráficos (capital, drawdown, PnL por par) são gerados sem erro.
2. `python main.py chart <PAR>` e confirmar que marcadores de trades reais (quando existirem em
   `data/trades.csv` para o par) aparecem distintos dos marcadores teóricos de sinal já existentes.

## Checklist final

- [ ] Suíte de testes completa passa.
- [ ] Nenhum passo acima exigiu `data/trades.csv`/`data/signals.csv`/`data/decisions.csv` reais —
  todos funcionam com fixtures sintéticas (confirma FR-010).
