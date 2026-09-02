# Fase 0 — Pesquisa: refresh periódico de pares dinâmicos

**Data:** 2026-09-02

---

## D1 — Intervalo de refresh

**Decisão:** `DYNAMIC_PAIRS_REFRESH_CYCLES = 1440` (≈ 24h, com
`POLL_INTERVAL = 60s`), configurável.

**Medição** (`market/selector.py::select_dynamic_pairs()`, ambiente local,
2026-09-02):

| Grandeza | Valor |
|---|---|
| Tempo de uma execução completa | **36,12 s** |
| Candidatos aprovados pelos filtros | 3 de até `DYNAMIC_PAIRS_CANDIDATES=20` |
| % do ciclo de 60s consumido, se rodasse toda vez | **60%** |

**Rationale.** 36s é mais da metade de um ciclo de 60s — rodar a cada ciclo
dobraria o tempo do ciclo em que o refresh acontece e multiplicaria por
`DYNAMIC_PAIRS_CANDIDATES` chamadas de rede a cada 60s, incompatível com o
hardening de rate limit já existente (`specs/BACKLOG.md` item 011). O custo
não escala com o intervalo — só acontece uma vez por refresh — então a
escolha real é "com que frequência a composição do mercado (volume,
tendência, volatilidade de 20 candles) muda o suficiente para justificar
re-selecionar".

24h foi escolhido por ser a cadência mais grosseira que ainda cobre o padrão
de VPS de longa duração que este projeto já comprovou (memória operacional:
26 pares, dezenas de dias contínuos) sem reagir a ruído intracandle — o
próprio seletor mede tendência sobre uma janela de 20 candles no timeframe de
produção (`TIMEFRAME`, default 4h ⇒ ~80h de janela), então re-selecionar a
cada poucas horas re-mediria a mesma janela quase sem mudança.

**Unidade em ciclos, não em horas** — mesmo padrão já usado por
`RECONCILIATION_INTERVAL_CYCLES` em `trading/runner.py` (constante local,
não `.env`). Diferença aqui: `DYNAMIC_PAIRS_REFRESH_CYCLES` fica em
`config/settings.py`, configurável via `.env`, porque já é onde
`DYNAMIC_PAIRS_ENABLED`/`_TOP_N`/`_CANDIDATES` vivem — manter o quarto
parâmetro da mesma família fora do `.env` seria inconsistente.

**Alternativas consideradas:**
- **A cada ciclo (60s)**: rejeitada pela medição acima — 60% do ciclo,
  incompatível com rate limit.
- **Configurável em horas** (`DYNAMIC_PAIRS_REFRESH_HOURS`), convertido para
  ciclos internamente: rejeitada por adicionar uma conversão
  (`horas * 3600 / POLL_INTERVAL`) sem ganho real — o operador já pensa em
  ciclos ao configurar `RECONCILIATION_INTERVAL_CYCLES`, mesma unidade em
  todo o arquivo.

---

## D2 — Comportamento em falha

**Decisão:** falha em `select_dynamic_pairs()` durante um refresh preserva a
lista ativa **vigente** (não volta para `PAIRS` original).

**Rationale.** `_load_active_pairs()` no boot já cai para `PAIRS` em caso de
erro (`except Exception: return PAIRS`) — mas isso é o boot, quando não há
lista "vigente" ainda. Num refresh em runtime, a lista vigente já reflete
horas/dias de operação (incluindo posições abertas, US2); descartá-la e
voltar para `PAIRS` estático jogaria fora a seleção anterior por causa de uma
falha transitória de rede, exatamente o tipo de "correção" que criaria mais
churn do que o problema que resolve. Mesmo princípio já usado em
`check_liquidity`/`estimate_slippage_pct` (falha vira estado conservador,
nunca uma ação mais agressiva que não fazer nada).

---

## D3 — Esquema do evento de auditoria

**Decisão:** `log_event("dynamic_pairs_refreshed", mode=TRADING_MODE,
added=[...], removed=[...], kept_for_open_position=[...])`, mesmo pipeline
de `logs/events-*.jsonl` já usado por `reconciliation_mismatch`,
`live_session_started`, `bot_cycle_error`.

**Rationale.** Reusa o formato já estabelecido
(`log_event(nome, mode=..., **campos)`), sem introduzir schema paralelo —
mesmo princípio do Princípio V da constitution. Os três campos cobrem
exatamente o que US3 pede: o que entrou, o que saiu, e o que foi mantido
apesar de não mais selecionado (a exceção de segurança de FR-002/US2 fica
visível no próprio evento, não escondida).

---

## Resumo das decisões

| # | Decisão | Efeito |
|---|---|---|
| D1 | Refresh a cada 1440 ciclos (~24h), configurável em ciclos | Custo real (36s/execução) medido; unidade consistente com `RECONCILIATION_INTERVAL_CYCLES` |
| D2 | Falha preserva lista vigente, não volta para `PAIRS` | Falha transitória de rede não descarta horas/dias de seleção |
| D3 | Evento `dynamic_pairs_refreshed` no pipeline já existente | Mudança de alocação de capital fica auditável, sem log paralelo |

## Fontes

- Medição própria, 2026-09-02: `market/selector.py::select_dynamic_pairs()`,
  ambiente local, `DYNAMIC_PAIRS_CANDIDATES=20` (default).
- `trading/runner.py` (leitura de código): `RECONCILIATION_INTERVAL_CYCLES`,
  `_load_active_pairs()`, laço principal.
- `specs/BACKLOG.md`, item 011 (rate limit hardening) — motivo pelo qual
  rodar o seletor a cada ciclo é descartado sem medição adicional.
