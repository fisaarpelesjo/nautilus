# Fase 0 — Pesquisa: limite de drawdown diário na carteira de H14

## D1 — Só o limite diário, não semanal/mensal; e por que é uma família diferente do circuit breaker

**Contexto.** `execution/order_manager.py` implementa três limites de
perda por período (diário/semanal/mensal), cada um com seu saldo de
referência independente (`_reference_balance()`), resetado no início do
período correspondente. Spec 044 testou o circuit breaker de perdas
consecutivas isolado e mediu um resultado degenerado: drawdown caiu
para 0,57%, mas `total_trades` colapsou de 595-931 para 6 — porque o
único reset é um trade lucrativo, raro numa base de profit factor
abaixo de 1 (`docs/research/registro-de-hipoteses.md` §4.15, atualização
spec 044).

**Decisão.** Esta spec implementa só a via diária dos três limites de
período. Semanal e mensal ficam para uma spec futura, condicionados ao
resultado diário não ser também degenerado.

**Por quê (uma-variável-por-vez).** Testar os três limites juntos
misturaria o efeito de cada granularidade — se o resultado for bom ou
ruim, não dá para saber qual dos três (ou a combinação) foi responsável.
O diário é o mais frequente dos três (reseta a cada ~6 candles de 4h, o
mais rápido dos três) — se ele já mostrar comportamento não-degenerado,
semanal e mensal são extensões naturais; se o diário já colapsar como o
circuit breaker, não há motivo para testar granularidades mais lentas
(que teriam ainda menos oportunidade de resetar).

**Por que "reset por calendário" é uma família estruturalmente
diferente de "reset por resultado" (circuit breaker, spec 044).** O
circuit breaker só destrava com um evento de MÉRITO (trade lucrativo) —
se a estratégia atravessa um trecho ruim prolongado, o mecanismo pode
nunca destravar, porque o evento que o destrava é exatamente o que
ficou escasso. O limite de drawdown diário destrava com um evento de
TEMPO (novo dia de calendário) — acontece sempre, independente de
qualquer trade fechar bem ou mal. Um dia inteiro no limite ainda vira,
garantidamente, um novo saldo de referência no dia seguinte. Isso não
garante que o resultado será bom, mas elimina por construção a falha
específica que produziu o colapso amostral de spec 044 — hipótese
testável, não presumida como verdadeira.

**Alternativa considerada e descartada.** Implementar os três limites
de uma vez, já combinados — descartada pela mesma disciplina de
uma-variável-por-vez usada em specs 040-044: impediria saber se um
resultado bom ou degenerado vem do diário, do semanal, do mensal, ou da
interação entre eles.
