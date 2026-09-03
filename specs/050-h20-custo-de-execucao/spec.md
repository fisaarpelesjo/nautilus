# Feature Specification: H20 — isolando o efeito do custo de execução

**Feature Branch**: `050-h20-custo-de-execucao`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: Spec 049 mediu o backtest real da
geometria `tp=2,0` (já confirmada estatisticamente em spec 048) e
encontrou 11/12 pares reprovados — divergência entre o sinal de rótulo
e a lucratividade real, com três mecanismos candidatos registrados sem
isolar nenhum: payoff pior (2:1,5 contra 3:1,5), trailing stop
diferente da barreira estática de rotulagem, e amostra por par uma
ordem de grandeza menor que a pooled. Esta spec isola o primeiro
candidato — custo de execução — reusando o mesmo método já aplicado a
H10 (E6, `docs/research/registro-de-hipoteses.md` linha 586: "+3,96%
com custo, +5,56% sem — custo consome 29% da vantagem bruta") e a H21
(E6, linha 2386): reexecutar com taxa e slippage zerados e comparar
contra o resultado com custo real. `backtesting/modelo.py::avaliar_par`
já calcula isso — o campo `AvaliacaoH14.retorno_sem_custo_modelo` já
existe desde H14 (spec 027) e já reflete a geometria correta desde a
correção de spec 049 (o bloco "E6 — custo de giro" foi um dos três
locais corrigidos). Não precisa de backtest novo: `cmd_geometria()`
(spec 048/049) já produz a lista `avaliacoes` com este campo populado
— só falta extrair e comparar.

---

## Contexto e tese

**Por que este candidato primeiro.** Dos três mecanismos candidatos
registrados em spec 049, o custo de execução é o único que já tem
instrumento pronto e testado (E6, usado em H10 e H21) — medir os
outros dois (trailing stop vs. barreira estática; amostra por par)
exigiria mecânica nova. Testar o candidato mais barato primeiro, antes
de construir instrumentação nova para os outros dois, é a ordem que
minimiza esforço por informação obtida.

**Não decide os outros dois candidatos.** Se o custo explicar toda a
divergência, os outros dois candidatos ficam sem necessidade de teste
adicional — navalha de Occam aplicada depois de medir, não antes. Se o
custo explicar só parte, os outros dois continuam candidatos em aberto
para specs futuras.

**Zero mecânica nova.** `retorno_sem_custo_modelo` já existe, já é
calculado automaticamente por `avaliar_par` sempre que o modelo
converge (bloco "E6 — custo de giro", `backtesting/modelo.py`), e já
usa a geometria correta desde a correção de spec 049. Esta spec só
expõe o campo já calculado — nenhuma chamada de backtest adicional.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Comparar retorno com e sem custo, por par (Priority: P1)

O pesquisador obtém, por par, o retorno real (com custo, já publicado
em spec 049) ao lado do retorno sem custo (`retorno_sem_custo_modelo`,
já calculado), e a fração da vantagem bruta que o custo consome —
mesma métrica já usada em H10/H21.

**Why this priority**: é a pergunta da hipótese — sem o comparativo,
não há como saber se o custo de execução é (parte d)a explicação para
a divergência entre o sinal de rótulo confirmado e o backtest real
reprovado.

**Independent Test**: confirmar que `avaliacoes` (já produzido por
`run_modelo_scan` dentro de `cmd_geometria`) tem `retorno_sem_custo_modelo`
populado para todo par com `a.modelo.convergiu`, e que o valor reflete
a geometria `tp=2,0` (não a de produção) — regressão já coberta por
spec 049.

**Acceptance Scenarios**:

1. **Given** os 12 pares já avaliados com a geometria `tp=2,0`
   (spec 049), **When** `cmd_geometria` (ou uma extensão dele) compara
   `total_return_pct` (com custo) contra `retorno_sem_custo_modelo`
   (sem custo) por par, **Then** reporta os dois números e a fração
   consumida, mesma fórmula de H10/H21.
2. **Given** o resultado agregado, **When** comparado à divergência
   registrada em spec 049 (11/12 pares reprovados), **Then** o
   registro declara explicitamente se o custo explica toda, parte, ou
   nenhuma fração observável da divergência.

---

### Edge Cases

- Par sem `a.modelo.convergiu`: `retorno_sem_custo_modelo` permanece
  `None` — já tratado pelo código existente, sem necessidade de
  mudança.
- Vantagem bruta (sem custo) negativa ou zero: a fração "consumida"
  não tem leitura direta (dividir por uma vantagem negativa inverte o
  sinal) — reportado como caso à parte, não forçado à fórmula padrão.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST reportar, por par, `total_return_pct`
  (com custo) e `retorno_sem_custo_modelo` (sem custo), ambos já
  calculados por `avaliar_par` — nenhum backtest novo.
- **FR-002**: O sistema MUST calcular a fração da vantagem bruta
  consumida pelo custo, mesma fórmula já usada em H10/H21
  (`(sem_custo - com_custo) / sem_custo`), quando `sem_custo` for
  positivo.
- **FR-003**: O sistema MUST agregar a comparação (ex.: quantos pares
  teriam sido aprovados sem custo) e registrar se o custo explica a
  divergência de spec 049, total ou parcialmente.
- **FR-004**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/`.

### Key Entities

- Nenhuma entidade nova — `AvaliacaoH14.retorno_sem_custo_modelo` já
  existe.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Comparação com/sem custo é reportada por par, sem
  backtest adicional.
- **SC-002**: O registro declara explicitamente a fração da
  divergência de spec 049 explicada por custo.
- **SC-003**: Nenhuma ordem real é enviada; produção permanece
  idêntica.

---

## Assumptions

- **Geometria avaliada**: `tp=2,0`, a mesma de specs 048/049 — nenhuma
  escolha nova.
- Esta spec não decide os outros dois candidatos (trailing stop,
  amostra por par) — ficam em aberto, condicionados ao resultado
  medido aqui.
