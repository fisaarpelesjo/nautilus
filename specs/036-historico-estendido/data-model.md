# Fase 1 — Modelo de dados: histórico estendido

Nenhuma entidade nova. Três constantes trocadas, mesma forma, valor novo:

| Local | Antes | Depois |
|---|---|---|
| `backtesting/modelo.py::avaliar_par` (default `df=None`) | `fetch_ohlcv(par, TIMEFRAME, 2000)` | `fetch_ohlcv(par, TIMEFRAME, 6000)` |
| `backtesting/modelo.py::coletar_eventos` | `fetch_ohlcv(par, TIMEFRAME, 2000)` | `fetch_ohlcv(par, TIMEFRAME, 6000)` |
| `backtesting/onchain_hipotese.py::avaliar_h17` | `fetch_ohlcv(par, TIMEFRAME, 2000)` | `fetch_ohlcv(par, TIMEFRAME, 6000)` |
| `backtesting/horizonte.py::run_horizonte_scan`/`medir_disponibilidade` | `solicitado: int = 2000` | `solicitado: int = 6000` |

Nenhuma mudança de tipo, assinatura pública ou dataclass. Os resultados
(`AvaliacaoH14`, `RelatorioH17`, `RelatorioHorizonte`) já existentes
continuam com os mesmos campos — só os valores de `n_treino`/`n_teste`/
`obtido`/`cobertura` mudam, refletindo a amostra maior.

## Comparação registrada (não uma entidade de código, um artefato de doc)

Cada reavaliação produz uma linha "antes/depois" no
`docs/research/registro-de-hipoteses.md`:

| Campo | Descrição |
|---|---|
| Valor publicado | O número já registrado (ex.: H17 "7 operações, abaixo do mínimo de 10") |
| Valor novo | O número medido com 6.000 candles |
| Veredito mudou? | Sim/não, e para quê |
