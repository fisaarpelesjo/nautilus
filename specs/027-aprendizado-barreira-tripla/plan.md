# Implementation Plan: H14 — Aprendizado supervisionado com barreira tripla

**Branch**: `027-aprendizado-barreira-tripla` | **Date**: 2026-09-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/027-aprendizado-barreira-tripla/spec.md`

## Summary

Rotular cada evento pela barreira que o preço toca primeiro, treinar um
classificador de baixa capacidade sobre atributos declarados, e medir se ele
supera a estratégia de regras **e** o mesmo modelo com rótulos embaralhados.

A Fase 0 fixou o desenho por medição e produziu o que nenhuma hipótese anterior
teve: **um limiar de sucesso quantitativo declarado antes do teste**. Com as
barreiras do próprio bot, uma entrada aleatória tem expectativa de −0,241 ATR e
razão de chances alvo/stop de 0,372; empatar exige 0,500. O modelo precisa
elevar essa razão em **+34,3% relativo** — critério interno à decisão, que não
depende do regime do período.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: pandas, numpy, statsmodels (já presente, usado no
portão ADF de H10), rich — **nenhuma nova** (FR-016)

**Storage**: `reports/modelo_{timestamp}.{json,csv,md}`

**Testing**: pytest, estendendo `tests/` existente

**Target Platform**: CLI local; nenhuma alteração no serviço em produção

**Project Type**: projeto único (bot + ferramentas de pesquisa)

**Performance Goals**: a rotulagem é O(n × limite) por par — 2.000 × 24 no pior
caso, trivial. A estimação de 6 parâmetros sobre ~16.000 amostras é imediata. A
avaliação completa deve terminar em minutos, não dezenas de minutos.

**Constraints**: 5 atributos + intercepto sobre ~16.000 amostras (2.700 por
parâmetro); `EDGE_MIN_TRADES = 10` e `MIN_WINDOW_CANDLES = 150` inalterados;
embargo de 24 velas

**Scale/Scope**: 12 pares, 23.412 eventos rotulados, 333 dias

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Situação | Verificação |
|---|---|---|
| **I. Safety First** | **Conforme.** Nenhuma ordem, nenhum `TRADING_MODE`, nenhum caminho de execução tocado. Ferramenta de pesquisa offline. | FR-015; cenário 10 do quickstart |
| **II. No Secrets in Code** | **Conforme.** Nenhum segredo, nenhuma variável de ambiente nova. | — |
| **III. Test Before Implement** | **Conforme.** Toda task com critério declarado antes da implementação. **Ver nota abaixo.** | `tasks.md` |
| **IV. Incremental Delivery** | **Conforme.** Uma fase por commit, testes verdes, push antes da seguinte. | Fluxo Incremental |
| **V. Observability Mandatory** | **Conforme.** Relatório em `reports/`; contagem por estado antes da tabela; diagnóstico de purga; falha vira estado, não silêncio. | FR-009, FR-012, FR-014 |
| **VI. Idempotency** | **N/A.** Nenhuma ordem é enviada. | — |
| **VII. Explain Before Code** | **Conforme.** D1–D6 em `research.md`, cada uma com a medição que a sustenta. | `research.md` |

**Nota sobre o Princípio III.** Na spec 026 os testes foram escritos *depois* do
módulo, e o desvio foi declarado no commit e compensado por verificação de
mutação. Aqui a ordem correta é obrigatória: os caminhos de falha desta spec
(vazamento por purga, rótulo embaralhado) produzem resultados que **parecem
bons**, e escrever o teste depois de ver o número é o cenário exato em que a
racionalização acontece.

**Restrições técnicas.** Não introduz alavancagem, não altera `max_leverage`,
não toca permissões de API, **não adiciona dependência**.

**Re-verificação pós-desenho (Fase 1):** sem violação. O desenho não cria
caminho de produção, não altera `evaluate_approval` e não duplica lógica —
reusa `preparar`, `_simular`, `split_train_validation` e as guardas de
`volatilidade.py`/`barras.py`.

## Project Structure

### Documentation (this feature)

```text
specs/027-aprendizado-barreira-tripla/
├── plan.md              # Este arquivo
├── spec.md              # Requisitos
├── research.md          # Fase 0 — D1..D6, com medição
├── data-model.md        # Fase 1 — entidades e os 13 estados
├── quickstart.md        # Fase 1 — 12 cenários
├── contracts/
│   └── cli-modelo.md    # Fase 1 — contrato de CLI
├── checklists/
│   └── requirements.md  # Qualidade da spec
└── tasks.md             # Fase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
strategy/
└── barreira_tripla.py         # NOVO: rotulagem e atributos declarados
backtesting/
├── purga.py                   # NOVO: divisão purgada com embargo global
├── modelo.py                  # NOVO: estimação, embaralhamento, avaliação
├── volatilidade.py            # reusado: ganho_de_timing, guarda confundido
├── barras.py                  # reusado: padrão de comparação e classificação
├── horizonte.py               # reusado: preparar, _simular
└── validation.py              # reusado: split_train_validation
main.py                        # +cmd_modelo, aliases `modelo`/`ml`
tests/
├── test_barreira_tripla.py    # NOVO: rotulagem, causalidade, atributos
├── test_purga.py              # NOVO: sobreposição, embargo, globalidade
└── test_modelo.py             # NOVO: embaralhamento, estados, convergência
```

**Por que `barreira_tripla.py` fica em `strategy/`:** é derivação de rótulo e
atributo a partir de indicadores, da mesma família de `strategy/diagnostics.py`.
A purga é procedimento de validação e fica em `backtesting/`.

## Complexity Tracking

| Decisão | Por que a complexidade é necessária | Alternativa mais simples rejeitada |
|---|---|---|
| Purga **global** entre pares (D4) | Pares correlacionados a 0,71 (medido em H9): purgar por par deixaria o desfecho de BTC no treino enquanto ETH está no teste | Purga por par: mais simples e produziria desempenho artificial |
| Estado `insuficiente` separado de `sem_sinal` | "Há sinal e ele não paga as barreiras" é o único achado positivo possível se H14 não for aprovada | Colapsar em reprovação: perderia a distinção |
| `razao_chances_decidido` além do backtest | Acurácia é enganosa aqui — prever sempre "stop" acerta 62,8% e nunca opera | Usar acurácia: métrica que premia não decidir |

## Fases

### Fase 0 — Pesquisa ✅

Concluída. D1 (estimador), D2 (barreiras e limiar de sucesso), D3 (atributos e
colinearidade), D4 (purga, embargo e agrupamento), D5 (integração), D6
(executabilidade). Todas por medição sobre 23.412 eventos.

### Fase 1 — Desenho ✅

Concluída: `data-model.md` (13 estados ordenados), `contracts/cli-modelo.md`,
`quickstart.md` (12 cenários).

### Fase 2 — Tarefas

`/speckit-tasks`. Ordem prevista:

1. **Setup** — módulos e fumaça
2. **Foundational** — rotulagem causal + atributos + **purga global**; bloqueia tudo
3. **US1 (P1)** — avaliação pareada modelo × regras
4. **US3 (P1)** — rótulo embaralhado e os estados `sem_sinal`/`insuficiente`
5. **US2 (P1)** — verificação de purga no relatório
6. **US4 (P2)** — custo de giro
7. **Polish** — relatório, documentação, execução, veredito, fila

**US3 vem antes de US2 na ordem de implementação** porque o estado
`sem_sinal` é o que torna qualquer número interpretável, enquanto a US2 na fase
5 é apenas a *exposição* da purga no relatório — o mecanismo dela já está na
Foundational, onde bloqueia tudo.

## Riscos herdados do registro

| Risco | Origem | Mitigação nesta spec |
|---|---|---|
| Vazamento por sobreposição de rótulos | M2 (filtro comparando passado com indicador corrente) | FR-005/FR-006 e cenários 2 e 3 do quickstart |
| Vazamento entre pares correlacionados | H9 (correlação 0,71) | D4: purga temporal e global |
| Sobreajuste lido como descoberta | H13 (1 aprovação em 96, abaixo do acaso) | D1: 6 parâmetros, 2.700 amostras cada; US3 obrigatória |
| Menos participação lida como habilidade | M7, M10, M11 | FR-010: desconto de exposição + guarda `confundido` |
| Amostra insuficiente lida como reprovação | H10, H11, M9 | FR-011: inconclusivo precede métrica |
| Aprovação inexecutável | H13 D6 | D6: ressalva de retreino e degradação silenciosa |
| Duas implementações da mesma lógica | M1 | D5: reusa motor, guardas e critérios |
