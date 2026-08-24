# Research: Camada de dados multi-mercado para pesquisa

**Feature**: 023-dados-multi-mercado | **Data**: 2026-08-24

Tudo abaixo foi **medido**, não presumido — a decisão de escopo desta feature depende de saber o que a fonte de dados realmente entrega.

---

## D1. Fonte de dados não-cripto

**Decisão**: `yfinance` como primeira (e por ora única) fonte não-cripto.

**Rationale**: medido em 2026-08-24, cobre os quatro mercados que a spec exige, sem chave de API e sem custo:

| Mercado | Símbolo testado | Candles 1h (2 anos) |
|---|---|---|
| Ação EUA | `AAPL` | 876 |
| Ação BR | `PETR4.SA` | 874 |
| Forex | `EURUSD=X` | 3.058 |
| Futuro | `ES=F` | 2.877 |
| Índice | `^GSPC` | 876 |

Entrega OHLCV no mesmo formato conceitual já usado (`Open/High/Low/Close/Volume`), exigindo apenas normalização de nome de coluna para a convenção minúscula do projeto.

**Alternativas consideradas**:
- **Alpha Vantage / Twelve Data / Polygon**: qualidade melhor (ajuste de proventos confiável), mas exigem chave e têm limite agressivo no plano gratuito. Rejeitadas por conflitarem com o objetivo de triagem barata — a feature existe para decidir *se* vale investir num mercado, não para operá-lo.
- **ccxt com outra exchange**: não resolve, ccxt é cripto-only.
- **Alpaca via ccxt** (existe no ccxt): cobre ações EUA, mas não forex/futuros/índices, e exige conta. Fica como candidata futura *se* ações EUA provarem valer a pena — é o caminho natural quando houver execução.

---

## D2. Timeframe de 4h existe, mas com teto de histórico

**Decisão**: manter `4h` como timeframe de comparação, aceitando janela menor que a de cripto.

**Rationale**: `4h` **é** suportado pelo yfinance, ao contrário do que se poderia supor. Mas o histórico intradiário é limitado a **730 dias** pela fonte:

| Período pedido | Candles 4h obtidos |
|---|---|
| 3 meses | 126 |
| 6 meses | 251 |
| 1 ano | 498 |
| 2 anos | **993** |
| `max` | vazio (erro: "must be within the last 730 days") |

Cripto entrega 2.000 candles; ações entregam ~993 no melhor caso. **Consequência direta**: `candle_limit=2000` não pode ser assumido para mercados não-cripto — pedir mais do que a fonte tem devolve menos, silenciosamente.

**Validação crítica** — o split treino/validação exigido por FR-012 **cabe** nessa janela:

```
total=993 → treino=695, validação=298
MIN_WINDOW_CANDLES=150 por fatia → split válido ✅
```

Ou seja, a confirmação fora da amostra é viável em ações/forex/futuros com 2 anos de histórico 4h. Não seria com 6 meses (251 candles → validação de 75, abaixo do mínimo).

**Alternativas consideradas**:
- **Usar 1d** para mercados não-cripto: dá mais histórico (500 candles de 2 anos, e `max` funciona indo a décadas), mas quebra a comparabilidade com cripto — a estratégia se comporta diferente por timeframe, e comparar 4h-cripto com 1d-ações mediria duas coisas. Rejeitado.
- **Usar 1h**: mais candles (3.469 em 2 anos), mas já medimos neste projeto que 1h degrada o resultado por ruído e custo. Rejeitado como padrão; permanece disponível.

---

## D3. Reuso da validação out-of-sample (FR-012/013/014)

**Decisão**: reusar `backtesting/validation.py` — `split_train_validation()` e `run_backtest_with_validation()` — sem escrever mecanismo novo.

**Rationale**: a infraestrutura já faz exatamente o que a spec pede:
- `split_train_validation()` divide em fatias **contíguas e não embaralhadas** (correto para série temporal), com `MIN_WINDOW_CANDLES=150` por fatia e retorno de `None` quando o split é inválido — que é a política de "falha explícita" exigida por FR-005
- Os sinais são pré-calculados sobre o dataframe **inteiro antes do split**, evitando que o `.shift(1)` do cruzamento de EMA perca contexto na fronteira da fatia — detalhe já resolvido ali que uma implementação nova provavelmente erraria
- `evaluate_approval()` já é aplicado **sobre a fatia de validação**, não sobre o treino

