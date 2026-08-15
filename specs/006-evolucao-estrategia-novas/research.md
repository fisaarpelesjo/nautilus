# Research: Evolução da Estratégia

Fase 0 do `/speckit-plan`. Nenhum item do Technical Context ficou como `NEEDS CLARIFICATION`.

## `run_backtest()` precisa aceitar a estratégia como parâmetro (dependência transversal de US4/US5)

- **Decision**: `backtesting/engine.py` `run_backtest(symbol, timeframe, initial_capital=1000.0,
  candle_limit=2000, strategy=None)` — quando `strategy` for `None`, mantém `EmaRsiStrategy()` como
  hoje. `simulate_backtest()` já é genérico (chama `strategy.generate_signal(df.iloc[:i])` por candle
  quando `precomputed_signals` não é passado) — nenhuma mudança adicional necessária ali.
- **Rationale**: os 3 chamadores atuais (`backtesting/multi.py`, `backtesting/scanner.py`,
  `main.py cmd_backtest`) usam só os parâmetros posicionais/nomeados já existentes — um `strategy`
  opcional no fim da assinatura é 100% aditivo, sem quebrar nenhum deles.
- **Alternatives considered**: criar uma função `run_backtest_with_strategy()` paralela — rejeitado,
  duplicaria toda a lógica de fetch/print_report só para trocar uma linha; passar a estratégia via
  variável de módulo/config global — rejeitado, tornaria testes com múltiplas estratégias na mesma
  execução (comando de comparação, US5) dependentes de estado mutável compartilhado.

## Regime de mercado via ADX(14) (US1)

- **Decision**: `strategy/ema_rsi.py` `calculate_indicators()` ganha `df["adx"]` via
  `ta.trend.ADXIndicator(high, low, close, window=14).adx()`. Novo `REGIME_ADX_THRESHOLD` (config,
  default `20`, valor comumente citado em literatura de análise técnica para separar
  trending/sideways) classifica cada candle: `adx >= threshold` → `"trending"`, `adx < threshold` →
  `"sideways"`, `NaN`/indisponível → `"indefinido"` (tratado como `sideways` para fins de bloqueio,
  conservador). Novo `REGIME_FILTER_ENABLED` (config, default `false` — aditivo, preserva
  comportamento atual) bloqueia novas entradas quando o regime do candle atual for `sideways`/
  `indefinido`.
- **Rationale**: `ta.trend.ADXIndicator` já é a mesma biblioteca (`ta`) usada para EMA/RSI/MACD/BB —
  nenhuma dependência nova. Limiar único e configurável (não dois limiares trending/sideways
  separados com uma zona neutra) mantém a implementação inicial simples; se o backtest mostrar
  benefício em ter uma zona de histerese, isso fica como evolução futura, não bloqueante para esta
  spec.
- **Alternatives considered**: classificar em 3 faixas (trending forte / fraco / sideways) — rejeitado
  por complexidade extra sem pedido explícito na spec; calcular regime só sob demanda no comando de
  diagnóstico (não por candle) — rejeitado, spec exige registro em `data/decisions.csv` por ciclo.
- **Registro em `data/decisions.csv`**: reusa o padrão já estabelecido (nova coluna `regime`, mesmo
  mecanismo de `trading/decision_logger.py` que já grava `blockers`/indicadores por ciclo) — não um
  arquivo novo.

## Volatilidade elevada via `ATR_ratio` (US2)

- **Decision**: `ATR_ratio = atr / close`, calculado onde `atr` já existe (reuso direto, sem novo
  indicador). Novo `HIGH_VOLATILITY_ATR_RATIO` (config, default `0.05`, ou seja ATR ≥ 5% do preço)
  e `HIGH_VOLATILITY_FILTER_ENABLED` (config, default `false`). Quando ativo e `ATR_ratio` excede o
  limiar num candle de sinal de compra, a entrada é bloqueada com motivo específico
  (`"volatilidade elevada"`) — mesmo padrão de bloqueio configurável e aditivo de US1, e mesma
  precedência já decidida no Edge Case do `spec.md` (bloqueio de risco tem precedência sobre
  permissão de oportunidade, ex: Bollinger adaptativo de US3).
- **Rationale**: bloquear (em vez de recalcular SL/TP dinamicamente para "mais conservador") foi
  escolhido para a v1 desta capacidade — o risk manager já ajusta SL/TP via ATR proporcionalmente
  (`ATR_SL_MULTIPLIER`/`ATR_TP_MULTIPLIER`), então um ATR alto já produz um SL/TP proporcionalmente
  mais largo automaticamente; o risco real não coberto por esse ajuste automático é abrir posição
  justamente no candle de maior stress (gap, notícia, liquidação em cascata), que bloquear resolve
  diretamente.
- **Alternatives considered**: recalcular multiplicadores de ATR dinamicamente por regime de
  volatilidade (ex: `ATR_SL_MULTIPLIER` maior quando `ATR_ratio` alto) — mais sofisticado, mas expande
  a superfície de teste (interação entre 2 sistemas de ajuste de risco simultâneos); mantido como
  possível evolução futura, não necessário para fechar FR-005 ("bloquear OU ajustar", satisfeito por
  qualquer um dos dois).

## Filtro Bollinger adaptativo (US3)

