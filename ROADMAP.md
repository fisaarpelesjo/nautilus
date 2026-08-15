# Roadmap

Este roteiro organiza as proximas melhorias do bot por impacto na chance de lucro real e reducao de risco. A prioridade nao e adicionar mais sinais rapidamente; e criar um processo confiavel para provar se uma estrategia tem vantagem antes de considerar `TRADING_MODE=live`.

O projeto ja possui uma base importante: backtest com taxas e slippage, metricas como profit factor/drawdown/Sharpe, otimizador de parametros, analise de `data/trades.csv`, selecao dinamica de pares, blacklist, paper mode, persistencia de estado e limites basicos de risco. Os itens abaixo focam no que ainda falta para transformar esses recursos em um fluxo de validacao mais rigoroso.

## Principios de Execucao

- Cada item deve ser pequeno o suficiente para ter teste, commit e validacao propria.
- Mudancas de estrategia devem ser validadas primeiro em backtest, depois em paper mode, antes de qualquer uso em live.
- Qualquer funcionalidade que afete execucao real deve preservar `TRADING_MODE=paper` como padrao e exigir salvaguardas explicitas para live.
- Resultados de experimentos e decisoes sobre parametros devem ser registrados em `STRATEGY_REVIEW.md`.
- Runtime artifacts como CSVs locais, logs, cache, estado e relatorios gerados nao devem ser commitados.

## Fase 1 - Medir se a estrategia realmente vence alternativas simples

Objetivo: evitar otimizar no escuro. Antes de mexer muito na estrategia, o bot precisa responder se ele supera uma referencia simples como comprar e segurar o mesmo ativo.

1. [x] **Benchmark buy-and-hold no backtest**
   - Implementar retorno buy-and-hold por par e timeframe usando o mesmo periodo do backtest.
   - Exibir retorno da estrategia, retorno buy-and-hold, diferenca e vencedor.
   - Por que melhora: lucro isolado nao basta. Se a estrategia rende +5% enquanto buy-and-hold rende +25%, ela destruiu oportunidade apesar de parecer positiva.

2. [x] **Criterios automaticos de aprovacao**
   - Criar uma funcao de avaliacao que marque estrategia/par como aprovado, reprovado ou inconclusivo.
   - Criterios iniciais: retorno acima do buy-and-hold, profit factor > 1.2, expectativa positiva, drawdown maximo aceitavel e numero minimo de trades.
   - Por que melhora: reduz decisao subjetiva e evita escolher parametros por impressao visual ou por um unico backtest bom.
   - **Concluido** (`specs/002-multi-pair-approval`): `backtesting/approval.py`
     `evaluate_approval()` (generalizado de `evaluate_validation()`, spec 001 US3) aplicado em
     `edge`, `multibacktest` e `scan`, alem de `backtest --validate`.

3. [x] **Ranking de pares por qualidade**
   - Ordenar pares por profit factor, expectativa, drawdown, numero de trades, consistencia e diferenca contra buy-and-hold.
   - Integrar o ranking aos comandos de backtest multipar e scanner.
   - Por que melhora: em cripto, a estrategia pode funcionar em alguns ativos e falhar em outros. O ranking ajuda a escolher onde operar e onde bloquear.
   - **Concluido** (`specs/002-multi-pair-approval`): `backtesting/approval.py` `ranking_key()`
     reusa o `edge_score` (que ja combina esses criterios) para ordenar `multibacktest` e `scan`;
     amostra abaixo de `MIN_TRADES_FOR_RANKING=3` nunca domina o topo do ranking (achado de
     `/code-review high` — protecao que o `.score` ad hoc antigo do `scanner.py` tinha e a migracao
     inicial para `edge_score` quase perdeu).
   - Debito tecnico registrado (nao corrigido nesta spec, achado de `/code-review high`):
     `MultiResult` (`multi.py`) e `ScanResult` (`scanner.py`) sao dataclasses quase-duplicadas, com
     tratamento de erro que ja diverge entre os dois (linha de erro inline vs secao separada).
     Unificar ficaria fora do escopo desta spec — candidato para uma proxima iteracao de "Qualidade
     de Codigo".

