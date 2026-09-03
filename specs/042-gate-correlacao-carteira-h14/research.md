# Fase 0 — Pesquisa: gate de correlação na carteira de H14

**Data:** 2026-09-03

---

## D1 — Checagem ponto-no-tempo, não a função de produção direto

**Decisão:** nova função `_correlacionado_com_posicao_aberta(par,
preparados, posicoes_abertas, t, lookback=CORRELATION_LOOKBACK,
limiar=MAX_POSITION_CORRELATION)` — mesma semântica e mesmos limiares de
`risk/correlation.py::check_correlated_exposure`, mas:

- Fonte de dado: `preparados[par]["close"]` (já em memória, já fatiado
  até `t` pela mecânica de carteira existente) — nunca `fetch_ohlcv` ao
  vivo.
- Retorno: fração de `pct_change()` sobre os últimos `lookback` valores
  **anteriores ou iguais a `t`** — nunca um candle posterior.

**Rationale — por que não reusar `check_correlated_exposure` como
está.** A função de produção existe para o loop ao vivo, onde "agora" é
sempre o presente real. Chamada dentro de um backtest, ela buscaria os
candles mais recentes DISPONÍVEIS HOJE via rede — não os disponíveis no
instante histórico `t` sendo simulado. Duas consequências, ambas
desqualificantes:

1. **Vazamento de futuro.** Um candle de 2024 no backtest "veria"
   correlação calculada com dado de 2026 — o mesmo tipo de erro que a
   spec 020 (MTF) já corrigiu (`as_of`) e que este projeto trata como
   defeito sério, não detalhe.
2. **Custo de rede inviável.** Milhares de candles × múltiplos pares
   candidatos × múltiplas posições abertas significariam milhares de
   chamadas de API por execução de carteira — a mesma ordem de grandeza
   de problema que já motivou D6 de spec 037 (nunca reimplementar o
   motor de backtest, sempre reusar) aplicada aqui na direção oposta:
   não reusar uma função cuja forma de I/O não serve ao propósito.

**Por que os limiares não são redeclarados.** `MAX_POSITION_CORRELATION`
(0,7) e `CORRELATION_LOOKBACK` (50) já são os valores reais usados pela
produção — divergir deles testaria um gate diferente do que
efetivamente protege o bot, sem nenhuma medição nova que justificasse a
divergência.

---

## Resumo

| # | Decisão | Efeito |
|---|---|---|
| D1 | Checagem ponto-no-tempo nova, mesma semântica/limiares da função de produção | Sem vazamento de futuro, sem custo de rede proibitivo, mesmo gate que a produção efetivamente usa |

## Fontes

- `risk/correlation.py::check_correlated_exposure` — semântica e
  limiares reusados; forma de I/O (fetch ao vivo) não reusada, pelos
  motivos de D1.
- `docs/research/registro-de-hipoteses.md` §4.15 (H14, atualização
  spec 040) — motivação direta: "a produção já tem exatamente o
  mecanismo ativo que faltou aqui... testar esse gate seria a hipótese
  natural seguinte."
- `config/settings.py` — `MAX_POSITION_CORRELATION=0,7`,
  `CORRELATION_LOOKBACK=50`, valores reais de produção.
