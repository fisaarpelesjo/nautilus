# Backlog de Specs

Fila de specs candidatas derivadas do `ROADMAP.md`, para trabalhar uma de cada vez pelo fluxo do
GitHub Spec Kit (`/speckit-specify` → `/speckit-plan` → `/speckit-tasks` → `/speckit-implement`),
seguindo o Fluxo Incremental do `CLAUDE.md` (tópico pequeno → teste → commit → push).

Coluna **Autonomia**:
- **Sozinho**: dá para especificar, implementar, testar (inclusive contra dados reais da Binance,
  que sao publicos) e validar sem depender de nada que só o operador tem/decide.
- **Parcial**: a maior parte é código que dá para construir sozinho, mas uma fatia especifica exige
  o operador (ex: rodar o bot em paper mode por dias/semanas — isso é tempo real passando, não
  simulável).
- **Bloqueado**: depende de uma decisão ou insumo do operador antes de começar (dinheiro real,
  preferência de produto, etc.) — não deve ser puxado da fila sem essa decisão.

| # | Spec candidata | Autonomia | Status |
|---|---|---|---|
| 001 | Hardening Incremental (idempotência/reconciliação, circuit breaker/kill switch, out-of-sample) | Sozinho | ✅ Concluída (`specs/001-hardening-incremental/`) |
| 002 | Decisão de aprovação multi-par | Sozinho | ✅ Concluída (`specs/002-multi-pair-approval/`) |
| 003 | Otimização sem overfitting | Sozinho | ✅ Concluída (`specs/003-robust-optimization/`) |
| 004 | Métricas de risco avançadas | Sozinho | ✅ Concluída (`specs/004-advanced-risk-metrics/`) |
| 005 | Proteções finais para live | Sozinho | ✅ Concluída (`specs/005-live-protections/`, US1-US4 + Polish) |
| 006 | Evolução da estratégia | Parcial | ✅ Parte autônoma concluída (`specs/006-evolucao-estrategia-novas/`, US1-US5 + Polish); "validar preset operacional atual" (Fase 4 item 1) segue pendente — depende de operação paper real |
| 007 | Observabilidade operacional / forward test | Parcial | ✅ Parte autônoma concluída (`specs/007-observabilidade-operacional-capacidades/`, US1-US5 + Polish); forward test formal e comparação paper-vs-backtest (Fase 5 itens 1 e 4) seguem pendentes — dependem de operação paper real |
| 008 | Replay acelerado do loop real | Sozinho | ✅ Concluída (`specs/008-replay-acelerado-loop/`, US1-US2 + Polish) — fora do backlog original, criada em resposta a uma pergunta do operador sobre alternativas a esperar operação paper real; aproximação parcial de 007 item 4, não substitui |
| 009 | Itens remanescentes do ROADMAP (relatórios, diagnóstico agressivo, edge out-of-sample, indicadores médios) | Sozinho | ✅ Concluída (`specs/009-itens-remanescentes-roadmap/`, US1-US4 + Polish) — fora do backlog original, criada após auditoria completa do `ROADMAP.md` (não só deste arquivo) revelar 4 itens pequenos genuinamente não implementados |
| 010 | Paridade de custos entre paper e backtest (fee/slippage em `_paper_buy`/`_paper_sell`) | Sozinho | ✅ Concluída (`specs/010-paridade-custos-paper/`, US1-US2 + Polish) — fora do backlog original, achado crítico de uma auditoria completa de código (não só docs) cruzada com pesquisa de boas práticas de bots de trading; o paper mode rodando na VPS desde 2026-08-16 estava registrando PnL sistematicamente ~0,3%/round-trip mais otimista que a realidade |
| 011 | Singleton do exchange + retry/backoff de rate limit (`data/fetcher.py`) | Sozinho | ✅ Concluída (`specs/011-rate-limit-hardening/`, US1-US2 + Polish) — risco operacional real pro deploy de 26 pares na VPS; escopo ampliado durante a especificação ao descobrir que `backtesting/scanner.py` tinha o mesmo problema fora de `data/fetcher.py` |
| 012 | MTF fail-closed + profundidade de liquidez próxima ao preço | Sozinho | 🟡 Parcial — MTF fail-closed corrigido em 2026-08-18 (auditoria de código pós-deploy, fora de uma spec formal: `mtf_confirmed()` agora retorna `False` em erro de rede, igual ao resto de `position_lifecycle.py`); falta ainda a parte de profundidade de liquidez próxima ao preço (`execution/liquidity.py::check_liquidity` soma os 20 níveis do order book, não só os próximos ao preço). Nota: `estimate_slippage_pct()` (spec 018) já caminha o book corretamente para o cálculo de slippage — falta aplicar o mesmo critério ao gate de profundidade |
| 013 | Risco de correlação entre posições simultâneas | Sozinho | ✅ Concluída em 2026-08-18 (`risk/correlation.py`, fora do fluxo formal de spec — implementado direto após pesquisa aprofundada de mercado confirmar o gap) — `MAX_POSITION_CORRELATION`/`CORRELATION_LOOKBACK`, bloqueador novo em `handle_entry_candidate` |
| 014 | Refresh periódico de pares dinâmicos (`DYNAMIC_PAIRS_ENABLED`) | Sozinho | 📋 Candidata — baixa urgência (não é a config atual), mas relevante dado o padrão comprovado de VPS de longa duração |
| 015 | Avançado (ML, multi-corretora) | Bloqueado | ⏸️ Fora da fila — ROADMAP.md já diz "só depois que validação/risco/operação estiverem maduros" |
| 016 | Teto de perda por trade + circuit breaker destravável | Sozinho | ✅ Concluída em 2026-08-18 (fora do fluxo formal de spec) — `MAX_STOP_LOSS_PCT` (SL via ATR não tinha limite prático: ACE/USDT abriu com stop a ~20% da entrada) e `CIRCUIT_BREAKER_COOLDOWN_HOURS` (breaker ativado sem posição aberta travava para sempre, pois nada gerava o trade lucrativo que o resetava) |
| 017 | Risco de correlação entre posições | Sozinho | ✅ Concluída em 2026-08-18 — ver 013 (mesma entrega, `risk/correlation.py`) |
| 018 | Slippage medido no order book real | Sozinho | ✅ Concluída em 2026-08-24 — `estimate_slippage_pct()` caminha o book em vez de usar `BACKTEST_SLIPPAGE_PCT` fixo para todo par; a constante vira piso (slippage de latência) e fallback. Medição: a $100/ordem a maioria dos pares dá 0,000% (a constante era conservadora); o ganho aparece em ordens grandes, onde ela subestimaria muito |
| 019 | **Trailing stop no motor de backtest** | Sozinho | ✅ Concluída em 2026-08-24 — **furo metodológico grave**: `simulate_backtest()` usava stop fixo na entrada enquanto a produção movia o stop a cada novo topo. Backtest e produção mediam estratégias diferentes, e **toda decisão de par/parâmetro do projeto saiu da régua errada**. Impacto medido: DOGE 2,24→0,86, ZEC 1,49→1,02, ADA 1,79→0,97, UNI 1,74→0,41 (os quatro deixaram de aprovar e foram removidos de `PAIRS`); ORCA 1,75→2,38 |
| 020 | MTF point-in-time no replay | Sozinho | ✅ Concluída em 2026-08-24 — `mtf_confirmed()` comparava preço histórico contra a EMA de tendência de **hoje**, filtro baseado no futuro. Viés direcional (bloqueava as entradas antigas mais baratas, que tendem a ser vencedoras): em NIL/USDT o replay descartava o trade de +$17,36 e mantinha o de -$8,24. Parâmetro `as_of` opcional; produção inalterada |
| 021 | `MIN_PRICE_USDT` só existe no loop ao vivo, não no backtest | Sozinho | 📋 Candidata — `trading/runner.py` descarta pares abaixo do preço mínimo antes de avaliar o sinal, mas `backtesting/engine.py` não tem filtro equivalente: um par sub-$0.001 passa no backtest e nunca opera em produção. Descoberto em 2026-08-24 — **LUNC/USDT ficou 8 dias em `PAIRS` sem gerar uma única decisão**, e era `PAIRS[0]` (alvo padrão de `backtest`/`edge`/`chart`), então vereditos daquele período foram calculados sobre um par que o bot nunca operou |
| 022 | Replay: cooldown/drawdown/circuit breaker por relógio real | Sozinho | 📋 Candidata — baixa prioridade. Esses três usam `datetime.now()` em vez do timestamp do candle simulado; um replay de meses roda em segundos, então os períodos raramente viram e bloqueios podem se estender além do que o bot real faria. Os timestamps dos trades do replay também são a hora de execução, não a do candle. Exigiria rotear tempo simulado por mais partes da cadeia de produção — só vale se o replay virar ferramenta central |

