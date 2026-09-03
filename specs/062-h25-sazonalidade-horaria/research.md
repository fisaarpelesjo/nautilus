# Research: H25 — sazonalidade por sessão de negociação (hora do dia)

## D1 — janelas pré-registradas, não descobertas olhando dado

Três blocos de 8h UTC, convenção de mercado (não escolhidos após medir
nada):

| Janela | Horas UTC | Racional |
|---|---|---|
| Ásia | 00h–08h | Tóquio/Hong Kong/Singapura em horário comercial |
| Europa | 08h–16h | Londres/Frankfurt em horário comercial |
| EUA | 16h–24h | Nova York em horário comercial |

Cobertura: as três janelas somam exatamente 24h sem sobreposição
(testado — `test_janelas_cobrem_as_24_horas_sem_sobreposicao`).

**Framing: restringir, não evitar.** "Filtro" aqui significa permitir
`BUY` só DENTRO da janela declarada — mesma framing de bloqueio que H5
usou (suprimir entradas em dias específicos), não "evitar" a janela. A
escolha é arbitrária entre as duas framings possíveis; documentada para
que não pareça ambígua depois.

**Escopo do filtro: só entrada, nunca saída.** Mesmo princípio já
estabelecido pelos filtros aditivos existentes em produção
(`REGIME_FILTER_ENABLED`/`HIGH_VOLATILITY_FILTER_ENABLED`,
`strategy/ema_rsi.py`): uma posição já aberta sempre pode sair por
`SELL`, stop ou take-profit — o filtro nunca prende capital numa
posição perdedora só porque a hora "errada" chegou.

## D2 — universo: UNIVERSO_H11, não escolhido para este teste

`backtesting.horizonte.UNIVERSO_H11` (12 pares) — já estabelecido por
specs anteriores (H11, H14, H20), reusado sem alteração. Timeframe `4h`
(mesmo de toda a linha de investigação).

## D3 — a disciplina que evita repetir a armadilha de H5

H5 (`docs/research/registro-de-hipoteses.md` §4.6) reprovou
especificamente por **"só na busca"**: profit factor melhorou na janela
de descoberta (BTC/USDT 0,81→1,49), mas a confirmação via
`multimarket` deu profit factor de **0,01** — o filtro não carregava
informação real, só se ajustou ao ruído daquela janela específica.

Duas garantias estruturais contra repetir isso:

1. **Pré-registro total.** As 3 janelas × 12 pares = 36 combinações são
   TODAS reportadas — nenhuma seleção post-hoc de "qual janela olhar"
   depois de ver o resultado. H5 testou só 1 dia (segunda-feira,
   escolhido a partir da amostra de paper) — aqui não há esse grau de
   liberdade.
2. **Confirmação fora da amostra obrigatória, mesma bateria já
   estabelecida.** Reusa `backtesting.multimarket.classify()` — a MESMA
   função que já decide `confirmado`/`defensivo`/`só_na_busca`/
   `reprovado`/`inconclusivo` para H10/H14/H20 (via `run_scan`). Nenhum
   critério novo inventado para esta spec ter mais chance de passar.
   Só `confirmado` (aprovado na busca E na validação) conta como
   evidência real — `só_na_busca` é reportado, mas nunca apresentado
   como aprovação.

## Hipótese declarada antes de medir

**Principal:** ao menos uma das 36 combinações atinge `confirmado`.

**Alternativa, com igual peso:** nenhuma confirma — mesmo padrão de H5,
fecha a família "filtro de tempo sobre H1" (as duas granularidades
óbvias, dia da semana e hora do dia, ambas testadas com a mesma
disciplina).

## Reprodução

`python main.py sazonalidade` · `reports/sazonalidade_*.json`.

(Resultado real preenchido após a execução — ver
`docs/research/registro-de-hipoteses.md` §6.3 para o número medido.)
