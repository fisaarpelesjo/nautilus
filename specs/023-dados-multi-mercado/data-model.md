# Data Model: Camada de dados multi-mercado

**Feature**: 023-dados-multi-mercado | **Data**: 2026-08-24

---

## Market

Categoria de ativos com características próprias de negociação. Determina qual fonte busca os dados e qual perfil de custo a simulação aplica.

| Campo | Tipo | Descrição |
|---|---|---|
| `name` | str | Identificador do mercado: `crypto`, `stocks_us`, `stocks_br`, `forex`, `futures`, `index` |
| `source` | str | Nome da fonte que atende este mercado (`ccxt`, `yfinance`) |
| `continuous` | bool | `True` para 24/7 (cripto, forex ~24/5); `False` para pregão com gap de abertura |
| `cost` | CostProfile | Perfil de custo aplicado na simulação |
| `tradable` | bool | `True` só para mercados com execução implementada. Hoje: apenas `crypto` |

**Regras**:
- `tradable=False` MUST bloquear o símbolo no caminho de operação ao vivo (FR-007)
- `continuous=False` MUST marcar o resultado com o aviso de gap (FR-009)
- Um mercado sem `cost` definido MUST recusar avaliação (FR-004) — nunca herdar o de outro

---

## CostProfile

Custo de execução de um mercado, usado pela simulação para calcular resultado líquido.

| Campo | Tipo | Descrição |
|---|---|---|
| `fee_rate` | float | Taxa proporcional ao valor nocional |
| `slippage_pct` | float | Deslizamento de preço aplicado na entrada e na saída |
| `source_note` | str | De onde o número veio e o que ele aproxima — auditabilidade (FR-011) |

**Regras**:
- Ambos os valores MUST ser `>= 0`
- Mercados com corretagem fixa (ações, futuros) são representados por um percentual equivalente ao tamanho de ordem configurado. `source_note` MUST registrar essa aproximação — é imprecisa para dimensionamento fino, suficiente para triagem
- Estes campos alimentam os parâmetros `fee_rate`/`slippage_pct` que `simulate_backtest()` **já aceita** — nenhuma mudança na assinatura do motor

---

## DataSource

Origem de séries históricas. Contrato uniforme para que `fetch_ohlcv()` não saiba qual fonte está usando.

| Campo | Tipo | Descrição |
|---|---|---|
| `name` | str | `ccxt` ou `yfinance` |
| `max_history_candles` | int \| None | Teto conhecido da fonte para o timeframe pedido; `None` quando não há |

**Operação**: `fetch_ohlcv(symbol, timeframe, limit) -> DataFrame`

**Contrato de retorno** — igual entre fontes, para que os consumidores não mudem:
- Índice: `DatetimeIndex` ordenado crescente, sem duplicatas
- Colunas: `open`, `high`, `low`, `close`, `volume` (minúsculas)
- MUST levantar exceção quando não puder atender — nunca devolver DataFrame vazio ou parcial silenciosamente (FR-005)
- Quando `limit` exceder o disponível, MUST registrar a lacuna de forma detectável (risco técnico 3 de `research.md`: pedir 2.000 e receber 993 hoje não gera sinal nenhum)

---

## Symbol

Identificador de um ativo dentro de um mercado.

| Campo | Tipo | Descrição |
|---|---|---|
| `raw` | str | Como o operador escreveu: `BTC/USDT`, `AAPL`, `PETR4.SA`, `EURUSD=X`, `ES=F`, `^GSPC` |
| `market` | Market | Mercado resolvido a partir do formato |

**Regras de resolução** (da mais específica para a mais geral):

| Padrão | Mercado |
|---|---|
| contém `/` e termina em `/USDT` | `crypto` |
| termina em `.SA` | `stocks_br` |
| termina em `=X` | `forex` |
| termina em `=F` | `futures` |
| começa com `^` | `index` |
| demais alfanuméricos | `stocks_us` |

- A resolução MUST ser determinística e inequívoca
- Símbolo não resolvível MUST falhar explicitamente, nunca cair num mercado padrão
- A chave de cache MUST permanecer única entre mercados (hoje `f"{symbol}_{timeframe}"`; a implementação MUST verificar ausência de colisão)

---

## BacktestResult *(entidade existente, estendida)*

Campos novos, ambos com padrão que preserva o comportamento atual:

| Campo | Tipo | Padrão | Descrição |
|---|---|---|---|
| `market` | str \| None | `None` | Mercado avaliado — auditabilidade (FR-011) |
| `cost_profile_note` | str \| None | `None` | Qual perfil de custo foi aplicado (FR-011) |
| `has_session_gaps` | bool | `False` | Mercado descontínuo: teto de perda por trade não age dentro do gap (FR-009) |
| `requested_candles` | int \| None | `None` | Quanto foi pedido, para comparar com o obtido |

Campo `below_min_price` (spec 021) permanece — é a restrição estrutural equivalente no mercado cripto.

---

## MultiMarketScanResult

Resultado de uma varredura de estratégia × símbolo, com o guarda-corpo contra descoberta por acaso.

| Campo | Tipo | Descrição |
|---|---|---|
| `combinations_tested` | int | Quantas combinações foram avaliadas (FR-013) |
| `entries` | list[ScanEntry] | Uma por combinação |

**ScanEntry**:

| Campo | Tipo | Descrição |
|---|---|---|
| `strategy_name` | str | Estratégia avaliada |
| `symbol` | Symbol | Símbolo avaliado |
| `search_result` | BacktestResult | Desempenho na janela de busca |
| `confirmation_result` | BacktestResult \| None | Desempenho na janela de confirmação; `None` se o split foi inválido |
| `status` | str | `confirmado` \| `so_na_busca` \| `reprovado` \| `inconclusivo` |

**Regras** — o núcleo da decisão do operador sobre viés de descoberta:
- `status="confirmado"` MUST exigir aprovação na janela de **confirmação**, não na de busca (FR-012)
- Uma combinação que passa só na busca MUST receber `so_na_busca` e MUST NOT ser apresentada como aprovada (FR-014)
- `confirmation_result=None` (histórico insuficiente para dividir) MUST resultar em `inconclusivo` — jamais aprovar por omissão de dado
- `combinations_tested` MUST aparecer no relatório, para que uma aprovação isolada seja lida com o peso estatístico correto

**Reuso**: a divisão das janelas vem de `split_train_validation()` e a avaliação de `evaluate_approval()`, ambos existentes em `backtesting/`. Nenhum critério de aprovação novo é criado — decisão D3 de `research.md`.
