# Feature Specification: Itens Remanescentes do ROADMAP

**Feature Branch**: `009-itens-remanescentes-roadmap`

**Created**: 2026-08-15

**Status**: Concluída (US1-US4 implementadas, revisadas e commitadas; Polish completo)

**Input**: User description: "Itens remanescentes do ROADMAP.md Fases 1, 1.1 e 3 que ficaram
pendentes desde antes deste backlog SDD começar, achados numa auditoria completa do documento (não
estavam em specs/BACKLOG.md). Escopo: exportação de relatórios em `reports/` (JSON/CSV/Markdown);
diagnóstico agressivo em `diagnose_profile()`; out-of-sample no relatório de edge; indicadores
médios por decisão em `data/decisions_analysis.py`. Tudo testável com dados públicos de backtest ou
fixtures sintéticas."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Guardar um histórico auditável de cada execução (Priority: P1)

Como operador do bot, eu quero que backtest/scan/otimização/análise salvem seus resultados em
arquivos versionados (JSON, CSV, Markdown) num diretório `reports/`, para comparar experimentos ao
longo do tempo sem precisar reproduzir manualmente cada execução.

**Why this priority**: É a base para os operadores comparem qualquer coisa ao longo do tempo — sem
isso, cada execução é efêmera (só existe na tela). Maior valor de longo prazo entre os 4 itens desta
spec.

**Independent Test**: Rodar `python main.py backtest` (ou `scan`/`multibacktest`/`optimize`) e
confirmar que um arquivo aparece em `reports/` com parâmetros, período, custos e métricas, nos 3
formatos.

**Acceptance Scenarios**:

1. **Given** `python main.py backtest` roda com sucesso, **When** a execução termina, **Then** um
   arquivo JSON, um CSV e um Markdown aparecem em `reports/` com parâmetros usados, período
   testado, custos, slippage e métricas do resultado.
2. **Given** múltiplas execuções ao longo do tempo, **When** o operador olha `reports/`, **Then**
   cada execução tem seu próprio arquivo (timestamp no nome), sem sobrescrever execuções
   anteriores.

---

### User Story 2 - Reconhecer uma estratégia agressiva, não só uma defensiva (Priority: P2)

Como operador do bot, eu quero que o diagnóstico de perfil também identifique quando uma estratégia
teve retorno muito acima do buy-and-hold às custas de um drawdown alto, para não confundir "correu
risco alto e valeu a pena nesta amostra" com "estratégia simplesmente boa".

**Why this priority**: Extensão pequena e direta de uma capacidade já existente
(`diagnose_profile()`), menor escopo que US1.

**Independent Test**: Rodar `diagnose_profile()` sobre um resultado com drawdown alto e retorno bem
acima do buy-and-hold, confirmando que retorna o diagnóstico "perfil agressivo".

**Acceptance Scenarios**:

1. **Given** um resultado de backtest com drawdown acima do limite aceitável e retorno
   significativamente acima do buy-and-hold, **When** `diagnose_profile()` roda, **Then** retorna
   um diagnóstico de perfil agressivo.
2. **Given** um resultado nem defensivo nem agressivo (nenhum dos dois padrões), **When**
   `diagnose_profile()` roda, **Then** continua retornando `None`, sem forçar uma classificação.

---

### User Story 3 - Ver se o edge se sustenta fora dos dados usados para validar (Priority: P3)

Como operador do bot, eu quero uma opção no relatório de edge que mostre o veredito calculado
especificamente sobre uma fatia de dados que não influenciou nenhuma decisão anterior, para não
confundir um edge que só existe nos dados já vistos com um edge que se sustentaria em dados novos.

**Why this priority**: Reusa infraestrutura já validada (`split_train_validation`, spec 001) — é
mais uma opção de exibição que uma capacidade nova, por isso prioridade menor que US1/US2.

**Independent Test**: Rodar `python main.py edge --validate` e confirmar que o veredito exibido é
calculado sobre a fatia de validação (out-of-sample), com o resultado de treino mostrado para
comparação, não escondido.

**Acceptance Scenarios**:

1. **Given** `python main.py edge --validate` roda para um par com histórico suficiente, **When**
   o relatório é exibido, **Then** mostra o resultado de treino e o resultado de validação lado a
   lado, com o veredito de aprovação calculado sobre a validação.
2. **Given** `python main.py edge` roda sem a flag, **When** o relatório é exibido, **Then** o
   comportamento continua idêntico ao já existente (janela única, sem split).

---

### User Story 4 - Saber que indicador está separando entradas boas de ruins (Priority: P4)

Como operador do bot, eu quero ver o valor médio dos indicadores (RSI, entre outros já registrados)
agrupado por tipo de decisão (HOLD, BUY, SELL, bloqueado), para identificar rapidamente se um filtro
específico está bloqueando entradas em contextos que na verdade eram bons.

**Why this priority**: Ferramenta de diagnóstico adicional sobre uma capacidade já existente
(`data/decisions_analysis.py`) — menor prioridade por ser um refinamento, não uma capacidade nova.

