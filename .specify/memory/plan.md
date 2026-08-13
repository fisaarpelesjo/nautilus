# plan.md — Refatoração incremental do bot (SDD)

Derivado de `project-spec.yml` (`refactor_plan` + `architecture`). Cada fase é um PR/série de commits pequenos, seguindo o Fluxo Incremental do `CLAUDE.md`: tópico → testes → commit → push → próximo tópico.

---

## Fase 1 — Foundation (CI, lint, type-check)

**Objetivo:** dar rede de segurança para todas as fases seguintes, sem tocar em lógica de trading.

**Design:**
- `ruff` para lint + format, config em `pyproject.toml`. Regras iniciais conservadoras (não quebrar o código existente com regras estilísticas agressivas) — focar em bugs reais (F, E, B) primeiro, formatação depois.
- `mypy` só em `risk/manager.py` e `execution/order_manager.py` de início (módulos críticos de dinheiro real). Resto do projeto fica fora do type-check por ora — expandir depois é um custo baixo e incremental.
- `pytest-cov` para medir cobertura atual como baseline, sem gate de CI bloqueante no início (registrar o número, não quebrar build por ele).
- `pre-commit` com os hooks acima, para pegar problemas antes do commit.
- GitHub Actions: um único workflow `ci.yml` com 3 jobs sequenciais (lint → type-check → test), rodando em `push` e `pull_request` para `main`.

**Por que essa ordem:** lint é o mais barato de configurar e menos disruptivo; mypy escopado só nos módulos críticos evita uma enxurrada de erros em código legado que não vamos tocar agora; CI por último porque depende dos dois anteriores estarem estáveis localmente primeiro.

**Arquivos afetados:** `pyproject.toml` (novo), `.pre-commit-config.yaml` (novo), `.github/workflows/ci.yml` (novo), `requirements.txt` (adiciona ruff, mypy, pytest-cov, pre-commit como dev deps — ou `requirements-dev.txt` separado).

**Risco:** baixo — nada disso muda comportamento do bot, só tooling.

---

## Fase 2 — Execution hardening (P6 da constitution)

**Objetivo:** fechar o gap real de idempotência e reconciliação em `execution/order_manager.py`, e completar o circuit breaker.

**Design:**
1. **clientOrderId:** gerar um ID único por ordem (ex: prefixo curto + uuid4 truncado + timestamp) antes de chamar `create_order` via ccxt. Persistir esse ID junto com a ordem em `state.json`/`trade_store`. Em modo paper, simular o mesmo campo para manter paridade de código entre paper e live (evita bug que só aparece em live).
2. **Reconciliação:** função nova (ex: `execution/reconciliation.py` ou método em `order_manager.py`) chamada (a) na inicialização do bot e (b) periodicamente no loop do `runner.py` (ex: a cada N ciclos). Busca posições/ordens abertas reais via ccxt e compara com `state.json`. Divergência → loga evento estruturado + alerta Telegram, **não corrige automaticamente** (correção automática de dinheiro real é arriscada demais sem supervisão — isso vira decisão manual do usuário, documentada no alerta).
3. **Circuit breaker de perdas consecutivas:** novo contador em `state.json` (`consecutive_losses`), incrementado a cada stop loss fechado com prejuízo, resetado a cada trade positivo. Threshold configurável via `.env` (`MAX_CONSECUTIVE_LOSSES`, default sugerido 3 — a validar com o usuário durante a implementação, não hardcoded sem revisão). Ao atingir o threshold, suspende novas entradas (mesmo mecanismo que já existe para `DAILY_DRAWDOWN_LIMIT`).
4. **Kill switch manual:** novo subcomando `python main.py kill` que seta uma flag persistida (`state.json` ou arquivo separado tipo `data/killswitch.flag`) lida pelo `runner.py` a cada ciclo — se ativa, suspende novas entradas mas continua gerenciando posições abertas (fechar posições abertas à força é decisão separada, mais arriscada — fora de escopo deste subcomando). Subcomando `python main.py resume` para desativar.

**Por que reconciliação não corrige automaticamente:** um bug na lógica de correção automática poderia amplificar um problema já existente (ex: fechar posição que na verdade estava certa). Alertar e deixar decisão para o humano é mais seguro para um bot pessoal sem monitoramento 24/7.

**Arquivos afetados:** `execution/order_manager.py`, `trading/runner.py`, `risk/manager.py` (ou novo `risk/circuit_breaker.py`), `main.py` (novo subcomando), `config/settings.py` (nova var `MAX_CONSECUTIVE_LOSSES`), `data/state_store.py`.

**Risco:** médio-alto — toca módulos críticos. Cada sub-tarefa (clientOrderId, reconciliação, circuit breaker, kill switch) é um commit separado, testado isoladamente, validado em paper mode antes de considerar live.

---

## Fase 3 — Observability extension

**Objetivo:** os três novos comportamentos de risco (reconciliação com divergência, circuit breaker, kill switch) aparecem no mesmo pipeline de eventos que já existe — não um sistema novo.

**Design:** reusar `utils/logger.py` (eventos JSONL) e `utils/notifier.py` (Telegram). Definir 3 novos tipos de evento (`reconciliation_mismatch`, `circuit_breaker_triggered`, `killswitch_toggled`) seguindo o mesmo formato dos eventos existentes.

**Arquivos afetados:** `utils/logger.py`, `utils/notifier.py`, pontos de chamada em `execution/order_manager.py` / `trading/runner.py` / `main.py` criados na Fase 2.

**Risco:** baixo — é só instrumentação sobre código que a Fase 2 já criou.

---

## Fase 4 — Strategy validation hardening

**Objetivo:** walk-forward/out-of-sample sobre o motor de backtest existente (`backtesting/engine.py`), sem trocar de motor.

**Design:** dividir o período histórico em janelas (ex: 70% treino/otimização, 30% validação out-of-sample, ou walk-forward com múltiplas janelas rolantes). Rodar a estratégia (com parâmetros fixados na janela de treino, se vier do `optimize`) na janela de validação e reportar as métricas separadamente — a métrica que importa para aprovação é a de out-of-sample, não a de treino. Formalizar a função de aprovação automática já esboçada no `ROADMAP.md` (item 2 da Fase 1 do roadmap): retorno > buy-and-hold, profit factor > 1.2, drawdown aceitável, nº mínimo de trades — todos avaliados na janela out-of-sample.

**Arquivos afetados:** `backtesting/engine.py`, possivelmente novo `backtesting/validation.py`, `main.py` (se virar novo subcomando ou flag em `backtest`/`optimize`).

**Risco:** baixo — é aditivo ao backtest, não muda execução ao vivo.

---

## Fase 5 — Persistence review (deferred)

Não implementar agora. Só medir. Ver `project-spec.yml` para critério de quando revisitar.

---

## Fase 6 — Hardening & go-live checklist

**Objetivo:** checklist de segurança antes de qualquer mudança das Fases 2–4 rodar em `TRADING_MODE=live`.

**Design:** documento simples (pode virar seção do `STRATEGY_REVIEW.md` ou `ROADMAP.md`) com checklist manual: permissões da API key, período mínimo em paper mode, teste manual do kill switch, processo de rollback (`git revert` + restaurar `state.json` de backup). Não é código, é processo — aprovação final é do usuário, não automatizável.

---

## Ordem de execução

Fases 1 → 2 → 3 → 4 são sequenciais (cada uma depende da anterior estar estável). Fase 5 é condicional/adiada. Fase 6 é um checklist contínuo, revisitado sempre que Fase 2 gerar uma mudança candidata a live.
