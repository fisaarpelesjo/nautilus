# CLI Contract: Comportamento Afetado

Fase 1 do `/speckit-plan`. Um comando novo, nenhuma mudança em comandos existentes.

## `python main.py replay <PAR>` (novo)

- **Input**: símbolo do par (ex: `BTC/USDT`).
- **Efeito**: roda o motor de decisão real (`handle_entry_candidate`/`handle_open_position`) candle
  a candle sobre histórico público, com `OrderManager` totalmente isolado (nunca toca
  `data/state.json`/`data/trades.csv`/`data/signals.csv`/`data/decisions.csv` reais, nunca envia
  ordem real, nunca dispara Telegram real).
- **Output (stdout)**: relatório com trades do replay e comparação contra um backtest simples do
  mesmo par/período, incluindo limitações conhecidas (cooldown baseado em relógio real, MTF não
  point-in-time).
- **Efeito colateral observável**: nenhum nos arquivos reais do bot. Chamadas de rede só leem dados
  públicos (OHLCV, MTF) — nenhuma credencial exigida, nenhuma ordem enviada.
