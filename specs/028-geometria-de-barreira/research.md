# Fase 0 — Pesquisa: H20, geometria de barreira

**Data:** 2026-09-01

> **Este documento foi escrito em duas etapas deliberadamente separadas.**
> A seção D1 — a regra de seleção — foi redigida e **commitada antes** de
> qualquer medição de geometria existir. As seções seguintes foram preenchidas
> depois. O histórico do git é a prova de que a regra não foi ajustada ao
> resultado, e essa prova é a única coisa que separa H20 de uma varredura de
> parâmetro.

---

## D1 — A regra de seleção *(declarada antes da medição)*

### Conjunto de geometrias candidatas

Stop fixo em `1,5 × ATR` — o mesmo do bot e o mesmo de H14. Varia-se apenas a
distância do alvo:

```
tp ∈ {2,0 · 2,5 · 3,0 · 4,0 · 5,0 · 6,0} × ATR
```

`tp = 3,0` é a geometria de referência (H14). Limite de tempo fixo em 24 velas.

Variar só o alvo é deliberado: mexer nos dois eixos multiplicaria o conjunto sem
responder nada que o eixo do alvo não responda, e o stop tem significado
operacional próprio — é o que limita a perda por operação.

### A regra

Seja, para cada geometria:

- `razao_base` — razão de chances alvo/stop **observada na série**, sem modelo
- `empate = sl / tp` — o ponto de equilíbrio imposto pela geometria
- `E = 1,318` — a elevação relativa que H14 mediu (0,3896 → 0,5134)
- `F = 1,09` — folga exigida sobre o empate

**Uma geometria é elegível quando:**

```
(1)  razao_base × E  ≥  empate × F
(2)  fração de eventos terminando por LIMITE DE TEMPO  ≤  25%
(3)  eventos com desfecho alvo ou stop  ≥  1.000
```

**Entre as elegíveis, seleciona-se a de menor `tp`** — a mais conservadora, mais
próxima da geometria de referência. Empate de `tp` é impossível no conjunto
declarado, então a seleção é determinística.

**Se nenhuma for elegível, H20 se encerra sem avaliação de modelo.** A regra não
é relaxada. Este é um desfecho legítimo (FR-006).

### De onde sai cada número

**`E = 1,318`.** É a elevação medida em H14: o modelo levou a razão de chances
de 0,3896 (todos os eventos) para 0,5134 (subconjunto decidido), com `z = +5,21`
e `p < 0,0001`. Usá-la aqui é usar um resultado medido para **formular a regra**,
que Assumptions autoriza explicitamente. O que FR-008 proíbe — e que não será
feito — é reutilizá-la como se fosse o resultado da geometria nova.

**`F = 1,09`.** Sai do poder estatístico de H14, não de escolha. Com 1.580
decisões, rejeitar o empate a 5% unilateral exige fração de alvos acima de
`0,3333 + 1,645 × 18,7/1580 = 0,3528`, isto é, razão de chances acima de
**0,545** contra um empate de 0,500 — uma folga de **+9%**. Exigir menos
selecionaria uma geometria em que, mesmo dando tudo certo, o resultado ficaria
dentro do ruído. Foi exatamente o que aconteceu em H14, e é o achado M13.

**Teto de 25% por limite de tempo.** Em `tp = 3,0` a medição de H14 deu 12,8%.
Um alvo mais distante empurra eventos para o limite de tempo, e a razão de
chances descreve apenas os que tocam alvo ou stop (FR-009). Acima de um quarto
da amostra terminando por tempo, a razão passa a falar de uma minoria dos
eventos e a comparação entre geometrias perde sentido.

**Mínimo de 1.000 desfechos.** H14 operou com 1.580 e não conseguiu resolver a
margem. Abaixo de 1.000 a situação só piora, e o resultado seria inconclusivo
por construção.

### O que a regra deliberadamente não faz

Não consulta nenhum modelo treinado na geometria candidata (FR-004). Não escolhe
a geometria de maior margem — escolhe a **menor `tp` que satisfaz o critério**,
porque maximizar a margem seria otimizar sobre o conjunto e reintroduziria o
problema de testes múltiplos por outra porta.

---

## D2 — Perfis medidos

*(Preenchido após a medição. Ver commit anterior para a data de declaração da
regra.)*

**Pendente.**

---

## D3 — Geometria selecionada

*(Preenchido após a medição.)*

**Pendente.**

---

## D4 — Ponto de integração

**Decisão:** reusar `strategy/barreira_tripla.py` e `backtesting/modelo.py` sem
alteração de lógica. `ParametrosBarreira` já é parametrizado por `sl_mult`,
`tp_mult` e `limite_velas`, e `limiar_de_decisao`/`limiar_de_empate` já derivam
dos multiplicadores.

A medição sem modelo (US1) precisa apenas de `rotular` e `razao_de_chances`, que
já existem. A avaliação (US3) é `run_modelo_scan` com outros parâmetros.

**Consequência:** H20 adiciona pouco código. O trabalho está na disciplina da
seleção, não na implementação.

---

## D5 — Executabilidade operacional

Herda integralmente as ressalvas de H14: avaliar o modelo por ciclo é barato,
mas não existe mecanismo de retreino nem de detecção de degradação, e a
degradação é silenciosa.

**Uma ressalva adicional, específica de H20.** Uma geometria com alvo mais
distante mantém posições abertas por mais tempo, o que aumenta a exposição a
eventos de gap e a interações com o trailing stop que o bot já aplica. Se H20
for aprovada, essa interação precisa de avaliação própria antes de qualquer
consideração operacional — não está no escopo desta spec.

## Fontes

- `docs/research/registro-de-hipoteses.md` §4.15 (H14: elevação de +31,8%,
  `z = +5,21`; margem não resolvida, `z = +0,50`), §5 (M13).
- `specs/027-aprendizado-barreira-tripla/research.md` (D2: expectativa de
  −0,241 ATR ao acaso; razão de empate 0,500).
- Medição própria, 2026-09-01 — ver D2.
