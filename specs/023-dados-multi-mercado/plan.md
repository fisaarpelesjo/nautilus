# Implementation Plan: Camada de dados multi-mercado para pesquisa

**Branch**: `023-dados-multi-mercado` | **Date**: 2026-08-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/023-dados-multi-mercado/spec.md`

## Summary

Abstrair o único ponto de entrada de candles (`data/fetcher.py::fetch_ohlcv`) para suportar fontes além de ccxt/Binance, permitindo que o motor de backtest existente avalie estratégias em ações, forex, futuros e índices. Cripto permanece o padrão, com comportamento bit a bit idêntico. Nenhuma execução é construída para os mercados novos — a feature entrega capacidade de **medir**, não de operar.

A pesquisa (ver [research.md](research.md)) confirmou que `yfinance` cobre os quatro mercados sem custo, que o timeframe `4h` é suportado (com teto de 730 dias de histórico), e que a validação out-of-sample exigida por FR-012 **já existe** em `backtesting/validation.py` e cabe na janela disponível.

## Technical Context

**Language/Version**: Python 3.12 (venv do projeto)

**Primary Dependencies**: `yfinance` (nova, fonte não-cripto) sobre as existentes `ccxt`, `pandas`, `ta`, `rich`

**Storage**: nenhuma nova — resultados continuam em `reports/` via `utils/report_export.py`

**Testing**: `pytest` (suíte existente em `tests/`, estendida — Princípio III da Constituição)

**Target Platform**: CLI local e VPS Linux (mesma do bot)

**Project Type**: CLI / bot de trading — módulo único, sem separação frontend/backend

**Performance Goals**: sem meta rígida. Uma varredura multi-mercado é comando sob demanda, não caminho quente. Restrição prática: não degradar o ciclo de 60s do bot ao vivo (que não usa este caminho)

**Constraints**:
- Histórico intradiário limitado a 730 dias na fonte não-cripto (~993 candles em 4h) contra 2.000 em cripto
- Nenhuma chamada de rede nova no caminho de execução ao vivo
- `fetch_ticker`/`fetch_tickers`/`fetch_balance`/`fetch_order_book` permanecem cripto-only

**Scale/Scope**: dezenas de símbolos por varredura, poucas estratégias. Não há requisito de concorrência

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação | Situação |
|---|---|---|
| **I. Safety First** | A feature não toca `risk/manager.py`, `execution/order_manager.py` nem `trading/position_lifecycle.py`. FR-006 exige comportamento idêntico no caminho ao vivo; FR-007 exige recusa explícita de símbolo sem execução | ✅ Passa — e **reforça** o princípio |
| **II. No Secrets in Code** | A fonte escolhida não exige chave de API. Nenhum segredo novo entra no projeto | ✅ Passa |
| **III. Test Before Implement** | Cada task terá critério de teste. A suíte `tests/` existente é estendida, não substituída. Inclui teste de não-regressão do caminho cripto | ✅ Passa |
| **IV. Incremental Delivery** | Entrega fatiada por história de usuário, commit por tópico, sem reescrita monolítica | ✅ Passa |
| **V. Observability Mandatory** | FR-011 exige registrar mercado e perfil de custo em cada resultado, reusando `utils/report_export.py` — sem pipeline paralelo | ✅ Passa |
| **VI. Idempotency and Reconciliation** | Não se aplica: nenhuma ordem é enviada. O caminho de execução permanece intocado | ✅ N/A |
| **VII. Explain Before Code** | Decisões de design registradas em `research.md` (D1-D6) antes da implementação, com rationale e alternativas | ✅ Passa |

**Restrição da Constituição**: *"O bot opera exclusivamente Binance Spot, somente posições long; Futures/alavancagem estão fora de escopo até decisão explícita em contrário."*

Esta feature **não viola** a restrição: ela habilita *avaliar* dados de outros mercados, sem operá-los. FR-007 existe justamente para tornar impossível que um símbolo não-cripto chegue ao caminho de execução. A restrição continua valendo integralmente para operação.

**Veredito do gate**: nenhuma violação. Nenhuma entrada necessária em Complexity Tracking.

### Reavaliação pós-design (Fase 1)

Após produzir `data-model.md`, `contracts/` e `quickstart.md`, os gates foram reavaliados:

- **Nenhuma violação nova.** O design não introduziu dependência no caminho de execução, não criou pipeline de log paralelo e não exige segredo novo.
- **Princípio I ficou mais forte que no gate inicial**: `contracts/data-source.md` restringe explicitamente `fetch_ticker`/`fetch_tickers`/`fetch_balance`/`fetch_order_book` a cripto — todas pertencem ao caminho de execução. A abstração não as expõe.
- **Princípio III ganhou um teste específico** que não existia no plano inicial: `test_crypto_no_regression.py`, derivado do contrato de não-regressão. Sem ele, a abstração seria a oportunidade perfeita para repetir o padrão que já custou caro duas vezes neste projeto — dois pontos do sistema discordando silenciosamente.
- **Princípio V**: `contracts/cli.md` fixa que a varredura exporta por `utils/report_export.py`, o pipeline existente.

## Project Structure

### Documentation (this feature)

```text
specs/023-dados-multi-mercado/
├── spec.md              # Especificação (/speckit-specify)
├── plan.md              # Este arquivo (/speckit-plan)
├── research.md          # Fase 0 — decisões D1-D6 medidas
├── data-model.md        # Fase 1 — entidades e regras
├── quickstart.md        # Fase 1 — validação executável
├── contracts/           # Fase 1 — contratos de interface
└── tasks.md             # Fase 2 (/speckit-tasks — NÃO criado aqui)
```

### Source Code (repository root)

```text
config/
└── settings.py                 # MODIFICADO: perfis de custo por mercado; relaxar validação /USDT