## 002 — Decisão de aprovação multi-par

Estende `backtesting/validation.py` (US3 da spec 001) para além de um par por vez.

- Critérios automáticos de aprovação (ROADMAP Fase 1 item 2) generalizados, não só dentro de
  `backtest --validate`
- Ranking de pares por qualidade (Fase 1 item 3), integrado a `multibacktest`/`scan`
- Edge por par e timeframe (Fase 1.1 item 5): veredito aprovado/reprovado/inconclusivo em
  `multibacktest`, `scan`, `select`
- Classificação automática + motivos no `python main.py edge` (Fase 1.1 itens 1, 2)
- Alerta de amostra insuficiente configurável (Fase 1.1 item 3)
- Diagnóstico defensivo vs agressivo (Fase 1.1 item 4)
- Refinar `edge_score` para escala interpretável (Fase 1.1 item 8)

Por que primeiro: resolve diretamente a limitação que a validação de US3 esbarrou (amostra pequena
par a par, sem visão agregada) — maior valor imediato, 100% código + dados públicos da Binance.

## 003 — Otimização sem overfitting

- Split treino/teste integrado ao `backtesting/optimizer.py` (hoje escolhe parâmetros sobre o
  histórico inteiro; `split_train_validation()` de 001 existe mas não é usada aqui) — Fase 2 item 1
