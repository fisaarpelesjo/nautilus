# Fase 0 — Pesquisa: motor de carteira para aprovação de H14

**Data:** 2026-09-02

---

## D1 — Capital inicial

**Decisão:** `1.000,0` USDT, o mesmo default de
`backtesting/engine.py::run_backtest`/`simulate_backtest`.

**Rationale.** Um valor novo, escolhido só para esta spec, arriscaria
enviesar a leitura percentual de drawdown (drawdown percentual não muda
com o valor absoluto de capital nesta mecânica de dimensionamento
proporcional, mas usar o mesmo número já publicado em toda avaliação do
projeto remove qualquer dúvida sobre comparabilidade).

---

## D2 — Extensão opt-in de `avaliar_par` para expor a previsão de teste

**Decisão:** novo parâmetro `retornar_previsao: bool = False` em
`backtesting/modelo.py::avaliar_par`. Quando `True`, popula um novo campo
`AvaliacaoH14.previsao_teste: Optional[pd.Series]` — probabilidade
prevista pelo modelo já treinado (mesmos coeficientes, mesma chamada de
`prever()` já usada internamente), indexada pelo timestamp de cada candle
da janela de teste do par. Default `False` preserva o comportamento atual
byte a byte — mesmo padrão já usado por `atributos`/`extrair_atributos_fn`
(spec 034, H17), testado por regressão explícita antes de qualquer uso.

**Rationale.** O motor de carteira precisa da probabilidade candle a
candle para decidir quando abrir posição em cada par — hoje `avaliar_par`
só devolve métricas agregadas (`ResultadoModelo`), não a série usada para
calculá-las. Duas alternativas descartadas:

- **Retreinar o modelo dentro do motor de carteira.** Rejeitada: duplica a
  lógica de treino/purga global já em `modelo.py`, e arrisca produzir
  coeficientes sutilmente diferentes dos já publicados em H14 — o motor de
  carteira deixaria de responder "H14 sob concorrência de capital" e
  passaria a responder "um modelo parecido com H14".
- **Reconstruir a previsão fora de `modelo.py`, a partir só dos
  coeficientes já expostos em `ResultadoModelo.coeficientes`.** Rejeitada:
  reimplementaria a fórmula de `prever()` (sigmoide sobre
  `const + Σ coef·atributo`) num segundo lugar — mesmo risco de divergência
  silenciosa que o projeto já evita em outras partes (ex.: sincronizar
  filtros entre `generate_signal` e `precompute_signals`, `CLAUDE.md`).

A extensão opt-in evita as duas: usa a MESMA chamada de `prever()` já
feita dentro de `avaliar_par`, só devolve o resultado em vez de descartá-lo.

---

## D3 — Alinhamento de linha do tempo entre os 12 pares

**Decisão:** a janela de teste já é definida por um ÚNICO ponto de corte
global (`div.inicio_teste`, purga e embargo globais entre pares — D4 de
H14, `docs/research/registro-de-hipoteses.md` §4.15). O motor de carteira
usa a união dos timestamps de candle de todos os 12 pares dentro dessa
janela, avançando em ordem cronológica; um par sem candle num timestamp
específico simplesmente não participa daquele passo (sem preencher,
interpolar, ou usar o candle mais próximo).

**Rationale.** Os 12 pares usam o mesmo `TIMEFRAME` de produção e o mesmo
pedido de histórico (`fetch_ohlcv(par, TIMEFRAME, 6000)`, D1 de spec 036),
então os candles já nascem alinhados na prática — a união de timestamps é
uma garantia formal contra o caso raro de um par ter um candle ausente
(gap de listagem, manutenção da exchange), não uma tentativa de sincronizar
séries desalinhadas por natureza.

---

## D4 — Critério de desempate entre sinais simultâneos

**Decisão:** quando mais de um par sinaliza compra no mesmo candle e o
caixa/slots livres não cobrem todos, prioriza o par com maior probabilidade
prevista pelo modelo (`previsao_teste`, D2) naquele candle.

**Rationale.** É o único critério derivado do próprio sinal já calculado —
qualquer outro (ordem alfabética do par, ordem de listagem em
`UNIVERSO_H11`) seria arbitrário e não informativo. Declarado aqui, antes
de qualquer execução, para não virar escolha ajustada a um resultado
depois de vê-lo.

---

## D5 — Buy-and-hold de carteira

**Decisão:** capital inicial (D1) dividido igualmente entre os 12 pares no
primeiro candle da janela de teste, mantido sem rebalanceamento até o
último candle — buy-and-hold real de uma carteira igualmente ponderada,
não a média dos 12 retornos individuais de buy-and-hold.

**Rationale.** `evaluate_approval(require_beat_buy_hold=True)` por padrão
exige bater um buy-and-hold — sem essa definição, a comparação de carteira
não teria contra o que comparar. Igualmente ponderada porque é o análogo
direto de "capital dividido entre os pares", mesmo princípio já declarado
em `spec.md` Assumptions para o dimensionamento de posição, sem inventar
peso por par.

---

