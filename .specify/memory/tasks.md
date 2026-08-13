# tasks.md — Tarefas SDD

Cada task é pequena, testável e vira um commit isolado (Fluxo Incremental do `CLAUDE.md`). Tasks da Fase 1 estão detalhadas por serem a fase atual; fases seguintes ficam em nível mais alto e são detalhadas quando começarem (per `claude_code_operating_instructions` do spec).

---

## Fase 1 — Foundation

- [ ] **T1.1 — Configurar ruff**
  - Criar `pyproject.toml` com seção `[tool.ruff]`, regras `E, F, B` (bugs/erros óbvios, sem formatação agressiva ainda).
  - Rodar `ruff check .` e corrigir só o que for trivial/seguro (imports não usados, etc.) — não refatorar lógica.
  - Teste: `ruff check .` sai limpo (ou com exceções documentadas via `# noqa` pontual).
  - Commit: `chore: configurar ruff e corrigir lint basico`

- [ ] **T1.2 — Configurar mypy nos módulos críticos**
  - Adicionar `[tool.mypy]` no `pyproject.toml`, escopo inicial `files = ["risk/manager.py", "execution/order_manager.py"]`.
  - Corrigir type errors encontrados (ou anotar tipos faltantes) só nesses dois arquivos.
  - Teste: `mypy risk/manager.py execution/order_manager.py` sai limpo.
  - Commit: `chore: configurar mypy para risk manager e order manager`

- [ ] **T1.3 — Configurar pytest-cov e registrar baseline**
  - Adicionar `pytest-cov` a `requirements-dev.txt` (novo arquivo, separado do `requirements.txt` de runtime).
  - Rodar `pytest --cov` e registrar o número atual de cobertura no `STRATEGY_REVIEW.md` (ou `ROADMAP.md`) como baseline — sem gate bloqueante ainda.
  - Teste: suíte pytest completa continua verde com `--cov` habilitado.
  - Commit: `chore: adicionar pytest-cov e registrar baseline de cobertura`

- [ ] **T1.4 — Configurar pre-commit**
  - Criar `.pre-commit-config.yaml` com hooks: ruff (lint+format), mypy (só nos 2 arquivos críticos), pytest -k unit (se houver marcação, senão pytest --co para smoke).
  - Documentar `pre-commit install` no README.
  - Teste: `pre-commit run --all-files` passa.
  - Commit: `chore: configurar pre-commit hooks`

- [ ] **T1.5 — CI no GitHub Actions**
  - Criar `.github/workflows/ci.yml`: jobs `lint` (ruff) → `typecheck` (mypy) → `test` (pytest), rodando em `push`/`pull_request` para `main`.
  - Teste: push de um commit trivial mostra os 3 jobs verdes no GitHub Actions.
  - Commit: `feat: adicionar CI com lint, type-check e testes`

**Acceptance da fase:** CI verde, pre-commit funcionando localmente, baseline de cobertura documentado. Nenhuma mudança de comportamento do bot.

---

## Fase 2 — Execution hardening (detalhar ao iniciar)

- [ ] T2.1 — clientOrderId único em toda ordem (paper + live), testes de unicidade/persistência
- [ ] T2.2 — Reconciliação na inicialização do bot (compara `state.json` vs conta real via ccxt), com teste simulando divergência
- [ ] T2.3 — Reconciliação periódica no loop do `runner.py`
- [ ] T2.4 — Circuit breaker de perdas consecutivas (`MAX_CONSECUTIVE_LOSSES` em `.env`), com teste de ativação/reset
- [ ] T2.5 — Kill switch manual (`python main.py kill` / `resume`), com teste de toggle e persistência

Cada uma validada em paper mode antes de passar para a próxima.

---

## Fase 3 — Observability extension (detalhar ao iniciar)

- [ ] T3.1 — Evento `reconciliation_mismatch` (JSONL + Telegram)
- [ ] T3.2 — Evento `circuit_breaker_triggered` (JSONL + Telegram)
- [ ] T3.3 — Evento `killswitch_toggled` (JSONL + Telegram)

---

## Fase 4 — Strategy validation hardening (detalhar ao iniciar)

- [ ] T4.1 — Split walk-forward/out-of-sample no `backtesting/engine.py`
- [ ] T4.2 — Relatório mostrando métricas in-sample vs out-of-sample lado a lado
- [ ] T4.3 — Função de aprovação automática (critérios do `ROADMAP.md` item 2) avaliada em out-of-sample

---

## Fase 5 — Persistence review (deferred, não gerar tasks agora)

## Fase 6 — Go-live checklist (processo, não código — ver `plan.md`)
