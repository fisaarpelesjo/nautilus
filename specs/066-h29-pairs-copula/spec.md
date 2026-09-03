# Feature Specification: H29 — pairs trading via cópula gaussiana

**Feature Branch**: `066-h29-pairs-copula`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: H10 (arbitragem estatística por cointegração,
`backtesting/pairs_trading.py`) mede a distância entre os dois preços
via z-score sobre um spread linear — REPROVADA (2026-09-03, profit
factor 0,15, drawdown 16,61%). Cópulas modelam a distribuição conjunta
completa dos retornos das duas pernas, capturando dependência não-linear
(cauda) que o z-score linear não vê — mecanismo estatisticamente
diferente sobre o MESMO par de ativos. Já citado nas referências do
registro (`docs/research/copula-based-trading-of-cointegrated-
cryptocurrency-pairs.md`, Tadi & Witzany 2025), nunca implementado.
Adicionada à fila em 2026-09-03 junto com H27/H28/H30/H31/H32/H33,
revisão de literatura pós-encerramento da busca original.

---

## Contexto e tese

**Por que testar de novo o mesmo par de ativos.** H10 já respondeu "os
pares cointegram?" (sim) e "um sinal linear (z-score) sobre isso
produz vantagem operável?" (não, por margem ampla). Esta spec pergunta
uma coisa diferente: será que a dependência captada pela cópula — que
o z-score, por ser uma medida de distância linear no spread, não
enxerga — produz um sinal de entrada/saída de qualidade diferente sobre
os MESMOS pares cointegrados?

**Precondição verificada antes de qualquer código.** Antes de escrever
o módulo de cópula, `selecionar_pares`/`PairsParams` de H10 (sem
alteração) foram rodados sobre dado real (`UNIVERSO_AMPLO_HISTORICO_
COMPLETO`, 22 pares, 6.000 candles): 3 pares cointegrados reais
encontrados na janela final (SOL-AVAX meia-vida 9,6, ETH-AVAX 13,5,
BNB-AVAX 15,7, todos ADF p < 0,02). A precondição — "existe relação
real pra modelar" — está satisfeita; H10 foi reprovada pelo SINAL, não
pela ausência de relação. Sem essa checagem, construir a cópula sobre
pares que não cointegram desperdiçaria esforço numa pergunta já
respondida.

**Hipótese declarada antes de medir.** A cópula gaussiana, aplicada
sobre os mesmos pares e o mesmo mecanismo long-only de H10, produz um
resultado materialmente diferente (profit factor mais alto, drawdown
mais baixo) do z-score linear.

**Hipótese alternativa, com igual peso.** O sinal de entrada, embora
estatisticamente mais sofisticado, não muda o resultado econômico —
mesma leitura de H10 (PF 0,15) com uma ferramenta mais cara. Isso seria
consistente com a leitura acumulada do registro (§8): o obstáculo é
custo de execução e geometria de saída, não a forma exata do sinal
estatístico de entrada.

**Restrição herdada de H10, sem mudança.** Long-only (chaves spot-only,
CLAUDE.md) — mesma sacrifício de neutralidade a mercado já declarado em
H10, avaliado com o mesmo `ganho_de_timing_pp` onde aplicável.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir o resultado do sinal de cópula sobre os pares de H10 (Priority: P1)

O pesquisador obtém drawdown, profit factor e total de trades da
carteira de pares operada pelo sinal de cópula, treino e validação,
comparado lado a lado com o resultado já publicado de H10 (z-score).

**Why this priority**: é a pergunta da hipótese.

**Independent Test**: `run_pairs_copula_backtest` sobre um par
cointegrado sintético (mesmo gerador de `tests/test_pairs_trading.py`)
abre e fecha posições coerentes com o sinal de cópula, sem exceção.

**Acceptance Scenarios**:

1. **Given** um par cointegrado real (`selecionar_pares`, sem
   alteração), **When** `run_pairs_copula_backtest` roda, **Then**
   produz um `BacktestResult` usando h1|2 (distribuição condicional da
   cópula) como sinal de entrada/saída em vez de z-score.
2. **Given** o resultado da validação, **When** comparado ao já
   publicado de H10 (spec 054: 10 trades, PF 0,15, drawdown 16,61%),
   **Then** os dois aparecem lado a lado — nunca um substitui o outro.
3. **Given** rho=0 (independência) ou u1=u2=0,5 (equilíbrio), **When**
   `h_condicional` é avaliado, **Then** devolve os valores de
   referência da forma fechada (h=u1 sob independência; h=0,5 no
   equilíbrio) — verificável analiticamente, sem depender de dado real.

---

### Edge Cases

- **Correlação da cópula (rho) próxima de ±1**: `h_condicional` usa
  `max(1e-9, 1 - rho²)` no denominador — não divide por zero.
- **Janela de formação menor que o mínimo (30 observações)**: o par é
  pulado nesse candle (sinal `None`), não gera erro nem entrada
  espúria.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST reusar `selecionar_pares`/`PairsParams` de
  H10 sem alteração — a seleção de pares não muda.
- **FR-002**: O sistema MUST ajustar a cópula (marginais via CDF
  empírica, correlação gaussiana sobre os escores normais) só com dados
  até o candle anterior ao avaliado — nunca vazar o candle atual para a
  própria cópula que o avalia.
- **FR-003**: O sistema MUST declarar UMA família de cópula (gaussiana)
  e UM corte de entrada/saída antes de qualquer medição real — sem
  testar múltiplas famílias/cortes e escolher o melhor depois.
- **FR-004**: O sistema MUST usar o mesmo split treino/validação de H10
  (`split_treino_validacao`) e o mesmo `evaluate_approval` — sem
  critério novo.
- **FR-005**: O sistema MUST reportar o resultado ao lado do já
  publicado de H10 — nunca substituindo.
- **FR-006**: O sistema MUST NOT enviar ordem real nem alterar
  `trading/`, `execution/` ou `risk/`.

### Key Entities

- **CopulaParams**: formação, corte de entrada (`entrada_h`), corte de
  saída (`saida_h`), corte de stop (`stop_h`), máximo de pares.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `python main.py pairs_copula` produz treino/validação
  comparável ao já publicado de H10.
- **SC-002**: O veredito de `evaluate_approval()` é registrado, sem
  critério novo.
- **SC-003**: Nenhuma ordem real é enviada; produção permanece idêntica.

---

## Assumptions

- **Universo**: `UNIVERSO_AMPLO_HISTORICO_COMPLETO` (22 pares, mesmo de
  H10) — comparabilidade direta.
- Resultado desta spec não substitui o veredito já publicado de H10 —
  é uma pergunta nova sobre o mesmo par de ativos.
- Cópula gaussiana (não t-Student nem outras famílias) — declarada como
  a mais simples e defensável, mesma disciplina de simplicidade de H14
  ("6 parâmetros bastaram").
