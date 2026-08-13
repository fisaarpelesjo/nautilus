<!--
Sync Impact Report
- Version change: (none) -> 1.0.0
- Modified principles: n/a (primeira ratificacao)
- Added principles: I. Safety First, II. No Secrets in Code, III. Test Before Implement,
  IV. Incremental Delivery, V. Observability Mandatory, VI. Idempotency and Reconciliation,
  VII. Explain Before Code
- Added sections: Restricoes Tecnicas e de Seguranca, Development Workflow, Governance
- Removed sections: n/a
- Templates requiring updates: .specify/templates/plan-template.md (OK, generico),
  .specify/templates/spec-template.md (OK, generico),
  .specify/templates/tasks-template.md (OK, generico)
- Follow-up TODOs: nenhum
-->

# binance-daytrade-bot Constitution

## Core Principles

### I. Safety First
Nenhuma mudanca em `risk/manager.py`, `execution/order_manager.py` ou
`trading/position_lifecycle.py` vai para `TRADING_MODE=live` sem antes rodar em paper
mode e, quando aplicavel, Binance Testnet. `TRADING_MODE=live` MUST exigir
`LIVE_TRADING_CONFIRMATION` explicito em `config/settings.py` — esse guard-rail nao
pode ser removido nem contornado. Rationale: e um bot pessoal de dinheiro real; um bug
silencioso em execucao pode causar perda financeira direta e sem supervisao 24/7.

### II. No Secrets in Code
`BINANCE_API_KEY`/`SECRET` e `TELEGRAM_*` MUST viver somente em `.env` (ja listado em
`.gitignore`). Nenhum commit pode incluir um `.env` real ou uma chave/API secret em
texto plano. `.env.example` MUST permanecer sem valores reais. Rationale: vazamento de
chave de API da Binance, mesmo sem permissao de saque, expoe estrategia e permissoes de
trading a terceiros.

### III. Test Before Implement
Cada task de um `tasks.md` MUST ter um criterio de teste definido antes da
implementacao. O projeto ja mantem uma suite `pytest` em `tests/` — toda task nova
MUST estender essa suite, nao recomecar uma paralela. Rationale: um bot que decide
sozinho quando comprar/vender nao pode depender de validacao manual "no olho" a cada
mudanca.

### IV. Incremental Delivery
Toda mudanca nao trivial MUST seguir o Fluxo Incremental do `CLAUDE.md`: topico
pequeno → rodar os testes relevantes → commit em Conventional Commit (portugues) →
push para `origin/main` → so entao proximo topico. MUST NOT existir uma reescrita
grande entregue em um unico commit. Rationale: reduz o raio de explosao de qualquer
regressao e mantem o bot sempre em um estado que pode rodar.

### V. Observability Mandatory
O projeto ja grava eventos estruturados em `logs/events-YYYY-MM-DD.jsonl` e decisoes
por ciclo em `data/decisions.csv`. Toda nova decisao de risco (kill switch, circuit
breaker, rejeicao de ordem) MUST gerar evento nesse mesmo pipeline — MUST NOT
introduzir um sistema de logging paralelo. Rationale: um segundo pipeline de log
fragmenta a auditoria exatamente onde ela mais importa (decisoes de risco).

### VI. Idempotency and Reconciliation
Toda ordem enviada a exchange MUST usar um `clientOrderId` unico, e o estado local
(`state.json`) MUST ser reconciliado periodicamente contra a conta real na Binance.
Gap real confirmado em 2026-08-13: `execution/order_manager.py` ainda nao implementa
nenhum dos dois. Ate ser fechado, este e o item de maior prioridade de qualquer plano
de hardening. Rationale: sem idempotencia e reconciliacao, um retry de rede pode
duplicar uma ordem, e um drift entre bot e exchange pode passar despercebido.

### VII. Explain Before Code
Antes de implementar uma task complexa (risk engine, order executor), o design
escolhido e o porque MUST ser resumido em 3-5 linhas e documentado no commit
correspondente antes de prosseguir para o codigo. Rationale: mudancas em modulos que
mexem com dinheiro real precisam de uma decisao explicita e revisavel, nao uma
implementacao silenciosa.

## Restricoes Tecnicas e de Seguranca

O bot opera exclusivamente Binance Spot, somente posicoes long (`max_leverage = 1`);
Futures/alavancagem estao fora de escopo ate decisao explicita em contrario. Chaves de
API da Binance MUST ter apenas permissao de leitura e trading spot — MUST NOT habilitar
saque. Uso e pessoal/single-account; nao ha requisito de multi-usuario. Persistencia
continua em CSV/JSON (`data/*.csv`, `state.json`) enquanto o volume de dados nao
justificar um banco — ver `specs/001-hardening-incremental/spec.yml` para o registro
dessa decisao e seu criterio de revisao.

## Development Workflow

Todo trabalho no repositorio segue metodologia SDD (Spec-Driven Development): specify
→ plan → tasks → implement, nessa ordem, por fase/feature. Cada iniciativa grande vira
uma pasta propria em `specs/<NNN>-<slug>/` com `spec.yml`/`spec.md`, `plan.md` e
`tasks.md`. Nenhum codigo de implementacao MUST ser escrito sem antes existir um
`tasks.md` para a fase atual cobrindo aquela mudanca. Sempre que uma pergunta em aberto
(`open_questions`) for bloqueante para a fase atual, o trabalho MUST parar e perguntar
ao usuario em vez de assumir. CLAUDE.md e AGENTS.md MUST permanecer sincronizados —
qualquer alteracao em um MUST ser replicada no outro no mesmo commit.

## Governance

Esta constitution tem precedencia sobre qualquer atalho de implementacao ou
preferencia individual de estilo dentro deste repositorio. Emendas exigem: (1) o
principio ou secao alterada documentado com a razao da mudanca, (2) incremento de
versao seguindo semver (MAJOR para remocao/redefinicao incompativel de principio,
MINOR para novo principio/secao, PATCH para clarificacao redacional), e (3) commit
dedicado (`docs: amend constitution to vX.Y.Z ...`) separado de qualquer mudanca de
codigo. Toda spec nova sob `specs/` MUST ser compativel com os principios aqui
definidos; um conflito detectado durante `/speckit-analyze` (ou revisao manual
equivalente) bloqueia a fase de `implement` ate ser resolvido.

**Version**: 1.0.0 | **Ratified**: 2026-08-13 | **Last Amended**: 2026-08-13