4. [ ] **Exportacao de relatorios em `reports/`**
   - Salvar resultados de backtest, scan, otimizacao e analise nos formatos JSON, CSV e Markdown.
   - Incluir parametros usados, periodo testado, custos, slippage, metricas e ranking.
   - Por que melhora: cria historico auditavel. Sem relatorios versionados por execucao local, fica dificil comparar experimentos e evitar repetir testes.

## Fase 1.1 - Evoluir o relatorio de edge

Objetivo: transformar o `python main.py edge` de um painel de metricas em uma decisao operacional clara. O comando ja mostra retorno, expectativa, payoff, buy-and-hold, edge vs benchmark e score inicial; agora precisa explicar a qualidade desses numeros e onde eles devem ser usados.

1. [x] **Classificacao automatica do edge**
   - Mostrar status final como `APROVADO`, `REPROVADO` ou `INCONCLUSIVO`.
   - Usar criterios como minimo de trades, profit factor > 1.2, expectativa positiva, edge vs buy-and-hold positivo e drawdown aceitavel.
   - Por que melhora: evita interpretar numeros manualmente toda vez e reduz risco de operar uma estrategia que parece boa em uma metrica isolada.
   - **Concluido** (`specs/002-multi-pair-approval`): `python main.py edge` (antes um alias literal
     de `backtest`) agora mostra `VEREDITO: APROVADO/REPROVADO/INCONCLUSIVO` via
     `backtesting/validation.py` `run_edge_report()`.

2. [x] **Motivos da classificacao**
   - Exibir lista curta com os principais motivos do status.
   - Exemplo: `Reprovado: perdeu para buy-and-hold por -70.76%`, `Amostra baixa: 7 trades`, `Ponto positivo: drawdown baixo`.
   - Por que melhora: explica a decisao e mostra exatamente qual gargalo precisa ser atacado.
   - **Concluido** (`specs/002-multi-pair-approval`): `ApprovalVerdict.reasons` lista os motivos
     especificos (amostra, profit factor, drawdown, retorno vs buy-hold).

3. [x] **Alerta de amostra insuficiente**
   - Destacar quando o numero de trades for baixo demais para conclusao confiavel.
   - Comecar com minimo configuravel, por exemplo 30 trades.
   - Por que melhora: 5 ou 10 trades podem gerar profit factor alto por acaso. O relatorio precisa impedir conclusoes fortes com pouca evidencia.
   - **Concluido** (`specs/002-multi-pair-approval`): `EDGE_MIN_TRADES` configuravel via `.env`
     (default `10`, nao `30` como o exemplo original sugeria -- mesmo valor ja usado desde a spec
     001 para nao mudar comportamento default; ajustar para 30 e so trocar a variavel).

4. [ ] **Diagnostico defensivo vs agressivo**
   - Classificar casos em que a estrategia tem baixo drawdown e expectativa positiva, mas perde muito para buy-and-hold.
   - Exemplo: `Perfil defensivo: preservou capital, mas capturou pouco da alta`.
   - Por que melhora: diferencia uma estrategia ruim de uma estrategia conservadora que talvez sirva para mercados laterais ou de queda, mas nao para bull market.
   - **Parcial** (`specs/002-multi-pair-approval`): `backtesting/approval.py` `diagnose_profile()`
     implementa so o lado "defensivo" (o unico exemplo citado aqui). O lado "agressivo" (ex: alto
     drawdown mas retorno muito acima do buy-hold) nao foi escopado nesta spec.

5. [x] **Edge por par e timeframe**
   - Levar as metricas de edge para `multibacktest`, `scan` e selecao dinamica.
   - Mostrar quais pares/timeframes passam, falham ou ficam inconclusivos.
   - Por que melhora: um unico par pode enganar. A chance de lucro real depende de consistencia em varios ativos e janelas.
   - **Concluido para `multibacktest`/`scan`** (`specs/002-multi-pair-approval`): veredito + ranking
     por qualidade nos dois comandos. Selecao dinamica (`market/selector.py`) nao foi tocada nesta
     spec.

