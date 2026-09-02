---

description: "Task list for H14 — aprendizado supervisionado com barreira tripla"
---

# Tasks: H14 — Aprendizado supervisionado com barreira tripla

**Input**: Design documents from `/specs/027-aprendizado-barreira-tripla/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: obrigatórios, e **escritos antes da implementação**. Constituição,
Princípio III. Ver a nota do `plan.md`: os caminhos de falha desta spec produzem
resultados que *parecem bons*, e escrever o teste depois de ver o número é o
cenário exato da racionalização.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos distintos, sem dependência)
- **[Story]**: US1, US2, US3, US4 conforme a spec

## Path Conventions

Projeto único. Código em `strategy/`, `backtesting/`, `main.py`; testes em
`tests/`; documentação em `docs/`.

---

## Phase 1: Setup

- [X] T001 Criar `strategy/barreira_tripla.py` com docstring declarando a tese, o limiar de sucesso de D2 (razão de chances 0,500 contra 0,372 observada) e por que acurácia não é a métrica
- [X] T002 [P] Criar `backtesting/purga.py` com docstring explicando por que a purga é global entre pares (correlação 0,71 medida em H9)
- [X] T003 [P] Criar `backtesting/modelo.py`, `tests/test_barreira_tripla.py`, `tests/test_purga.py` e `tests/test_modelo.py` com testes de fumaça

**Checkpoint**: módulos importáveis, suíte verde.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: rotulagem causal, atributos declarados e purga global. Tudo depende
disto, e os três são os caminhos de falso positivo desta spec.

**⚠️ BLOQUEIA todas as histórias.**

### Tests ⚠️ (escrever primeiro, confirmar que falham)

- [X] T004 [P] Teste em `tests/test_barreira_tripla.py`: o rótulo é `+1` quando o alvo é tocado antes do stop, `−1` no caso inverso, `0` quando nenhum é tocado no limite — sobre séries construídas para cada caso
- [X] T005 [P] [US1] Teste de **causalidade** em `tests/test_barreira_tripla.py`: alterar um preço **anterior** ao evento não muda o rótulo dele; alterar um preço dentro do horizonte muda — FR-004
- [X] T006 [P] Teste em `tests/test_barreira_tripla.py`: `fim_horizonte` é o instante em que a barreira foi tocada, ou o limite de tempo quando nenhuma foi
- [X] T007 [P] Teste em `tests/test_barreira_tripla.py`: ATR ausente ou não positivo produz evento sem rótulo, nunca um rótulo arbitrário
- [X] T008 [P] Teste em `tests/test_barreira_tripla.py`: o conjunto de atributos é exatamente os cinco declarados, e todos são adimensionais ou normalizados pelo preço — FR-003
- [X] T009 [P] [US2] Teste em `tests/test_purga.py`: nenhuma amostra de treino sobrevive com `fim_horizonte` alcançando a janela de teste — FR-005
- [X] T010 [P] [US2] Teste em `tests/test_purga.py`: as amostras no intervalo de embargo após o teste são removidas do treino — FR-006
- [X] T011 [P] [US2] Teste em `tests/test_purga.py`: a purga é **global** — uma amostra de um par sai do treino quando a janela de teste é de **outro** par, se o horizonte alcançar — D4, o defeito que a correlação de 0,71 tornaria invisível
- [X] T012 [P] [US2] Teste em `tests/test_purga.py`: purga que esvazia o treino abaixo do mínimo produz resultado inconclusivo, com o número declarado — FR-005/FR-011

### Implementation

- [X] T013 Implementar `ParametrosBarreira` e `rotular(df, params)` em `strategy/barreira_tripla.py`, devolvendo rótulo, rótulo bruto e `fim_horizonte`
- [X] T014 Implementar `ATRIBUTOS` e `extrair_atributos(df)` em `strategy/barreira_tripla.py` com os cinco de D3
- [X] T015 Implementar `distribuicao_classes(rotulos)` e `razao_de_chances(rotulos)` em `strategy/barreira_tripla.py`
- [X] T016 Implementar `DivisaoPurgada` e `dividir_com_purga(eventos, ratio, embargo)` em `backtesting/purga.py`, operando no eixo do tempo sobre todos os pares de uma vez
- [X] T017 Implementar a contagem de `n_purgadas` e `n_embargadas`, usadas pelo diagnóstico do relatório

**Checkpoint**: rotulagem causal provada, purga global provada.

---

## Phase 3: User Story 1 — Descobrir se o classificador supera as regras (P1) 🎯

**Goal**: produzir, por par, as métricas do modelo e das regras sobre a mesma
série e o mesmo período.

### Tests for User Story 1 ⚠️

- [X] T018 [P] [US1] Teste em `tests/test_modelo.py`: `AvaliacaoH14` calcula `delta_retorno`, `delta_drawdown` e `delta_exposicao` como modelo menos regras
- [X] T019 [P] [US1] Teste em `tests/test_modelo.py`: falha de convergência produz `nao_convergiu`, nunca métricas calculadas sobre estimação inválida — FR-012
- [X] T020 [P] [US1] Teste em `tests/test_modelo.py`: rótulos todos na mesma classe produzem `classe_unica` — FR-012
- [X] T021 [P] [US1] Teste em `tests/test_modelo.py`: amostra abaixo do mínimo em qualquer versão produz `inconclusivo`, nunca `piora` — FR-011

### Implementation for User Story 1

- [X] T022 [US1] Implementar `ResultadoModelo` e `estimar(treino, atributos)` em `backtesting/modelo.py`, com falha de convergência como estado explícito
- [X] T023 [US1] Implementar `razao_chances_decidido` em `ResultadoModelo` — a métrica central, medida apenas onde o modelo decide entrar
- [X] T024 [US1] Implementar `AvaliacaoH14` com as grandezas derivadas de `data-model.md`
- [ ] T025 [US1] Implementar `avaliar_par(par, params)` em `backtesting/modelo.py`, reusando `preparar()` e `_simular()` de `horizonte.py`
- [ ] T026 [US1] Implementar `run_modelo_scan(pares, params)`, sem abortar quando um par falha — FR-014
- [ ] T027 [US1] Implementar `cmd_modelo()` em `main.py` e os aliases `modelo` e `ml`

**Checkpoint**: US1 funcional. **Ainda não é MVP defensável — falta US3.**

---

## Phase 4: User Story 3 — Distinguir sinal de ajuste a ruído (P1)

**⚠️ Sem esta fase, US1 produz resposta inutilizável.** Um classificador sempre
encontra alguma estrutura; a pergunta é se ela está nos dados ou na capacidade
do modelo.

### Tests for User Story 3 ⚠️

- [X] T028 [P] [US3] Teste em `tests/test_modelo.py`: o embaralhamento preserva a distribuição das classes e destrói a associação atributo–rótulo — FR-007
- [X] T029 [P] [US3] Teste em `tests/test_modelo.py`: desempenho indistinguível do embaralhado produz `sem_sinal`, nunca aprovação — FR-008
- [X] T030 [P] [US3] Teste em `tests/test_modelo.py`: modelo que se distingue do embaralhado mas com `razao_chances_decidido <= 0,500` produz `insuficiente`, distinto de `sem_sinal` e de `melhora`
- [X] T031 [P] [US3] Teste em `tests/test_modelo.py`: `melhora` exige superar as regras, o embaralhado **e** a razão de empate, com confirmação fora da amostra

### Implementation for User Story 3

- [X] T032 [US3] Implementar `embaralhar_rotulos(rotulos, semente)` em `backtesting/modelo.py`, preservando a distribuição
- [ ] T033 [US3] Executar o modelo embaralhado em `avaliar_par` e armazenar em `AvaliacaoH14.embaralhado`
- [X] T034 [US3] Implementar `classificar_avaliacao` em `backtesting/modelo.py` com os 13 estados de `data-model.md`, **na ordem declarada**
- [ ] T035 [US3] Exibir `delta_vs_embaralhado` e `razao_chances_decidido` na tabela, adjacentes aos deltas contra as regras
- [ ] T036 [US3] Adicionar legenda em `main.py` para `sem sinal`, `insuficiente`, `confundido`, `só na busca`, e declarar por que acurácia não aparece

**Checkpoint**: MVP defensável.

---

## Phase 5: User Story 2 — Tornar a purga verificável no relatório (P1)

**Nota**: o mecanismo já está na Foundational. Esta fase o torna **visível**.

### Tests for User Story 2 ⚠️

- [ ] T037 [P] [US2] Teste em `tests/test_purga.py`: sobre as séries reais do universo, nenhuma amostra de treino tem horizonte alcançando teste ou embargo
- [ ] T038 [P] [US2] Teste em `tests/test_purga.py`: a contagem de purgadas e embargadas é reportada e diferente de zero quando há sobreposição

### Implementation for User Story 2

- [ ] T039 [US2] Implementar o diagnóstico de purga na saída de `main.py`: amostras removidas por sobreposição e por embargo, e o treino restante

---

## Phase 6: User Story 4 — Separar vantagem de custo de giro (P2)

### Tests for User Story 4 ⚠️

- [ ] T040 [P] [US4] Teste em `tests/test_modelo.py`: `delta_operacoes` e `delta_custo` são calculados entre modelo e regras
- [ ] T041 [P] [US4] Teste em `tests/test_modelo.py`: reexecução sem custo produz retorno maior ou igual em ambas as versões

### Implementation for User Story 4

- [ ] T042 [US4] Implementar `retorno_sem_custo_modelo` e `retorno_sem_custo_regras` em `avaliar_par`
- [ ] T043 [US4] Exibir operações e custo de cada versão, e o agregado de custo de giro no resumo

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T044 [P] Exportar para `reports/modelo_{timestamp}.{json,csv,md}` via `utils/report_export.py`
- [ ] T045 [P] Documentar o comando em `CLAUDE.md` e `AGENTS.md` **no mesmo commit**
- [ ] T046 [P] Documentar em `docs/08-comandos-cli.md`, incluindo o limiar de 0,500 e por que acurácia não é a métrica
- [ ] T047 Executar a avaliação completa **sem truncar a saída** e registrar o veredito de H14 em `docs/research/registro-de-hipoteses.md`, confrontando as predições de `research.md` com o observado
- [ ] T048 Registrar a declaração de executabilidade (FR-017), incluindo a ausência de retreino e de detecção de degradação
- [ ] T049 Reordenar a fila conforme o resultado, e atualizar a nota §6.3-b sobre a família direcional
- [ ] T050 Executar os doze cenários de `quickstart.md`
- [ ] T051 Confirmar `git diff --stat` vazio em `risk/`, `execution/`, `trading/`, `strategy/` (exceto o arquivo novo) e nos arquivos de dependência, e rodar a suíte completa sem redução na contagem

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (F1)**: sem dependências
- **Foundational (F2)**: depende de F1 — **BLOQUEIA todas as histórias**
- **US1 (F3)**: depende de F2
- **US3 (F4)**: depende de F3 — as duas formam o MVP
- **US2 (F5)**: mecanismo em F2; exibição depende de F3
- **US4 (F6)**: depende de F3
- **Polish (F7)**: depende das histórias desejadas

### Dependência específica

T047 depende de T044: o veredito só pode ser registrado depois que a avaliação
rodar e o relatório existir. **A execução não pode ser truncada** — em H12 um
`| head` fechou o pipe, o processo morreu antes de exportar, e o relatório mais
recente no diretório era o da execução anterior.

### Within Each User Story

- Testes escritos e **falhando** antes da implementação (Constituição III)
- Entidades antes dos serviços; serviços antes da exibição

### Parallel Opportunities

- T004–T012 em paralelo (testes de rotulagem e purga)
- T018–T021, T028–T031, T037–T038, T040–T041 em paralelo
- T044, T045 e T046 em paralelo

**Restrição real:** T013–T017, T022–T027, T032–T036, T039 e T042–T043 escrevem
nos mesmos três arquivos de código e são sequenciais entre si.

---

## Implementation Strategy

### MVP = US1 **e** US3

Como nas specs 025 e 026, o MVP exige duas histórias. US1 sozinha produz uma
tabela em que qualquer desempenho aparece como descoberta. Parar ali seria pior
que não implementar.

1. F1 Setup
2. F2 Foundational — rotulagem causal e purga global; bloqueia tudo
3. F3 US1
4. F4 US3
5. **PARAR e VALIDAR**: cenários 5 e 6 do `quickstart.md`
6. Só então a pergunta de H14 está respondida de forma utilizável

---

## Notes

- **Predição registrada em `research.md` antes da execução:** o resultado mais
  provável é que o modelo não se distinga do embaralhado. Nesse caso H14 fecha a
  família direcional com catorze hipóteses de suporte.
- **Segunda predição:** se o modelo se distinguir do embaralhado mas não atingir
  a razão de 0,500, o estado correto é `insuficiente` — categoria nova, e o
  achado desta spec.
- Se a estimação não convergir na maioria dos pares, é defeito de colinearidade,
  não achado — a Fase 0 selecionou atributos com correlação máxima de 0,699 para
  evitar isso.
- Nenhuma task altera `risk/`, `execution/`, `trading/` ou os arquivos de
  dependência. T051 verifica.
