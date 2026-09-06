# Research: H39 — Arbitragem estatística via PCA/eigenportfolio (Avellaneda-Lee)

## D1 — universo e alinhamento

`UNIVERSO_AMPLO_HISTORICO_COMPLETO` (22 pares, `backtesting/pairs_trading.py`,
mesmo de H10/H29). Índice alinhado pela interseção comum de todos os
pares antes de qualquer cálculo — mesma correção do bug de colapso de
índice já catalogado por H10 (M14, spec 052): incluir um par com
histórico mais curto sem alinhar primeiro encolheria a janela inteira
para o tamanho do mais curto de forma silenciosa.

## D2 — número de componentes principais

PCA via `numpy.linalg.eigh` sobre a matriz de covariância dos retornos
padronizados (`(retorno - média)/desvio`, por ativo, calculado só na
fatia de treino). Número de componentes = suficiente para explicar
≥55% da variância total acumulada, com teto de 10 — heurística clássica
do paper original (Avellaneda-Lee usam ETFs setoriais ou os primeiros N
componentes que explicam a maior parte da variância; aqui, sem ETFs
setoriais em cripto, o critério de variância acumulada é a adaptação
direta). Não ajustado depois de ver quantos componentes o cripto realmente
produz — é esperado (e já documentado na literatura) que poucos
componentes expliquem a maior parte da variância, dado o fator BTC
dominante.

## D3 — estimação só no treino

Pesos de fator (autovetores) E parâmetros do processo Ornstein-Uhlenbeck
(média de equilíbrio, sigma de equilíbrio) estimados exclusivamente sobre
a fatia de treino (`backtesting.validation.split_train_validation`, mesmo
corte de 70/30 já usado por qualquer outra hipótese desta bateria) e
aplicados SEM reajuste à fatia de validação — mesma disciplina de
H26/H35/H38. Os retornos de validação são padronizados usando a MÉDIA E
DESVIO do treino (nunca os próprios), para não vazar informação futura
para dentro da normalização.

**Ajuste do processo OU (AR(1) sobre o resíduo integrado):**
`X_t = a + b·X_{t-1} + ε_t` (OLS). Se `b` não estiver em `(0, 1)`, o
processo não é estacionário/revertente — ativo excluído. Média de
equilíbrio `m = a/(1-b)`; sigma de equilíbrio
`σ_eq = std(ε)·√(1/(1-b²))` (fórmula padrão da variância estacionária de
um processo AR(1)). `s-score_t = (X_t - m)/σ_eq`.

## D4 — filtro de meia-vida, reusando H10

Meia-vida do resíduo integrado (na fatia de treino) estimada por
`backtesting/pairs_trading.py::meia_vida_reversao` — MESMA função já
usada por H10, sem reimplementar o estimador AR(1) de meia-vida (a
função já resolve exatamente esse cálculo: `Δspread = λ·spread_defasado + erro`,
`meia_vida = -ln(2)/λ`, `inf` se não reversível). Ativo com meia-vida
fora de `[2, 120]` candles (mesma faixa de `PairsParams.meia_vida_min/max`
de H10) é excluído da avaliação de estratégia — muito rápido é ruído de
microestrutura, muito lento o carrego come o retorno (mesmo raciocínio
já documentado por H10).

## D5 — limiares de entrada/saída, valores clássicos do paper

Entrada (BUY) quando o s-score cruza de cima para baixo do limiar
`-1,25`; saída (SELL) quando cruza de baixo para cima do limiar `-0,5`.
Valores do paper original de Avellaneda-Lee (2008) — não ajustados para
o universo cripto, nem recalibrados depois de ver o resultado.

## D6 — limitação estrutural: sem hedge, aposta direcional

O método original negocia o RESÍDUO com hedge dollar-neutral (compra o
ativo, vende os eigenportfolios na proporção da carga estimada). O bot é
long-only (`CLAUDE.md`) — sem infraestrutura de short para os
eigenportfolios. Esta implementação entra e sai apenas no ATIVO, sem
hedge: uma aposta direcional condicionada ao resíduo estar esticado, não
uma posição neutra ao fator de mercado. **Consequência declarada antes de
medir**: se o fator (tipicamente dominado por BTC) mover fortemente
durante o trade, o P&L reflete esse movimento de mercado, não só a
reversão do resíduo — risco real que o método original elimina e esta
implementação não pode. Reportado como limitação no resultado e no
registro (FR-006), não escondido atrás de um número que pareceria melhor
sem essa ressalva.

## Nota de instrumentação — terceira hipótese sobre o harness comum

Cada ativo que sobrevive ao filtro de meia-vida (D4) é avaliado
individualmente pela bateria E1-E6 (`backtesting/bateria_hipotese.py`,
já usada por H34/H36/H37). O sinal (s-score) é pré-calculado UMA VEZ
sobre o índice completo de cada ativo (parâmetros travados no treino) e
passado como `precomputed_signals` a `simulate_backtest` — mesma correção
de performance já aplicada em H36 (recalcular por candle dentro do loop
seria custoso sem necessidade, já que o sinal não depende de quantos
candles totais existem).

## Hipótese declarada antes de medir

**Principal:** o resíduo (após remover a exposição aos componentes
principais, estimados só no treino) de pelo menos alguns ativos reverte
de forma suficientemente estável para que o s-score produza vantagem real
na validação fora da amostra.

**Alternativa, com peso igual, e mais provável dado a literatura (SSRN,
Jay Jung 2025) e a limitação D6:** o fator BTC dominante e a
instabilidade das correlações de altcoin fazem o resíduo se comportar
como ruído — meia-vida fora da faixa negociável para a maioria dos
ativos, ou dentro da faixa mas sem vantagem que sobreviva à validação, e
a ausência de hedge (D6) adiciona risco de fator que pode dominar
qualquer sinal de reversão residual genuíno.

## Reprodução

`python main.py pcaeigen` · `reports/pca_eigenportfolio_*.json`.

(Resultado real preenchido após a execução — ver
`docs/research/registro-de-hipoteses.md` §6.3 para o veredito medido, com
comparação explícita contra a literatura.)
