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
| 012 | MTF fail-closed + profundidade de liquidez próxima ao preço | Sozinho | 🟡 Parcial — MTF fail-closed corrigido em 2026-08-18 (auditoria de código pós-deploy, fora de uma spec formal: `mtf_confirmed()` agora retorna `False` em erro de rede, igual ao resto de `position_lifecycle.py`); falta ainda a parte de profundidade de liquidez próxima ao preço (`execution/liquidity.py` soma os 20 níveis do order book, não só os próximos ao preço) |
| 013 | Risco de correlação entre posições simultâneas | Sozinho | 📋 Candidata — gap de pesquisa (não da auditoria de código): `MAX_POSITIONS` limita quantidade, não exposição correlacionada entre pares que se movem juntos |
| 014 | Refresh periódico de pares dinâmicos (`DYNAMIC_PAIRS_ENABLED`) | Sozinho | 📋 Candidata — baixa urgência (não é a config atual), mas relevante dado o padrão comprovado de VPS de longa duração |
| 015 | Avançado (ML, multi-corretora) | Bloqueado | ⏸️ Fora da fila — ROADMAP.md já diz "só depois que validação/risco/operação estiverem maduros" |

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

002 → 003 → 004 → 005 → 006 (parte sozinho) → 007 (parte sozinho) → 009 → 010 → 011

**Status (2026-08-16)**: 001-005, 008, 009, 010 e 011 concluídas. 006 e 007 com a parte autônoma
concluída — resta apenas o que depende do operador: "validar preset operacional atual" (006, Fase
4 item 1), forward test formal e comparação paper-vs-backtest (007, Fase 5 itens 1 e 4) — todos
exigem histórico real de operação paper rodando por um período. O bot está em operação paper
contínua desde 2026-08-16 (26 pares, VPS dedicada), agora com custo de execução realista (spec
010) e conexão resiliente a rate limit (spec 011) — essas duas pendências têm um relógio real
correndo, não são mais bloqueio indefinido.

012-014 são candidatas da mesma auditoria (ver tabela acima), ainda não especificadas em detalhe.
015 fica fora da fila até o resto amadurecer, conforme o próprio `ROADMAP.md` já recomenda.
