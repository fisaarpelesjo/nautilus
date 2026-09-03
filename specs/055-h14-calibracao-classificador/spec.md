# Feature Specification: H14 — calibração do classificador de entrada

**Feature Branch**: `055-h14-calibracao-classificador`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: A linha de overlays de risco sobre a
carteira de H14 fechou (specs 040-047, teto de drawdown ~20%/profit
factor 0,68, nenhuma combinação resolve) apontando para dois próximos
passos: o classificador de entrada em si, ou o mecanismo de saída. Esta
spec ataca o classificador: o subconjunto já decidido em produção
(prob > `limiar_de_decisao`) tem razão de chances que sobrevive ao
teste de confiança do projeto (`supera_empate_com_confianca`)? Um corte
mais estrito (menos trades, mais confiantes) concentra qualidade — razão
sobe de forma sustentada — ou só reduz a amostra sem melhorar a razão?
Pooled sobre `UNIVERSO_H11`, sem tocar em nenhum parâmetro do modelo —
só agrupa previsões já calculadas (`avaliar_par(..., retornar_previsao=True)`,
existente desde spec 037) por corte de probabilidade.

---

## Contexto e tese

**Por que o classificador agora, não mais overlay de risco.** Spec 047
fechou a linha de investigação de overlays de risco com uma frase
explícita: "nenhum overlay que só decide QUANDO/QUANTO abrir consegue
consertar uma taxa de acerto por trade que já nasce abaixo do
necessário. Os próximos passos, se houver, atacam outra parte do
mecanismo — o classificador de entrada em si (...) ou o mecanismo de
saída". Esta spec testa a primeira opção antes da segunda porque é mais
barata de medir: reusa a probabilidade já calculada por `avaliar_par`,
sem precisar reimplementar o mecanismo de saída da carteira.

**Hipótese declarada antes de medir.** O classificador emite uma
probabilidade contínua; a produção binariza em `prob > limiar_de_decisao`
(0,3333, derivado das barreiras — não é parâmetro ajustável). Se a
probabilidade for bem calibrada, um corte mais estrito que 0,3333 deveria
concentrar as previsões mais confiantes e produzir razão de chances
**maior e crescente** à medida que o corte sobe — abrindo caminho para
uma variante de entrada por confiança (só operar acima de um corte mais
alto) capaz de reduzir o número de trades ruins sem descartar os bons.

**Expectativa alternativa, também declarada.** Se a probabilidade for
apenas "boa o bastante para cruzar o limiar de decisão, mas não
ordenada dentro do subconjunto decidido" (achatada), subir o corte só
reduz a amostra sem melhorar a razão de forma sustentada — refutando a
variante de entrada por confiança sem precisar construí-la.

**Zero mecânica nova em produção.** Reusa `avaliar_par`,
`coletar_eventos`, `limiar_de_decisao`, `limiar_de_empate`,
`supera_empate_com_confianca` (todos de `backtesting/modelo.py`, sem
alteração) e `rotular` (`strategy/barreira_tripla.py`, sem alteração).
Nenhum parâmetro de trading, risco ou execução muda.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir a razão de chances por corte de confiança (Priority: P1)

O pesquisador obtém, para uma lista de cortes de probabilidade
(incluindo o limiar real de produção), quantas previsões cada corte
mantém e qual a razão de chances alvo/stop realizada nesse subconjunto,
com o veredito de `supera_empate_com_confianca` para cada um.

**Why this priority**: é a pergunta da hipótese — decide se existe uma
cauda de alta confiança explorável ou não.

**Independent Test**: `avaliar_calibracao` sobre previsões e rótulos
sintéticos (sem buscar dado real) produz as contagens corretas de
alvo/stop/tempo por corte e delega a significância à função já testada
do projeto.

**Acceptance Scenarios**:

1. **Given** `UNIVERSO_H11` e os parâmetros padrão de H14, **When**
   `avaliar_calibracao()` roda, **Then** devolve o limiar real, o ponto
   de empate e uma faixa por corte testado (incluindo o limiar real como
   corte 0) com n/alvo/stop/tempo/razão/significância.
2. **Given** o resultado, **When** comparado corte a corte, **Then** o
   registro documenta se a razão cresce de forma sustentada (confirma a
   hipótese) ou fica achatada / colapsa em amostra (refuta).

---

### Edge Cases

- **Corte sem nenhum stop**: razão vira infinito; `supera_empate_com_confianca`
  não roda sobre denominador zero — tratado como "não significativo" por
  falta de evidência, não como aprovação automática.
- **Corte tão alto que a amostra fica de dígito único**: esperado e
  informativo — mostra onde a amostra deixa de sustentar qualquer
  leitura, não é tratado como erro.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST agrupar as previsões pooled de
  `UNIVERSO_H11` por uma lista de cortes de probabilidade, incluindo o
  limiar real de decisão como um dos cortes.
- **FR-002**: Para cada corte, o sistema MUST contar alvo/stop/tempo a
  partir de `rotulo_bruto` (não de `rotulo`, que colapsa stop e tempo).
- **FR-003**: Para cada corte, o sistema MUST aplicar
  `supera_empate_com_confianca` (Wilson CI) sobre as contagens daquele
  corte especificamente — nunca ler a razão pontual isolada.
- **FR-004**: O sistema MUST reportar os cortes lado a lado (não
  escolher um "vencedor" sem mostrar os demais).
- **FR-005**: O sistema MUST NOT alterar nenhum parâmetro de
  `strategy/`, `risk/`, `execution/` ou `trading/`.

### Key Entities

- **FaixaCalibracao**: corte, n, alvo, stop, tempo, razão, se supera o
  empate com confiança.
- **ResultadoCalibracao**: limiar real, empate, número de pares, lista
  de `FaixaCalibracao`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `python main.py calibracao` produz a tabela de faixas por
  corte, reproduzível a qualquer momento.
- **SC-002**: O registro de hipóteses documenta explicitamente se a
  hipótese de cauda de alta confiança se confirma ou se refuta, com os
  números medidos.
- **SC-003**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Universo e barreiras**: `UNIVERSO_H11` (12 pares) e
  `ParametrosBarreira()` padrão (stop 1,5×ATR, alvo 3,0×ATR, 24 velas) —
  os mesmos de toda a linha de investigação de H14 (specs 036-047).
- Se a hipótese for refutada, fecha a frente de "filtro de confiança
  binário" especificamente — não fecha a frente do classificador como um
  todo (ex.: dimensionar posição pela confiança, em vez de filtrar, é uma
  hipótese distinta e não testada aqui).
- Resultado desta spec não substitui nenhum veredito já publicado de
  H14 — é uma pergunta nova sobre o mesmo classificador já medido.
