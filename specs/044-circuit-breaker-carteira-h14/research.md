# Fase 0 — Pesquisa: circuit breaker de perdas consecutivas na carteira de H14

## D1 — Escopo reduzido em relação ao circuit breaker de produção (sem cooldown por tempo)

**Contexto.** `execution/order_manager.py` implementa o circuit breaker
real com duas vias de reset: (a) primária — o próximo trade fechado com
`pnl > 0` zera `consecutive_losses`; (b) secundária —
`check_circuit_breaker_timeout()`, chamado uma vez por ciclo, autodesativa
o breaker depois de `CIRCUIT_BREAKER_COOLDOWN_HOURS` mesmo sem nenhum
trade lucrativo. A via (b) existe especificamente para o cenário em que o
breaker ativa **sem nenhuma posição aberta** — sem isso, o bot travaria
para sempre, já que não sobraria trade nenhum para gerar o lucro que
reseta o contador (documentado em `CLAUDE.md`, seção "Circuit breaker").

**Decisão.** Esta spec implementa só a via (a) — reset por trade
lucrativo. A via (b) não é portada.

**Por quê.** O cenário que a via (b) resolve — breaker ativo e zero
posições abertas por horas — é estrutural de operação ao vivo (um único
par pode ficar sem sinal de entrada por muito tempo). Não ocorre numa
carteira simulada de 12 pares sobre ~2,7 anos de histórico: com 12 pares
concorrentes, há sempre candidatos e posições fechando ao longo da
série — o reset primário por trade lucrativo é estatisticamente
garantido de ser exercitado. Portar a via (b) exigiria decidir uma
unidade de "tempo" dentro do simulador (que já opera em candles, não
em relógio de parede) sem nenhum cenário de teste que a exercitasse —
mecânica nova sem propósito medível, contra a disciplina do projeto de
não adicionar mecanismo sem motivo testável.

**Consequência.** Se a via (a) sozinha já reproduz o comportamento
prático do circuit breaker de produção no contexto de carteira (nunca
trava indefinidamente, porque sempre há trade fechando em algum dos 12
pares), a semântica testada aqui é equivalente à de produção para efeito
de medir o impacto no drawdown — só mais simples de implementar e
verificar.

**Alternativa considerada e descartada.** Portar a via (b) com uma
unidade arbitrária (ex.: N candles em vez de horas) — descartada por
introduzir um parâmetro novo sem contrapartida em produção, quebrando o
princípio de "reuso de mecânica já declarada" que motiva toda esta
spec.
