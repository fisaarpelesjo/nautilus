# Fase 0 — Pesquisa: histórico estendido

**Data:** 2026-09-02

---

## D1 — Novo teto de histórico

**Decisão:** `6.000` candles (de `2.000`), para os chamadores dentro do
escopo (`backtesting/modelo.py`, `backtesting/onchain_hipotese.py`,
`backtesting/horizonte.py`).

**Medição** (`data/fetcher.py::fetch_ohlcv`, 2026-09-02): pedido de 6.000
candles de 4h devolveu os 6.000 completos para os 12 pares de
`UNIVERSO_H11`, cobrindo 2023-12-07 a 2026-09-02 (~2,7 anos), em ~35s no
total (1,8-8,8s por par). `BTC/USDT`/`ATOM/USDT` chegam a ~14.999 (desde
2019-10-29) antes de um teto real — não verificado para os outros 10
pares, por isso não é o número declarado.

**Rationale.** 6.000 é o maior valor confirmado disponível para **todo**
o universo usado por H10/H11/H14/H17, não o máximo teórico de um par
isolado — usar um número não verificado para os 12 arriscaria alguns
pares devolverem menos que o pedido silenciosamente compensável só por
sorte de qual par se testa primeiro.

**Alternativa considerada e rejeitada:** usar o teto de ~15.000 medido
para BTC/ATOM. Rejeitada por não estar verificada para o universo inteiro
— exatamente o tipo de suposição não medida que este projeto evita.

---

## D2 — Escopo dos chamadores

**Decisão:** só os módulos de H10/H11/H14/H17 mudam — `backtesting/
modelo.py` (`avaliar_par`, `coletar_eventos`), `backtesting/
onchain_hipotese.py` (`avaliar_h17`), `backtesting/horizonte.py`
(`run_horizonte_scan`, `medir_disponibilidade`, default de `solicitado`).
`backtesting/engine.py::run_backtest` (usado por `backtest`/`edge`/
`compare`/`scan`/`optimize`) **não muda** (FR-005).

**Rationale.** `run_backtest` serve comandos de uso geral, não só a
bateria de hipóteses — mudar seu teto teria efeito em todo comando que o
usa, fora do que esta spec se propõe a medir. Escopo deliberadamente
estreito.

---

## D3 — H10 fora do escopo

**Decisão:** `backtesting/pairs_trading.py::run_pairs_backtest` não é
tocado nesta spec — nunca ganhou comando CLI nem chamador permanente
(medido: `grep` só encontra uso no próprio módulo e no teste). Registrado
em `spec.md` Assumptions/FR-007 como trabalho futuro.

---

## Resumo

| # | Decisão | Efeito |
|---|---|---|
| D1 | Teto 2.000 → 6.000, medido pro universo inteiro | 3x o histórico, sem risco de sub-entrega silenciosa |
| D2 | Só módulos de H10/H11/H14/H17 — `run_backtest` intocado | Sem efeito em comandos de uso geral |
| D3 | H10 fora do escopo, declarado | Sem CLI permanente hoje; spec própria depois |

## Fontes

- Medição própria, 2026-09-02: `data/fetcher.py::fetch_ohlcv` sobre
  `UNIVERSO_H11` (12 pares) e BTC/ATOM isolados.
- `backtesting/horizonte.py` (comentários já existentes sobre limitação
  de histórico semanal, reusados sem reinterpretação).
- `grep -rln "run_pairs_backtest"` — confirma ausência de chamador
  permanente.
