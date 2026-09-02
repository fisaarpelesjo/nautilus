# Fase 1 — Modelo de dados: refresh periódico de pares dinâmicos

Nenhuma entidade persistida nova. `active_pairs` (já existente, `list[str]`
local a `trading/runner.py::run()`) passa de "atribuída uma vez no boot" para
"reatribuída periodicamente em runtime".

## `_refresh_active_pairs(manager, active_pairs) -> tuple[list[str], dict]`

Função nova, mesmo padrão de `_run_reconciliation(manager, active_pairs)`
(extraída, testável com um `_FakeManager`, chamada do loop principal).

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `manager` | `OrderManager` | Para `manager.has_position(symbol)` — a guarda de segurança (FR-002) |
| `active_pairs` | `list[str]` | Lista vigente antes do refresh |

**Retorno:**

| Campo | Tipo | Descrição |
|---|---|---|
| `nova_lista` | `list[str]` | `selecionados ∪ {símbolos de active_pairs com posição aberta}` |
| `resumo` | `dict` | `{"added": [...], "removed": [...], "kept_for_open_position": [...]}` — vira os campos do evento (D3) |

**Invariante central (FR-002):** para todo `s` em `active_pairs` anterior,
se `manager.has_position(s)`, então `s` está em `nova_lista`. A remoção só é
possível para símbolos sem posição aberta.

**Falha em `select_dynamic_pairs()`** (D2): a função captura a exceção e
retorna `(active_pairs, {"added": [], "removed": [], "kept_for_open_position":
[], "error": str(exc)})` — lista vigente preservada, erro visível no evento
em vez de silencioso.

---

## `DYNAMIC_PAIRS_REFRESH_CYCLES` (`config/settings.py`, nova constante)

| Campo | Tipo | Padrão | Descrição |
|---|---|---|---|
| `DYNAMIC_PAIRS_REFRESH_CYCLES` | `int` | `1440` (D1, ~24h a 60s/ciclo) | Ciclos entre refreshes; só relevante com `DYNAMIC_PAIRS_ENABLED=true` |

Validado em `validate_config()` (mesmo padrão de `DYNAMIC_PAIRS_TOP_N`/
`_CANDIDATES`): `DYNAMIC_PAIRS_REFRESH_CYCLES < 1` é erro de configuração.

---

## Evento `dynamic_pairs_refreshed` (D3)

Gravado via `log_event()` já existente, em `logs/events-YYYY-MM-DD.jsonl`.

| Campo | Descrição |
|---|---|
| `mode` | `TRADING_MODE`, mesmo padrão dos demais eventos |
| `added` | Símbolos novos na lista |
| `removed` | Símbolos que saíram (nunca inclui um com posição aberta) |
| `kept_for_open_position` | Símbolos que o seletor não escolheria mais, mas permanecem por posição aberta (FR-002 tornado visível) |
| `error` | Presente só quando a seleção falhou (D2) — lista preservada |

Gravado em **todo** refresh, inclusive quando nada muda (US3, Acceptance
Scenario 2) — os três campos aparecem vazios, não o evento inteiro omitido.
