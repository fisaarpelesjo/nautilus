# Research: H14 — calibração do classificador de entrada

## D1 — diagnóstico ad-hoc, dois bugs corrigidos antes de qualquer conclusão

Antes de escrever este módulo, um script fora do repositório (não
commitado, mesmo padrão de diagnóstico usado em specs 052/054) rodou a
mesma pergunta pooled sobre `UNIVERSO_H11`. Duas rodadas foram
necessárias:

**Rodada 1 (com bug).** Importou `limiar_de_empate(p)` esperando o
limiar de decisão real e imprimiu "ponto de empate: 0.5000". `rotulo_bruto`
foi contado com `.isna().sum()` para a classe "tempo". Resultado: os
quintis de probabilidade previstos variavam entre 0,222 e 0,341 —
inteiramente **abaixo** de 0,5 — e a soma de alvo+stop+tempo por quintil
não batia com o `n` do quintil (faltavam ~20% dos eventos).

**Causa raiz 1 — função errada.** `limiar_de_empate(params)` devolve a
**razão de chances** de empate (`sl_mult/tp_mult` = 0,500) — não o
**limiar de probabilidade** usado pela produção para decidir
(`limiar_de_decisao(params)` = `sl_mult/(sl_mult+tp_mult)` = 0,3333).
São duas grandezas diferentes do mesmo par de parâmetros; o nome
parecido induziu o erro. `backtesting/modelo.py` já documenta as duas
funções lado a lado (linhas 66 e 279) — a confusão foi de quem escreveu
o diagnóstico, não do código.

**Causa raiz 2 — encoding de timeout.** `strategy/barreira_tripla.py::rotular`
usa `bruto = np.full(n, np.nan)` só como valor inicial para ATR
inválido (pulado no laço); o caso de timeout dentro do laço é
`r, fim = 0, limite` — **0, não NaN**. Contar "tempo" via `.isna().sum()`
só pegava o caso raro de ATR inválido, não os timeouts genuínos.

**Rodada 2 (corrigida).** Trocado para `limiar_de_decisao` e para
`(sub_rot == 0).sum()`. Resultado coerente: soma de alvo+stop+tempo bate
com `n` em todo quintil, e o limiar real de produção (0,3333) fica
dentro do intervalo de probabilidades observado, não fora dele.

## D2 — o subconjunto decidido, reconciliado com o já publicado

Com a correção, o subconjunto que a produção já decide (`prob > 0,3333`)
sobre `UNIVERSO_H11`/6.000 candles: **968 alvo, 1.378 stop, razão
0,7025**. O número já publicado em §4.15 (spec 036, mesmo universo e
histórico) é **971 alvo, 1.394 stop, razão 0,6966** — diferença de
0,3-1,1% nas contagens, atribuída a detalhe de alinhamento de índice
entre o script ad-hoc e o reprodutor de produção (ordem de
`dropna`/`intersection`), não a uma divergência de metodologia. As duas
medições concordam na conclusão que importa: a razão do subconjunto
decidido está bem acima do empate (0,500) e sobrevive ao IC de Wilson
(`supera_empate_com_confianca` = `True` nas duas).

## D3 — hipótese declarada antes da medição final (varredura de corte)

**Pergunta:** a probabilidade prevista, dentro do subconjunto já
decidido, tem uma cauda de alta confiança que um corte mais estrito
poderia isolar — abrindo caminho para uma variante de entrada por
confiança?

**Hipótese principal (o que tornaria a ideia útil):** razão de chances
**crescente e sustentada** conforme o corte sobe (0,3333 → 0,35 → 0,40 →
...), com `supera_empate_com_confianca` continuando `True` em cada
faixa — evidência de uma cauda explorável.

**Hipótese alternativa (declarada com igual peso, não só como
formalidade):** razão **achatada** (sem tendência clara) enquanto a
amostra ainda sustenta significância, seguida de colapso de amostra sem
ganho de razão — refutando a ideia sem precisar construir a variante de
entrada.

Cortes testados, decididos antes de rodar: `0,3333` (limiar real),
`0,35`, `0,40`, `0,45`, `0,50`, `0,55`, `0,60` — intervalo regular acima
do limiar real, parando quando a amostra fica de dígito único.

### Resultado (medido, `python main.py calibracao`, `UNIVERSO_H11`)

| corte | n | alvo | stop | razão | supera_empate_ci95 |
|---|---|---|---|---|---|
| 0,3333 (real) | 2.486 | 968 | 1.378 | 0,7025 | **True** |
| 0,35 | 1.056 | 411 | 597 | 0,6884 | **True** |
| 0,40 | 80 | 32 | 44 | 0,7273 | **False** |
| 0,45 | 17 | 10 | 6 | 1,6667 | **True** (amostra minúscula) |
| 0,50 | 6 | 2 | 3 | 0,6667 | **False** |
| 0,55 | 1 | 1 | 0 | inf | **False** |
| 0,60 | 1 | 1 | 0 | inf | **False** |

**A hipótese alternativa se confirma.** Entre 0,3333 e 0,35 — a única
faixa de dois pontos com amostra grande o bastante para comparar — a
razão **não sobe**, fica praticamente igual (0,7025 → 0,6884, dentro do
ruído). A partir de 0,40 a amostra desaba (80, depois 17, 6, 1, 1) e a
razão oscila sem padrão (0,73 → 1,67 → 0,67 → inf) — exatamente o
comportamento de ruído amostral, não de sinal crescente. O ponto em
0,45 "supera" por acaso com `n=17`, o mesmo padrão que motivou
`supera_empate_com_confianca` existir (M9/M13 do registro): ponto
estimado bom sem amostra para sustentar.

**Não existe cauda de alta confiança explorável.** A qualidade do
subconjunto decidido é essencialmente **plana** entre 0,33 e 0,35 (onde
ainda há amostra pra dizer algo) e depois só evapora — subir o corte não
troca "trades ruins" por "trades bons", só descarta amostra até sobrar
ruído. A variante de entrada por confiança (filtro binário mais
estrito) está refutada por este resultado — não vale a pena construí-la.

## O que isso não decide

- Não refuta o classificador em si — o subconjunto já decidido em
  0,3333 continua com razão real e significativa (0,70 > empate 0,50),
  igual ao já publicado em §4.15.
- Não testa **dimensionar** a posição pela confiança (apostar menos nas
  previsões fracas, mais nas fortes, sem descartar nenhuma) — mecanismo
  diferente de filtrar, não coberto aqui.
- Não testa o mecanismo de saída (take-profit ATR + stop trailing,
  nunca alterado em nenhuma das nove specs de H14 até aqui) — a outra
  frente que spec 047 deixou em aberto.

## Reprodução

`python main.py calibracao` · `reports/calibracao_*.json`.