## D6 — Módulo novo, reuso do motor de métricas

**Decisão:** `backtesting/portfolio_h14.py`, novo arquivo. Reusa `Trade`/
`BacktestResult`/`_calculate_advanced_metrics` (`backtesting/engine.py`) e
`evaluate_approval` (`backtesting/approval.py`) sem alteração — mesmo
padrão já estabelecido por `backtesting/grid.py` (spec 035, H18) e
`backtesting/onchain_hipotese.py` (spec 034, H17): cada avaliação nova
deste registro produz um `BacktestResult` compatível com o motor já
existente, nunca um formato de resultado paralelo.

**Rationale.** `backtesting/modelo.py` já é grande e mistura treino,
purga e avaliação por par — adicionar a mecânica de carteira (caixa
compartilhado, fila de prioridade, teto de posições) no mesmo arquivo
tornaria as duas responsabilidades mais difíceis de testar isoladamente.
Um módulo novo, que apenas CONSOME `run_modelo_scan()`/`avaliar_par`
(D2), mantém a fronteira clara: `modelo.py` treina e avalia por par;
`portfolio_h14.py` simula a carteira que resulta de usar esse modelo.

---

## D7 — Mecanismo de saída: trailing/ATR, não as barreiras de rotulagem

**Decisão:** cada posição sai pelo mesmo mecanismo já usado pelo backtest
publicado de H14 — take-profit por ATR (`entrada + ATR_TP_MULTIPLIER×ATR`)
e stop **trailing** (`_stop_price`/lógica de
`backtesting/engine.py::simulate_backtest`, mesma fórmula de
`trading/position_lifecycle.py::handle_open_position` em produção): o
stop só sobe, nunca desce, acompanhando o novo máximo desde a entrada.
Sem limite de tempo (velas).

**Correção registrada aqui.** `spec.md`/`plan.md` originais (antes desta
decisão) descreviam a saída como as barreiras de `strategy/
barreira_tripla.py::rotular` (alvo/stop fixo/24 velas) — verificado, ao ler
`backtesting/modelo.py::_resultado_modelo`/`_simular_com_sinais`, que isso
está **errado**: essas barreiras rotulam o alvo de TREINO do classificador
(`rotular()`), mas `AvaliacaoH14.modelo.backtest` — o número que H14
publicou como desempenho — vem de `simulate_backtest(prep_teste,
estrategia, precomputed_signals=sinais)`, o motor genérico do projeto, que
nunca usa essas barreiras para gerir a posição: aplica take-profit por ATR
e stop trailing, sem timeout. Medir com as barreiras de rotulagem mediria
uma estratégia diferente de H14 com o mesmo nome.

**Rationale.** O propósito desta spec é medir o risco de carteira de H14
tal como H14 foi medido e publicado — reusar `simulate_backtest`
(via `_take_profit_price`/`_stop_price`/`_close_trade`, já importáveis de
`backtesting/engine.py`, mesmo padrão de reuso de `modelo.py`/`grid.py`
com funções privadas do módulo) garante isso. Divergir do mecanismo real
de H14 tornaria o veredito desta spec sobre uma estratégia hipotética, não
sobre H14.

---

## Resumo

| # | Decisão | Efeito |
|---|---|---|
| D1 | Capital inicial 1.000 USDT | Mesmo default já publicado em todo o projeto |
| D2 | `avaliar_par(retornar_previsao=True)`, opt-in, regressão testada | Motor de carteira usa a previsão já treinada, sem retreinar nem duplicar a fórmula |
| D3 | União de timestamps dentro da janela de teste já globalmente definida | Sem sincronização nova a inventar — os pares já nascem alinhados |
| D4 | Desempate por maior probabilidade prevista | Critério derivado do próprio sinal, declarado antes de medir |
| D5 | Buy-and-hold de carteira igualmente ponderada | `evaluate_approval` tem contra o que comparar, sem critério novo |
| D6 | `backtesting/portfolio_h14.py`, novo módulo, reuso total do motor de métricas | Fronteira clara entre treino/avaliação por par e simulação de carteira |
| D7 | Saída por take-profit ATR + stop trailing (mesmo mecanismo do backtest publicado), não as barreiras de rotulagem | Corrige leitura errada de `spec.md`/`plan.md` originais — mede H14 como H14 foi de fato medido |

## Fontes

- `docs/research/registro-de-hipoteses.md` §4.15 (H14) — veredito atual,
  limitação de drawdown agregado explicitamente registrada.
- `backtesting/modelo.py` (`avaliar_par`, `run_modelo_scan`,
  `resumo_agregado`, `prever`) — mecanismo de treino/avaliação reusado sem
  alteração de comportamento default.
- `backtesting/grid.py` (spec 035) — precedente direto de módulo de
  pesquisa novo que reusa `Trade`/`BacktestResult`/`evaluate_approval` sem
  duplicar métricas.
- `CLAUDE.md` — fórmula de dimensionamento de posição já documentada
  (`min(MAX_ORDER_SIZE_USDT, (saldo/slots_livres_restantes)*0.95)`).