6. [ ] **Edge anualizado e retorno por exposicao**
   - Calcular retorno anualizado da estrategia, buy-and-hold anualizado e retorno por tempo exposto.
   - Por que melhora: uma estrategia exposta apenas 7% do tempo precisa ser julgada tambem pela eficiencia do capital, nao so pelo retorno bruto.

7. [ ] **Out-of-sample no relatorio de edge**
   - Mostrar edge separado entre periodo de treino e periodo de teste quando o backtest vier do otimizador ou de validacao walk-forward.
   - Por que melhora: edge em dados usados para escolher parametros pode ser overfitting. O dado fora da amostra e o que mais importa.

8. [x] **Refinar o `edge_score`**
   - Transformar o score atual em escala interpretavel, por exemplo 0-100 ou faixas `Forte`, `Medio`, `Fraco`, `Reprovado`.
   - Documentar pesos e penalidades: benchmark, profit factor, expectativa, drawdown, amostra e exposicao.
   - Por que melhora: o score atual e util como primeira heuristica, mas ainda nao e facil de comparar entre pares, timeframes e versoes da estrategia.
   - **Concluido** (`specs/002-multi-pair-approval`): `backtesting/engine.py` `edge_score_band()`
     mapeia o score para Forte/Medio/Fraco/Reprovado (limiares fixos, nao 0-100 normalizado --
     decisao documentada em `specs/002-multi-pair-approval/research.md`), exibido em
     `edge`/`multibacktest`/`scan`.

## Fase 2 - Reduzir overfitting

Objetivo: separar o que funcionou por vantagem real do que funcionou por ajuste excessivo ao passado.