data/
├── fetcher.py                  # MODIFICADO: fetch_ohlcv delega à fonte resolvida pelo mercado
├── markets.py                  # NOVO: definição de mercado, resolução símbolo -> mercado
└── sources/                    # NOVO: implementações de fonte de dados
    ├── __init__.py             #   registro e resolução de fonte
    ├── ccxt_source.py          #   fonte cripto (extraída do fetcher atual, comportamento intocado)
    └── yfinance_source.py      #   fonte não-cripto (ações, forex, futuros, índices)

backtesting/
├── engine.py                   # MODIFICADO: custo resolvido por mercado; registrar mercado no resultado
├── compare.py                  # MODIFICADO: aceitar símbolos multi-mercado; contagem de combinações
└── multimarket.py              # NOVO: varredura estratégia x símbolo com confirmação out-of-sample

trading/
└── runner.py                   # MODIFICADO: recusar símbolo sem execução na inicialização (FR-007)

tests/
├── test_markets.py             # NOVO: resolução símbolo -> mercado, perfis de custo
├── test_sources.py             # NOVO: contrato de fonte, falha fechada, normalização
├── test_multimarket.py         # NOVO: varredura, confirmação out-of-sample, contagem
└── test_crypto_no_regression.py# NOVO: caminho cripto idêntico antes/depois (risco técnico 1)
```

**Structure Decision**: módulo único (o projeto já é assim), estendido por composição em vez de reescrita. A abstração entra atrás de `fetch_ohlcv()`, cuja assinatura **não muda** — nenhum dos ~10 consumidores existentes (backtest, compare, scan, optimize, validation, replay, runner, chart, selector, diagnostics) precisa ser tocado para continuar funcionando.

`data/sources/ccxt_source.py` recebe o código atual do fetcher **sem alteração de lógica**, para que a abstração não seja oportunidade de introduzir mudança de comportamento em cripto — o risco técnico nº 1 de `research.md`.

## Sequenciamento por história de usuário

Alinhado ao Princípio IV (entrega incremental) e às prioridades da spec:

| Ordem | História | Entrega | Testável isoladamente por |
|---|---|---|---|
| 1 | **US4** (P1) — preservação do ao vivo | Abstração de fonte + `ccxt_source` + teste de não-regressão | Caminho cripto produz resultado idêntico |
| 2 | **US1** (P1) — avaliar mercado novo | `yfinance_source`, `markets.py`, relaxar validação de config | Backtest sobre símbolo de ações retorna métricas completas |
| 3 | **US2** (P1) — custo por mercado | Perfis de custo, recusa quando ausente | Mesmo símbolo com custos diferentes muda resultado; mercado sem perfil é recusado |
| 4 | **US3** (P2) — varredura comparativa | `multimarket.py` com confirmação out-of-sample | Tabela única multi-mercado, aprovação só com confirmação fora da janela de busca |

US4 vem primeiro deliberadamente: é a rede de segurança. Estabelecer que cripto não regrediu **antes** de introduzir a segunda fonte torna qualquer divergência posterior atribuível à mudança que a causou.

## Complexity Tracking

> Preenchido apenas se o Constitution Check tiver violações a justificar.

Sem violações. Nenhuma entrada.
