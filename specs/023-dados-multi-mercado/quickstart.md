# Quickstart: validação da camada multi-mercado

**Feature**: 023-dados-multi-mercado | **Data**: 2026-08-24

Cenários executáveis que provam a feature ponta a ponta. Cada um mapeia para histórias e requisitos da [spec](spec.md).

## Pré-requisitos

```bash
cd <raiz do repositorio>
.venv\Scripts\activate          # Windows
pip install -r requirements.txt  # inclui a nova dependencia de fonte nao-cripto
```

---

## Cenário 1 — Cripto não regrediu (US4, FR-006)

**O mais importante.** Prova que a abstração não mudou o comportamento existente.

```bash
python -m pytest tests/test_crypto_no_regression.py -v
python main.py backtest BTC/USDT
```

**Esperado**: o resultado do backtest cripto é idêntico ao anterior à feature — mesmas métricas, mesmo veredito, mesmo número de trades.

**Falha significa**: a abstração alterou o caminho cripto. Bloqueia tudo — é o risco técnico nº 1 de [research.md](research.md).

---

## Cenário 2 — Avaliar mercado novo (US1, FR-001)

```bash
python main.py backtest AAPL          # acao EUA
python main.py backtest PETR4.SA      # acao BR
python main.py backtest EURUSD=X      # forex
python main.py backtest ES=F          # futuro
```

**Esperado**: cada um retorna o relatório completo — retorno, profit factor, drawdown, win rate, veredito — no mesmo formato do cripto. O resultado indica o **mercado** e o **perfil de custo** aplicados.

Nos mercados descontínuos (ações, futuros), o resultado traz o aviso de que o teto de perda por trade não age dentro de um gap de abertura (FR-009).

---

## Cenário 3 — Dado indisponível falha explicitamente (FR-005)

```bash
python main.py backtest SIMBOLO_QUE_NAO_EXISTE
python main.py backtest AAPL --candle-limit 5000   # acima do teto de 730 dias da fonte
```

**Esperado**: mensagem explícita de dado indisponível ou de histórico insuficiente. **Nunca** um relatório com números que pareçam válidos.

No segundo caso, o resultado deve deixar detectável que foram pedidos 5.000 candles e obtidos ~993 — comparar cripto (2.000) com ações (993) sem notar a diferença desbalancearia a análise.

---

## Cenário 4 — Custo por mercado (US2, FR-003/FR-004)

```bash
python -m pytest tests/test_markets.py -v
```

**Esperado**:
- O mesmo comportamento de preço simulado em mercados de custos diferentes produz resultado líquido pior no de custo maior
- Um mercado **sem** perfil de custo declarado é recusado com motivo explícito — nunca avaliado com o custo de cripto por omissão

**Por que importa**: foi exatamente o mecanismo inverso (custo de par líquido aplicado a book fino) que fez ACE/BIO/ALLO parecerem operáveis e entregarem prejuízo real.

---

## Cenário 5 — Varredura com confirmação fora da amostra (US3, FR-012/013/014)

```bash
python main.py multimarket
```

**Esperado**:
- Contagem de combinações avaliadas em destaque
- Tabela ranqueada com métricas da janela de **busca** e da janela de **confirmação**
- Combinação que passou só na busca aparece como `so na busca`, visualmente distinta de `confirmado` — e **não** é apresentada como aprovada
- Combinação sem histórico para dividir as janelas aparece como `inconclusivo`
- Símbolo que falhou aparece marcado como erro, sem interromper os demais

**Verificação manual**: nenhuma linha marcada `confirmado` pode ter `confirmation_result` vazio.

---

## Cenário 6 — Operação ao vivo recusa mercado sem execução (FR-007)

```bash
# com um simbolo nao-cripto na lista de operacao do .env
python main.py bot
```

**Esperado**: recusa explícita na inicialização, nomeando o símbolo e o motivo. O bot **não** inicia o loop.

**Por que importa**: sem isso, um ticker de ação em `PAIRS` cairia no caminho de execução que só sabe operar cripto — mesmo padrão que deixou `LUNC/USDT` inerte por 8 dias sem ninguém perceber.

---

## Suíte completa

```bash
python -m pytest -q
```

**Esperado**: todos os testes passam, incluindo os 359 anteriores à feature. Nenhuma regressão.