- Walk-forward validation com janelas deslizantes — Fase 2 item 2
- Análise Monte Carlo de sequências de trades — Fase 2 item 3

## 004 — Métricas de risco avançadas

- Sortino Ratio, Calmar Ratio no backtest/análise — Fase 3 itens 1, 2
- Tempo em posição e retorno anualizado — Fase 3 item 3
- Análise automática de `data/decisions.csv` (o que mais bloqueia entradas) — Fase 3 item 4

## 005 — Proteções finais para live

Continuação direta de US1/US2 da spec 001.

- Confirmação explícita ao ligar `TRADING_MODE=live` — Fase 6 item 1
- Checagem de liquidez e spread antes da ordem — Fase 6 item 3
- Execução inteligente de ordens: limit/stop, rastreamento de preenchimento parcial (reconciliação
  de saldo já existe desde US1; falta o resto) — Fase 6 item 4
- Limites de perda semanal/mensal (diário + circuit breaker já existem desde US2) — Fase 6 item 5

## 006 — Evolução da estratégia (parcial)

- Sozinho: Bollinger adaptativo, regime detection via ADX, detecção de volatilidade elevada, nova
  `strategy/breakout.py`, comando de comparativo entre estratégias/presets — tudo testável via
  backtest com dados públicos
- Precisa do operador: "Validar preset operacional atual" exige rodar em paper mode por um período
  real, não só backtest — a parte de backtest eu faço, a validação em paper depende de tempo
  passando com o bot rodando

## 007 — Observabilidade operacional / forward test (parcial)

- Sozinho: separar caixa/posições/patrimônio no `status`, contexto explícito no `edge`, painel
  local (`python main.py painel`), modo debug de sinal, gráficos de performance
- Precisa do operador: forward test formal e comparação paper-vs-backtest exigem histórico real de
  paper mode rodando por um período — não dá para gerar esse dado, só a ferramenta que o analisa

## 009 — Itens remanescentes do ROADMAP

Auditoria completa do `ROADMAP.md` (não só deste arquivo) revelou 4 itens pequenos, genuinamente
não implementados, que não tinham entrado no backlog original:

- Exportação de relatórios de backtest/scan/multibacktest/optimize em `reports/` (Fase 1 item 4)
- Diagnóstico de perfil "agressivo" complementando o "defensivo" já existente (Fase 1.1 item 4)
- Out-of-sample no relatório de edge via `edge --validate` (Fase 1.1 item 7)
- Indicadores médios por sinal em `python main.py decisions` (Fase 3 item 4)

Também corrigiu um item já entregue pela spec 004 (edge anualizado/retorno por exposição, Fase 1.1
item 6) que tinha ficado sem marcar por engano no `ROADMAP.md`.

## 010 — Paridade de custos entre paper e backtest

Achado crítico de uma auditoria completa do projeto (código + pesquisa de boas práticas de bots de
trading retail, não só releitura do `ROADMAP.md`): `execution/order_manager.py`
`_paper_buy()`/`_paper_sell()` calculavam custo/proceeds sem aplicar `BACKTEST_FEE_RATE`/
`BACKTEST_SLIPPAGE_PCT`, já usados em todo `backtesting/engine.py`. O bot em paper mode (rodando
na VPS desde 2026-08-16, coletando os dados que vão validar a estratégia) registrava PnL
sistematicamente ~0,3%/round-trip mais otimista que a realidade — capaz de inverter o sinal de
trades marginais.