**Isto é decisivo para a feature**: o custo de FR-012 (a decisão do operador de exigir confirmação fora da janela de busca) cai drasticamente, porque o mecanismo existe e é testado. O que falta é aplicá-lo na varredura multi-mercado e registrar a contagem de combinações (FR-013) e a distinção visual (FR-014).

**Alternativa considerada**: correção estatística tipo Bonferroni sobre o p-valor. Rejeitada — exigiria um modelo estatístico que o projeto não tem, e o operador já escolheu a abordagem de validação out-of-sample.

---

## D4. Ponto único de abstração

**Decisão**: abstrair em `data/fetcher.py::fetch_ohlcv()`, mantendo a assinatura atual.

**Rationale**: `fetch_ohlcv(symbol, timeframe, limit)` é o **único** ponto por onde todo consumo de candle passa — backtest, compare, scan, optimize, validation, replay e o loop ao vivo. Abstrair ali cobre tudo sem tocar em nenhum consumidor.

Restrições observadas no código atual que a implementação precisa respeitar:
- O cache é global e indexado por `f"{symbol}_{timeframe}"`. Símbolos de mercados diferentes precisam ser inequívocos nessa chave (`AAPL` vs `AAPL.SA` já são distintos naturalmente; verificar colisão é obrigação da implementação)
- A estratégia de cache incremental (busca 5 candles novos e faz merge) é específica de ccxt. Uma fonte com limite de requisição diferente pode precisar de política própria
- `fetch_ticker`, `fetch_tickers`, `fetch_balance` e `fetch_order_book` são **cripto-only e devem permanecer assim** — são usados por seleção dinâmica de pares, liquidez e execução, nenhum dos quais entra nesta feature

---

## D5. Custo por mercado (FR-003/FR-004)

**Decisão**: perfil de custo declarado por mercado, com recusa explícita quando ausente.

**Rationale**: o motor já aceita `fee_rate` e `slippage_pct` como parâmetros de `simulate_backtest()` — não são constantes fixas no caminho de backtest. Basta resolvê-los por mercado antes de chamar.

Diferenças estruturais que o perfil precisa acomodar:

| Mercado | Custo dominante | Modelagem |
|---|---|---|
| Cripto | taxa percentual | direto (já é assim) |
| Ações | corretagem fixa por ordem + spread | percentual equivalente ao tamanho de ordem configurado |
| Forex | spread (sem corretagem típica) | percentual |
| Futuros | valor fixo por contrato | percentual equivalente |

A aproximação de custo fixo → percentual é registrada nas Assumptions da spec: precisa para triagem, imprecisa para dimensionamento fino. **FR-004 é o guarda-corpo**: mercado sem perfil declarado não pode cair no custo de cripto por omissão — foi exatamente esse mecanismo (slippage de par líquido aplicado a book fino) que fez ACE/BIO/ALLO parecerem operáveis e entregarem prejuízo real.

---

## D6. Descontinuidade de pregão (FR-009)

**Decisão**: sinalizar no resultado, não modelar no motor.

**Rationale**: cripto opera 24/7; ações e futuros têm gap entre fechamento e abertura. A proteção de perda por trade (`MAX_STOP_LOSS_PCT`, teto de 8%) **não age dentro de um gap** — o preço salta o stop.

Modelar isso corretamente exigiria simular execução em mercado com pregão, o que está explicitamente fora de escopo (a feature não constrói execução). A alternativa honesta é **marcar o resultado**, para que o operador saiba que a perda real naquele mercado pode exceder o teto simulado.

Isto segue o padrão já estabelecido no projeto de documentar limitação conhecida em vez de escondê-la — e de nunca deixar um número parecer mais confiável do que é.

---

## Riscos técnicos identificados

1. **Divergência entre caminhos** — introduzir uma segunda fonte cria a possibilidade de pesquisa e produção discordarem. Este projeto já foi atingido duas vezes por esse padrão (simulação sem trailing stop; confirmação de tendência olhando o futuro), e nas duas o defeito passou despercebido por não existir teste comparando os dois caminhos. **Mitigação obrigatória**: teste que garanta que o caminho cripto produz resultado idêntico antes e depois da abstração.

2. **Qualidade de dado gratuito** — yfinance não garante ajuste de proventos consistente. Para ações, um dividendo não ajustado aparece como queda de preço que a estratégia lê como sinal. Aceito para triagem; registrar como limitação.

3. **`candle_limit` silenciosamente não atendido** — pedir 2000 candles e receber 993 não gera erro. Precisa ser detectado e reportado, senão a comparação cripto × ações fica desbalanceada sem ninguém notar.
