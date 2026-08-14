# Feature Specification: Otimização Sem Overfitting

**Feature Branch**: `003-robust-optimization`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Otimização sem overfitting: reduzir o risco de escolher parâmetros de
estratégia que só funcionam por ajuste excessivo ao histórico usado para otimizar. Escopo (ver
`specs/BACKLOG.md` item 003, derivado do `ROADMAP.md` Fase 2): split treino/teste integrado a
`backtesting/optimizer.py` (hoje o grid search escolhe parâmetros avaliando sobre o histórico inteiro,
sem nunca validar fora da amostra); walk-forward validation com janelas deslizantes (mínimo 3 períodos
out-of-sample), agregando resultado médio e pior janela; análise Monte Carlo reamostrando a sequência
de trades para estimar risco de drawdown extremo e de ruína."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Saber se os parâmetros escolhidos sobrevivem fora do histórico usado para escolhê-los (Priority: P1)

Como operador do bot, eu quero que o otimizador de parâmetros mostre o desempenho do conjunto
vencedor também num período que não influenciou a escolha, para não confiar em parâmetros que só
parecem bons porque foram ajustados exatamente ao histórico testado.

**Why this priority**: É o gap central desta spec — hoje `python main.py optimize` escolhe o "melhor"
conjunto de parâmetros olhando só para o histórico inteiro de cada par, então o resultado reportado
pode ser inteiramente fruto de ajuste excessivo (overfitting), sem nenhum sinal de alerta. Sem isso, as
outras duas capacidades desta spec (walk-forward, Monte Carlo) analisam o sintoma, não resolvem a causa
raiz.

**Independent Test**: Pode ser testado isoladamente rodando `python main.py optimize` sobre um par
conhecido e confirmando que o relatório mostra duas métricas por conjunto de parâmetros — desempenho
na fatia de treino (usada para escolher) e desempenho na fatia de validação (não usada) — claramente
identificadas como tal.

**Acceptance Scenarios**:

1. **Given** um par com histórico suficiente para treino e validação, **When** o otimizador roda,
   **Then** a busca em grade avalia e escolhe o conjunto de parâmetros vencedor usando só a fatia de
   treino, e o relatório mostra o desempenho desse mesmo conjunto também na fatia de validação, lado a
   lado.
2. **Given** o conjunto de parâmetros vencedor no treino, **When** seu desempenho na validação é muito
   pior (ex: retorno positivo no treino, negativo na validação), **Then** essa divergência é visível
   no relatório sem exigir que o operador compare números manualmente entre execuções separadas.
3. **Given** um par sem histórico suficiente para formar as duas fatias, **When** o otimizador roda
   para esse par, **Then** o par é reportado como sem validação possível, em vez de silenciosamente
   usar o histórico inteiro sem avisar.

---

### User Story 2 - Confirmar que os parâmetros funcionam em mais de um recorte de mercado (Priority: P2)

Como operador do bot, eu quero rodar a validação em várias janelas deslizantes de tempo (não só uma
divisão treino/teste), para saber se os parâmetros escolhidos se sustentam em diferentes regimes de
mercado (lateral, queda, alta forte), não só no recorte específico que a User Story 1 usou.

**Why this priority**: Depende da mesma base de reaproveitamento de parâmetros vencedores da User
Story 1, mas amplia a evidência — uma única divisão treino/teste pode mascarar fragilidade que só
aparece em determinado regime de mercado. É P2 porque é uma extensão de robustez sobre a User Story 1,
não uma capacidade independente dela.

**Independent Test**: Pode ser testado isoladamente rodando a validação walk-forward sobre um par com
histórico longo e confirmando que o relatório mostra pelo menos 3 janelas out-of-sample, cada uma com
suas próprias métricas, mais um resumo agregado (média e pior janela).

**Acceptance Scenarios**:

1. **Given** um par com histórico longo o suficiente para pelo menos 3 janelas deslizantes, **When**
   a validação walk-forward roda, **Then** o relatório mostra o desempenho de cada janela
   individualmente e um resumo com a média e a pior janela.