- Slippage no preço de entrada/saída, inclusive em saídas por stop/take (não só por sinal) — US1
- Taxa sobre o valor nocional de entrada/saída, saldo insuficiente considera custo total — US2
- `_live_buy`/`_live_sell` intocados — execução real já paga custo real
- Paridade verificada em percentual (`pnl_pct`) contra `simulate_backtest()`, não em dólar
  absoluto — as duas funções usam convenções de sizing diferentes (nocional fixo no backtest,
  quantidade fixa no paper) que produzem o mesmo `pnl_pct` mas não o mesmo `pnl` em dólar

## 011 — Singleton de exchange + retry de rate limit

`data/fetcher.py` `get_exchange()` instanciava um `ccxt.binance` novo a cada chamada, zerando o
rate-limiter interno do ccxt — sem proteção real contra limite de taxa da Binance. Risco
operacional direto pro deploy de 26 pares na VPS (vários chamadas por ciclo de 60s).

- `get_exchange()` cacheia uma instância por modo (`sandbox`/produção), com `reset_exchange_cache()`
  explícito para testes — US1
- Retry com backoff curto (3 tentativas) especificamente para `ccxt.RateLimitExceeded`/
  `ccxt.DDoSProtection` (HTTP 429/418) nas 4 funções públicas de `data/fetcher.py`; qualquer outro
  erro propaga sem retry — US2
- Escopo ampliado durante a especificação: `backtesting/scanner.py` também instanciava
  `ccxt.binance` direto (`get_top_pairs()`, e `_get_volume()` dentro de um loop por par, pior que
  o problema original) — corrigido para reusar `get_exchange()`/`fetch_ticker()`, mesma causa
  raiz, mesmo tamanho de mudança

## Ordem sugerida

Executada: 002 → 003 → 004 → 005 → 006 (parte sozinho) → 007 (parte sozinho) → 009 → 010 → 011
→ 013 → 016 → 017 → 018 → 019 → 020

Próximas, se e quando fizer sentido: **021** (é a que tem efeito real — um par inválido hoje passa
silenciosamente no backtest e nunca opera) → 012 (metade restante) → 022 → 014.

**Status (2026-08-24)**: 001-005, 008-011, 013 e 016-020 concluídas. 006 e 007 seguem com a parte
autônoma concluída — resta o que depende do operador: "validar preset operacional atual" (006,
Fase 4 item 1), forward test formal e comparação paper-vs-backtest (007, Fase 5 itens 1 e 4).
Continuam exigindo tempo real de operação paper.

**Pendentes**: 012 (metade — profundidade de liquidez próxima ao preço), 014 (refresh de pares
dinâmicos, baixa urgência), 021 (`MIN_PRICE_USDT` ausente no backtest) e 022 (relógio real no
replay, baixa prioridade). 015 fica fora da fila até o resto amadurecer.

### O que mudou desde 2026-08-16 e por quê importa

As entregas 016-020 não vieram do backlog original: saíram de auditorias sucessivas motivadas por
resultado ruim em operação real. Duas delas (**019** e **020**) são de natureza diferente das
demais e vale registrar o padrão:

- Não eram bugs — cada arquivo estava correto isoladamente. Eram **dois pontos do sistema
  discordando sobre qual é a estratégia**: backtest sem trailing stop enquanto a produção usava
  trailing; replay olhando o futuro no MTF enquanto a produção olha o presente.
- Nenhum teste pegava isso, porque nenhum teste comparava backtest contra produção.
- O sintoma estava nos dados o tempo todo: três trades reais fecharam por "Stop Loss" **com
  lucro** (impossível sob stop fixo). **Quando o resultado real contém algo que o modelo não
  consegue produzir, o modelo está errado — não o dado.**

Consequência prática: **toda decisão de par e parâmetro tomada antes de 2026-08-24 saiu de uma
régua quebrada**, incluindo vereditos de `compare`/`scan`/`optimize`/`edge`. Os pares adicionados
com base nela (DOGE, ZEC, ADA, UNI) foram removidos de `PAIRS`. Optou-se deliberadamente por
**não** recortar a lista para os pares que agora aprovam — selecionar pares pelo desempenho no
mesmo histórico que os avalia é viés de seleção, e trocaria um erro metodológico por outro.

### O que continua sem resposta

Nenhuma dessas correções torna a estratégia lucrativa, e é importante que o backlog não sugira o
contrário. Com a régua corrigida, o quadro **piorou**: profit factor mediano caiu de 0,69 para
0,60 e o paper mode segue negativo. A conclusão medida de quatro formas independentes (paper real,
scan de 30 pares, grid de 648 combinações, literatura acadêmica em `docs/research/`) é que
cruzamento EMA/RSI não tem vantagem preditiva em cripto. As correções tornaram os números
**verdadeiros**, não melhores — e o valor disso é evitar decidir com dado maquiado.
