---

description: "Task list for H13 — barras dirigidas por informação"
---

# Tasks: H13 — Barras dirigidas por informação

**Input**: Design documents from `/specs/026-barras-por-informacao/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: obrigatórios. Constituição, Princípio III — critério de teste definido
**antes** da implementação, estendendo a suíte `pytest` existente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos distintos, sem dependência)
- **[Story]**: US1, US2, US3, US4 conforme a spec

## Path Conventions

Projeto único. Código em `data/`, `backtesting/`, `main.py`; testes em `tests/`;
documentação em `docs/`.

---

## Phase 1: Setup

- [X] T001 Criar `data/bars.py` com docstring de módulo declarando a tese de H13, por que o índice da barra é o instante de fechamento, e a perda declarada em relação a dados de negociação (~12% da largura típica, D1)
- [X] T002 [P] Criar `tests/test_bars.py` com teste de fumaça que importa o módulo e verifica a API pública
- [X] T003 [P] Criar `backtesting/barras.py` e `tests/test_barras_scan.py` com o mesmo padrão

**Checkpoint**: módulos importáveis, suíte verde.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: a construção de barras e sua causalidade. Tudo depende disto.

**⚠️ BLOQUEIA todas as histórias.** E a causalidade (US3) vive aqui na prática,
não numa fase posterior: o teste precisa existir **antes** de qualquer resultado
ser olhado, senão há incentivo a racionalizar um número bom.

### Tests ⚠️

- [X] T004 [P] Teste em `tests/test_bars.py`: agregação de um grupo de candles produz `open` do primeiro, `high` máximo, `low` mínimo, `close` do último, `volume` somado — data-model.md
- [X] T005 [P] Teste em `tests/test_bars.py`: o índice de cada barra é o instante do **último** candle do grupo, nunca o do primeiro — indexar pela abertura dataria a barra num momento em que seu conteúdo era desconhecido
- [X] T006 [P] [US3] Teste de **causalidade** em `tests/test_bars.py`: barras construídas incrementalmente prefixo a prefixo são idênticas às construídas sobre a série completa — FR-003, a maior fonte de falso positivo desta spec (classe de defeito de M2)
- [X] T007 [P] Teste em `tests/test_bars.py`: a última barra, se não cruzou o limiar, **não** aparece na saída — FR-004
- [X] T008 [P] Teste em `tests/test_bars.py`: limiar não positivo é rejeitado, sem produzir série degenerada
- [X] T009 [P] Teste em `tests/test_bars.py`: série sem coluna de volume, ou com volume zerado, produz erro explícito e nunca uma barra silenciosamente errada

### Implementation

- [X] T010 Implementar `TipoBarra` e `ParametrosBarra` em `data/bars.py` conforme data-model.md
- [X] T011 Implementar `construir_dollar_bars(df, limiar)` em `data/bars.py`, acumulando `close × volume` e fechando ao cruzar
- [X] T012 Implementar `construir_cusum_bars(df, limiar)` em `data/bars.py`, acumulando desvio positivo e negativo de retornos
- [X] T013 Implementar `calibrar_limiar(df, tipo, barras_alvo, tolerancia, max_iteracoes)` em `data/bars.py` com o passo de Newton de D2, consultando **exclusivamente a contagem de barras**
- [X] T014 Teste em `tests/test_bars.py`: `calibrar_limiar` converge para dentro da tolerância em no máximo 6 iterações, e nenhuma métrica de retorno participa da calibração — FR-014
- [X] T015 Implementar `candles_origem` e `duracao_horas` nas séries produzidas, usados pelo diagnóstico de reamostragem

**Checkpoint**: barras construídas, causalidade provada, calibração convergindo.

---

## Phase 3: User Story 1 — Descobrir se a amostragem muda o resultado (P1) 🎯

**Goal**: produzir, por combinação, as métricas nas duas versões ancoradas no
mesmo intervalo de calendário.

**Independent Test**: `python main.py barras` devolve tabela pareada com
observações, intervalo comum e métricas de cada versão.

### Tests for User Story 1 ⚠️

- [X] T016 [P] [US1] Teste em `tests/test_barras_scan.py`: `ComparacaoBarras` calcula `delta_drawdown`, `delta_retorno` e `razao_observacoes` como barras menos tempo
- [X] T017 [P] [US1] Teste em `tests/test_barras_scan.py`: buy-and-hold divergente entre as versões além da tolerância produz `erro`, não uma comparação silenciosa — FR-007
- [X] T018 [P] [US1] Teste em `tests/test_barras_scan.py`: reamostragem que produz aproximadamente uma barra por candle recebe `inerte`, nunca `piora` — FR-012, a lição de H12
- [X] T019 [P] [US1] Teste em `tests/test_barras_scan.py`: aquecimento que não cabe no histórico **em dias de calendário** produz `inconclusivo` — FR-010, a lição de H11
- [X] T020 [P] [US1] Teste em `tests/test_barras_scan.py`: amostra abaixo do mínimo em **qualquer** das versões produz `inconclusivo`, nunca `piora` — FR-011

### Implementation for User Story 1

- [X] T021 [US1] Implementar `ComparacaoBarras` em `backtesting/barras.py` com as grandezas derivadas de data-model.md
- [X] T022 [US1] Implementar `comparar_amostragem(estrategia, nome, par, tipo, params)` em `backtesting/barras.py`, buscando base 1h × 8000, construindo as duas versões e reusando `preparar()` de `horizonte.py`
- [X] T023 [US1] Garantir em `comparar_amostragem` que as duas versões cobrem o mesmo intervalo de calendário, e registrar `inicio`/`fim` na comparação — FR-005
- [X] T024 [US1] Implementar `run_barras_scan(estrategias, pares, tipos, params)` em `backtesting/barras.py`, sem abortar a varredura quando uma combinação falha — FR-016
- [X] T025 [US1] Implementar `cmd_barras()` em `main.py` e registrar os aliases `barras` e `bars`, conforme contracts/cli-barras.md
- [X] T026 [US1] Implementar a exibição em `main.py`: parâmetros, contagem por estado **antes** da tabela, tabela pareada com observações e deltas

**Checkpoint**: US1 funcional. **Ainda não é MVP defensável — falta US2.**

---

## Phase 4: User Story 2 — Impedir que menos participação vire vantagem (P1)

**Goal**: distinguir melhora real de simples redução de participação.

**⚠️ Sem esta fase, US1 produz resposta inutilizável.** Barras mais grossas
produzem menos sinais e menos exposição; num mercado em queda isso sozinho
melhora o retorno relativo. O registro documenta três formas do mesmo erro (M7,
M10, M11) e a nota de M11 avisa que é razoável supor que existam outras.

### Tests for User Story 2 ⚠️

- [X] T027 [P] [US2] Teste em `tests/test_barras_scan.py`: combinação cujo ganho não sobrevive ao desconto de exposição recebe `sem_vantagem`, não `melhora` — FR-009
- [X] T028 [P] [US2] Teste em `tests/test_barras_scan.py`: combinação cuja versão de tempo tem retorno ≤ 0 recebe `confundido`, nunca `melhora` — guarda M11 reusada de `volatilidade.py`
- [X] T029 [P] [US2] Teste em `tests/test_barras_scan.py`: `melhora` exige confirmação na fatia fora da amostra; sem ela, `so_na_busca` ou `inconclusivo` — lição de H10
- [X] T030 [P] [US2] Teste em `tests/test_barras_scan.py`: `delta_exposicao` usa exposição de **tempo** e é reportado em toda comparação avaliada — FR-008, D4

### Implementation for User Story 2

- [X] T031 [US2] Implementar `delta_exposicao` e `delta_timing` em `ComparacaoBarras` reusando `ganho_de_timing` de `volatilidade.py` com a exposição de tempo — sem redefinir a métrica
- [X] T032 [US2] Implementar a fatia de validação em `comparar_amostragem` via `split_train_validation`, e `delta_timing_validacao`
- [X] T033 [US2] Implementar `classificar_comparacao_barras` em `backtesting/barras.py` com os 12 estados de data-model.md, **na ordem declarada**
- [X] T034 [US2] Exibir `delta_exposicao` e `delta_timing` na tabela de `main.py`, adjacentes ao delta de drawdown
- [X] T035 [US2] Adicionar legenda em `main.py` declarando o significado de `inerte`, `confundido`, `só na busca` e o que `dTiming` desconta

**Checkpoint**: MVP defensável. As histórias P1 de comparação completas.

---

## Phase 5: User Story 3 — Verificação de causalidade no relatório (P1)

**Goal**: tornar a causalidade verificável por quem lê o relatório, não apenas
pela suíte.

**Nota**: o teste central de US3 (T006) já está na fase Foundational, de
propósito. Esta fase acrescenta o que torna a propriedade **visível**.

### Tests for User Story 3 ⚠️

- [X] T036 [P] [US3] Teste em `tests/test_bars.py`: construção incremental sobre as 12 séries reais do universo produz igualdade exata com a construção completa — a versão do T006 sobre dado real, não sintético
- [X] T037 [P] [US3] Teste em `tests/test_bars.py`: nenhum campo de uma barra depende de candle posterior ao seu fechamento, verificado por perturbação — alterar um candle futuro não altera barras já fechadas

### Implementation for User Story 3

- [X] T038 [US3] Implementar o diagnóstico de reamostragem em `main.py`: candles por barra (mediana e p90) e percentual de barras de um candle só, por variante — é o número que distingue "não houve vantagem" de "o instrumento não mediu nada"

**Checkpoint**: causalidade provada em dado real e diagnóstico visível.

---

## Phase 6: User Story 4 — Separar vantagem de custo de giro (P2)

**Goal**: distinguir efeito da amostragem de efeito do custo adicional.

### Tests for User Story 4 ⚠️

- [X] T039 [P] [US4] Teste em `tests/test_barras_scan.py`: `delta_operacoes` e `delta_custo` são calculados entre as versões
- [X] T040 [P] [US4] Teste em `tests/test_barras_scan.py`: reexecução sem custo produz retorno maior ou igual em ambas as versões

### Implementation for User Story 4

- [X] T041 [US4] Implementar `retorno_sem_custo_tempo` e `retorno_sem_custo_barras` em `comparar_amostragem`, reexecutando com `fee_rate=0.0` e `slippage_pct=0.0`
- [X] T042 [US4] Exibir operações e custo de cada versão na tabela de `main.py`, e o agregado de custo de giro no resumo

**Checkpoint**: as quatro histórias funcionam de forma independente.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T043 [P] Exportar o resultado para `reports/barras_{timestamp}.{json,csv,md}` via `utils/report_export.py`
- [X] T044 [P] Documentar o comando em `CLAUDE.md` e `AGENTS.md` **no mesmo commit** — a constituição exige sincronia
- [X] T045 [P] Documentar em `docs/08-comandos-cli.md`, incluindo o significado de `inerte` e `confundido` e a ressalva de executabilidade (D6)
- [X] T046 Executar a varredura completa e registrar o veredito de H13 em `docs/research/registro-de-hipoteses.md`, confrontando a predição de `research.md` com o observado
- [X] T047 Registrar em `docs/research/registro-de-hipoteses.md` a declaração de executabilidade operacional (FR-017), incluindo a ressalva de recalibração de limiar
- [X] T048 Reordenar a fila de hipóteses conforme o resultado
- [X] T049 Executar os dez cenários de `quickstart.md` e confirmar que todos passam
- [X] T050 Confirmar `git diff --stat` vazio em `risk/`, `execution/`, `trading/` e `data/fetcher.py`, e rodar a suíte completa sem redução na contagem

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (F1)**: sem dependências
- **Foundational (F2)**: depende de F1 — **BLOQUEIA todas as histórias**
- **US1 (F3)**: depende de F2
- **US2 (F4)**: depende de F2 e de US1 — as duas formam o MVP
- **US3 (F5)**: T006 já em F2; F5 depende de US1 para o diagnóstico
- **US4 (F6)**: depende de F2; testável isoladamente
- **Polish (F7)**: depende das histórias desejadas

### Dependência específica

T046 depende de T043: o veredito só pode ser registrado depois que a varredura
rodar e o relatório existir. **A varredura precisa ser executada sem truncar a
saída** — em H12 um `| head` fechou o pipe, o processo morreu antes de exportar,
e o relatório mais recente no diretório era o da execução anterior.

### Within Each User Story

- Testes escritos e **falhando** antes da implementação (Constituição III)
- Entidades antes dos serviços; serviços antes da exibição
- História completa antes da próxima prioridade

### Parallel Opportunities

- T004–T009 em paralelo (testes de construção)
- T016–T020 em paralelo
- T027–T030 em paralelo
- T036 e T037 em paralelo
- T039 e T040 em paralelo
- T043, T044 e T045 em paralelo

**Restrição real:** T010–T015, T021–T026, T031–T035, T038 e T041–T042 escrevem
em `data/bars.py`, `backtesting/barras.py` ou `main.py` e **não** podem ser
paralelizados entre si, mesmo pertencendo a histórias diferentes.

---

## Implementation Strategy

### MVP = US1 **e** US2

Como na spec 025, o MVP exige duas histórias. US1 sozinha produz uma tabela em
que amostragem mais grossa aparece como melhoria — resposta que parece boa e não
é. Parar em US1 seria pior que não implementar, porque produziria evidência
enganosa que entraria no registro.

1. F1 Setup
2. F2 Foundational — **inclui a causalidade**, bloqueia tudo
3. F3 US1
4. F4 US2
5. **PARAR e VALIDAR**: cenários 2 e 3 do `quickstart.md`
6. Só então a pergunta de H13 está respondida de forma utilizável

### Entrega incremental

Cada fase termina em commit próprio, testes passando, push antes da próxima —
Fluxo Incremental do `CLAUDE.md` e Princípio IV.

---

## Notes

- **Predição registrada em `research.md` antes da execução:** o resultado mais
  provável é que a amostragem mude os números sem mudar o veredito. Se for esse
  o caso, H13 encerra a suspeita de que as doze reprovações anteriores mediram o
  relógio em vez da estratégia.
- **Segunda predição registrada:** espera-se `delta_exposicao_tempo` diferente
  de zero. Se vier zero como em H12, a premissa de D4 está errada e essa é a
  descoberta — seria a quarta forma da família M7/M10/M11.
- Se a construção de barras produzir maioria de barras com um candle, é defeito
  de calibração, não achado — a Fase 0 mediu 9–11% e o número deve se manter.
- Nenhuma task altera `risk/`, `execution/`, `trading/` ou `data/fetcher.py`.
  T050 verifica.
- Nenhuma task adiciona dependência.
