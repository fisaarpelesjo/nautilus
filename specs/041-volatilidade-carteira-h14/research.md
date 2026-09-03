# Fase 0 — Pesquisa: dimensionamento por volatilidade na carteira de H14

**Data:** 2026-09-03

Diferente da maioria das specs deste registro, quase toda decisão
numérica já estava declarada e medida antes desta spec — em spec 025
(H12). Esta Fase 0 declara só o que é novo: ONDE aplicar o fator já
existente.

---

## D1 — Ponto de aplicação: depois do dimensionamento já existente

**Decisão:** em `_simular_carteira_core` (spec 037), o fator de
`fator_volatilidade(atr_ratio)` multiplica `order_size` **depois** de
`min(MAX_ORDER_SIZE_USDT, (caixa/slots_livres)*0,95)` e do ajuste por
caixa disponível — nunca antes, nunca substituindo essas checagens.

**Rationale.** Mesmo princípio já declarado em spec 025 para
`simulate_backtest`: "o fator é aplicado DEPOIS do teto por ordem e da
reserva de caixa — compondo com as regras existentes em vez de
substitui-las... essa linha só pode REDUZIR o tamanho." Aplicar antes
(ex.: sobre o caixa bruto, antes do teto por ordem) permitiria, em
teoria, uma sequência de arredondamentos que burlasse o teto — não
existe esse risco aplicando por último.

**Por que não há D2, D3...** Alvo (0,02), piso (0,20) e a fórmula em si
(`min(1.0, alvo/atr_ratio)`) já foram declarados e medidos em spec 025 —
medir de novo para esta spec seria o mesmo erro que o projeto evita
(reabrir um número já fixado só porque o contexto de uso mudou, sem
razão para esperar que a distribuição de `atr_ratio` seja diferente
entre os pares usados então e agora — ambos vêm do mesmo `UNIVERSO_H11`
de 12 pares, FR-005).

---

## Resumo

| # | Decisão | Efeito |
|---|---|---|
| D1 | Fator aplicado depois do dimensionamento já existente (teto/caixa) | Impossível burlar o teto de posição; mesmo princípio de spec 025 |

## Fontes

- `docs/research/registro-de-hipoteses.md` §4.13 (H12) — conclusão que
  motivou o redirecionamento desta spec: "H12 não pode ser testada
  enquanto nenhuma estratégia tiver expectativa positiva."
- `docs/research/registro-de-hipoteses.md` §4.15 (H14, atualização
  spec 040) — mecanismo provável do drawdown de carteira (correlação
  entre ativos de risco sobe durante quedas amplas, quando `atr_ratio`
  também sobe) — motivação direta desta spec.
- `backtesting/volatilidade.py` (spec 025) — `fator_volatilidade`,
  `ParametrosVolatilidade`, `ALVO_PADRAO`, `FATOR_MINIMO_PADRAO`,
  reusados sem alteração.
