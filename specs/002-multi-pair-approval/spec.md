# Feature Specification: Decisão de Aprovação Multi-Par

**Feature Branch**: `002-multi-pair-approval`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Decisão de aprovação multi-par: estender a validação out-of-sample e os
critérios de aprovação automática (aprovado/reprovado/inconclusivo) já implementados em
`backtesting/validation.py` (spec 001-hardening-incremental, US3) para além de um único par por vez.
Hoje `python main.py backtest --validate` só avalia `PAIRS[0]`; o operador precisa rodar par a par
manualmente para ter visão de onde a estratégia realmente tem vantagem. Escopo (ver
`specs/BACKLOG.md` item 002, derivado do `ROADMAP.md` Fase 1 e Fase 1.1): critérios automáticos de
aprovação generalizados; ranking de pares por qualidade integrado a `multibacktest`/`scan`; edge por
par e timeframe; classificação automática com motivos no `edge`; alerta de amostra insuficiente
configurável; diagnóstico defensivo vs agressivo; `edge_score` numa escala interpretável."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver de relance em quais pares a estratégia tem vantagem real (Priority: P1)

Como operador do bot, eu quero rodar um único comando sobre vários pares e ver, lado a lado, qual
deles tem veredito de aprovação (aprovado/reprovado/inconclusivo) e por quê, para não precisar rodar
`backtest --validate` par a par manualmente e tentar montar esse quadro na cabeça.

**Why this priority**: É exatamente a limitação que a validação out-of-sample da spec
`001-hardening-incremental` esbarrou — cada par testado isoladamente teve amostra pequena demais
para uma conclusão confiável, e não há hoje nenhuma visão agregada entre pares. Sem isso, o operador
continua decidindo "no olho" onde a estratégia funciona.

**Independent Test**: Pode ser testado isoladamente rodando `multibacktest` e `scan` sobre a lista de
pares configurada e conferindo que cada par mostra um veredito com motivo, ordenado por qualidade —
sem precisar de nenhuma outra parte desta spec.

**Acceptance Scenarios**:

1. **Given** a lista de pares configurada (`PAIRS`), **When** `python main.py multibacktest` roda,
   **Then** cada par mostra um veredito (aprovado/reprovado/inconclusivo) com pelo menos um motivo, e
   os pares aparecem ordenados por qualidade (profit factor, expectativa, drawdown, consistência e
   diferença vs buy-and-hold), não pela ordem em que foram configurados.
2. **Given** o scanner busca os top pares por volume, **When** `python main.py scan` roda o backtest
   de cada um, **Then** o mesmo veredito/ranking aparece no relatório do scan.
3. **Given** um par não acumula trades suficientes na janela testada, **When** o veredito é
   calculado, **Then** ele aparece como inconclusivo — nunca como aprovado por omissão de amostra.

---

### User Story 2 - Entender por que um par foi reprovado sem interpretar números na mão (Priority: P2)

Como operador do bot, eu quero que `python main.py edge` explique o veredito de um par com motivos
curtos e diga se ele é "defensivo" (perde pouco, mas também ganha pouco) em vez de simplesmente
"ruim", para não ter que reinterpretar as mesmas métricas toda vez que rodo o relatório.

**Why this priority**: Depende dos mesmos critérios de veredito da User Story 1, mas aplica ao
relatório de um único par (`edge`) em vez de múltiplos — é uma evolução de UX sobre a mesma base,
não uma capacidade nova de decisão.

**Independent Test**: Pode ser testado isoladamente rodando `python main.py edge` sobre um par
conhecido e comparando a saída (motivos, diagnóstico defensivo/agressivo, alerta de amostra) contra o
comportamento atual, que só mostra números sem interpretação.

**Acceptance Scenarios**:

