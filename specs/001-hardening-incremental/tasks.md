---

description: "Task list for 001-hardening-incremental"
---

# Tasks: Hardening Incremental do Bot de Daytrade

**Input**: Design documents from `/specs/001-hardening-incremental/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/cli.md](./contracts/cli.md)

**Tests**: Incluídos — a constitution (III. Test Before Implement) exige critério de teste definido
antes de cada implementação.

**Organization**: Tarefas agrupadas por User Story (US1/US2/US3, ver `spec.md`) para permitir
implementação e validação independentes de cada uma.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependência)
- **[Story]**: A qual User Story a tarefa pertence (US1, US2, US3)
- Caminhos de arquivo reais do repositório incluídos em cada descrição

## Path Conventions

Projeto único na raiz do repositório (não é `src/`/`frontend`/`backend`) — ver `plan.md` → Project
Structure para o mapeamento completo de módulos existentes.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar o ambiente de desenvolvimento e a base de lint, sem tocar lógica de trading.

- [x] T001 Instalar Python 3.12 e criar `.venv` no ambiente de desenvolvimento (não havia Python
      instalado na máquina de desenvolvimento)
- [x] T002 Instalar dependências de `requirements.txt` na `.venv` e corrigir gap encontrado: `rich`
      era usado em 6 arquivos mas não estava listado — commit `fix: adicionar dependencia rich
      faltante no requirements.txt`
- [x] T003 [P] Configurar `ruff` em `pyproject.toml` (regras E, F, B; E501 ignorada por ora) e
      corrigir lint básico (imports não usados, dead code trivial, `zip(..., strict=True)`) — commit
      `chore: configurar ruff e corrigir lint basico`. Achado no processo: `backtesting/scanner.py`
      calculava uma cor de tabela e nunca aplicava — corrigido em commit separado
      (`fix: aplicar cor no titulo da tabela do relatorio de scan`)

**Checkpoint**: Ambiente pronto, lint básico limpo.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Rede de segurança (type-check, cobertura, CI) que deve existir antes de mexer em
`risk/manager.py` e `execution/order_manager.py` nas User Stories seguintes.

**⚠️ CRITICAL**: Nenhuma tarefa de US1/US2/US3 que toque `risk/` ou `execution/` deve começar antes
de T007 (CI) estar concluída.

- [x] T004 Configurar `mypy` em `pyproject.toml` escopado em `risk/manager.py` e
      `execution/order_manager.py` (`check_untyped_defs=true`, `ignore_missing_imports=true`) —
      commit `chore: configurar mypy para risk manager e order manager`
- [x] T005 Configurar `pytest-cov` e registrar baseline de cobertura (66% geral, 93% em
      `risk/manager.py`, 36% em `execution/order_manager.py`) em `ROADMAP.md` — commit
      `chore: adicionar pytest-cov e registrar baseline de cobertura`
- [x] T006 [P] Instalar e validar `pre-commit` (`.pre-commit-config.yaml` com hooks de ruff --fix,
      mypy nos módulos críticos e pytest): `pre-commit install` + `pre-commit run --all-files`
      passando, documentado no `README.md`. Achado no processo: `pytest` rodado direto (sem
      `python -m`) quebrava por import error (`ModuleNotFoundError`) — corrigido com
      `[tool.pytest.ini_options] pythonpath = ["."]` em `pyproject.toml`
- [x] T007 Criar `.github/workflows/ci.yml`: jobs `lint` (ruff) → `typecheck` (mypy) → `test`
      (pytest), rodando em `push`/`pull_request` para `main`

**Checkpoint**: Foundational concluída — CI configurada, pre-commit funcionando localmente. Phase 3
(User Story 1) pode começar em uma próxima sessão.

---

## Phase 3: User Story 1 - Ordens nunca duplicam nem ficam fora de sincronia (Priority: P1) 🎯 MVP

**Goal**: Toda ordem tem `clientOrderId` único; `state.json` é reconciliado contra a conta real na
Binance na inicialização e periodicamente, com alerta (não correção automática) em caso de
divergência.

**Independent Test**: Ver `quickstart.md` → US1.

### Tests for User Story 1 ⚠️

> Escrever estes testes primeiro; devem falhar antes da implementação.

- [x] T008 [P] [US1] Teste: `clientOrderId` único gerado e persistido por ordem (paper e live) em
      `tests/test_order_manager_safety.py`
- [x] T009 [P] [US1] Teste: reconciliação detecta divergência entre `state.json` e conta real
      (mockada) em `tests/test_reconciliation.py` (novo arquivo)
- [x] T010 [P] [US1] Teste: reconciliação não roda quando `TRADING_MODE=paper` em
      `tests/test_reconciliation.py`

### Implementation for User Story 1

- [x] T011 [US1] Gerar e persistir `client_order_id` em toda ordem criada em
      `execution/order_manager.py` (`_generate_client_order_id()`; paper e live, passado à Binance
      via `params={"newClientOrderId": ...}`)
- [x] T012 [US1] Persistir `client_order_id` no registro de trade fechado em `data/trade_store.py`
      (novo campo em `TRADE_HEADERS`)
- [x] T013 [US1] Implementar `execution/reconciliation.py` — compara posições locais (`state.json`)
      com saldo real via `ccxt fetch_balance()` (não `fetch_positions`: Binance Spot não tem conceito
      de "position", só saldo do ativo base), retorna `ReconciliationResult` `ok`/`mismatch` com
      tolerância de 1% para taxas/arredondamento
- [x] T014 [US1] Chamar reconciliação na inicialização do bot em `trading/runner.py` (`_run_reconciliation`,
      que já é um no-op em paper mode via `reconcile()` retornando `None`)
- [x] T015 [US1] Chamar reconciliação periódica dentro do loop existente de 60s em
      `trading/runner.py` — a cada `RECONCILIATION_INTERVAL_CYCLES=30` ciclos (~30min)
- [x] T016 [US1] Evento `reconciliation_mismatch` (e `reconciliation_error` para falha de API) em
      `utils/logger.py` (JSONL) e alerta em `utils/notifier.py` (Telegram) via `_run_reconciliation`;
      último resultado persistido em `OrderManager.last_reconciliation` (`record_reconciliation`)
- [x] T017 [US1] Exibir resultado da última reconciliação em `python main.py status`
      (`cmd_status` em `main.py`, só quando `TRADING_MODE=live`)

**Checkpoint**: US1 completa e testável de forma independente — gap P6 da constitution fechado.
47 testes passando, ruff/mypy limpos.

`/code-review high` rodado antes do commit encontrou 4 problemas reais, todos corrigidos antes de
comitar:
1. `_live_sell` apagava a posição local mesmo quando a venda falhava — corrigido: só remove a
   posição no caminho de sucesso; erro mantém a posição local e alerta via Telegram.
2. `reconcile()` só detectava posição local sem saldo real, não o inverso (saldo real sem posição
   local) — corrigido: novo parâmetro `tracked_symbols` checa os dois sentidos, limitado aos pares
   que o bot acompanha (evita alertar sobre outros ativos da mesma conta).
3. `ensure_csv` não migrava o cabeçalho de um CSV já existente ao adicionar `client_order_id` —
   corrigido de forma genérica em `data/csv_utils.py` (afeta trades/signals/decisions).
4. Chamada de reconciliação na inicialização não estava protegida por `try/except` como a
   periódica — corrigido: todo o corpo de `_run_reconciliation` agora está dentro do try.

Segunda rodada de `/code-review high` (sobre o commit já com os 4 fixes acima) encontrou mais 8
problemas — 6 corrigidos, 2 avaliados e deliberadamente não corrigidos (justificativa abaixo):

5. `handle_open_position` (`trading/position_lifecycle.py`) reportava a posição como fechada (linha
   da tabela, cooldown, trade_event com PnL calculado) mesmo quando `close_position` falha
   silenciosamente e mantém a posição — corrigido: agora checa `manager.has_position(symbol)` depois
   de chamar `close_position`, no mesmo padrão já usado em `handle_entry_candidate`.
6. `_live_sell`: `del`/`_persist_state()` estavam dentro do mesmo `try` que `log_event`/
   `send_telegram`, então uma falha *depois* da venda ter sido aceita pela exchange (ex: disco cheio
   ao gravar o JSONL) caía no `except` escrito para "a venda falhou", reportando erro falso e
   mantendo a posição local por engano — corrigido: a posição só é removida no caminho de sucesso da
   chamada à exchange; falhas de log/persistência depois disso são isoladas em try/except próprios
   que não reescrevem o resultado da venda.
7. `_generate_client_order_id()` gerava um ID novo a cada tentativa de venda, inclusive em retry
   após timeout — isso anulava o propósito de idempotência (a Binance só reconhece um retry como
   "a mesma ordem" se o `clientOrderId` for igual). Corrigido: novo campo
   `Position.pending_close_client_order_id`, gerado uma vez e persistido; reusado em toda tentativa
   de fechar a mesma posição até ela fechar de verdade.
8. `_run_reconciliation`: o `except` nunca chamava `record_reconciliation`, então uma falha
   persistente de reconciliação (ex: API key perdeu permissão) deixava `python main.py status`
   mostrando o último resultado "ok" antigo, escondendo que a reconciliação estava falhando —
   corrigido: falha agora grava `status="error"` com a mensagem do erro.
9. `DUST_THRESHOLD_PCT` era uma quantidade absoluta (0.0001 unidades) aplicada igual a qualquer
   ativo, apesar do nome sugerir percentual — muito permissivo para ativos caros, ruidoso para
   baratos. Corrigido: `DUST_THRESHOLD_USDT` compara valor em USDT via `fetch_ticker`; se o preço não
   puder ser obtido, trata como não-dust (prefere falso positivo a esconder divergência real).
10. `float(totals.get(base, 0.0))` quebrava com `TypeError` se a Binance retornasse `None` para um
    ativo — corrigido para `float(totals.get(base) or 0.0)` nos dois sentidos da checagem.
11. `_migrate_header` (`data/csv_utils.py`) truncava e reescrevia o CSV sem atomicidade — um crash no
    meio da escrita podia perder meses de histórico de trades. Corrigido: escreve em `.tmp` e troca
    com `os.replace` (atômico).
12. `ensure_csv` passou a abrir e ler a primeira linha do arquivo a cada chamada, mesmo com o
    cabeçalho já correto — chamado a cada ciclo por par via `decision_store`/`signal_store`.
    Corrigido: cache em memória (`_verified_paths`) evita reabrir o arquivo após a primeira
    confirmação no processo.

Não corrigidos (avaliados e descartados conscientemente):
- `record_reconciliation` reserializa o `state.json` inteiro a cada reconciliação (a cada ~30min) só
  para persistir 3 campos — I/O desprezível para o volume de dados deste bot (poucas posições,
  arquivo de poucos KB); resolver isso agora seria otimização prematura.
- US1 inteira foi entregue em um commit só, contrariando o Fluxo Incremental do `CLAUDE.md` — válido
  como observação de processo, mas não é algo para "corrigir" no código (reescrever o histórico já
  publicado seria mais arriscado que o problema). Fica como aprendizado para as próximas User
  Stories: commits menores por sub-tópico, revisão antes do push final da story.

Antes da 3ª rodada, passei pelas lentes de arquitetura/segurança/QA/governança de spec (não só
correção): achei 2 gaps de teste — nada garantia que `reconcile()` nunca muda `manager.positions`
(FR-003) nem que uma divergência real dispara `send_telegram`/`log_event` no nível do runner
(SC-002). Testes adicionados (`test_reconcile_never_mutates_local_positions`,
`test_run_reconciliation_alerts_on_mismatch`).

Terceira rodada de `/code-review high` (sobre os fixes da 2ª rodada) encontrou mais 3 problemas — 2
corrigidos, 1 avaliado e descartado:

13. `_estimate_value_usdt` retornava `0.0` (não o `inf` documentado) quando `fetch_ticker` tinha
    sucesso mas devolvia `last=None` (par ilíquido, sem trade recente) — `float(None or 0.0)` vira
    zero, então um saldo real virava "dust" por omissão. Corrigido: `None`/preço ausente agora conta
    como "preço indisponível" (→ `inf`), igual a uma exceção.
14. Depois de uma venda live confirmada, se `_persist_state()` falhasse (I/O), o erro só era
    logado — um restart nesse intervalo ressuscitaria a posição já vendida a partir do
    `state.json` desatualizado, e a próxima tentativa de fechar reusaria o
    `pending_close_client_order_id` já consumido, que a Binance rejeitaria como duplicata (posição
    "presa" até a reconciliação periódica pegar, ~30min). Corrigido com
    `_persist_state_with_retry`: uma tentativa extra antes de desistir. Não elimina o risco por
    completo (só reduz a janela) — a reconciliação continua sendo a rede de segurança final para o
    pior caso, e isso está documentado no código.

Não corrigido (avaliado e descartado):
- `_estimate_value_usdt` faz uma chamada de rede (`fetch_ticker`) por símbolo rastreado sem posição
  local durante a reconciliação — só acontece no caminho raro (saldo órfão sem posição local, que é
  exatamente o cenário anômalo que a reconciliação existe para detectar) e roda a cada ~30min, não a
  cada ciclo — mesma categoria de trade-off do item de `record_reconciliation` acima.

61 testes passando (5 novos desde a rodada 2), ruff/mypy limpos.

Quarta rodada de `/code-review high` encontrou mais 2 problemas, os dois corrigidos:

15. **Gap pré-existente, não introduzido por esta feature, mas no escopo direto dela**: `_live_sell`
    nunca chamava `log_trade` nem atualizava `realized_pnl`/`daily_pnl`/`total_trades`/
    `winning_trades` (diferente de `_paper_sell`, que sempre fez isso). Resultado: em modo live, o
    circuit breaker de `DAILY_DRAWDOWN_LIMIT` nunca disparava de verdade, e `data/trades.csv` nunca
    tinha registro de trade live nenhum. Corrigido: `_live_sell` agora calcula PnL (preço de saída do
    fill da ordem, com fallback para `current_price` e depois `entry_price`), atualiza os mesmos
    contadores que o caminho paper, e chama `log_trade`. `close_position` agora repassa
    `current_price` para `_live_sell` (antes só ia para `_paper_sell`).
16. **Regressão introduzida por mim na rodada 2**: o cache `_verified_paths` de `ensure_csv` (pensado
    para evitar reabrir o arquivo em toda chamada) fazia com que um CSV apagado/truncado por fora
    (rotação de log, crash) no meio da vida do processo nunca mais recuperasse o cabeçalho —
    `log_trade`/`log_signal` passavam a escrever linhas cruas num arquivo sem header. Corrigido:
    revertido o cache por completo. O custo de I/O que ele evitava (abrir e ler uma linha por
    ciclo/par) é desprezível perto do risco de corromper o histórico de trades silenciosamente —
    decisão consciente de preferir correção a uma otimização pequena.

62 testes passando (1 novo desde a rodada 3), ruff/mypy limpos.

Quinta rodada de `/code-review high` encontrou mais 4 problemas — 2 corrigidos, 2 avaliados e
descartados:

17. A geração do `pending_close_client_order_id` (primeira tentativa de venda) chamava
    `self._persist_state()` direto, sem try/except, ao contrário do resto do método já protegido.
    Corrigido: usa `_persist_state_with_retry` como o resto de `_live_sell`.
18. O ajuste de trailing stop em `trading/position_lifecycle.py` chamava `manager._persist_state()`
    direto, sem proteção — uma falha ali abortava o ciclo inteiro daquele símbolo antes mesmo dos
    checks de SL/TP rodarem, driblando toda a blindagem adicionada nesta mesma função (achado #5).
    Corrigido: usa `manager._persist_state_with_retry(...)`.

Não corrigidos (avaliados e descartados):
- Se `create_market_sell_order` gerar timeout depois da Binance já ter aceitado a ordem, o retry
  reusa o mesmo `client_order_id` e a Binance rejeita como duplicata — essa rejeição hoje é tratada
  igual a uma falha genérica, entao o bot re-alerta a cada ciclo (~60s) ate a reconciliacao periodica
  (ate 30 ciclos, ~30min) detectar e sinalizar a divergencia. O jeito "certo" de resolver isso de
  verdade seria consultar o status real da ordem na exchange (`fetch_order`/`fetch_my_trades`) antes
  de decidir se foi de fato erro ou duplicata — isso e uma feature de verificacao de status de ordem
  bem maior que o escopo desta spec (idempotencia + reconciliacao), nao um ajuste pontual. Fica
  registrado como candidato a item de ROADMAP; o pior caso (posicao "presa" ate 30min, sem risco
  financeiro pois o ativo ja foi vendido de verdade) continua coberto pela reconciliacao.
- `_estimate_value_usdt` chama `fetch_ticker` por símbolo sem posição local durante a reconciliação —
  o review citou o "~5s por chamada completa" do `CLAUDE.md` como risco de travar o loop, mas esse
  número é especificamente sobre `fetch_ohlcv` com 100 candles (endpoint pesado), não sobre
  `fetch_ticker` (endpoint leve, resposta de um único objeto). Mantida a decisão das rodadas 3/4:
  caminho raro (só quando há saldo órfão sem posição local) e pouco frequente (a cada ~30min).

65 testes passando (3 novos desde a rodada 4), ruff/mypy limpos.

Sexta rodada de `/code-review high` encontrou mais 2 problemas, os dois corrigidos:

19. `data/state_store.py` `save_state()` não era atômico (`open(..., "w")` trunca antes de escrever)
    — inconsistente com o fix já aplicado em `data/csv_utils.py`, e `state.json` é ainda mais crítico
    (posições abertas, cooldowns, `pending_close_client_order_id`). Se as duas tentativas de
    `_persist_state_with_retry` falhassem no meio da escrita, o bot subiria com um `state.json`
    corrompido/vazio e travaria no próximo start (`json.JSONDecodeError` não tratado) — pior que o
    problema que o retry tentava mitigar. Corrigido: mesmo padrão `.tmp` + `os.replace`.
20. Em `_live_sell`, `log_trade`/`log_event`/`send_telegram` (pós-venda confirmada) estavam no mesmo
    `try/except` — uma falha na primeira chamada (`log_trade`) pulava as outras duas, apesar de serem
    ações de observabilidade independentes. Corrigido: cada uma isolada no seu próprio try/except.

67 testes passando (2 novos desde a rodada 5), ruff/mypy limpos.

Sétima rodada de `/code-review high` encontrou mais 5 problemas — 4 corrigidos, 1 é o próprio
processo de revisão (endereçado abaixo, fora do código):

21. `_paper_sell` tinha exatamente o mesmo problema já corrigido em `_live_sell` na rodada 6
    (achado #20): contadores (`total_trades`, `realized_pnl`, `daily_pnl`) incrementados antes de
    `log_trade`/`log_event`/telegram, sem isolamento — se uma dessas chamadas falhasse, a exceção
    subia sem tratamento (`_paper_sell` não tinha try/except nenhum), a posição nunca era removida, e
    o próximo ciclo contabilizaria o mesmo trade de novo. Corrigido com o mesmo padrão: posição
    removida e persistida antes do log, cada ação de observabilidade isolada no seu try/except.
22. Em `_run_reconciliation`, `record_reconciliation` era chamado *antes* do alerta de divergência —
    se a persistência falhasse durante uma divergência real, o alerta (`log_event`/`send_telegram`
    com os diffs de verdade) nunca rodava, e o `except` só registrava `status="error"` perdendo os
    diffs originais. Corrigido: alerta primeiro (cada passo isolado), persistência por último,
    também isolada.
23. Padrão de escrita atômica (`.tmp` + `os.replace`) estava duplicado entre `data/csv_utils.py` e
    `data/state_store.py`. Extraído para `data/atomic_io.py` (`atomic_write`), usado pelos dois. Bônus
    encontrado escrevendo o teste do próprio helper: a versão original deixava o `.tmp` para trás se
    `write_fn` falhasse no meio — corrigido para limpar o `.tmp` nesse caso.
24. Os 3 ramos de fechamento em `handle_open_position` (stop loss/take profit/sinal de venda)
    repetiam a mesma sequência `close_position` → checar `has_position` → atualizar `row`/
    `trade_events` quase palavra por palavra — risco real de um ajuste futuro esquecer um dos três
    ramos (o review usou a palavra "quase" porque isso já quase aconteceu). Extraído para
    `_attempt_close`, uma função só, parametrizada pela regra de cooldown de cada caso.
25. **Processo, não código**: o review apontou (de novo) que o trabalho acumulado das rodadas 2-7
    inteiras seguia sem commit — reincidência do achado #9 da rodada 2. Resolvido logo abaixo: commit
    do acumulado antes de continuar para a rodada 8, e a partir da User Story 2 os commits acontecem
    por sub-tópico dentro da própria story, não só ao final dela.

Commitado (`f00d0cb`) e enviado ao `origin/main` antes de continuar. 79 testes, ruff/mypy limpos.

Oitava rodada de `/code-review high` (sobre o commit `f00d0cb`) encontrou mais 10 problemas — a
essa altura, o próprio review usou o histórico deste `tasks.md` para diferenciar achados novos de
riscos já aceitos conscientemente, o que ajudou a manter o foco. 8 corrigidos, 2 avaliados e
descartados:

26. **O mais grave**: `_live_buy` gerava um `client_order_id` novo a cada chamada — o mesmo problema
    já corrigido em `_live_sell` na rodada 3 (achado #7), só que no lado da compra. Um timeout depois
    da Binance já ter aceitado a ordem faria o próximo ciclo comprar de novo com um ID novo: uma
    segunda ordem de compra de verdade, capital duplicado. Corrigido com o mesmo padrão do lado da
    venda: novo `OrderManager.pending_open_client_order_ids` (dict por symbol, já que ainda não existe
    `Position` para guardar o campo antes da compra confirmar), persistido e reusado até a compra
    confirmar ou falhar definitivamente.
27. `_live_buy` também tinha o mesmo problema do achado #6 (rodada 6): chamada à exchange, criação da
    `Position`, persistência e log/alerta tudo no mesmo `try/except` — uma falha de persistência
    depois de uma compra bem-sucedida virava "Erro ao comprar" falso. Corrigido com o mesmo padrão de
    `_live_sell`/`_paper_sell`: posição criada e persistida (com retry) antes do log, log/alerta
    isolados em try/except próprios.
28. `_paper_buy` chamava `self._persist_state()` direto, sem retry nem isolamento do log/alerta —
    mesma classe de gap já fechada em `_paper_sell`, `_live_sell` e `_live_buy`. Corrigido.
29. `record_reconciliation` ainda chamava `self._persist_state()` (sem retry), inconsistente com o
    padrão já aplicado em todo outro ponto de persistência crítica. Corrigido para usar
    `_persist_state_with_retry`.
30. `load_state()` não tinha tratamento para `state.json` corrompido — um `json.JSONDecodeError` não
    tratado derrubava a inicialização do bot sem explicação. Mas retornar `{}` silenciosamente (como
    se não houvesse estado) seria pior: esconderia posições abertas de verdade. Corrigido para
    levantar um erro claro e acionável, sem inicializar com estado vazio.
31. `atomic_write`: o `os.replace` final estava *fora* do try/except de limpeza do `.tmp` — se o
    próprio `replace` falhasse (achado relevante porque este repositório vive numa pasta sincronizada
    pelo OneDrive, que pode segurar um arquivo brevemente durante upload), o `.tmp` ficava para trás.
    Corrigido: `replace` agora dentro do mesmo try/except.
32. Em `_live_sell`, o `log_trade` gravava `client_order_id=pos.client_order_id` (o ID da ordem de
    COMPRA que abriu a posição) enquanto o `log_event` do mesmo fechamento usava o ID da ordem de
    VENDA (`pending_close_client_order_id`) — dois valores diferentes sob o mesmo nome de campo,
    dificultando rastrear um fechamento específico. Corrigido: nova coluna `close_client_order_id`
    em `TRADE_HEADERS`, `client_order_id` continua sendo sempre o ID de abertura.
33. `_attempt_close` (`trading/position_lifecycle.py`) usava `manager.paper_balance_usdt`
    incondicionalmente no "saldo após o trade" exibido, mesmo em modo live (onde esse campo nunca é
    atualizado e fica travado no valor simulado padrão) — diferente de `handle_entry_candidate`, que
    já bifurca por `TRADING_MODE`. Corrigido com a mesma bifurcação.

Não corrigidos (avaliados e descartados):
- `_attempt_close` calcula pnl/pnl_pct a partir de `current_price` (estimativa no momento do sinal),
  não do preço de execução real que `_live_sell` usa internamente para `log_trade`/contadores — em
  modo live, slippage pode fazer a decisão de cooldown e o valor exibido no terminal discordarem do
  que fica gravado em `trades.csv`. Esse cálculo (`position_pnl`) já existia antes desta spec e não
  foi alterado por nenhum dos meus commits — é um comportamento pré-existente, não introduzido nem
  agravado por esta feature. Fica como candidato a item de `ROADMAP.md` (unificar o cálculo de PnL
  entre estimativa de sinal e preço de execução real, paper e live), fora do escopo de "idempotência +
  reconciliação" desta spec.
- `_estimate_value_usdt` chamando `fetch_ticker` por símbolo sem posição local, sequencial, dentro da
  reconciliação síncrona — terceira vez que esse ponto é levantado (rodadas 3, 5 e agora 8). Decisão
  final mantida: caminho raro (só quando há saldo órfão sem posição local — o cenário anômalo que a
  reconciliação existe para detectar) e pouco frequente (a cada ~30min, não a cada ciclo). Registrado
  aqui para não ser reaberto sem uma mudança real de contexto (ex: se `tracked_symbols` crescer muito
  ou a reconciliação passar a rodar com mais frequência).

79 testes passando (7 novos desde o commit `f00d0cb`), ruff/mypy limpos.

Commitado (`ce4d5a1`) e enviado ao `origin/main` antes de continuar.

Nona rodada de `/code-review high` (sobre o commit `ce4d5a1`) encontrou mais 7 problemas — 6
corrigidos, 1 avaliado e descartado. A essa altura o review já cruzava achados novos com o histórico
de decisões deste `tasks.md`, o que ajudou a não reabrir pontos já resolvidos.

34. `_live_buy` tinha o mesmo problema do achado #2 (rodada 6): o ramo de **erro** (chamada à
    exchange falhou) tinha `log_event`/`send_telegram` no mesmo bloco lógico sem isolamento entre
    si — igual no `_live_sell`. Como esse tipo de gap já tinha se repetido 3 vezes em métodos
    diferentes (achados #2, #20, #21, #27), extraí um helper `_safe_step(prefixo, fn)` e apliquei
    nos 4 métodos (`_paper_buy`, `_paper_sell`, `_live_buy`, `_live_sell`), sucesso e erro, ~12
    pontos de chamada — resolve este achado e o achado #7 da mesma rodada (duplicação do padrão
    try/except) ao mesmo tempo.
35. Achado pelo próprio `ruff` ao aplicar o `_safe_step`: usar a variável `e` de
    `except Exception as e:` dentro de uma lambda é um anti-padrão real — Python remove `e` do
    escopo ao sair do bloco `except` (para evitar ciclo de referência com o traceback). Como as
    lambdas rodam de forma síncrona all `_safe_step` (antes do `e` sumir), não haveria bug em
    runtime aqui, mas o `ruff` marcou `F821` corretamente como código frágil. Corrigido: captura
    `str(e)` numa variável local antes de construir as lambdas.
36. `_persist_state_with_retry` tentava de novo sem nenhuma pausa entre tentativas — se o motivo for
    um lock transitório (ex: o cliente de sincronização do OneDrive segurando o arquivo, achado #31
    da rodada 8), duas tentativas em sequência imediata têm quase a mesma chance de falhar que uma
    só. Adicionado `time.sleep(0.2)` entre tentativas.
37. `_attempt_close` exibia `manager.paper_balance_usdt` ou, em live, o resultado de
    `_get_usdt_balance()` — que retorna `0.0` em caso de falha ao buscar o saldo real. Isso é seguro
    para dimensionar uma nova ordem (`handle_entry_candidate`, onde "saldo desconhecido" e "saldo
    zero" levam à mesma decisão conservadora), mas era enganoso para *exibir*: um trade fechado com
    sucesso podia aparecer com "saldo $0,00" só porque a chamada de rede subsequente falhou.
    Corrigido: novo `_current_balance(manager)` retorna `None` (não `0.0`) quando o saldo real não
    pode ser obtido; `utils/display.py` `trade_result` passou a aceitar `None` e mostrar
    "indisponível" em vez de formatar como dinheiro.
38. A lógica de bifurcar saldo por `TRADING_MODE` estava duplicada entre `handle_entry_candidate` e
    `_attempt_close` — unificada em `_current_balance`, usado pelos dois (com `or 0.0` em
    `handle_entry_candidate`, onde um fallback numérico é a escolha certa).

Não corrigidos (avaliados e descartados):
- `_persist_state_with_retry` ainda pode esgotar as duas tentativas e nunca persistir — nesse caso
  (falha dupla + crash antes de qualquer persistência futura bem-sucedida), o `pending_open_client_order_ids`/
  `pending_close_client_order_id` recém-gerado pode se perder, e um restart geraria um ID novo,
  reabrindo o risco que esse mecanismo existe para fechar. Isso é uma limitação inerente a qualquer
  retry com número finito de tentativas — não existe fix que elimine o risco por completo sem
  persistência garantida (fora do alcance de um `state.json` em disco local). A reconciliação
  periódica continua sendo a rede de segurança final para esse caso, como já documentado desde a
  rodada 5.
- **Processo, de novo**: terceira vez que o review aponta granularidade de commit (rodadas 2, 7, 9).
  A partir daqui, a política adotada é: um commit por rodada de review (o que já vinha acontecendo
  desde a rodada 8), não um commit por achado individual — dividir mais que isso não é proporcional
  para correções descobertas em conjunto na mesma revisão. Não reabrir este ponto salvo mudança real
  de contexto.

83 testes passando (4 novos desde o commit `ce4d5a1`), ruff/mypy limpos.

Commitado (`a247176`) e enviado ao `origin/main` antes de continuar.

Décima rodada de `/code-review high` (sobre o commit `a247176`) encontrou mais 7 problemas — os
achados começaram a ficar mais sutis/de menor severidade, sinal de que a implementação está
convergindo. 5 corrigidos, 2 avaliados e descartados:

39. **O mais grave**: `available = (_current_balance(manager) or 0.0) / slots_left` em
    `handle_entry_candidate` reintroduzia exatamente o problema que o achado #37 (rodada 9) tinha
    corrigido em `_attempt_close` — saldo desconhecido virava `0.0` silenciosamente, e uma ordem de
    **quantidade zero de verdade** seguia para `calculate_risk` → `_live_buy` →
    `create_market_buy_order(symbol, 0.0, ...)`, uma chamada real à Binance fadada a ser rejeitada
    (filtro MIN_NOTIONAL/LOT_SIZE), gastando uma tentativa de `pending_open_client_order_ids` e
    escondendo a causa real (saldo indisponível) atrás de um "erro ao comprar" genérico. Corrigido:
    saldo desconhecido agora vira um bloqueio explícito (`"saldo indisponivel"`) antes de calcular
    `available`, no mesmo lugar que os outros bloqueios (`sem slot`, `cooldown`, etc.) — e só busca o
    saldo se nenhum bloqueio mais barato já descartou a entrada, preservando o short-circuit
    original.
40. `_run_reconciliation` (`trading/runner.py`) ainda reimplementava à mão o mesmo padrão que
    `_safe_step` foi criado para substituir em `execution/order_manager.py`, na rodada anterior.
    Extraído `safe_step(logger, prefixo, fn)` para `utils/logger.py` (módulo compartilhado, já que
    `_safe_step` era privado de `order_manager.py`), usado agora pelos dois módulos.
41. O trio `msg = ...` / `def _notify(): ...` / `_safe_step(...)` estava duplicado nos 4 métodos de
    ordem, mesmo já existindo o `_safe_step`. Extraído `_notify_safe(prefix, msg)` em
    `execution/order_manager.py`, reduzindo cada ponto de chamada a uma linha.
42. `handle_entry_candidate` não tinha nenhum teste (nem antes nem depois desta spec) — o gap que
    permitiu o achado #39 passar despercebido. Adicionados testes cobrindo bloqueio por saldo
    desconhecido e abertura normal com saldo conhecido.
43. Só existia teste de isolamento do ramo de erro (achado #34, rodada 9) para `_live_sell`, não para
    `_live_buy`, apesar do fix ter sido aplicado aos dois. Adicionado o teste espelhado.

Não corrigidos (avaliados e descartados):
- `time.sleep(0.2)` dentro do retry de `_persist_state_with_retry` bloqueia a thread única do bot
  durante uma falha de persistência. Pior caso realista: todas as `MAX_POSITIONS=5` posições
  falhando persistência no mesmo ciclo, ~1 segundo de atraso total dentro de um orçamento de 60s por
  ciclo — desprezível, e o sleep existe justamente para servir o propósito do retry (achado #36,
  rodada 9). Mantido.
- `_current_balance` faz uma chamada de rede (`fetch_balance`) não cacheada por chamada, podendo
  somar algumas chamadas no mesmo ciclo (um fechamento + uma abertura, por exemplo). Mesma categoria
  de trade-off já aceito para `_estimate_value_usdt`/`fetch_ticker` na reconciliação (rodadas 3, 5,
  8): custo de rede real, mas baixo e dentro do orçamento de 60s por ciclo — não justifica uma
  camada de cache só para isso no escopo desta spec.

86 testes passando (3 novos desde o commit `a247176`), ruff/mypy limpos.

Commitado (`3a36fc3`) e enviado ao `origin/main` antes de continuar.

Décima primeira rodada de `/code-review high` (sobre o commit `3a36fc3`) encontrou só 3 problemas —
o review explicitamente relatou que **nenhum bug de correção sobreviveu ao escrutínio** desta vez,
sinal de convergência. 2 corrigidos, 1 é observação de processo (não código):

44. A correção do achado #39 (rodada anterior) buscava o saldo *antes* do MTF, invertendo a ordem
    original (MTF antes do saldo) e gastando uma chamada de rede extra sempre que o MTF já bloqueava
    a entrada. Corrigido: saldo volta a ser checado só depois do MTF passar, preservando o
    short-circuit original — e adicionado teste garantindo que o saldo não é buscado quando o MTF
    bloqueia.
45. `_safe_step` em `execution/order_manager.py` tinha virado um wrapper de uma linha só chamando
    `utils.logger.safe_step` — sobra da extração da rodada 10. Removido; todos os ~11 pontos de
    chamada agora usam `safe_step(log, ...)` direto.

Não corrigido (observação de processo, não código):
- O título do commit da rodada 10 tinha 76 caracteres, acima do limite de 72 do `CLAUDE.md`. Não dá
  para reescrever um commit já publicado sem risco desproporcional ao problema (mensagem de commit).
  Cuidado redobrado com o tamanho do título a partir daqui.

87 testes passando (1 novo desde o commit `3a36fc3`), ruff/mypy limpos.

Commitado (`d430abe`) e enviado ao `origin/main`.

Décima segunda rodada de `/code-review high` encontrou só 1 problema: um comentário mencionando
`_safe_step` (removido na rodada anterior). Corrigido — trocado por `safe_step`.

87 testes passando, ruff/mypy limpos.

**Status da User Story 1**: 12 rodadas de `/code-review high`, ~45 achados corrigidos, curva de
achados por rodada caindo de forma consistente (4 → 8 → 3 → 2 → 4 → 8 → 7 → 5 → 4 → 2 → 1) até
"nenhum bug de correção sobrevive ao escrutínio" nas duas últimas rodadas.

**Rodada 13 (confirmação final, sobre o commit `83886bb`): 0 achados.** O review reportou
explicitamente que não há mais superfície de lógica nova para revisar. **User Story 1 aprovada.**

---

## Phase 4: User Story 2 - Circuit breaker além do limite diário de drawdown (Priority: P2)

**Goal**: Bot suspende novas entradas após N perdas consecutivas configuráveis; operador pode
suspender/retomar novas entradas manualmente via CLI a qualquer momento.

**Independent Test**: Ver `quickstart.md` → US2.

### Tests for User Story 2 ⚠️

- [x] T018 [P] [US2] Teste: `consecutive_losses` incrementa em trade com prejuízo e reseta em trade
      com lucro (`tests/test_order_manager_safety.py` — ver nota de design abaixo, não
      `tests/test_risk_manager.py`)
- [x] T019 [P] [US2] Teste: `circuit_breaker_active` vira `true` ao atingir `MAX_CONSECUTIVE_LOSSES`
      e bloqueia novas entradas (`tests/test_order_manager_safety.py` + `tests/test_position_lifecycle.py`)
- [x] T020 [P] [US2] Teste: `killswitch_active` bloqueia novas entradas e persiste entre reinícios
      simulados (`tests/test_killswitch_store.py` novo + `tests/test_position_lifecycle.py`)

### Implementation for User Story 2

Nota de design (desvio de `research.md`): o contador de perdas seguidas (`consecutive_losses`,
`circuit_breaker_active`) ficou dentro do `OrderManager`/`state.json`, mas o **kill switch NÃO** —
ficou num arquivo próprio (`data/killswitch.json`, novo `data/killswitch_store.py`). Motivo: o
`OrderManager` reescreve `state.json` inteiro a cada `_persist_state()` (a cada trade, ajuste de
trailing stop, etc.); se `killswitch_active` morasse lá, uma escrita normal do bot **enquanto
rodando** sobrescreveria de volta o flag ativado externamente pelo comando `python main.py kill`
rodado em outro processo — um risco real de corrida que `research.md` não tinha considerado (a
razão registrada lá para rejeitar um arquivo separado foi só "evitar mais uma fonte de estado",
sem essa análise). `python main.py status` já mostra os dois estados juntos, então a divisão em
dois arquivos não perde visibilidade.

- [x] T021 [US2] `MAX_CONSECUTIVE_LOSSES` em `config/settings.py` (default 3), validação em
      `validate_config()`
- [x] T022 [US2] Campos `consecutive_losses` e `circuit_breaker_active` persistidos via
      `OrderManager`/`state.json` (não em `data/state_store.py` diretamente — mesmo padrão de
      `total_trades`/`realized_pnl`, que também não vivem em `state_store.py`)
- [x] T023 [US2] `OrderManager._update_consecutive_losses(pnl)`, chamado por `_paper_sell` e
      `_live_sell` ao fechar um trade — contador GLOBAL (não por par), consistente com
      `MAX_ENTRIES_PER_CYCLE=1` já tratar entradas como recurso compartilhado
- [x] T024 [US2] `handle_entry_candidate` (`trading/position_lifecycle.py`) bloqueia com
      `"circuit breaker"` quando `manager.circuit_breaker_active`
- [x] T025 [US2] `data/killswitch_store.py` novo (`load_killswitch`/`save_killswitch`, escrita
      atômica via `data/atomic_io.py`) — não em `data/state_store.py` (ver nota de design acima)
- [x] T026 [US2] Subcomandos `kill`/`resume` em `main.py`, seguindo `contracts/cli.md`
- [x] T027 [US2] `trading/runner.py` lê `load_killswitch()` do disco uma vez por ciclo (não guarda em
      memória — precisa refletir uma ativação externa no próximo ciclo, não só num restart) e passa
      para `handle_entry_candidate`, que bloqueia com `"kill switch"`
- [x] T028 [US2] Eventos `circuit_breaker_triggered` (em `OrderManager`) e `killswitch_toggled` (em
      `main.py`), ambos via `safe_step` (JSONL + Telegram, isolados um do outro)

**Checkpoint**: US1 e US2 funcionam de forma independente uma da outra. 100 testes passando,
ruff/mypy limpos.

Primeira rodada de `/code-review high` (sobre o commit `c0f68ac`) encontrou 1 problema, corrigido:

46. `_update_consecutive_losses` (`execution/order_manager.py`) tratava um trade fechado com
    `pnl == 0` (breakeven, ex: saída por sinal de venda exatamente no preço de entrada) como vitória
    — o `else` do `if pnl < 0` cobria `pnl >= 0`, resetando `consecutive_losses` e
    `circuit_breaker_active` — contradizendo `data-model.md` (linha 31: reset só em `pnl > 0`).
    Isso permitia burlar o circuit breaker: uma sequência de perdas intercalada com trades de
    breakeven nunca acumulava o contador até `MAX_CONSECUTIVE_LOSSES`. Corrigido: `else` trocado por
    `elif pnl > 0`; `pnl == 0` agora não altera o contador nem o estado do circuit breaker. Teste
    `test_consecutive_losses_unaffected_by_breakeven_trade` adicionado — nenhum teste existente
    cobria `pnl == 0`.

101 testes passando (1 novo), ruff/mypy limpos.

**Status da User Story 2**: 1 rodada de `/code-review high`, 1 achado corrigido. **User Story 2
aprovada.**

---

## Phase 5: User Story 3 - Validação de estratégia fora da amostra (Priority: P3)

**Goal**: Relatório de backtest mostra métricas separadas para a janela de treino/otimização e para
a janela de validação out-of-sample, com veredito de aprovação automática baseado só na validação.

**Independent Test**: Ver `quickstart.md` → US3.

### Tests for User Story 3 ⚠️

- [ ] T029 [P] [US3] Teste: split treino/validação divide o histórico em janelas contíguas e não
      sobrepostas em `tests/test_backtesting_engine.py`
- [ ] T030 [P] [US3] Teste: critérios de aprovação automática (retorno > buy-hold, profit factor >
      1.2, drawdown aceitável, nº mínimo de trades) avaliados sobre `validation_metrics`, não
      `train_metrics`, em `tests/test_backtesting_engine.py`

### Implementation for User Story 3

- [ ] T031 [US3] Função de split treino/validação sobre o DataFrame de candles em
      `backtesting/engine.py` (ou novo `backtesting/validation.py` se o escopo justificar um arquivo
      separado — decisão na hora da implementação) (depende de T029 falhando)
- [ ] T032 [US3] Formalizar função de aprovação automática (já esboçada como item do `ROADMAP.md`
      Fase 1) aplicada à janela de validação (depende de T030 falhando, T031)
- [ ] T033 [US3] Exibir métricas in-sample vs out-of-sample lado a lado no relatório de backtest
      (`backtesting/engine.py` / `utils/display.py`) (depende de T031, T032)

**Checkpoint**: US1, US2 e US3 funcionam de forma independente.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentação e checklist de go-live — não altera comportamento do bot.

- [ ] T034 [P] Atualizar `ROADMAP.md` marcando os itens de reconciliação/circuit breaker/split
      treino-teste como concluídos, com link para esta spec
- [ ] T035 [P] Atualizar `STRATEGY_REVIEW.md` com o primeiro resultado real de validação
      out-of-sample rodado
- [ ] T036 Sincronizar `CLAUDE.md` e `AGENTS.md` no mesmo commit: novos comandos `kill`/`resume`,
      variável `MAX_CONSECUTIVE_LOSSES`, comportamento de reconciliação
- [ ] T037 Checklist de go-live antes de qualquer uso em `TRADING_MODE=live` desta feature:
      confirmar API key sem permissão de saque, rodar em paper mode por período mínimo definido pelo
      usuário, testar kill switch manualmente, documentar processo de rollback (`git revert` +
      restaurar backup de `state.json`)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências — CONCLUÍDA.
- **Foundational (Phase 2)**: Depende de Setup — BLOQUEIA todas as User Stories. T006/T007 ainda
  pendentes.
- **User Stories (Phase 3+)**: Todas dependem de Foundational completa.
  - US1 (P1) primeiro — é o MVP desta spec (gap P6 da constitution).
  - US2 (P2) e US3 (P3) são independentes entre si e de US1; podem seguir em paralelo ou em ordem de
    prioridade (P1 → P2 → P3), conforme `CLAUDE.md` prefere fatias pequenas e sequenciais.
- **Polish (Phase 6)**: Depende das User Stories que forem concluídas.

### User Story Dependencies

- **US1 (P1)**: Pode começar após Foundational. Sem dependência de US2/US3.
- **US2 (P2)**: Pode começar após Foundational. Sem dependência de US1/US3 (usa `state.json`, mas
  campos diferentes dos de US1 — sem conflito de merge esperado se implementadas em commits
  separados).
- **US3 (P3)**: Pode começar após Foundational. Sem dependência de US1/US2 (só toca
  `backtesting/engine.py`).

### Within Each User Story

- Testes MUST ser escritos e falhar antes da implementação (constitution III).
- Dentro de US1: T011/T012 (order manager) antes de T013 (reconciliação) fazer sentido de ponta a
  ponta, mas T013 não depende tecnicamente de T011/T012 — podem ser feitas em qualquer ordem.
- Dentro de US2: contador de perdas (T021-T024) e kill switch (T025-T027) são independentes entre
  si; T028 (eventos) depende de ambos existirem.
- Dentro de US3: T031 antes de T032 antes de T033 (cada uma depende da anterior).

### Parallel Opportunities

- T008, T009, T010 (testes de US1) podem ser escritos em paralelo — arquivos diferentes.
- T018, T019, T020 (testes de US2) podem ser escritos em paralelo.
- T029, T030 (testes de US3) podem ser escritos em paralelo.
- T034, T035 (Polish) podem rodar em paralelo.
- Seguindo o Fluxo Incremental do `CLAUDE.md`, mesmo com oportunidades de paralelismo, este projeto
  é mantido por uma pessoa — a prática real é sequencial, tópico por tópico, commit por commit.

---

## Implementation Strategy

### MVP First (User Story 1)

1. Completar Phase 1: Setup — CONCLUÍDA.
2. Completar Phase 2: Foundational (T006, T007 pendentes) — CRÍTICO, bloqueia tudo abaixo.
3. Completar Phase 3: User Story 1 (idempotência + reconciliação).
4. Validar US1 isoladamente em paper mode (`quickstart.md` → US1) antes de seguir.

### Incremental Delivery

1. Setup + Foundational → base pronta.
2. US1 → validar → é o MVP desta spec (fecha o gap P6 da constitution).
3. US2 → validar → circuit breaker mais completo.
4. US3 → validar → validação de estratégia mais rigorosa.
5. Polish → documentação e checklist de go-live.

Cada etapa segue o Fluxo Incremental do `CLAUDE.md`: tarefa pequena → testes → commit Conventional
Commit em português → push para `origin/main` → próxima tarefa.

---

## Notes

- [P] = arquivos diferentes, sem dependência.
- [Story] mapeia a tarefa à User Story correspondente, para rastreabilidade.
- Verificar que os testes falham antes de implementar (constitution III).
- Commit após cada tarefa ou grupo lógico pequeno — nunca uma User Story inteira em um commit só.
- Nenhuma tarefa desta lista habilita `TRADING_MODE=live` automaticamente — isso é sempre uma
  decisão manual do operador, após o checklist de T037.