**Independent Test**: Rodar `python main.py decisions` sobre um histórico (real ou sintético) com
RSI variando entre ciclos HOLD e BUY, confirmando que a média de RSI aparece separada por tipo de
decisão.

**Acceptance Scenarios**:

1. **Given** um histórico de decisões com RSI registrado, **When** `python main.py decisions`
   roda, **Then** mostra o RSI médio (e outros indicadores já registrados no CSV) agrupado por
   sinal (HOLD/BUY/SELL).
2. **Given** nenhum dado disponível, **When** o comando roda, **Then** continua mostrando o estado
   vazio explícito já existente, sem erro.

---

### Edge Cases

- O que acontece se `reports/` não existir ainda? → Criado automaticamente na primeira execução,
  mesmo padrão já usado por `data/ohlcv/` (`Path.mkdir(parents=True, exist_ok=True)`).
- O que acontece se `python main.py edge --validate` for chamado num par sem histórico suficiente
  para split (mesma regra já validada por `split_train_validation`)? → Mesmo comportamento já
  existente em `backtest --validate` para essa condição — não uma falha nova.
- O que acontece se um indicador estiver ausente em alguma linha de `data/decisions.csv` (histórico
  de antes desta spec, sem uma coluna nova)? → Ignorado no cálculo da média, não quebra o comando —
  mesmo princípio tolerante já usado por `_load_decisions()`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST salvar o resultado de execuções de backtest/scan/multibacktest/
  otimização em `reports/`, nos formatos JSON, CSV e Markdown, incluindo parâmetros usados, período
  testado, custos, slippage e métricas.
- **FR-002**: O sistema MUST nomear cada arquivo de relatório de forma que múltiplas execuções não
  se sobrescrevam (timestamp no nome do arquivo).
- **FR-003**: O sistema MUST identificar um perfil "agressivo" (drawdown alto, retorno bem acima do
  buy-and-hold) em `diagnose_profile()`, complementando o perfil "defensivo" já existente, sem
  forçar uma classificação quando nenhum dos dois padrões se aplica.
- **FR-004**: O sistema MUST oferecer uma opção (`--validate`) em `python main.py edge` que calcule
  o veredito de aprovação sobre uma fatia de validação out-of-sample, reusando
  `split_train_validation` já existente, mostrando também o resultado de treino para comparação.
- **FR-005**: O sistema MUST manter o comportamento atual de `python main.py edge` (sem a flag)
  inalterado.
- **FR-006**: O sistema MUST calcular e exibir o valor médio de indicadores já registrados em
  `data/decisions.csv` (no mínimo RSI), agrupado por tipo de sinal (HOLD/BUY/SELL).
- **FR-007**: Nenhuma tarefa desta spec MUST exigir histórico real de operação paper para ser
  validada — toda validação usa dados públicos de backtest ou fixtures sintéticas.

### Key Entities

- **Relatório exportado**: snapshot de uma execução (parâmetros, período, custos, métricas,
  ranking quando aplicável), em 3 formatos, salvo em `reports/`.
- **Perfil agressivo**: complemento do perfil defensivo já existente, mesmo tipo de diagnóstico
  textual complementar ao veredito de aprovação.
- **Relatório de edge com validação**: par de resultados (treino, validação) com o veredito
  calculado sobre a validação, reusando a mesma infraestrutura de `backtest --validate`.
- **Indicadores médios por decisão**: agregação de valores numéricos já presentes em
  `data/decisions.csv`, agrupados por `signal`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cada execução de `backtest`/`scan`/`multibacktest`/`optimize` produz um arquivo novo
  em `reports/` (3 formatos), sem sobrescrever execuções anteriores.
- **SC-002**: `diagnose_profile()` distingue corretamente entre perfil defensivo, agressivo e
  nenhum dos dois, em pelo menos um caso sintético de cada.
- **SC-003**: `python main.py edge --validate` produz um veredito calculado sobre dados que não
  influenciaram o treino, verificável comparando contra o resultado de `backtest --validate` para
  o mesmo par/período.
- **SC-004**: `python main.py decisions` mostra RSI médio (e demais indicadores já registrados)
  separado por sinal, sem exigir histórico real de operação paper — fixture sintética é suficiente.

## Assumptions

- "Formatos JSON, CSV e Markdown" (US1) usam serialização direta das dataclasses de resultado já
  existentes (`BacktestResult`, `MultiResult`/`ScanResult`) — não inventa um schema novo.
- "Perfil agressivo" (US2) reusa os mesmos limiares já definidos em `evaluate_approval()`
  (`MAX_ACCEPTABLE_DRAWDOWN_PCT`), mesmo princípio já aplicado ao perfil defensivo — não introduz um
  segundo conjunto de números "drawdown alto" divergente no mesmo relatório.
- "Out-of-sample no relatório de edge" (US3) reusa `split_train_validation`/`simulate_backtest` já
  validados (spec 001) — não duplica lógica de split.
- "Indicadores médios por decisão" (US4) começa por RSI (exemplo citado no `ROADMAP.md`), extensível
  a outros indicadores já registrados no CSV (`volume_ratio`, `atr_pct`, `trend_gap_pct`) sem
  exigir uma segunda spec para isso.