1. [x] **Split treino/teste no otimizador**
   - Otimizar parametros em uma parte dos candles e validar o resultado em periodo posterior nao usado na escolha.
   - Mostrar metricas separadas de treino e teste.
   - Por que melhora: parametros podem parecer otimos porque foram escolhidos para aquele recorte historico. O teste fora da amostra mede se eles sobrevivem em dados novos.
   - **Concluido** (`specs/003-robust-optimization`): `python main.py optimize --validate` reusa
     `split_train_validation()` (spec 001) por simbolo, pontua/escolhe os candidatos so na fatia de
     treino, e reavalia os `top_n` (nao so o #1) contra a fatia de validacao -- lado a lado no
     relatorio. Simbolos sem historico suficiente entram em `validation_symbols_skipped`, sem
     distorcer a media dos demais. `optimize` sem flag continua identico.

2. [x] **Walk-forward validation**
   - Substituir ou complementar o split unico por janelas deslizantes com no minimo 3 periodos out-of-sample.
   - Agregar resultado medio e pior janela.
   - Por que melhora: mercado muda de regime. Uma unica divisao treino/teste pode esconder fragilidade em periodos laterais, quedas fortes ou euforia.
   - **Concluido** (`specs/003-robust-optimization`): `python main.py optimize --walk-forward`
     (implica `--validate`) avalia o conjunto de parametros JA ESCOLHIDO (nao reotimiza por janela --
     decisao documentada em `research.md`, evita overfitting por regime) em >=3 janelas deslizantes
     via `backtesting/robustness.py` `walk_forward_validate()`. Histórico insuficiente para o minimo
     de janelas é reportado explicitamente, nunca roda com menos janelas silenciosamente.

3. [x] **Analise Monte Carlo**
   - Reamostrar sequencias de trades e simular variacoes de ordem dos resultados.
   - Estimar probabilidade de drawdown extremo, sequencia de perdas e risco de ruina.
   - Por que melhora: mesmo uma estrategia lucrativa pode quebrar emocional ou financeiramente se a distribuicao de perdas for ruim.
   - **Concluido** (`specs/003-robust-optimization`): `python main.py backtest --montecarlo`
     reamostra (bootstrap com reposicao, 1000 simulacoes) a ordem dos trades via
     `backtesting/robustness.py` `monte_carlo_resample()`, estimando mediana/p95 de drawdown maximo
     e maior sequencia de perdas esperada; aviso de confianca baixa reusa `EDGE_MIN_TRADES`
     (spec 002).

## Fase 3 - Melhorar metricas de risco

Objetivo: medir qualidade do retorno, nao apenas retorno bruto.

1. [x] **Sortino Ratio no backtest e analise**
   - Calcular retorno ajustado apenas pela volatilidade negativa.
   - Por que melhora: Sharpe penaliza volatilidade positiva e negativa igualmente. Para trading, perdas e quedas importam mais.
   - **Concluido** (`specs/004-advanced-risk-metrics`): `backtesting/engine.py` `_simplified_sortino()`
     (mesma base do Sharpe, desvio so do downside), exibido em todo relatorio de backtest.

2. [x] **Calmar Ratio no backtest e analise**
   - Calcular retorno anualizado dividido pelo max drawdown.
   - Por que melhora: mostra se o retorno compensa o pior rebaixamento sofrido. E uma metrica pratica para estrategias com cauda de risco.
   - **Concluido** (`specs/004-advanced-risk-metrics`): `annualized_return_pct / max_drawdown_pct`,
     exibido em todo relatorio de backtest.

3. [x] **Tempo em posicao e retorno anualizado**
   - Medir exposicao ao mercado, retorno anualizado e retorno por tempo exposto.
   - Por que melhora: uma estrategia que fica pouco tempo comprada precisa ser comparada de forma justa contra buy-and-hold e contra risco de ficar fora de grandes altas.
   - **Concluido** (`specs/004-advanced-risk-metrics`): `annualized_return_pct` (juros compostos, base
     365 dias) e `return_per_exposure_pct` (`None` explicito quando exposicao e zero), exibidos em
     todo relatorio de backtest. Exposicao (`exposure_pct`) ja existia antes desta spec.

4. [ ] **Analise automatica de `data/decisions.csv`**
   - Criar comando para resumir sinais, decisoes finais, bloqueios, filtros que mais impediram entrada e indicadores medios por decisao.
   - Por que melhora: mostra se o bot esta parado por excesso de filtro, entrando em contexto ruim ou bloqueando bons sinais por uma regra especifica.
   - **Parcial** (`specs/004-advanced-risk-metrics`): `python main.py decisions` resume contagem de
     sinais (BUY/SELL/HOLD) e bloqueios mais frequentes ranqueados via novo
     `data/decisions_analysis.py`. "Indicadores medios por decisao" (ex: RSI medio em ciclos HOLD vs
     BUY) nao foi escopado nesta spec — candidato para uma proxima iteracao. Validado só com fixture
     sintética neste ambiente (sem `data/decisions.csv` real — bot nunca rodou continuamente aqui).

## Fase 4 - Validar e evoluir a estrategia atual

Objetivo: testar hipoteses de melhoria com evidencia, sem transformar a estrategia em um conjunto de regras impossivel de explicar.

1. [ ] **Validar preset operacional atual**
   - Rodar backtests e paper trading com `TIMEFRAME=1h`, `RSI_OVERBOUGHT=70`, `VOLUME_MIN_RATIO=1.0` e pullback ativo.
   - Registrar resultado em `STRATEGY_REVIEW.md`.
   - Por que melhora: o preset atual foi desenhado para aumentar frequencia de trades, mas ainda precisa provar que nao aumentou falsos sinais demais.

2. [ ] **Testar filtro Bollinger adaptativo**
   - Permitir entrada acima da banda superior somente quando tendencia e volume estiverem fortes.
   - Comparar contra o filtro fixo atual.
   - Por que melhora: o filtro atual evita compra esticada, mas tambem pode bloquear rompimentos fortes que sao comuns em cripto.

3. [ ] **Regime detection com ADX**
   - Calcular ADX(14) e classificar mercado como trending, sideways ou indefinido.
   - Em tendencia, permitir regras mais flexiveis; em lateralizacao, suspender ou endurecer entradas.
   - Registrar regime em `data/decisions.csv`.
   - Por que melhora: EMA crossover costuma perder dinheiro em mercado lateral. Detectar regime reduz trades onde a estrategia tem menor vantagem.

4. [ ] **Deteccao de volatilidade elevada**
   - Calcular `ATR_ratio = ATR14 / close`.
   - Quando volatilidade estiver alta, testar alvos/stops adaptados e bloqueios de entrada em candles extremos.
   - Por que melhora: cripto muda rapidamente de volatilidade. Stop e alvo fixos por regime podem ser apertados demais em explosoes e largos demais em consolidacao.

5. [ ] **Trading Range Breakout**
   - Implementar `strategy/breakout.py` herdando `BaseStrategy`.
   - Testar janelas 50/150/200 periodos e comparar contra EMA/RSI nos mesmos pares, custos e timeframes.
   - Por que melhora: estudos de analise tecnica em cripto indicam que regras de rompimento podem superar medias moveis em alguns ativos e periodos.

6. [ ] **Comparativo de estrategias e presets**
   - Criar comando para comparar EMA/RSI, breakout e presets diferentes em uma unica execucao.
   - Usar as mesmas metricas, benchmark e criterios de aprovacao.
   - Por que melhora: impede comparar resultados gerados em condicoes diferentes e ajuda a escolher a estrategia mais robusta, nao a mais recente.

## Fase 5 - Forward test e observabilidade operacional

Objetivo: aproximar o paper mode da realidade operacional antes de qualquer live.

1. [ ] **Forward test formal em paper mode**
   - Registrar carteira paper, trades, decisoes e metricas por periodo como uma avaliacao continua.
   - Comparar performance paper contra backtest do mesmo intervalo.
   - Por que melhora: backtest nao captura todos os problemas de execucao, latencia, dados incompletos e comportamento real do loop.

2. [ ] **Separar caixa, posicoes e patrimonio total**
   - Mostrar `caixa livre`, `valor em posicoes abertas`, `patrimonio total`, `PnL realizado`, `PnL nao realizado` e `PnL total`.
   - Aplicar no painel do bot, `status` e qualquer resumo operacional.
   - Por que melhora: hoje o saldo exibido pode parecer menor quando ha posicao aberta, porque representa caixa livre e nao patrimonio total. Isso evita confundir paper trading atual com capital final de backtest.

3. [ ] **Explicitar contexto do relatorio de edge**
   - Mostrar no `python main.py edge`: `modo: backtest simulado`, par, timeframe, periodo testado, capital inicial simulado e aviso de que nao e o saldo atual do paper bot.
   - Por que melhora: deixa claro que `Capital final` do edge e uma simulacao historica, enquanto o bot rodando usa estado real salvo em `data/state.json`.

4. [ ] **Comparar paper atual vs backtest do mesmo periodo**
   - Criar relatorio que use o intervalo em que o bot ficou ligado e rode um backtest equivalente no mesmo par/timeframe.
   - Comparar trades reais paper, trades simulados, diferenca de entrada/saida, slippage, sinais perdidos e patrimonio final.
   - Por que melhora: mostra se a execucao real do loop esta reproduzindo o backtest ou se ha divergencia por timing, cache, MTF, cooldown, posicoes abertas ou dados incompletos.

5. [ ] **Painel local**
   - Adicionar `python main.py painel` para mostrar saldo, posicoes abertas, PnL, ultimas operacoes, ultimos sinais, status dos pares e bloqueios recentes.
   - Por que melhora: reduz operacao as cegas. O operador precisa saber rapidamente se o bot esta saudavel, parado, exposto ou repetindo erros.

6. [ ] **Modo debug da estrategia**
   - Explicar por que cada par esta em `BUY`, `SELL` ou `HOLD`, incluindo EMA, RSI, volume, MTF, Bollinger, regime e cooldown.
   - Por que melhora: facilita diagnosticar sinais ausentes e evita mexer em parametros sem entender qual filtro esta dominando.

7. [ ] **Graficos de performance**
   - Gerar curva de capital, drawdown, PnL por par e candles com marcacoes de entrada/saida.
   - Por que melhora: algumas falhas aparecem melhor visualmente, como lucros concentrados em poucos trades, drawdown longo ou entradas logo antes de reversoes.

## Fase 6 - Protecoes para live

Objetivo: se um dia o bot for para dinheiro real, reduzir a chance de erro operacional ou perda fora do planejado.

1. [x] **Confirmacao explicita para live**
   - Exigir confirmacao manual clara ao iniciar com `TRADING_MODE=live`.
   - Mostrar pares, saldo, tamanho maximo por ordem, maximo de posicoes e limite de drawdown antes de operar.
   - Por que melhora: impede ligar live por engano ou com `.env` mal configurado.
   - **Concluido** (`specs/005-live-protections`, US1): `trading/runner.py`
     `_print_live_confirmation_banner()` exibe pares, saldo real, `MAX_ORDER_SIZE_USDT`,
     `MAX_POSITIONS` e os 4 limites de perda antes do loop principal em `TRADING_MODE=live`; grava
     evento `live_session_started`. Nao bloqueia inicializacao nao-interativa (so informativo, alem
     do `LIVE_TRADING_CONFIRMATION` ja existente). Nao aparece em `paper`.

2. [x] **Kill switch operacional**
   - Criar mecanismo para suspender novas entradas e/ou fechar posicoes conforme configuracao.
   - Pode ser arquivo local, variavel de ambiente ou comando dedicado.
   - Por que melhora: em falha de mercado, bug ou comportamento inesperado, a resposta precisa ser simples e rapida.
   - **Concluido** (`specs/001-hardening-incremental`, US2): `python main.py kill`/`resume`,
     persistido em `data/killswitch.json` (arquivo proprio, ver nota de design em `tasks.md` sobre por
     que nao mora em `state.json`). Suspende novas entradas; posicoes abertas continuam geridas
     normalmente (fechar posicoes automaticamente nao foi implementado -- decisao consciente de
     escopo, ver `spec.md` Edge Cases).

3. [x] **Checagem de liquidez e spread antes da ordem**
   - Validar order book, spread maximo, volume minimo e tamanho da ordem antes de comprar.
   - Por que melhora: slippage real pode destruir expectativa positiva, principalmente em pares menores.
   - **Concluido** (`specs/005-live-protections`, US3): novo `execution/liquidity.py`,
     `check_liquidity(symbol, order_size_usdt)` via `fetch_order_book` -- bloqueia com motivo
     especifico quando spread > `MAX_SPREAD_PCT_ENTRY` (novo, default 0.5%) ou profundidade do lado
     ask < `MIN_ORDERBOOK_DEPTH_USDT` (novo, default 3x `MAX_ORDER_SIZE_USDT`). Falha de rede vira
     bloqueio conservador, nunca aprovacao por omissao. Integrado em `handle_entry_candidate` depois
     do MTF.

4. [x] **Execucao inteligente de ordens**
   - Adicionar ordens limit/stop, reconciliacao de ordens, rastreamento de preenchimento parcial e verificacao de estado na corretora.
   - Por que melhora: ordem a mercado e estado local simples sao suficientes para paper, mas live exige reconciliar o que a corretora realmente executou.
   - **Concluido** (`specs/001-hardening-incremental` US1 + `specs/005-live-protections` US4):
     `execution/reconciliation.py` compara `state.json` com o saldo real via `fetch_balance()` na
     inicializacao e a cada ~30min, com alerta (nao correcao automatica) em divergencia;
     `clientOrderId` idempotente em toda ordem (paper e live). Ordens limit opcionais
     (`USE_LIMIT_ORDERS`, default `false`) via `_live_buy_limit`, preco = melhor ask do order book ja
     obtido pela checagem de liquidez; `pending_limit_orders` persistido em `state.json`, sobrevive a
     restart; `check_pending_limit_orders()` (uma vez por ciclo) resolve preenchimento total, parcial
     + timeout (`LIMIT_ORDER_TIMEOUT_CYCLES`, cancela o restante e abre so com o preenchido) ou zero +
     timeout (cancela e descarta). Nao implementado: ordens stop nativas da exchange (o stop
     loss/trailing continua sendo gerido localmente pelo bot, nao enviado como ordem stop para a
     corretora) -- fora de escopo desta spec, sem incidente ou necessidade real que o justifique ainda.
   - Item relacionado nao antecipado no ROADMAP original: `_generate_client_order_id()` idempotente
     tambem fecha o gap de retry-duplica-ordem em rede instavel (ver achados #7/#26 em `tasks.md`).

5. [x] **Limites de perda por dia, semana e mes**
   - Expandir o limite diario atual para limites semanais/mensais e bloqueio automatico apos sequencia ruim.
   - Por que melhora: protege contra degradacao gradual da estrategia e contra periodos em que o mercado deixou de favorecer o modelo.
   - **Concluido** (`specs/001-hardening-incremental` US2 + `specs/005-live-protections` US2):
     "bloqueio automatico apos sequencia ruim" via `MAX_CONSECUTIVE_LOSSES` (circuit breaker, contador
     global de perdas seguidas, reseta so em trade com `pnl > 0`). `WEEKLY_DRAWDOWN_LIMIT`/
     `MONTHLY_DRAWDOWN_LIMIT` novos, mesmo padrao do `DAILY_DRAWDOWN_LIMIT` ja existente, cada um com
     reset independente (dia/semana ISO/mes) e seu proprio saldo de referencia real. Corrigido no
     mesmo trabalho um bug real: `is_daily_limit_hit()` usava `DAILY_DRAWDOWN_LIMIT * 1000.0`
     (saldo paper default hardcoded) em vez do saldo real da conta -- agora cada periodo captura seu
     saldo de referencia via `OrderManager._reference_balance()`.

## Fase 7 - Avancado

Objetivo: explorar melhorias maiores somente depois que validacao, risco e operacao estiverem maduros.

1. [ ] **Filtro de sinal com aprendizado de maquina**
   - Coletar caracteristicas rotuladas em backtests e paper mode para opcionalmente filtrar entradas por probabilidade.
   - Por que melhora: pode reduzir falsos positivos, mas tem alto risco de overfitting. So deve vir depois de walk-forward e relatorios solidos.

2. [ ] **Multiplas corretoras**
   - Generalizar configuracao de corretora alem da Binance usando a base existente com `ccxt`.
   - Por que melhora: permite comparar liquidez/custos e reduz dependencia operacional, mas aumenta complexidade de execucao.

## Qualidade de Codigo

Refactor SDD iniciado em 2026-08-13 usando o GitHub Spec Kit oficial
(`specs/001-hardening-incremental/spec.md`, `plan.md`, `tasks.md`; principios em
`.specify/memory/constitution.md`). Fase de Setup/Foundational configurou ruff, mypy
(escopado em `risk/manager.py` e `execution/order_manager.py`), pytest-cov, pre-commit
(`.pre-commit-config.yaml`) e CI no GitHub Actions (`.github/workflows/ci.yml`, jobs
`lint` → `typecheck` → `test`) — `tasks.md` T006/T007 concluidas. A spec inteira
(US1/US2/US3 + Polish) foi concluida; ver `tasks.md` para o historico de 13+ rodadas de
`/code-review high` por User Story.

Baseline de cobertura de teste registrado em 2026-08-13 (`pytest --cov`): **66% no projeto inteiro**. Modulos criticos para o hardening da Fase 2:

- `risk/manager.py`: 93%
- `execution/order_manager.py`: 36% (foco do gap de idempotencia/reconciliacao, ver `.specify/memory/plan.md` Fase 2)
- `strategy/ema_rsi.py`: 77%
- `backtesting/engine.py`: 83%

Meta de `test_coverage_min_pct` da spec (80%) aplica-se primeiro a `risk/` e `execution/`, nao ao projeto inteiro.

## Referencias Internas

- `STRATEGY_REVIEW.md`: hipoteses, resultados locais e diagnostico da estrategia.
- `docs/research/`: artigos e notas sobre analise tecnica, custos, drawdown, out-of-sample e comparacao com buy-and-hold.
- `backtesting/engine.py`: simulacao historica, custos, slippage e metricas atuais.
- `backtesting/optimizer.py`: busca de parametros atual, ponto de partida para split treino/teste e walk-forward.
- `.specify/memory/constitution.md`: principios inegociaveis do projeto (SDD).
- `specs/001-hardening-incremental/`: spec, plan e tasks do refactor SDD em andamento (GitHub Spec Kit).
