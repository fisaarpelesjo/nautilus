# Implementation Plan: H13 — Barras dirigidas por informação

**Branch**: `026-barras-por-informacao` | **Date**: 2026-09-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/026-barras-por-informacao/spec.md`

## Summary

Converter candles de tempo fixo em barras que fecham quando uma quantidade de
atividade se acumula, e medir se isso muda o veredito das estratégias já
avaliadas. A reamostragem entra **entre a busca de dados e o cálculo de
indicadores**, de modo que motor, estratégias e produção permanecem intactos.

A abordagem técnica saiu da Fase 0: base de **1h × 8.000 candles = 333,3 dias**,
que é a mesma janela de calendário do `4h × 2.000` usado por todas as doze
hipóteses anteriores, e limiar calibrado por iteração de Newton até a contagem
de barras ficar a 5% da contagem de barras de tempo — pareando o tamanho de
amostra por construção, que é a restrição estrutural desta hipótese.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: pandas, ccxt (via `data/fetcher.py`), rich — nenhuma nova

**Storage**: `reports/barras_{timestamp}.{json,csv,md}` via `utils/report_export.py`

**Testing**: pytest, estendendo `tests/` existente

**Target Platform**: CLI local; nenhuma alteração no serviço em produção

**Project Type**: projeto único (bot + ferramentas de pesquisa)

**Performance Goals**: a varredura completa deve terminar em tempo comparável ao
de `horizonte` (31 min para 144 combinações). Aqui são 4 estratégias × 12 pares
× 2 variantes = 96 comparações pareadas, cada uma sobre 8.000 candles de base.
Indicadores calculados **uma vez** por série via `preparar()`, como em 024/025.

**Constraints**: fronteira de barra só cai em marca de hora (erro ~12% da
largura típica de barra); `MIN_WINDOW_CANDLES = 150` e `EDGE_MIN_TRADES = 10`
inalterados

**Scale/Scope**: 12 pares × 4 estratégias × 2 variantes de barra, 333 dias

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Situação | Verificação |
|---|---|---|
| **I. Safety First** | **Conforme.** Nenhuma ordem, nenhum `TRADING_MODE`, nenhum caminho de execução tocado. Ferramenta de pesquisa offline sobre histórico público. | FR-015; teste de diff vazio nos caminhos de produção |
| **II. No Secrets in Code** | **Conforme.** Nenhum segredo novo, nenhuma variável de ambiente nova. | — |
| **III. Test Before Implement** | **Conforme.** Toda task tem critério de teste declarado antes da implementação, estendendo `tests/`. | `tasks.md` |
| **IV. Incremental Delivery** | **Conforme.** Uma fase por commit, testes verdes, push antes da fase seguinte. | Fluxo Incremental do `CLAUDE.md` |
| **V. Observability Mandatory** | **Conforme.** Relatório exportado em `reports/`; contagem por estado antes da tabela; combinação que falha vira estado, não silêncio. | FR-006, FR-016 |
| **VI. Idempotency** | **N/A.** Nenhuma ordem é enviada. | — |
| **VII. Explain Before Code** | **Conforme.** D1–D6 registradas em `research.md` com a medição que as sustenta. | `research.md` |

**Restrições técnicas.** Não introduz alavancagem, não altera `max_leverage`,
não toca permissões de API. Não adiciona dependência.

**Re-verificação pós-desenho (Fase 1):** sem violação. O desenho não introduz
caminho de produção, não altera critério de aprovação (`evaluate_approval`
inalterado) e não cria segunda implementação de lógica existente — a comparação
pareada reusa a estrutura de `backtesting/volatilidade.py`, e a simulação reusa
`horizonte._simular`.

## Project Structure

### Documentation (this feature)

```text
specs/026-barras-por-informacao/
├── plan.md              # Este arquivo
├── spec.md              # Requisitos
├── research.md          # Fase 0 — D1..D6, com medição
├── data-model.md        # Fase 1 — entidades
├── quickstart.md        # Fase 1 — cenários de validação
├── contracts/
│   └── cli-barras.md    # Fase 1 — contrato de CLI
├── checklists/
│   └── requirements.md  # Qualidade da spec
└── tasks.md             # Fase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
data/
└── bars.py                    # NOVO: construção de barras dirigidas
backtesting/
├── barras.py                  # NOVO: comparação pareada e varredura
├── volatilidade.py            # reusado: exposicao_de_capital, guarda M11
├── horizonte.py               # reusado: preparar, _simular, _walk_forward_par
├── validation.py              # reusado: split_train_validation
└── approval.py                # reusado: evaluate_approval (inalterado)
main.py                        # +cmd_barras, aliases `barras`/`bars`
tests/
├── test_bars.py               # NOVO: construção, causalidade, casos de borda
└── test_barras_scan.py        # NOVO: comparação pareada e classificação
```

**Estrutura escolhida:** projeto único, seguindo a organização já existente. A
construção de barras vive em `data/` porque é transformação de série, não
avaliação; a comparação vive em `backtesting/` junto das demais varreduras.

## Complexity Tracking

Nenhuma violação de princípio a justificar. Duas observações de complexidade
assumida deliberadamente:

| Decisão | Por que a complexidade é necessária | Alternativa mais simples rejeitada |
|---|---|---|
| Calibração iterativa do limiar (D2) | Sem parear a contagem de barras, a comparação mede tamanho de amostra em vez de esquema de amostragem — a restrição estrutural desta hipótese | Limiar fixo em dólares: produziria 200 barras em TRX e 8.000 em BTC, medindo liquidez do par |
| Base de 1h com 8.000 candles (D1) | É o que iguala a janela de calendário aos 333 dias das doze avaliações anteriores | Base de 4h: barras grossas demais para significar algo; base de 15m: 4× mais requisições sem mudar a conclusão qualitativa |

## Fases

### Fase 0 — Pesquisa ✅

Concluída. `research.md` resolve D1 (granularidade), D2 (calibração do limiar),
D3 (variantes), D4 (medida de exposição), D5 (ponto de integração) e D6
(executabilidade operacional). Todas por medição sobre os 12 pares do universo.

### Fase 1 — Desenho ✅

Concluída: `data-model.md`, `contracts/cli-barras.md`, `quickstart.md`.

### Fase 2 — Tarefas

`/speckit-tasks`. Ordem prevista das fases de implementação:

1. **Setup** — módulos e testes de fumaça
2. **Foundational** — construção de barras e sua **causalidade**; bloqueia tudo
3. **US1 (P1)** — comparação pareada ancorada em calendário
4. **US2 (P1)** — desconto de exposição e guarda de base perdedora
5. **US3 (P1)** — verificação de causalidade por reconstrução incremental
6. **US4 (P2)** — separação de custo de giro
7. **Polish** — relatório, documentação, varredura, veredito no registro

**US3 é P1 e pertence à fase Foundational na prática.** A causalidade da
construção é o modo de falha que produziria a aprovação falsa mais convincente
desta spec, e M2 documenta que exatamente essa classe de defeito passou meses
despercebida no projeto. O teste de reconstrução incremental precisa existir
**antes** de qualquer resultado ser olhado — caso contrário há incentivo a
racionalizar um número bom.

## Riscos herdados do registro

| Risco | Origem | Mitigação nesta spec |
|---|---|---|
| Reamostragem inerte | H12: 37/48 combinações não mediram nada e apareciam como reprovação | Medido na Fase 0: 9–11% de barras de 1 candle. Estado `inerte` próprio, FR-012 |
| Aquecimento em número de barras, não em dias | H11: 50 candles semanais eram 350 dias | FR-010: aquecimento verificado em dias de calendário |
| Menos participação lida como habilidade | M7, M10, M11 | FR-008/FR-009: desconto de exposição em tempo + guarda `confundido` |
| Vazamento de futuro na construção | M2: filtro comparava passado contra indicador corrente | FR-003/FR-004 e US3: reconstrução incremental com igualdade exata |
| Amostra insuficiente lida como reprovação | H10, H11, M9 | FR-011: inconclusivo precede qualquer avaliação de métrica |
| Duas implementações da mesma lógica | M1 | D5: reusa `preparar`/`_simular`/`_walk_forward_par` |
