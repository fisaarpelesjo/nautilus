---

description: "Task list — camada de dados multi-mercado para pesquisa"
---

# Tasks: Camada de dados multi-mercado para pesquisa

**Input**: Design documents from `/specs/023-dados-multi-mercado/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/)

**Tests**: OBRIGATÓRIOS nesta feature. O Princípio III da Constituição deste projeto exige que cada task tenha critério de teste definido **antes** da implementação, estendendo a suíte `tests/` existente em vez de criar uma paralela.

**Organization**: agrupadas por história de usuário, na ordem de implementação definida em [plan.md](plan.md) — **US4 primeiro**, como rede de segurança, antes de introduzir a segunda fonte.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência)
- **[Story]**: a qual história pertence (US1, US2, US3, US4)
- Caminho de arquivo exato em cada descrição

## Path Conventions

Projeto de módulo único, com pacotes na raiz do repositório: `config/`, `data/`, `backtesting/`, `trading/`, `tests/`.

---

## Phase 1: Setup

**Purpose**: dependência nova disponível e declarada

- [X] T001 Adicionar `yfinance` a `requirements.txt`, mantendo a ordem alfabética/agrupamento já usado no arquivo
- [X] T002 Verificar que `pip install -r requirements.txt` instala limpo no venv e que `import yfinance` funciona

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: abstração de fonte e modelo de mercado, dos quais toda história depende

**⚠️ CRÍTICO**: nenhuma história pode começar antes desta fase terminar

**⚠️ ORDEM DELIBERADA**: T003 vem antes de T005-T007. O teste de não-regressão precisa existir e passar **contra o código atual** antes do refactor — senão ele vira teste escrito para o código novo, e deixa de provar equivalência. É a mitigação do risco técnico nº 1 de [research.md](research.md).

- [X] T003 Criar `tests/test_crypto_no_regression.py` com teste que fixa o comportamento ATUAL de `fetch_ohlcv` para cripto: formato do DataFrame (índice `DatetimeIndex` crescente sem duplicatas, colunas `open/high/low/close/volume` minúsculas), política de cache incremental (1ª chamada busca `limit`, seguintes buscam 5 e fazem merge) e propagação de exceção em falha. Rodar contra o código atual e confirmar que passa
- [X] T004 [P] Criar `tests/test_markets.py` com testes de resolução símbolo → mercado para os seis padrões de [data-model.md](data-model.md) (`/USDT`, `.SA`, `=X`, `=F`, `^`, alfanumérico), incluindo símbolo não resolvível falhando explicitamente
- [X] T005 Criar `data/markets.py` com `Market`, `CostProfile` e a função de resolução símbolo → mercado, satisfazendo T004. `tradable=True` apenas para `crypto`
- [ ] T006 [P] Criar `tests/test_sources.py` cobrindo o contrato de [contracts/data-source.md](contracts/data-source.md): normalização de coluna, ordenação do índice, exceção em símbolo inexistente / timeframe não suportado / zero candles, e detecção de `limit` não atendido
- [ ] T007 Criar `data/sources/__init__.py` com o protocolo de fonte e o registro que resolve mercado → fonte
- [ ] T008 Criar `data/sources/ccxt_source.py` movendo o código atual de `data/fetcher.py` **sem alterar lógica** — cache, singleton de exchange, retry de rate limit e `_to_df` idênticos
- [ ] T009 Reescrever `data/fetcher.py::fetch_ohlcv` para resolver o mercado do símbolo e delegar à fonte correspondente, **mantendo a assinatura** `(symbol, timeframe, limit)`. `fetch_ticker`/`fetch_tickers`/`fetch_balance`/`fetch_order_book` permanecem cripto-only e intocados
- [ ] T010 Rodar `tests/test_crypto_no_regression.py` novamente e confirmar que continua passando após o refactor — a prova de equivalência

**Checkpoint**: abstração pronta e cripto comprovadamente inalterado

---

## Phase 3: User Story 4 — Preservação do bot ao vivo (Priority: P1) 🎯 rede de segurança

**Goal**: garantir que nada desta feature altere o bot em operação, e que um símbolo sem execução não chegue ao loop.

**Independent Test**: rodar o ciclo de decisão com a configuração cripto atual e obter comportamento idêntico; configurar um símbolo não-cripto na lista de operação e ver a inicialização recusar.

- [ ] T011 [P] [US4] Adicionar a `tests/test_crypto_no_regression.py` um teste que roda o caminho de decisão de entrada com configuração cripto e compara a sequência de bloqueadores avaliados antes/depois — cobre FR-006
- [ ] T012 [US4] Adicionar a `tests/test_runner_live_banner.py` (ou arquivo novo `tests/test_runner_market_guard.py`) teste que exige recusa explícita na inicialização quando a lista de operação contém símbolo de mercado `tradable=False` — cobre FR-007
- [ ] T013 [US4] Implementar em `trading/runner.py` a verificação de inicialização que recusa símbolo de mercado sem execução, nomeando o símbolo e o motivo, satisfazendo T012

**Checkpoint**: bot ao vivo protegido e comprovadamente inalterado

---

## Phase 4: User Story 1 — Avaliar mercado novo (Priority: P1)

**Goal**: obter métricas completas de uma estratégia sobre símbolo de ações, forex, futuros ou índice, pelo mesmo motor e mesma régua do cripto.

**Independent Test**: `python main.py backtest AAPL` retorna relatório completo, comparável lado a lado com o de um par cripto.

- [ ] T014 [P] [US1] Adicionar a `tests/test_sources.py` testes da fonte não-cripto: normalização de `Open/High/Low/Close/Volume` → minúsculas, e recusa explícita de timeframe não suportado
- [ ] T015 [US1] Criar `data/sources/yfinance_source.py` implementando o protocolo de fonte, satisfazendo T014
- [ ] T016 [P] [US1] Adicionar a `tests/test_settings_validation.py` teste que confirma: símbolo não-cripto aceito na lista de **pesquisa**, e validação `/USDT` preservada na lista de **operação** — a distinção que impede o símbolo inoperável de chegar ao loop
- [ ] T017 [US1] Ajustar a validação em `config/settings.py` (~linha 147) conforme T016, sem afrouxar a proteção da lista de operação
- [ ] T018 [P] [US1] Adicionar a `tests/test_backtesting_engine.py` teste que confirma registro de `market` e `requested_candles` no resultado, e sinalização quando o obtido é menor que o pedido — cobre FR-011 e o risco técnico nº 3
- [ ] T019 [US1] Estender `BacktestResult` em `backtesting/engine.py` com `market`, `cost_profile_note`, `has_session_gaps` e `requested_candles`, todos com padrão que preserva o comportamento atual; preencher em `run_backtest()`, satisfazendo T018
- [ ] T020 [P] [US1] Adicionar teste que confirma o aviso de gap presente no resultado de mercado descontínuo e ausente em mercado contínuo — cobre FR-009
- [ ] T021 [US1] Implementar a sinalização de gap conforme T020, reusando `Market.continuous`

**Checkpoint**: US1 funcional — já responde a pergunta central da feature para um símbolo por vez

---

## Phase 5: User Story 2 — Custo por mercado (Priority: P1)

**Goal**: cada mercado avaliado com o seu próprio custo; mercado sem custo declarado é recusado.

**Independent Test**: o mesmo comportamento de preço em mercados de custo diferente produz resultado líquido pior no de custo maior; mercado sem perfil é recusado com motivo.

- [ ] T022 [P] [US2] Adicionar a `tests/test_markets.py` teste que confirma recusa explícita ao avaliar mercado sem `CostProfile` — MUST NOT cair no custo de cripto por omissão (FR-004)
- [ ] T023 [P] [US2] Adicionar teste que confirma que o mesmo cenário simulado sob dois perfis de custo produz resultado líquido pior no de custo maior (FR-003)
- [ ] T024 [US2] Definir os perfis de custo por mercado em `config/settings.py`, sobrescrevíveis por `.env`, com `source_note` registrando o que cada número aproxima (corretagem fixa → percentual equivalente)
- [ ] T025 [US2] Resolver `fee_rate`/`slippage_pct` por mercado em `backtesting/engine.py::run_backtest()` antes de chamar `simulate_backtest()`, e preencher `cost_profile_note` no resultado, satisfazendo T022 e T023

**Checkpoint**: nenhum resultado pode mais ser produzido com custo de mercado incorreto

---

## Phase 6: User Story 3 — Varredura multi-mercado (Priority: P2)

**Goal**: varrer estratégia × símbolo numa execução, com confirmação obrigatória fora da janela de busca.

**Independent Test**: `python main.py multimarket` produz tabela única ranqueada, onde nenhuma linha marcada `confirmado` tem janela de confirmação vazia.

- [ ] T026 [P] [US3] Criar `tests/test_multimarket.py` com teste que exige: combinação aprovada só na janela de busca recebe `so_na_busca` e NÃO é apresentada como aprovada (FR-014)
- [ ] T027 [P] [US3] Adicionar a `tests/test_multimarket.py` teste que exige `inconclusivo` quando o histórico é insuficiente para dividir as janelas — jamais aprovar por omissão de dado
- [ ] T028 [P] [US3] Adicionar a `tests/test_multimarket.py` teste que confirma `combinations_tested` registrado no resultado (FR-013)
- [ ] T029 [US3] Criar `backtesting/multimarket.py` com `MultiMarketScanResult` e `ScanEntry`, reusando `split_train_validation()` e `evaluate_approval()` existentes — sem critério de aprovação novo (decisão D3 de [research.md](research.md))
- [ ] T030 [US3] Implementar a varredura estratégia × símbolo em `backtesting/multimarket.py`, satisfazendo T026-T028, com símbolo que falha marcado como erro sem interromper os demais
- [ ] T031 [US3] Adicionar o comando `multimarket` a `main.py`, com a saída definida em [contracts/cli.md](contracts/cli.md): contagem em destaque, tabela ranqueada, status visualmente distinto, mercado e perfil de custo por linha
- [ ] T032 [US3] Integrar a exportação do resultado via `utils/report_export.py`, sem pipeline paralelo (Princípio V da Constituição)
- [ ] T033 [P] [US3] Estender `backtesting/compare.py` para aceitar lista multi-mercado, mantendo o comportamento atual quando recebe só cripto

**Checkpoint**: todas as histórias funcionais e independentes

---

## Phase 7: Polish & Cross-Cutting

- [ ] T034 [P] Atualizar `CLAUDE.md` e `AGENTS.md` (sincronizados no MESMO commit, conforme a Constituição) com: fontes de dados, mercados suportados, perfis de custo e o comando `multimarket`
- [ ] T035 [P] Atualizar `docs/07-configuracao.md` com as variáveis novas de perfil de custo
- [ ] T036 [P] Atualizar `docs/08-comandos-cli.md` com o comando `multimarket`
- [ ] T037 [P] Adicionar capítulo ou seção em `docs/` explicando a limitação de 730 dias da fonte não-cripto e por que o teto importa na comparação com cripto
- [ ] T038 Atualizar `specs/BACKLOG.md`: marcar 023 como concluída e registrar o que a varredura revelou
- [ ] T039 Executar todos os cenários de [quickstart.md](quickstart.md) e confirmar os resultados esperados
- [ ] T040 Rodar a suíte completa (`python -m pytest -q`) e confirmar que os 359 testes anteriores continuam passando, sem regressão

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências
- **Foundational (Phase 2)**: depende do Setup — **BLOQUEIA todas as histórias**
- **US4 (Phase 3)**: depende da Foundational. Deliberadamente primeira — é a rede de segurança
- **US1 (Phase 4)**: depende da Foundational e de US4 (a garantia de não-regressão precisa estar de pé antes de introduzir a segunda fonte)
- **US2 (Phase 5)**: depende de US1 (precisa de um mercado novo avaliável para aplicar custo diferente)
- **US3 (Phase 6)**: depende de US1 e US2 (varre mercados com custo correto)
- **Polish (Phase 7)**: depende das histórias desejadas

### Ordem crítica dentro da Foundational

T003 (teste de não-regressão) **antes** de T005-T009 (refactor), e T010 (reexecução) **depois**. Escrever o teste após o refactor o transformaria em teste do código novo, perdendo a capacidade de provar equivalência.

### Parallel Opportunities

- T004 e T006 em paralelo (arquivos de teste diferentes)
- T014, T016, T018, T020 em paralelo dentro de US1 (arquivos diferentes)
- T022 e T023 em paralelo dentro de US2
- T026, T027, T028 em paralelo dentro de US3
- T034-T037 em paralelo no Polish

---

## Implementation Strategy

### MVP

Phase 1 + Phase 2 + Phase 3 (US4) + Phase 4 (US1) já entregam a capacidade central: avaliar um símbolo não-cripto com o motor existente, sem risco para o bot em operação.

**Parar e validar aqui** é legítimo — responde a pergunta que motivou a feature para um símbolo por vez.

### Incremental

1. Setup + Foundational → abstração pronta, cripto provado intacto
2. US4 → bot ao vivo protegido
3. US1 → primeiro mercado novo avaliável **(MVP)**
4. US2 → custos corretos, resultados confiáveis
5. US3 → varredura em escala com guarda contra descoberta por acaso

### Notas

- Commit por task ou grupo lógico, em Conventional Commit português (Princípio IV)
- Confirmar que cada teste falha antes de implementar o que ele cobre (Princípio III)
- US2 é P1 junto com US1: entregar avaliação de mercado novo **sem** custo correto produziria números que parecem confiáveis e não são — o erro que já custou caro neste projeto com ACE/BIO/ALLO