2. **Given** os parâmetros são consistentemente bons em algumas janelas e ruins em outras, **When** o
   resumo agregado é calculado, **Then** a pior janela fica claramente visível, não escondida atrás de
   uma média favorável.
3. **Given** um par sem histórico suficiente para 3 janelas, **When** a validação walk-forward é
   solicitada para esse par, **Then** o sistema informa que não há dados suficientes, em vez de rodar
   com menos janelas silenciosamente.

---

### User Story 3 - Entender o risco de uma sequência ruim de perdas, não só o retorno médio (Priority: P3)

Como operador do bot, eu quero uma estimativa de quão ruim uma sequência de perdas pode ficar (mesmo
para uma estratégia lucrativa em média), para decidir se consigo tolerar esse risco financeira e
psicologicamente antes de operar com dinheiro real.

**Why this priority**: É um complemento analítico sobre um resultado de backtest já calculado (por
qualquer uma das User Stories anteriores ou pelo backtest simples já existente) — não depende delas
tecnicamente, mas é a "última milha" da validação (retorno médio positivo não implica que a estratégia
é operável na prática), por isso vem por último em prioridade.

**Independent Test**: Pode ser testado isoladamente rodando a análise sobre a lista de trades de um
backtest já existente e confirmando que o relatório mostra uma estimativa de probabilidade de
drawdown extremo e de sequência de perdas, derivada de reamostragens da ordem dos trades.

**Acceptance Scenarios**:

1. **Given** o resultado de um backtest com uma lista de trades fechados, **When** a análise Monte
   Carlo roda, **Then** o relatório mostra uma distribuição estimada de drawdown máximo (não só o
   valor único já observado no backtest original) e a maior sequência de perdas esperada.
2. **Given** uma estratégia com poucos trades (amostra pequena), **When** a análise Monte Carlo roda,
   **Then** o relatório indica que a confiança da estimativa é baixa, em vez de apresentar números
   precisos como se fossem confiáveis.
3. **Given** a mesma lista de trades, **When** a análise roda duas vezes, **Then** o resultado agregado
   (percentis de drawdown, por exemplo) é consistente entre execuções dentro de uma margem razoável,
   mesmo a ordem reamostrada sendo aleatória.

---

### Edge Cases

- O que acontece quando o par não tem histórico suficiente para a fatia de treino ou validação (User
  Story 1)? → Reportado como "validação não possível" para aquele par, sem interromper a otimização
  dos demais pares.
- O que acontece quando não há candles suficientes para 3 janelas walk-forward (User Story 2)? →
  Informado explicitamente; o sistema não substitui silenciosamente por menos janelas.
- O que acontece quando a amostra de trades é pequena demais para uma análise Monte Carlo confiável
  (User Story 3)? → O relatório sinaliza confiança baixa em vez de esconder a limitação.
- O que acontece se o conjunto de parâmetros vencedor no treino não tiver nenhum trade na fatia de
  validação? → Tratado como validação inconclusiva para esse conjunto, não como aprovação ou reprovação
  silenciosa.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST dividir o histórico de cada par em fatia de treino e fatia de validação
  antes de rodar a busca em grade, e a escolha do conjunto de parâmetros vencedor MUST considerar
  apenas a fatia de treino.
- **FR-002**: O sistema MUST reportar o desempenho do conjunto de parâmetros vencedor também na fatia
  de validação, lado a lado com o desempenho de treino, para todo par processado.
- **FR-003**: O sistema MUST indicar claramente quando a validação não foi possível para um par
  (histórico insuficiente), sem interromper o processamento dos demais pares.
- **FR-004**: O sistema MUST oferecer um modo de validação walk-forward que avalie o conjunto de
  parâmetros vencedor em pelo menos 3 janelas deslizantes não sobrepostas, quando houver histórico
  suficiente.
- **FR-005**: O sistema MUST agregar o resultado das janelas walk-forward em pelo menos duas métricas
  de resumo: desempenho médio entre janelas e desempenho da pior janela.
- **FR-006**: O sistema MUST indicar explicitamente quando não há histórico suficiente para o número
  mínimo de janelas walk-forward, em vez de rodar com menos janelas sem avisar.
