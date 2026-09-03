# Feature Specification: H20 reavaliada com histórico estendido

**Feature Branch**: `048-h20-historico-estendido`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: Reavaliar H20 (geometria de barreira) com
o histórico estendido de 6.000 candles (spec 036), a mesma elevação de
amostra que já fez o veredito de H14 mudar drasticamente (z=+0,50 →
z=+7,97). `backtesting/geometria.py::run_geometria_scan` foi
explicitamente excluído do escopo da spec 036 (D2) e continua com o
teto antigo de 2.000 candles — questão em aberto já registrada no
próprio registro (§4.15, atualização spec 036: "Se a mesma elevação de
amostra que resolveu H14 também desloca H20, é uma pergunta em aberto,
não uma correção deste registro"). Com 2.000 candles, H20 mediu a razão
de chances aterrissando a menos de 3% do ponto de empate em DUAS
geometrias independentes (0,997 e 1,027) — margem estreita o bastante
para ser plausivelmente um artefato de amostra pequena. **Nota de
correção em relação à intuição inicial**: diferente do veredito
original de H14 (achado M13, comparação por ponto único sem banda de
incerteza), a avaliação de H20 já nasceu depois de M13 ser corrigido e
já usa teste estatístico apropriado (contagem esperada vs. observada
sob a hipótese de empate, `run_modelo_scan` com
`ParametrosBarreira(tp_mult=2.0, sl_mult=1.5)` — D4/D3 de
`specs/028-geometria-de-barreira/research.md`) — não é um caso de M13
não corrigido, é uma medição já rigorosa que pode simplesmente mudar
com mais amostra, como qualquer teste estatístico legítimo pode. Muda
só o teto de candles de `fetch_ohlcv` em `run_geometria_scan` e em
`run_modelo_scan`/`coletar_eventos` (2.000 → 6.000, mesmo valor e mesma
justificativa de `specs/036-historico-estendido/`) — nenhuma mudança na
regra de seleção de geometria (FR-003/004/014 de spec 028, que
continuam valendo intocadas), nenhuma mudança no procedimento
estatístico de avaliação (D3/D4 de spec 028, já reusa
`run_modelo_scan` sem alteração de lógica), nenhum novo parâmetro,
nenhuma nova geometria candidata.

---

## Contexto e tese

**Por que agora, e por que isto fecha ou reabre a linha de investigação
de H14.** A conclusão registrada ao fechar os overlays de risco de H14
(specs 040-047) é que o gargalo não é composição de risco, é o profit
factor por trade — e a explicação estrutural para esse profit factor
baixo, medida em H20, é que o sinal aterrissa quase exatamente no ponto
de empate da geometria de saída. Se essa medição de empate for, ela
mesma, um artefato de amostra pequena (2.000 candles, a mesma limitação
que produziu o veredito errado original de H14), a conclusão de que "o
problema é o mecanismo de saída, não mais risco" pode estar apoiada
numa medição que não sobreviveria a mais dados — exatamente o padrão
que já aconteceu uma vez nesta investigação (H14, spec 036).

**Não é uma hipótese nova.** É a mesma pergunta de H20 (geometria de
barreira resolve a margem?), sobre o mesmo instrumento
(`backtesting/geometria.py` para seleção, `backtesting/modelo.py::
run_modelo_scan` para avaliação estatística — D4 de
`specs/028-geometria-de-barreira/research.md`), com o mesmo critério de
elegibilidade (FR-003/004/014 de spec 028) e o mesmo teste estatístico
(D3) — só a amostra muda, do jeito já validado por
`specs/036-historico-estendido/` para H14/H11/H17.

**Zero mecânica nova.** `run_geometria_scan` já aceita override de
`pares`; o ponto de mudança é o argumento `2000` → `6000` da chamada
`fetch_ohlcv` na linha 204 de `backtesting/geometria.py` — mesmo padrão
já aplicado em `backtesting/modelo.py`, `backtesting/onchain_hipotese.py`
e `backtesting/horizonte.py` (D2 de spec 036 excluiu especificamente
este módulo; esta spec fecha essa exclusão). A avaliação da geometria
selecionada (`run_modelo_scan` com `ParametrosBarreira` da geometria
escolhida) já herda o teto de 6.000 automaticamente — `modelo.py` já
foi migrado por spec 036.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reavaliar H20 com 6.000 candles (Priority: P1)

O pesquisador obtém a razão de chances de cada geometria candidata e o
veredito de elegibilidade sobre 6.000 candles (em vez de 2.000),
comparado explicitamente contra os números já publicados (razão/empate
0,997 em tp=2,0; 1,027 em tp=3,0 via H14).

**Why this priority**: é a pergunta da hipótese — sem o comparativo, não
há como saber se a margem estreita medida em H20 sobrevive a 3x mais
amostra ou se, como em H14, o veredito muda de forma que reabre a linha
de investigação da geometria de saída.

**Independent Test**: rodar `run_geometria_scan` com `2000` e com
`6000` sobre um cenário sintético reproduzível e confirmar que
`medir_perfis`/`selecionar` continuam determinísticos e sem exceção
com uma série 3x maior.

**Acceptance Scenarios**:

1. **Given** os 12 pares de `UNIVERSO_H11`, **When**
   `run_geometria_scan` roda com 6.000 candles, **Then** produz um
   `RelatorioGeometria` com a mesma estrutura de antes (perfis, geometria
   selecionada, regra declarada) — nenhum campo novo.
2. **Given** o resultado com 6.000 candles, **When** comparado ao já
   publicado (2.000 candles), **Then** os dois aparecem lado a lado no
   registro — o antigo nunca é apagado, só marcado como superado ou
   confirmado.
3. **Given** a nova amostra, **When** a razão de chances da geometria
   selecionada é avaliada contra o empate, **Then** usa o mesmo teste
   estatístico já aplicado no relatório original de H20 (contagem
   esperada vs. observada sob a hipótese de empate, via
   `run_modelo_scan`) — sem inventar um critério novo nem comparar só o
   ponto estimado.

---

### Edge Cases

- Se `MIN_DESFECHOS` (1000) não for atingido nem com 6.000 candles: seria
  o mesmo problema estrutural de H10 (universo pequeno demais) — resultado
  `inconclusivo`, não forçado a um veredito.
- Se a regra de seleção (FR-003/004/014 de spec 028) não elegir nenhuma
  geometria com a amostra maior: desfecho legítimo já previsto pelo
  próprio `selecionar()` (`None`), sem necessidade de ajuste de regra.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST mudar o teto de candles de
  `run_geometria_scan` de 2.000 para 6.000, mesmo valor e mesma
  justificativa declarados em `specs/036-historico-estendido/research.md`
  (D1) — sem nova medição de teto de histórico.
- **FR-002**: O sistema MUST NOT alterar a regra de seleção de geometria
  (`selecionar`, `regra_declarada`, `TPS_CANDIDATOS`, `SL_FIXO`,
  `FOLGA`, `ELEVACAO_H14`) — a regra já foi declarada antes de qualquer
  medição (FR-003 de spec 028) e mudar seus parâmetros agora reabriria
  exatamente o problema de ajuste-ao-resultado que a regra existe para
  evitar.
- **FR-003**: O sistema MUST avaliar a razão de chances da geometria
  selecionada com o mesmo teste estatístico já usado no relatório
  original de H20 (contagem esperada vs. observada sob a hipótese de
  empate, via `run_modelo_scan` com a `ParametrosBarreira` da geometria
  escolhida) — sem inventar critério novo.
- **FR-004**: O sistema MUST reportar o resultado com 6.000 candles ao
  lado do já publicado (2.000 candles) no registro — nunca substituindo.
- **FR-005**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/`.

### Key Entities

- Nenhuma entidade nova — `PerfilGeometria`/`RelatorioGeometria`
  (`backtesting/geometria.py`) reusados sem alteração de schema.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um `RelatorioGeometria` sobre 6.000 candles é produzido,
  comparável em estrutura ao já publicado (2.000 candles).
- **SC-002**: O veredito estatístico (contagem esperada vs. observada,
  z/p) sobre a geometria selecionada é registrado, mesmo teste do
  relatório original de H20.
- **SC-003**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **6.000 candles**: mesmo teto já medido e validado em
  `specs/036-historico-estendido/` para todo o `UNIVERSO_H11` — reusado
  sem remedição.
- **Regra de seleção de geometria**: já declarada em spec 028 — reusada
  sem alteração (FR-002).
- Confirmação ou reversão do veredito REPROVADA de H20 não invalida o
  fechamento da linha de overlays de risco de H14 (specs 040-047) — são
  perguntas relacionadas mas distintas: aquela pergunta se risco de
  carteira resolve o drawdown, esta pergunta se a geometria de saída
  resolve a margem por trade. Se H20 reverter, reabre uma frente
  diferente (ajustar a geometria de saída), não desfaz o fechamento dos
  overlays de risco.
