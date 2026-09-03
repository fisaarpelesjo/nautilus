# Fase 0 — Pesquisa: H20 com histórico estendido

## D1 — Reuso do teto de 6.000 candles, sem remedição

**Decisão:** `6.000` candles (de `2.000`), só para
`backtesting/geometria.py::run_geometria_scan`.

**Rationale.** `specs/036-historico-estendido/research.md` (D1) já
mediu e validou 6.000 como o maior valor confirmado disponível para
todo o `UNIVERSO_H11` (12 pares), coberto por `fetch_ohlcv` em ~35s
total. Essa medição não precisa ser refeita — `geometria.py` usa os
mesmos 12 pares, o mesmo `TIMEFRAME` (4h) e a mesma fonte
(`data/fetcher.py::fetch_ohlcv`) que os módulos já migrados. Reusar sem
remedir é a mesma disciplina que evita "varredura disfarçada": o número
não é escolhido para produzir um resultado, é herdado de uma decisão já
declarada e justificada noutra spec.

**Por que `geometria.py` ficou de fora de spec 036.** D2 de spec 036
delimitou o escopo aos módulos de H10/H11/H14/H17 — `geometria.py` (H20)
não estava na lista porque a pergunta em aberto ("será que muda o
veredito de H20 também?") foi deliberadamente registrada como fora de
escopo daquela spec, não esquecida (`docs/research/registro-de-
hipoteses.md` §4.15, atualização spec 036). Esta spec fecha exatamente
essa lacuna.

## D2 — Nenhuma mudança na avaliação estatística

**Decisão:** a avaliação da geometria selecionada continua via
`backtesting/modelo.py::run_modelo_scan(params=ParametrosBarreira(...))`
— já migrada para 6.000 candles por spec 036 (linhas 468/567 de
`modelo.py`). Nenhum código novo de teste estatístico.

**Rationale.** D4 de `specs/028-geometria-de-barreira/research.md` já
declarou que a avaliação reusa `run_modelo_scan` sem alteração de
lógica — e essa função já herda o teto de 6.000 de spec 036
automaticamente, por já estar no escopo daquela spec. O único código
que precisa mudar nesta spec é o teto de candles em `geometria.py`
(D1); a avaliação estatística (contagem esperada vs. observada sob a
hipótese de empate) já está correta e já vai rodar sobre a amostra
maior sem qualquer mudança adicional.

## D3 — Nota de correção sobre M13

**Contexto.** A intuição inicial do usuário para reabrir esta linha
comparava H20 ao veredito original errado de H14 (achado M13:
comparação por ponto único sem banda de incerteza, corrigido em
`supera_empate_com_confianca`).

**Verificação antes de escrever a spec.** `specs/028-geometria-de-
barreira/research.md` D3 já reporta o resultado de H20 como um teste
estatístico apropriado (`z = −0,07`, `p = 0,535`, contagem esperada
956,6 vs. observada 955) — não uma comparação de ponto único. H20 foi
avaliada DEPOIS de M13 já ter sido identificado e corrigido no mesmo
dia (2026-09-01), e sua própria spec já cita M13 como referência
conhecida. **Não é um caso de M13 não corrigido.**

**Consequência.** O motivo válido para reavaliar H20 não é "corrigir um
viés estatístico não corrigido" — é simplesmente que qualquer teste
estatístico legítimo pode mudar de resultado com mais amostra, e a
margem medida (0,997/1,027, a menos de 3% do empate) é estreita o
bastante para tornar essa possibilidade concreta, não hipotética. A
spec original (`spec.md`) foi corrigida para não misrepresentar o
trabalho anterior antes de qualquer código ser escrito.
