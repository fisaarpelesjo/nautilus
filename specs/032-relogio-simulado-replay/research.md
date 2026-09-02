# Fase 0 — Pesquisa: relógio simulado no replay

**Data:** 2026-09-02

---

## D1 — Mecanismo de indireção

**Decisão:** `execution/order_manager.py` ganha um módulo-nível
`_simulated_now: Optional[datetime] = None` e uma função `_now() ->
datetime` que retorna `_simulated_now` quando definido, senão
`datetime.now()`. Os 14 pontos de chamada relevantes (levantados por
`grep`, ver D2) passam a usar `_now()`.

**Rationale.** Fora do ambiente isolado do replay, `_simulated_now` nunca é
setado — `_now()` é `datetime.now()` byte a byte, mesmo padrão de "default
preserva comportamento" já usado em `mtf_confirmed(..., as_of=None)`
(spec 020). `trading/replay.py::_isolated_order_manager_environment()` já
salva/restaura atributos de módulo desse jeito exato
(`TRADING_MODE`, `load_state`, `save_state`, ...) — `_simulated_now` entra
na mesma lista, mesmo mecanismo, sem padrão novo.

**Alternativa considerada e rejeitada:** injetar `now: Callable` como
parâmetro em cada método (`set_cooldown(symbol, now=...)`, etc.) —
mudaria a assinatura de ~10 métodos públicos de `OrderManager`, todos
chamados pelo caminho de produção (`trading/position_lifecycle.py`,
`trading/runner.py`); a superfície de mudança seria maior sem ganho — o
objetivo (produção nunca muda) já é atingido por uma variável de módulo.

---

## D2 — Levantamento completo dos pontos de chamada

**Medição** (`grep -n "datetime.now()" execution/order_manager.py`):

| Linha | Contexto | Escopo desta spec |
|---|---|---|
| 38 | `_generate_client_order_id` — salt de unicidade junto com `uuid4()` | **Fora.** Não é cooldown/drawdown/circuit breaker/timestamp de trade (FR list do spec.md); trocar não muda nada observável (uuid4 já garante unicidade) |
| 84 | `Position.opened_at`, `default_factory=datetime.now` | **Dentro** (FR-006) |
| 174, 324 | `circuit_breaker_triggered_at` (ativação) | **Dentro** (FR-001) |
| 179, 189, 199, 422, 428, 434 | resets diário/semanal/mensal (`_restore_state`, `_check_*_reset`) | **Dentro** (FR-001) |
| 283 | `"updated_at"` no snapshot de estado persistido | **Fora do replay** — `save_state` já é mockado (no-op) pelo ambiente isolado; o valor é calculado mas nunca persiste. Convertido para `_now()` por consistência (mesmo padrão em todo o arquivo), sem efeito prático no replay |
| 347 | `check_circuit_breaker_timeout` | **Dentro** (FR-001) |
| 485, 491 | `set_cooldown`/`is_in_cooldown` | **Dentro** (FR-001) |
| 626, 951 | `"closed_at"` no registro de trade | **Dentro** (FR-006) |

**Rationale da exclusão da linha 38**: é a única chamada que não afeta
nenhuma decisão de risco nem nenhum timestamp reportado — existe só para
compor uma string única. Convertê-la ampliaria o diff sem servir a
nenhum FR desta spec.

---

## D3 — Onde o relógio simulado avança

**Decisão:** `trading/replay.py::run_replay()` seta
`order_manager._simulated_now = window.index[-1].to_pydatetime()` no
início de cada iteração do loop — mesmo valor já usado pelo parâmetro
`as_of` passado a `handle_entry_candidate` (spec 020), sem introduzir um
segundo conceito de "agora" simulado.

**Achado de auditoria (spec.md, Contexto), reconfirmado por leitura de
código**: `run_replay()` **nunca chama**
`manager.check_circuit_breaker_timeout()`. A produção
(`trading/runner.py`) chama isso a cada ciclo quando o breaker está ativo
(`if manager.circuit_breaker_active: safe_step(...,
manager.check_circuit_breaker_timeout)`). O replay precisa do mesmo
padrão — sem ele, mesmo com o relógio certo, o breaker nunca reavalia o
timeout.

---

## D4 — Restauração do relógio real

**Decisão:** `_isolated_order_manager_environment()` adiciona
`"_simulated_now": order_manager._simulated_now` ao dicionário
`originals`, restaurado no `finally` — mesmo padrão dos demais atributos
já isolados.

---

## D5 — Atualização da ressalva em `compare_to_backtest()`

**Decisão:** o parágrafo de "Limitações conhecidas" que cita cooldown,
resets de drawdown e timeout do circuit breaker usando relógio real deixa
de se aplicar — MUST ser reescrito para declarar que os três agora usam o
tempo simulado do candle, mantendo só as limitações que continuam reais
(nenhuma outra identificada por esta spec).

**Rationale.** Mesmo princípio da correção do MTF (spec 020): uma ressalva
que descreve um defeito já corrigido desinforma quem ler depois.

---

## Resumo das decisões

| # | Decisão | Efeito |
|---|---|---|
| D1 | `_simulated_now` (módulo) + `_now()`, default preserva comportamento | Mesmo padrão de `as_of=None` (spec 020) |
| D2 | 14 pontos de chamada dentro do escopo, 1 fora (client_order_id, linha 38) | Levantamento completo antes de qualquer edição |
| D3 | `run_replay()` seta `_simulated_now` por candle + chama `check_circuit_breaker_timeout()` (ausente hoje) | Fecha o achado de auditoria do spec.md |
| D4 | `_isolated_order_manager_environment` restaura `_simulated_now` no `finally` | Nunca vaza tempo simulado para fora do replay |
| D5 | Ressalva de `compare_to_backtest()` reescrita | Não descreve defeito já corrigido |

## Fontes

- Medição própria, 2026-09-02: `grep -n "datetime.now()"
  execution/order_manager.py` (15 ocorrências, 14 no escopo).
- `trading/replay.py` (leitura de código): confirma ausência da chamada a
  `check_circuit_breaker_timeout()`.
- `trading/runner.py`: padrão de chamada de produção, reusado no replay.
- `strategy/base.py`/`trading/position_lifecycle.py` (spec 020): padrão
  `as_of=None` que esta spec segue.
