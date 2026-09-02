# Implementation Plan: H20 — Geometria de barreira

**Branch**: `028-geometria-de-barreira` | **Date**: 2026-09-01 | **Spec**: [spec.md](spec.md)

## Summary

Medir como a margem entre razão de chances e ponto de empate responde à
geometria de saída, selecionar **uma** geometria por regra declarada antes da
medição, e avaliá-la com o procedimento de H14 sem alteração.

**O resultado inverteu a tese.** A razão de chances cai mais rápido que o ponto
de empate conforme o alvo se afasta: a folga vai de +0,3% em `tp = 2,0` a −48%
em `tp = 6,0`. A geometria não é alavanca sobre a margem, e o único sentido em
que ela responde é o contrário do proposto.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: pandas, numpy, statsmodels — **nenhuma nova**

**Storage**: reusa `reports/modelo_*.json` da avaliação

**Testing**: pytest, estendendo `tests/`

**Target Platform**: CLI local; produção intacta

**Performance Goals**: a medição de perfis é rotulagem pura — seis geometrias ×
12 pares × 2.000 candles, segundos. A avaliação com modelo é uma execução de
`run_modelo_scan`, comparável a H14.

**Constraints**: exatamente uma geometria avaliada com modelo (FR-014); a regra
não consulta desempenho (FR-004)

**Scale/Scope**: 6 geometrias medidas, 1 avaliada, 12 pares, 333 dias

## Constitution Check

| Princípio | Situação |
|---|---|
| **I. Safety First** | **Conforme.** Nenhum caminho de execução tocado. |
| **II. No Secrets in Code** | **Conforme.** |
| **III. Test Before Implement** | **Parcialmente conforme — ver nota.** |
| **IV. Incremental Delivery** | **Conforme.** Regra, veredito e módulo em commits separados. |
| **V. Observability Mandatory** | **Conforme.** `regra_declarada()` sai das mesmas constantes que a seleção aplica. |
| **VI. Idempotency** | **N/A.** |
| **VII. Explain Before Code** | **Conforme, e de forma verificável.** D1 commitado em `7cc19e0`, antes de qualquer medição. |

**Nota sobre o Princípio III, declarada e não minimizada.** A medição que
produziu o veredito rodou primeiro num script ad-hoc; o módulo e os testes vieram
depois, no commit `e83c1db`. A ordem correta seria a inversa.

O que **compensa** parcialmente: o módulo reproduz a medição ad-hoc número por
número, e os testes fixam as constantes da regra nos valores commitados em
`7cc19e0`, de modo que qualquer alteração posterior quebra um teste em vez de
passar despercebida. O que **não** compensa: se o módulo tivesse divergido do
script, eu teria descoberto isso depois de já ter registrado o veredito.

## Project Structure

```text
backtesting/
└── geometria.py               # NOVO: perfis, regra declarada, seleção
tests/
└── test_geometria.py          # NOVO: 16 testes, incluindo a guarda AST
```

Nada mais foi criado. `strategy/barreira_tripla.py` e `backtesting/modelo.py`
são reusados sem alteração — `ParametrosBarreira` já era parametrizado.

## Complexity Tracking

| Decisão | Por que necessária | Alternativa rejeitada |
|---|---|---|
| Regra commitada antes da medição | É a única prova de que ela não foi ajustada ao resultado | Escrever tudo junto: indistinguível de varredura |
| Selecionar a **menor** `tp` elegível | Maximizar a margem otimizaria sobre o conjunto | Escolher a de maior margem: testes múltiplos por outra porta |
| Guarda AST contra importar `modelo` | É a porta pela qual a regra consultaria desempenho | Confiar na disciplina: o defeito passaria silencioso |

## Fases

**Fase 0 ✅** — D1 (regra, commitada antes), D2 (perfis medidos), D3 (geometria
avaliada), D4 (integração), D5 (executabilidade).

**Fase 1 ✅** — o desenho é o próprio `research.md`: não há entidades novas além
de `PerfilGeometria`, e o contrato de CLI de H14 não muda.

**Fase 2 ✅** — `tasks.md`.

## Riscos herdados

| Risco | Origem | Mitigação |
|---|---|---|
| Varredura de parâmetro disfarçada | Este é **o** risco da spec | Regra commitada antes; guarda AST; uma geometria avaliada |
| Reutilizar número medido noutro contexto | Tentação natural com `E = 1,318` | FR-008; a elevação observada foi +21,1%, não +31,8% — a reutilização teria sido erro factual |
| Estimativa pontual sem incerteza | M13 | `supera_empate_com_confianca`, reusado sem alteração |
| Amostra insuficiente lida como reprovação | M9 | `MIN_DESFECHOS`, critério c3 |