1. **Given** o relatório de `edge` roda para um par, **When** o veredito é calculado, **Then**
   aparece uma lista curta com os principais motivos do status (ex: "perdeu para buy-and-hold por
   -70%", "amostra baixa: 7 trades").
2. **Given** a estratégia tem drawdown baixo e expectativa positiva, mas retorno muito abaixo do
   buy-and-hold, **When** o diagnóstico roda, **Then** o par é classificado como "perfil defensivo"
   em vez de reprovado sem contexto adicional.
3. **Given** o número mínimo de trades configurável não é atingido, **When** o veredito é calculado,
   **Then** aparece um alerta de amostra insuficiente, distinto de uma reprovação por critério de
   qualidade (ex: profit factor baixo).

---

### User Story 3 - Comparar `edge_score` entre pares numa escala legível (Priority: P3)

Como operador do bot, eu quero que o `edge_score` venha acompanhado de uma faixa legível (ex: Forte,
Médio, Fraco, Reprovado) em vez de só um número, para comparar pares/timeframes sem decorar a escala
numérica atual.

**Why this priority**: É uma melhoria de interpretabilidade sobre uma métrica que já existe — não
muda nenhuma decisão de aprovado/reprovado/inconclusivo (essas vêm das User Stories 1 e 2), só torna
o número mais fácil de comparar.

**Independent Test**: Pode ser testado isoladamente comparando o `edge_score` de dois pares com
resultados bem diferentes e confirmando que a faixa exibida reflete a diferença, com os pesos usados
documentados em algum lugar acessível (código ou doc), não só implícitos na fórmula.

**Acceptance Scenarios**:

1. **Given** dois pares com `edge_score` bem diferentes, **When** o relatório exibe o score, **Then**
   a faixa correspondente (Forte/Médio/Fraco/Reprovado) também aparece.
2. **Given** a fórmula do `edge_score`, **When** consultada, **Then** os pesos e penalidades usados
   (benchmark, profit factor, expectativa, drawdown, amostra) estão documentados.

---

### Edge Cases

- O que acontece quando nenhum par da lista atinge o número mínimo de trades? → Todos aparecem como
  inconclusivo; o relatório não pode sugerir "aprovado" por ausência de dado suficiente para reprovar.
- O que acontece se dois pares empatam no ranking de qualidade? → Critério de desempate definido e
  documentado (ex: profit factor, depois número de trades), não ordem arbitrária/instável entre
  execuções.
- O que acontece se buscar dados de um par específico falhar (rede, símbolo inválido, par deslistado)?
  → Esse par é marcado com erro no relatório e os demais continuam sendo processados normalmente; uma
  falha isolada não pode interromper o comando inteiro.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST expor uma função de avaliação de veredito (aprovado/reprovado/
  inconclusivo, com motivos) reutilizável fora do fluxo `backtest --validate`, generalizando a já
  existente em `backtesting/validation.py`.
- **FR-002**: O sistema MUST mostrar esse veredito e o(s) motivo(s) por par no relatório de
  `python main.py multibacktest`.
- **FR-003**: O sistema MUST mostrar esse veredito e o(s) motivo(s) por par no relatório de
  `python main.py scan`.
- **FR-004**: O sistema MUST ordenar os pares em `multibacktest` e `scan` por qualidade (profit
  factor, expectativa, drawdown, número de trades, consistência e diferença vs buy-and-hold), com
  critério de desempate documentado — não pela ordem de configuração em `PAIRS`.
- **FR-005**: O sistema MUST mostrar classificação (aprovado/reprovado/inconclusivo) e uma lista
  curta de motivos no relatório de `python main.py edge`.
- **FR-006**: O sistema MUST permitir configurar o número mínimo de trades usado para considerar uma
  amostra suficiente para veredito conclusivo, com um default razoável quando não configurado.
- **FR-007**: O sistema MUST diferenciar amostra insuficiente (inconclusivo) de reprovação por
  critério de qualidade (reprovado) — são motivos distintos, não podem ser confundidos no relatório.
- **FR-008**: O sistema MUST classificar como "perfil defensivo" os casos com drawdown baixo e
  expectativa positiva, mas retorno muito abaixo do buy-and-hold, em vez de reprovar sem esse
  contexto.
- **FR-009**: O sistema MUST expressar o `edge_score` numa faixa interpretável (ex: Forte/Médio/
  Fraco/Reprovado), além do valor numérico bruto já existente.
- **FR-010**: O sistema MUST documentar os pesos/penalidades usados no `edge_score` em local
  acessível (código comentado ou documentação), não apenas implícitos na fórmula.
- **FR-011**: O sistema MUST manter compatibilidade com o comportamento atual de
  `multibacktest`/`scan`/`edge` para quem não usa as novas capacidades — não pode quebrar a suíte de
  testes existente nem exigir novo parâmetro obrigatório para o uso básico já existente.
- **FR-012**: O sistema MUST continuar operando apenas com acesso público de dados da Binance (sem
  exigir credenciais), como confirmado na spec `001-hardening-incremental`.

### Key Entities

- **Veredito de aprovação**: status (aprovado/reprovado/inconclusivo) + lista de motivos, aplicado ao
  resultado de backtest de um par/timeframe — generalização da entidade já existente em
  `backtesting/validation.py`.
- **Ranking de pares**: lista ordenada de pares por qualidade, usada em `multibacktest` e `scan`.
- **Diagnóstico defensivo/agressivo**: classificação qualitativa complementar ao veredito, para casos
  de baixo risco mas baixa captura de alta.
- **Faixa de `edge_score`**: mapeamento do valor numérico do score para uma categoria legível (Forte/
  Médio/Fraco/Reprovado).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Rodando `multibacktest` ou `scan` sobre a lista de pares configurada, o operador
  identifica quais pares têm veredito aprovado só lendo o relatório de uma execução — sem precisar
  rodar `backtest --validate` par a par manualmente.
- **SC-002**: 100% dos pares com amostra abaixo do mínimo configurado aparecem como inconclusivo,
  nunca como aprovado, em qualquer execução de teste automatizado que force esse cenário.
- **SC-003**: Todo veredito reprovado ou inconclusivo exibido em `multibacktest`, `scan` ou `edge`
  vem acompanhado de pelo menos um motivo textual.
- **SC-004**: A suíte de testes existente antes desta spec continua passando sem alteração de
  comportamento fora do escopo definido aqui.
- **SC-005**: O `edge_score` de qualquer par testado vem acompanhado de uma faixa legível, com os
  pesos da fórmula verificáveis sem precisar rodar o código (documentados).

## Assumptions

- Reusa o motor de backtest (`backtesting/engine.py`) e a lógica de veredito já criada em
  `backtesting/validation.py` (spec 001, US3) como base, generalizando-a — não recria a lógica de
  aprovação do zero.
- "Qualidade" no ranking usa os mesmos critérios já citados no `ROADMAP.md` (profit factor,
  expectativa, drawdown, número de trades, consistência, diferença vs buy-and-hold); nenhuma métrica
  nova é introduzida fora desse conjunto nesta spec.
- O número mínimo de trades default segue o mesmo valor já usado em `evaluate_validation()` (10),
  salvo decisão diferente na fase de planejamento.
- Dados usados continuam sendo exclusivamente os já buscados publicamente na Binance via `ccxt`, sem
  necessidade de credenciais — como a spec 001 confirmou funcionar após o fix de `data/fetcher.py`.
- Não há requisito de compatibilidade retroativa de formato de relatório: a saída de
  `multibacktest`/`scan`/`edge` pode ganhar colunas/seções novas, desde que os comandos continuem
  funcionando para quem já os usa hoje.