- **FR-007**: O sistema MUST oferecer uma análise que reamostre a ordem da sequência de trades de um
  resultado de backtest e estime, a partir dessas reamostragens, a distribuição de drawdown máximo e
  da maior sequência de perdas.
- **FR-008**: O sistema MUST sinalizar quando a amostra de trades usada na análise de reamostragem for
  pequena demais para uma estimativa confiável.
- **FR-009**: O sistema MUST manter compatibilidade com o comportamento atual de
  `python main.py optimize` para quem não usa as novas capacidades (uso básico sem flags novas
  permanece com a saída de hoje).
- **FR-010**: O sistema MUST continuar operando apenas com acesso público de dados da Binance (sem
  exigir credenciais), como as specs anteriores já confirmaram funcionar.

### Key Entities

- **Resultado de otimização com validação**: para um conjunto de parâmetros vencedor, agrupa as
  métricas calculadas na fatia de treino e na fatia de validação, mais um indicador de se a validação
  foi possível.
- **Janela walk-forward**: um recorte de tempo com suas próprias métricas de desempenho para o
  conjunto de parâmetros avaliado; múltiplas janelas compõem o resultado agregado (média, pior
  janela).
- **Estimativa de risco por reamostragem**: distribuição resultante de reamostrar a ordem de uma lista
  de trades já fechados — inclui percentis de drawdown máximo, maior sequência de perdas esperada, e
  um indicador de confiança da amostra.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Rodando o otimizador sobre um par com histórico suficiente, o operador vê o desempenho
  de treino e de validação do conjunto vencedor na mesma execução, sem precisar rodar comandos
  separados nem comparar números manualmente entre execuções.
- **SC-002**: Um conjunto de parâmetros com desempenho de validação muito pior que o de treino é
  identificável no relatório sem exigir que o operador refaça o cálculo por conta própria.
- **SC-003**: A validação walk-forward, quando há histórico suficiente, sempre reporta no mínimo 3
  janelas e nunca reporta um resumo agregado calculado com menos janelas do que as efetivamente
  avaliadas.
- **SC-004**: A análise de reamostragem produz uma estimativa de drawdown mesmo quando o backtest
  original observou só um valor único de drawdown máximo, e marca claramente quando a amostra de
  trades é pequena demais para confiança alta.
- **SC-005**: Nenhuma das mudanças acima quebra o comportamento hoje coberto pela suíte de testes
  existente nem exige credenciais além do acesso público de dados da Binance.

## Assumptions

- Reusa `split_train_validation()` já existente em `backtesting/validation.py` (spec 001) para a
  divisão treino/validação da User Story 1, em vez de reimplementar a lógica de split.
- A busca em grade (`backtesting/optimizer.py`) continua sendo o motor de otimização — esta spec
  adiciona uma camada de validação sobre o resultado, não substitui o algoritmo de busca por outro
  (ex: busca bayesiana).
- "Janela deslizante" na User Story 2 significa fatias contíguas e não sobrepostas cobrindo o
  histórico disponível (mesmo espírito do split simples da spec 001), não necessariamente com
  sobreposição entre janelas — a decisão exata de contiguidade vs sobreposição fica para a fase de
  planejamento técnico.
- A análise Monte Carlo (User Story 3) reamostra a *ordem* dos trades já observados (bootstrap sem
  reposição da sequência, ou com reposição — a decidir na fase de planejamento), não gera trades
  sintéticos novos nem re-simula a estratégia sobre dados de mercado sintéticos.
- Nenhuma das três capacidades desta spec altera `risk/`, `execution/` ou `trading/`— é uma extensão
  de `backtesting/`, sem efeito em `TRADING_MODE=live`.
- Critério de "amostra pequena demais" nas User Stories 1 e 3 pode reusar os mesmos limiares já
  definidos em `backtesting/approval.py` (spec 002, ex: `EDGE_MIN_TRADES`) para não introduzir um
  terceiro número "mínimo de trades" divergente no projeto — decisão final na fase de planejamento.
