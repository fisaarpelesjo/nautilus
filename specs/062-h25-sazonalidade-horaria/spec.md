# Feature Specification: H25 — sazonalidade por sessão de negociação (hora do dia)

**Feature Branch**: `062-h25-sazonalidade-horaria`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: H5 (filtro de dia da semana) foi reprovada por
"só na busca" — passou na janela de descoberta, não se sustentou fora
dela. H25 testa a mesma ideia geral (restringir entradas por tempo) numa
granularidade diferente, nunca testada: hora do dia (sessão de
negociação — asiática, europeia, americana), não dia da semana.
Criptomoedas negociam 24/7, mas o volume histórico é dominado por
janelas horárias específicas.

---

## Contexto e tese

**Por que hora do dia, não mais dia da semana.** H5 já testou e reprovou
o filtro por dia da semana — replicar a mesma pergunta na mesma
granularidade não acrescentaria nada. Hora do dia é uma granularidade
genuinamente diferente: dentro de um único dia da semana, o volume e a
volatilidade de cripto variam por sessão de negociação dominante
(literatura de mercados 24/7 documenta isso em FX, mercado análogo mais
próximo).

**A armadilha que esta spec precisa evitar por construção, não por
esperança.** H5 falhou especificamente em "só na busca" — o filtro
melhorava o profit factor na janela onde foi descoberto, mas não se
sustentava fora dela. Esta spec usa a MESMA bateria de confirmação fora
da amostra que H10/H14/H20 já usam
(`backtesting.multimarket.classify`/`split_train_validation`) e reporta
TODAS as combinações testadas (3 janelas × 12 pares = 36),
pré-registradas antes de qualquer medição — não escolhidas depois de
olhar o resultado.

**Hipótese declarada antes de medir.** Pelo menos uma combinação
janela×par produz status `confirmado` (aprovada na busca E na
validação) — evidência real, não sorte de janela única.

**Hipótese alternativa, com igual peso.** Nenhuma combinação confirma —
mesmo padrão de H5, a hora do dia não carrega informação que a
estratégia de regras já não capture, e a família "filtro de tempo sobre
H1" fecha definitivamente (H5 dia da semana + H25 hora do dia, as duas
granularidades óbvias, ambas testadas).

**Escopo mínimo, zero mudança em produção.** Filtro aplicado só na
camada de backtest (máscara sobre o sinal já calculado por
`precompute_signals`) — não toca `strategy/ema_rsi.py` nem
`config/settings.py`. Nenhum parâmetro novo em produção.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir o efeito do filtro por sessão, confirmado fora da amostra (Priority: P1)

O pesquisador obtém, para cada combinação de janela horária (asiática/
europeia/americana) × par de `UNIVERSO_H11`, o profit factor com e sem
o filtro na janela de busca, e o status de confirmação fora da amostra
(`confirmado`/`defensivo`/`só_na_busca`/`reprovado`/`inconclusivo`/`erro`).

**Why this priority**: é a pergunta da hipótese — replica H5 numa
granularidade nova, com a disciplina que faltou em H5.

**Independent Test**: `filtrar_por_sessao` sobre uma série de sinais
sintética mascara `BUY` fora da janela e nunca toca `SELL` — testável
sem dado real.

**Acceptance Scenarios**:

1. **Given** um sinal `BUY` fora da janela declarada, **When**
   `filtrar_por_sessao` roda, **Then** o sinal vira `HOLD`.
2. **Given** um sinal `SELL` em qualquer hora, **When**
   `filtrar_por_sessao` roda, **Then** o sinal nunca é alterado.
3. **Given** as 36 combinações avaliadas, **When** reportadas, **Then**
   todas aparecem — nenhuma selecionada post-hoc por parecer melhor.
4. **Given** uma combinação com status `confirmado`, **When** o
   registro é escrito, **Then** é explicitamente distinguida de
   `só_na_busca`/`defensivo` — nunca apresentada como aprovação se não
   for `confirmado`.

---

### Edge Cases

- **Par com erro de busca de dado**: status `erro`, não interrompe a
  avaliação dos demais pares/janelas (mesmo padrão de `run_scan`).
- **Histórico insuficiente para dividir busca/validação**: status
  `inconclusivo` (herdado de `classify`), nunca aprovação por omissão.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST mascarar apenas sinais `BUY` fora da
  janela declarada — `SELL` nunca é bloqueado (posição já aberta sempre
  pode sair).
- **FR-002**: O sistema MUST testar as três janelas pré-registradas
  (asiática 0-8h, europeia 8-16h, americana 16-24h UTC) sobre
  `UNIVERSO_H11` — sem seleção post-hoc de qual janela reportar.
- **FR-003**: O sistema MUST classificar cada combinação via
  `backtesting.multimarket.classify` (mesma bateria de confirmação fora
  da amostra já usada por H10/H14/H20) — nenhum critério novo.
- **FR-004**: O sistema MUST NOT alterar `strategy/ema_rsi.py`,
  `config/settings.py` nem qualquer comportamento de produção.
- **FR-005**: O sistema MUST NOT enviar ordem real.

### Key Entities

- **ResultadoSazonalidadePar**: par, janela, profit factor base/filtrado
  na busca, status de confirmação.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `python main.py sazonalidade` produz as 36 combinações,
  cada uma com status de confirmação fora da amostra.
- **SC-002**: O registro documenta explicitamente quantas combinações
  (de quantas testadas) atingem `confirmado` — nunca confunde `só_na_busca`
  com aprovação.
- **SC-003**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Universo e timeframe**: `UNIVERSO_H11` (12 pares), `4h` — mesmos de
  toda a linha de investigação deste registro.
- Se nenhuma combinação confirmar, fecha a família "filtro de tempo
  sobre H1" (H5 + H25, as duas granularidades óbvias) — não motiva mais
  variações de janela horária sem uma hipótese de mecanismo nova.
