# Implementation Plan: Hardening Incremental do Bot de Daytrade

**Branch**: `001-hardening-incremental` | **Date**: 2026-08-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-hardening-incremental/spec.md`

## Summary

Fechar os gaps reais de segurança operacional encontrados por auditoria de código em 2026-08-13 no
bot de daytrade existente — idempotência de ordens + reconciliação com a exchange (US1/P1), circuit
breaker de perdas consecutivas + kill switch manual (US2/P2), e validação de estratégia out-of-sample
no motor de backtest já existente (US3/P3) — mantendo 100% de compatibilidade com o comportamento
atual (paper mode como padrão, mesmos comandos de `main.py`). Abordagem técnica: estender os módulos
já existentes (`execution/order_manager.py`, `risk/manager.py`, `trading/runner.py`,
`backtesting/engine.py`) em vez de introduzir novos serviços, bibliotecas ou infraestrutura.

## Technical Context

**Language/Version**: Python 3.10+ (3.12.10 instalado no ambiente de desenvolvimento)

**Primary Dependencies**: `ccxt` (conexão Binance), `pandas`/`ta` (indicadores e séries temporais),
`rich` (terminal), `pytest` (testes) — todas já em uso, nenhuma nova dependência de runtime é
necessária para as User Stories desta spec.

**Storage**: CSV/JSON (`data/*.csv`, `state.json`) — já em uso, mantém-se sem mudança de tecnologia
de persistência.

**Testing**: `pytest` (suíte existente em `tests/`, 32 testes, baseline de cobertura 66% registrado
em `ROADMAP.md`), estendida por esta feature — não substituída.

**Target Platform**: Processo local de longa duração (`python main.py bot`), Windows, sem
containerização.

**Project Type**: CLI + daemon de longa duração (monolito modular único, sem frontend/backend
separados).

**Performance Goals**: Sem requisito de latência sub-segundo — poll de 60s via REST já é suficiente
para o timeframe operacional (4h). Reconciliação periódica deve caber dentro desse mesmo ciclo sem
adicionar atraso perceptível.

**Constraints**: Binance Spot apenas, sem alavancagem (`max_leverage = 1`); `TRADING_MODE=live` MUST
continuar exigindo `LIVE_TRADING_CONFIRMATION` explícito; nenhuma correção automática de divergência
de reconciliação (só alerta) — ver Constitution Check.

**Scale/Scope**: Uso pessoal, conta única, até `MAX_POSITIONS` (hoje 5) posições simultâneas, até
~30 pares monitorados.

## Constitution Check

*GATE: Deve passar antes da Fase 0. Reavaliado após a Fase 1.*

Referência: `.specify/memory/constitution.md` v1.0.0.

| Princípio | Avaliação |
|---|---|
| I. Safety First | PASS — nenhuma User Story habilita `live` automaticamente; todas exigem validação em paper mode primeiro (ver `quickstart.md`). |
| II. No Secrets in Code | PASS — nenhuma nova variável de configuração envolve segredo (ex: `MAX_CONSECUTIVE_LOSSES` é um inteiro, não credencial). |
| III. Test Before Implement | PASS — cada tarefa em `tasks.md` tem critério de teste definido antes da implementação (ver seção "Tests" de cada User Story). |
| IV. Incremental Delivery | PASS — plano é dividido em Setup → Foundational → US1 → US2 → US3, cada uma um commit/PR pequeno, seguindo o Fluxo Incremental do `CLAUDE.md`. |
| V. Observability Mandatory | PASS — FR-003 exige que divergência de reconciliação, ativação de circuit breaker e toggle de kill switch gerem evento no mesmo pipeline JSONL/Telegram já existente (`utils/logger.py`, `utils/notifier.py`). |
| VI. Idempotency and Reconciliation | Endereçado diretamente por US1 (FR-001, FR-002, FR-003) — é o gap que motivou esta spec. |
| VII. Explain Before Code | PASS — este `plan.md` documenta o design antes de qualquer tarefa de implementação começar. |

Nenhuma violação identificada. Nenhuma entrada necessária em Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-hardening-incremental/
├── spec.md                       # Especificação (User Stories, requisitos, sucesso)
├── plan.md                       # Este arquivo
├── research.md                   # Fase 0 — decisões técnicas e alternativas consideradas
├── data-model.md                 # Fase 1 — entidades novas/alteradas
├── quickstart.md                 # Fase 1 — como validar cada User Story manualmente em paper mode
├── contracts/
│   └── cli.md                    # Fase 1 — contrato dos novos comandos de CLI (kill/resume)
├── checklists/
│   └── requirements.md           # Checklist de qualidade da spec
└── tasks.md                      # Fase 2 (/speckit-tasks) — tarefas executáveis
```

### Source Code (repository root)

Projeto existente, monolito modular — não é greenfield, então a estrutura abaixo é a real do
repositório, não um dos templates genéricos. Esta feature estende os módulos marcados com ✏️; os
demais são listados só para contexto de onde eles se encaixam.

```text
config/settings.py          # ✏️ nova var MAX_CONSECUTIVE_LOSSES
data/
├── state_store.py          # ✏️ novos campos: clientOrderId em ordens, contador de perdas, kill switch
├── trade_store.py          # ✏️ persistir clientOrderId por trade fechado
└── (demais módulos de data/ sem alteração)
risk/
└── manager.py              # ✏️ circuit breaker de perdas consecutivas
execution/
├── order_manager.py        # ✏️ geração de clientOrderId + reconciliação
└── reconciliation.py       # NOVO — comparação state.json vs conta real via ccxt
trading/
├── runner.py                # ✏️ chama reconciliação periódica + checa kill switch a cada ciclo
└── position_lifecycle.py    # sem alteração
backtesting/
├── engine.py                 # ✏️ split treino/validação out-of-sample
└── validation.py              # NOVO (opcional) — se a lógica de split não couber limpo em engine.py
utils/
├── logger.py                 # ✏️ novos tipos de evento JSONL
└── notifier.py                # ✏️ alertas para os novos eventos
main.py                       # ✏️ novos subcomandos `kill` / `resume`
tests/
├── test_order_manager_safety.py     # ✏️ estende para clientOrderId
├── test_risk_manager.py             # ✏️ estende para circuit breaker
├── test_backtesting_engine.py       # ✏️ estende para split out-of-sample
└── test_reconciliation.py           # NOVO
```

**Structure Decision**: Estender os módulos existentes no lugar, sem criar uma nova camada de
serviço/pacote. Dois arquivos novos justificados: `execution/reconciliation.py` (lógica de comparação
com a exchange é grande o suficiente para não poluir `order_manager.py`) e `tests/test_reconciliation.py`
(nova suíte de teste dedicada). `backtesting/validation.py` é opcional — decisão final na Fase de
implementação de US3, dependendo de quanto código o split exigir.

## Complexity Tracking

*Nenhuma violação da Constitution Check — seção vazia intencionalmente.*
