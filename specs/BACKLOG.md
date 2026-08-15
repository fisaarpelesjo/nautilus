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
| 006 | Evolução da estratégia | Parcial | 🔲 Pendente |
| 007 | Observabilidade operacional / forward test | Parcial | 🔲 Pendente |
| 008 | Avançado (ML, multi-corretora) | Bloqueado | ⏸️ Fora da fila — ROADMAP.md já diz "só depois que validação/risco/operação estiverem maduros" |

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

## Ordem sugerida

002 → 003 → 004 → 005 → 006 (parte sozinho) → 007 (parte sozinho)

008 fica fora da fila até o resto amadurecer, conforme o próprio `ROADMAP.md` já recomenda.
