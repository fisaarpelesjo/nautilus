# Fase 0 — Pesquisa: H12, dimensionamento por volatilidade

**Data:** 2026-09-01

A spec deixou três decisões para esta fase, todas resolvidas por medição.

---

## D1 — Medida de volatilidade

**Decisão:** usar `atr_ratio` — ATR(14) dividido pelo preço de fechamento.

**Rationale.** O indicador **já existe** e já é calculado por
`calculate_indicators` em todas as estratégias do projeto. É volatilidade
realizada normalizada pelo preço, que é exatamente o que a spec pede ("variação
típica dos retornos recentes"), e comparável entre pares de preços muito
diferentes.

Reusá-lo tem uma vantagem que uma medida nova não teria: o projeto já usa
`atr_ratio` para o filtro de volatilidade elevada e para o cálculo de stop loss.
Introduzir uma segunda medida de volatilidade criaria duas definições
concorrentes do mesmo conceito dentro do mesmo sistema.

**Alternativas consideradas.** Desvio padrão de log-retornos em janela fixa.
Rejeitada: exigiria decidir a janela — parâmetro novo a justificar — e produziria
número que não conversa com o `atr_ratio` que o resto do sistema já usa. O ATR
tem janela de 14 períodos herdada da configuração existente, então a janela já
está declarada e não é escolha nova.

---

## D2 — Fórmula do fator

**Decisão:**

```
fator = min(1.0, alvo_volatilidade / atr_ratio)
tamanho = tamanho_original × fator
```

**O teto de 1,0 é invariante de código, não convenção.** FR-003 proíbe ampliar a
posição e a constituição proíbe alavancagem (`max_leverage = 1`). Com o teto no
código, não existe caminho pelo qual esta feature aumente exposição — nem por
alvo mal configurado, nem por volatilidade anormalmente baixa.

**Casos degenerados.** `atr_ratio` nulo, ausente ou não finito devolve fator 1,0
— o tamanho que o sistema já calcularia. Recair no comportamento vigente é a
política de falha do projeto: dado desconhecido nunca vira decisão silenciosa.

---

## D3 — Valor do alvo de volatilidade

**Decisão:** `0,02`, próximo à mediana observada.

**Medição** (12 pares, 23.412 observações de 4h, 2026-09-01):

| Percentil | `atr_ratio` |
|---|---|
| p5 | 0,0064 |
| p25 | 0,0139 |
| **p50** | **0,0187** |
| p75 | 0,0242 |
| p90 | 0,0306 |
| p95 | 0,0359 |
| p99 | 0,0474 |

`HIGH_VOLATILITY_ATR_RATIO`, a constante que o projeto já usa para classificar
volatilidade elevada, vale 0,05 — cruzada em apenas **0,7%** das observações.
Usá-la como alvo tornaria o dimensionamento praticamente inerte.

Efeito de cada alvo candidato:

| Alvo | Fator médio | Observações com fator < 1 |
|---|---|---|
| 0,010 | 0,581 | 89% |
| 0,015 | 0,781 | 70% |
| **0,020** | **0,901** | **44%** |
| 0,030 | 0,981 | 11% |

**Rationale.** O alvo foi escolhido para o mecanismo ser **neutro na escala
média**, não para maximizar desempenho. Em 0,02 o fator médio é 0,90: metade das
observações fica intocada e a outra metade é reduzida proporcionalmente ao
excesso de volatilidade. Alvos menores transformam a feature em redução
generalizada de exposição, e alvos maiores a tornam inerte.

**Declaração honesta:** a mediana vem do mesmo universo que será avaliado, então
há calibração dentro da amostra. Ela é de **escala**, não de desempenho — nenhum
alvo foi testado contra retorno antes de ser fixado, e o alvo permanece único
para toda a avaliação. Varrer alvos até um passar seria o problema de testes
múltiplos que a confirmação fora da amostra existe para conter.

**Consequência que reforça US2.** Fator médio de 0,90 significa **exposição média
~10% menor**. Num mercado em queda, isso sozinho melhora o retorno relativo ao
buy-and-hold sem nenhuma capacidade de seleção. É a razão de o desconto de
exposição ser P1 e não refinamento.

---

## D4 — Ponto de integração

**Decisão:** parâmetro opcional em `engine.simulate_backtest`, com default que
preserva o comportamento atual.

**Rationale.** O tamanho é calculado dentro do laço de simulação, no momento da
entrada. As alternativas eram:

1. **Duplicar o laço** num motor próprio. Rejeitada — cria duas implementações da
   mesma lógica de execução, que é exatamente o defeito M1: backtest e produção
   rodando estratégias diferentes, com toda decisão anterior tomada com régua
   inconsistente.
2. **Alterar `risk/manager.py`**. Rejeitada — é caminho de produção, e FR-013
   exige que o bot em execução não mude. A constituição classifica esse arquivo
   como sujeito ao princípio Safety First.
3. **Parâmetro opcional no motor existente.** Adotada. Uma linha de assinatura,
   default `None`, comportamento idêntico quando ausente — verificável por teste
   de regressão comparando resultado com e sem o parâmetro.

---

## Resumo das decisões

| # | Decisão | Efeito na implementação |
|---|---|---|
| D1 | `atr_ratio` como medida | Nenhum indicador novo; reusa o que já está no DataFrame preparado |
| D2 | `min(1.0, alvo/atr_ratio)` | Teto de 1,0 no código torna ampliação impossível |
| D3 | Alvo 0,02 | Fator médio 0,90; exposição média ~10% menor |
| D4 | Parâmetro opcional no motor | Sem duplicar laço, sem tocar produção |

**Expectativa registrada antes da execução:** o dimensionamento reduzirá
drawdown — é o que o mecanismo faz. A pergunta aberta é se o retorno cai na
mesma proporção. Se cair, H12 está encerrada e o drawdown de H7 não era problema
de dimensionamento. Registrar a previsão antes permite distinguir, depois,
previsão de racionalização.

## Fontes

- Medição própria de `atr_ratio`, 2026-09-01, 12 pares × 2000 candles de 4h.
- `config/settings.py`: `HIGH_VOLATILITY_ATR_RATIO = 0.05`, `ATR` de 14 períodos.
- `docs/research/registro-de-hipoteses.md` §4.8 (H7, drawdown 11,76%), §5 (M1, M7).
