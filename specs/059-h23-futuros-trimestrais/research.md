# Research: H23 — prêmio de futuros trimestrais (contango) vs. funding perpétuo

## D1 — universo real: só BTC e ETH (verificado 2026-09-03)

Consulta via `ccxt` (`exchange.load_markets()`, `defaultType=future`)
mostrou 14 contratos com vencimento fixo na Binance, mas só 4 são
USDT-margined (o formato compatível com o resto do projeto, que já
opera USDT como quote): `BTC/USDT:USDT-260925`, `ETH/USDT:USDT-260925`,
`BTC/USDT:USDT-261225`, `ETH/USDT:USDT-261225`. Os outros 10 são
coin-margined (`BNB/USD`, `BTC/USD`, `ETH/USD`, `SOL/USD`, `XRP/USD`) —
excluídos por trazerem risco cambial na moeda de margem, fora do escopo
desta medição (que assume tudo denominado em USDT, mesma convenção de
H8). Universo pequeno e real, não escolhido — é o que existe.

## D2 — instantâneo, não série histórica (limitação declarada)

Diferente de funding rate (`fetch_funding_rate_history`, histórico
contínuo via endpoint dedicado), o preço de um contrato futuro com
vencimento fixo só existe enquanto o contrato está listado. Depois do
vencimento, o símbolo é descontinuado e não há preço consultável —
impossível reconstruir uma série de 1 ano como H8 fez para funding.
Esta medição é, por construção, um **retrato do prêmio no dia da
execução** para os contratos hoje listados (Set/2026 e Dez/2026) — não
uma série estatística com poder amostral. Declarado explicitamente,
não escondido atrás de uma tabela que pareça mais robusta do que é.

## D3 — custo e capital: reusa H8 sem duplicar

Mesma fórmula de `backtesting/funding_carry.py` (spec 058):
`CUSTO_ABERTURA_FECHAMENTO = 2 * (spot_taker + futures_taker)` — evento
único de abertura+fechamento, anualizado pela mesma base do prêmio
bruto (`365/dias_ate_vencimento`). Capital implantado = líquido sobre
nocional / 2 (posição sem alavancagem: nocional da perna spot + margem
≈ nocional da perna futura). Mesmo `BENCHMARK_RENDA_FIXA_AA` (5% a.a.)
de H8 — mesma pergunta de custo de oportunidade, não um número novo.

**Consequência não intuitiva, medida na prática (smoke test antes do
commit):** para contratos de curto prazo (próximos ao vencimento), o
custo fixo anualizado por `365/dias` pode superar o prêmio bruto e
produzir retorno líquido **negativo** — o custo não escala para baixo
com o prazo, então um contrato de 21 dias sofre um "imposto" anualizado
muito maior que um de 112 dias para o mesmo custo fixo em pontos
percentuais. Resultado esperado da fórmula, não um bug.

## D4 — hipótese declarada antes da medição final

**Principal:** o prêmio, mesmo positivo em alguns contratos, fica
abaixo do benchmark sobre capital implantado — mesma leitura de H8,
mecanismo diferente mas obstáculo econômico parecido.

**Alternativa, com igual peso:** o contrato de vencimento mais distante
(Dez/2026, mais tempo para o custo fixo diluir) supera o benchmark —
justificando considerar essa família de contrato como parte de uma
futura combinação com H8 (não decidido aqui).

## Reprodução

`python main.py basis` · `reports/basis_*.json`.

(Resultado real preenchido após a execução — ver
`docs/research/registro-de-hipoteses.md` §4.9 para o número medido.)