- **Decision**: em `strategy/ema_rsi.py` `generate_signal()`, `not_overextended` passa a ser
  `price <= curr["bb_upper"] or (above_trend and volume_ok and <novo threshold de forca>)` quando
  `ADAPTIVE_BOLLINGER_ENABLED` (config, default `false`) estiver ativo. "Tendência forte" reusa
  `above_trend` (preço > EMA de tendência) e `volume_ok` (volume > `VOLUME_MIN_RATIO` × média) —
  os mesmos critérios já usados na estratégia para "tendência e volume fortes", sem inventar um
  terceiro conjunto de regras.
- **Rationale**: reusar os critérios já existentes (em vez de um novo "score de força de tendência")
  mantém a mudança pequena e auditável — o comportamento adaptativo é uma OR condicional sobre uma
  condição já calculada, não uma feature nova de indicadores.
- **Alternatives considered**: usar apenas `above_trend` sem exigir `volume_ok` — rejeitado, um
  rompimento sem volume tem historicamente maior taxa de falha (fakeout), contradiz o próprio motivo
  do filtro Bollinger existir.

## `strategy/breakout.py` (US4)

- **Decision**: nova classe `BreakoutStrategy(BaseStrategy)`, parametrizada por `window` (testável em
  50/150/200, default via `BREAKOUT_WINDOW` config). `calculate_indicators()` computa
  `df["breakout_high"] = df["high"].rolling(window).max().shift(1)` e `df["breakout_low"] =
  df["low"].rolling(window).min().shift(1)` (shift(1) exclui o candle atual, evita look-ahead —
  mesmo cuidado já aplicado a `precompute_signals` em `backtesting/engine.py` para EMA crossover).
  `generate_signal()`: BUY quando `close > breakout_high` da janela anterior; SELL quando
  `close < breakout_low`. Inclui `df["atr"]` (mesmo indicador ATR já usado por `EmaRsiStrategy`, via
  `ta.volatility.AverageTrueRange`) para compatibilidade com `risk/manager.py` (SL/TP dinâmico) e
  `trading/position_lifecycle.py` (trailing stop) sem exigir mudança nesses módulos.
- **Rationale**: definição clássica de rompimento de faixa (Donchian channel), já citada no
  `spec.md` Assumptions como escopo desta spec — reusar `ta.volatility.AverageTrueRange` para o ATR
  evita duplicar a lógica já validada em `EmaRsiStrategy`.
- **Alternatives considered**: confirmar rompimento só no fechamento do candle seguinte (evita
  fakeouts intracandle) — mais robusto, mas o motor de backtest já opera em base de candle fechado
  (`df.iloc[:i]` exclui o candle atual do sinal), então esse cuidado já é automático nesta
  infraestrutura; não precisa de lógica extra.
- **Dados insuficientes** (Edge Case do spec.md): `len(df) < window` → mesma resposta já usada por
  `EmaRsiStrategy` para dados insuficientes (`Signal.HOLD`, motivo explícito), reusando o padrão
  existente em vez de inventar um novo.

## Comando de comparativo entre estratégias/presets (US5)

- **Decision**: novo `backtesting/compare.py`, função `run_comparison(strategies: dict[str,
  BaseStrategy], pairs=None, timeframe=None)` — roda `run_backtest(pair, timeframe, strategy=strategy)`
  (usando o novo parâmetro de `run_backtest`, ver decisão acima) para cada combinação
  estratégia×par, reusando `evaluate_approval`/`edge_score`/`ranking_key` já existentes
  (`backtesting/approval.py`, spec 002) para veredito e ordenação — mesma tabela Rich já usada em
  `backtesting/multi.py`, com uma coluna adicional de nome da estratégia/preset. Novo comando
  `python main.py compare`/`comparar`, com a lista de estratégias/presets a comparar inicialmente
  fixa no código (mesmo padrão de `PAIRS` fixo em `backtesting/multi.py`), não configurável via
  `.env` nesta primeira versão — evita expandir a superfície de configuração antes de o comando
  provar valor em uso.
- **Rationale**: reusar `evaluate_approval`/`edge_score` (em vez de um critério de comparação novo) é
  um requisito explícito do `spec.md` (FR-009, Acceptance Scenario 2) — mantém o comparativo
  consistente com `edge`/`multibacktest`/`scan` já existentes.
- **Alternatives considered**: lista de estratégias configurável via `.env` (string de nomes) —
  rejeitado por complexidade de serialização (instanciar classes Python a partir de uma string de
  config) desproporcional ao valor nesta primeira versão; o código-fonte já é o lugar natural para
  declarar "quais estratégias eu quero comparar hoje", mesmo padrão de `backtesting/multi.py`.

## Superfície de configuração nova

- `REGIME_ADX_THRESHOLD` (default `20`), `REGIME_FILTER_ENABLED` (default `false`).
- `HIGH_VOLATILITY_ATR_RATIO` (default `0.05`), `HIGH_VOLATILITY_FILTER_ENABLED` (default `false`).
- `ADAPTIVE_BOLLINGER_ENABLED` (default `false`).
- `BREAKOUT_WINDOW` (default `150`, meio-termo das 3 janelas citadas na spec — 50/150/200 continuam
  testáveis via `EmaRsiParams`-like dataclass parametrizável em `BreakoutStrategy.__init__`, não
  exigem 3 variáveis de config separadas).
- Todos os `*_ENABLED` desligados por padrão (FR-010: aditivo, sem mudar comportamento de quem não
  habilitar) — mesmo princípio já usado em `USE_LIMIT_ORDERS` (spec 005).
