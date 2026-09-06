# Research: H38 — Gate por volatilidade implícita (Deribit DVOL)

## D1 — a pergunta e o critério, declarados antes de medir

A mesma população de eventos de entrada do sinal primário (EMA/RSI,
`precompute_signals`, rotulados pela barreira tripla de H14) que H27 já
mediu (`backtesting/meta_labeling.py::avaliar_precondicao`) é dividida em
dois subgrupos pelo nível de DVOL (BTC) no momento de cada evento: decil
mais alto da própria série de DVOL ("stress") vs. o resto. **Critério de
precondição, declarado antes de medir:** o subgrupo "resto" precisa ter
razão alvo/stop MAIOR que o subgrupo "dvol alto" — direção declarada
antes de ver qualquer número (DVOL alto discrimina para PIOR, não para
melhor). Se a razão não for maior, ou os dois forem indistinguíveis, a
precondição não é atendida.

## D2 — o número de partida já publicado (H27)

O resultado real já medido e publicado por H27 (`docs/research/registro-de-hipoteses.md`
§4.15/spec 064) sobre essa MESMA população, pooled em `UNIVERSO_H11`,
6.000 candles por par: `n=740, alvo=227, stop=453, razão=0,5011` — bem
perto do empate (0,5000), sem superar com confiança. **Consequência
declarada antes de medir:** dividir uma população de 740 eventos (453
stops) em dois subgrupos por DVOL vai produzir amostras ainda menores em
cada lado — a mesma disciplina de M9/M13 (intervalo de confiança mais
largo com amostra menor) torna MUITO provável que nenhum dos dois
subgrupos, isoladamente, supere o empate com confiança. Isso não invalida
o teste: o critério de precondição (D1) compara os DOIS PONTOS estimados
entre si, não exige que qualquer um dos dois isoladamente supere o
empate.

## D3 — decil calibrado sobre a própria série de DVOL

Decil mais alto (90º percentil, mesmo padrão de decil de H26/H35, só
invertido: "mais alto" em vez de "mais baixo", porque aqui o extremo que
importa é volatilidade EM STRESS, não crowding de posição) da distribuição
histórica do próprio DVOL — não um valor absoluto (ex.: "DVOL > 80") que
privilegiaria arbitrariamente o regime de volatilidade vigente no período
medido.

## D4 — alinhamento causal e exclusão de eventos sem DVOL

Mesma disciplina causal D-1 de H17/H32/H36 (reimplementada localmente em
`backtesting/dvol_gate.py`, mesma decisão de não inverter a direção de
dependência do projeto): evento no dia D usa o DVOL de fechamento do dia
D-1. Evento cujo dia não tem DVOL alinhável (fora da retenção da fonte)
é EXCLUÍDO da divisão — nunca presumido um nível de DVOL sem dado real.

## D5 — retenção real do endpoint, medida (não presumida)

Probe real via `requests` nesta sessão (2026-09-06,
`get_volatility_index_data`, `currency=BTC`, `resolution=86400`): 901
pontos diários, de 2024-03-19 a 2026-09-06 — sem paginação necessária
(resolução diária cobre o intervalo pedido numa única chamada, diferente
do teto de 1000 registros por chamada que aparece em resoluções mais
finas). Cobertura suficiente para alinhar com o histórico de 6.000
candles (~2,7 anos) usado por H27, embora não cubra a janela inteira —
eventos antes de 2024-03-19 são excluídos da divisão por DVOL (D4), sem
afetar o número já publicado de H27 (que não depende de DVOL).

## Comparação planejada com H27

Mesma arquitetura de precondição (dividir a MESMA população de eventos em
subgrupos e comparar), fonte de dado e propósito diferentes: H27
verifica se o PRÓPRIO sinal primário carrega informação (baseline vs.
entrada primária); H38 verifica se uma variável de MERCADO externa
(volatilidade implícita) discrimina dentro da população que já passou
pelo crivo de H27. Os dois podem legitimamente chegar a "precondição não
atendida" por razões diferentes — H27 por o sinal primário não superar o
empate global; H38 por o DVOL não discriminar dentro do sinal primário —
sem contradição entre os dois resultados.

## Hipótese declarada antes de medir

**Principal:** eventos de entrada com DVOL no decil mais alto têm razão
alvo/stop pior que o resto, evidenciando que o gate discrimina.

**Alternativa, com peso igual, e mais provável dado D2:** os dois
subgrupos não diferem de forma que importe — o nível de DVOL no momento
da entrada não carrega informação adicional sobre o resultado do trade
primário, além do que o próprio sinal EMA/RSI já carrega (que por si só
já está quase no empate). Precondição não atendida, mesmo desfecho
estrutural de H27 — spec encerrada por desenho, sem prosseguir para uma
implementação completa do gate aditivo em produção.

## Reprodução

`python main.py dvolgate` · `reports/dvol_gate_*.json`.

(Resultado real preenchido após a execução — ver
`docs/research/registro-de-hipoteses.md` §6.1 para o veredito medido, com
comparação explícita contra H27.)
