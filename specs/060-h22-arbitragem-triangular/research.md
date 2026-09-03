# Research: H22 — arbitragem triangular intra-corretora

## D1 — por que o obstáculo dominante de H15 não se aplica aqui

H15 (spec 029, corrigida em spec 053/M15) mede diferencial entre DUAS
corretoras diferentes. O achado central de H15: mesmo após paralelizar
a leitura, 5 das 15 combinações de corretoras nunca produziram uma
observação válida — `gate` é consistentemente mais lenta em termos
ABSOLUTOS que as outras cinco corretoras a partir da VPS usada, uma
característica real de rede entre servidores diferentes, não um defeito
de instrumento corrigível por paralelismo.

Arbitragem triangular lê três livros da MESMA corretora — não há
"corretora lenta" a comparar contra "corretora rápida"; as três
requisições saem do mesmo processo, para o mesmo host, com a mesma
infraestrutura de rede. O teto de latência (D3) deveria ser
folgadamente cumprido, ao contrário de H15.

## D2 — custo de três pernas na mesma corretora

Diferente de H15 (custo varia por corretora, de 0,10% a 0,40% por
perna — `TAXA_TOMADOR` em `backtesting/arbitragem.py`), aqui as três
pernas são sempre a mesma corretora (Binance) — mesma taxa taker spot
em todas: 0,10% (`CUSTO_TAKER_BINANCE`, já verificada nesta sessão para
H8/spec 058). Custo total do ciclo: **0,30%** (3 × 0,10%) — teto de
lucratividade mais simples de calcular que H15, onde cada combinação de
corretoras tem um custo diferente.

## D3 — teto de latência reusado de H15, conservador aqui

`TETO_LATENCIA_MS = 2000`, mesmo valor de H15/spec 029, reusado por
comparabilidade entre as duas hipóteses de arbitragem deste registro —
não recalibrado para parecer mais favorável. Smoke test local (leitura
real da Binance, 2026-09-03): intervalo medido entre as três pernas foi
**797ms**, bem abaixo do teto — consistente com D1 (sem obstáculo de
latência entre corretoras).

## D4 — agregação exige o mínimo na direção MENOS coberta, diferente de H15

H15 tem 15 combinações de corretoras **independentes** — uma pode ter
40 observações enquanto outra tem zero, porque cada `ler_livro` de uma
corretora pode falhar isoladamente sem afetar as demais. `agregar()` de
H15 usa a combinação MAIS coberta para o estado descritivo, porque a
pergunta ali é "existe ALGUMA combinação com evidência real?".

Aqui, as duas direções (`direto`/`inverso`) do mesmo triângulo nascem
**sempre juntas** no mesmo ciclo — ou as três pernas leem com sucesso e
as duas direções ganham uma observação, ou o ciclo inteiro é abortado
(D5) e nenhuma direção ganha nada. Como as duas direções deveriam ter
cobertura igual por construção, exigir o mínimo na MENOS coberta é a
checagem correta — qualquer divergência sinalizaria um bug de
contagem, não uma corretora lenta específica como em H15.

## D5 — perna indisponível aborta o ciclo inteiro, sem medição parcial

Diferente de H15 (uma combinação de duas corretoras é independente das
outras 14 — falha isolada não aborta o ciclo, FR-011 original), aqui as
três pernas formam um ÚNICO ciclo — um livro faltando (`ETH/BTC`, por
exemplo) impede o cálculo de QUALQUER direção, não só de uma parte. Uma
"medição parcial" (ex.: calcular só a perna 1 e 2) não teria significado
econômico — não descreve um ciclo executável.

## Hipótese declarada antes de medir

**Principal:** diferencial líquido negativo ou muito próximo de zero na
maioria das observações — mercados líquidos da Binance são competidos
por arbitragem triangular há anos; ausência do obstáculo de latência
entre corretoras não implica ausência de concorrência (bots
intra-corretora operam na escala de milissegundos, mais rápido que
qualquer polling via API pública consegue medir).

**Alternativa, com igual peso:** a ausência do obstáculo que
inutilizou 14 das 15 combinações de H15 permite capturar
desalinhamentos momentâneos reais entre os três livros — mesmo raros,
mensuráveis numa campanha de ≥ 30 observações por direção.

## Reprodução

`python main.py triangular` (padrão: `BTC/USDT` × `ETH/BTC` ×
`ETH/USDT`) · `data/arbitragem_triangular.jsonl` · `reports/triangular_*.json`.

(Resultado da campanha real preenchido após execução — ver
`docs/research/registro-de-hipoteses.md` §6.1 para o número medido.)
