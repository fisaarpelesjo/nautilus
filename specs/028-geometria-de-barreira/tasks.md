---

description: "Task list for H20 — geometria de barreira"
---

# Tasks: H20 — Geometria de barreira

**Tests**: obrigatórios. Ver a nota do `plan.md` sobre a ordem efetivamente
seguida — os testes vieram depois da medição, e isso está declarado.

---

## Phase 1: Regra declarada *(antes de qualquer medição)*

- [X] T001 Redigir a regra de seleção em `research.md` D1, com a procedência de cada constante
- [X] T002 **Commitar a regra antes de medir qualquer geometria** — `7cc19e0`

**Checkpoint**: a regra está carimbada no git. Sem isto, nada do que vem depois
é distinguível de varredura.

---

## Phase 2: Medição sem modelo (US1)

- [X] T003 Medir os perfis das seis geometrias candidatas: razão de chances, ponto de empate, distribuição das três classes
- [X] T004 Confrontar a medição com a tese — a razão cai mais rápido que o empate, e a tese está invertida
- [X] T005 Registrar os perfis em `research.md` D2

---

## Phase 3: Seleção e avaliação (US2, US3)

- [X] T006 Aplicar a regra declarada aos perfis medidos
- [X] T007 Avaliar a geometria selecionada com `run_modelo_scan`, sem alterar o procedimento de H14
- [X] T008 Separar os dois testes: há sinal (contra a taxa base) e paga a geometria (contra o empate)
- [X] T009 Registrar a geometria avaliada em `research.md` D3

---

## Phase 4: Código reproduzível

- [X] T010 Implementar `PerfilGeometria` com `n_desfechos` excluindo limite de tempo — FR-009
- [X] T011 Implementar `regra_declarada()` a partir das mesmas constantes que a seleção aplica — FR-003
- [X] T012 Implementar `medir_perfis()` e `selecionar()`, com `None` para nenhuma elegível — FR-006
- [X] T013 Teste: guarda AST contra importar `backtesting.modelo` — FR-004
- [X] T014 Teste: constantes fixadas nos valores de `7cc19e0`
- [X] T015 Teste: seleciona a menor `tp`, não a de maior margem
- [X] T016 Teste: alvo mais distante reduz a razão de chances
- [X] T017 Verificar que o módulo reproduz a medição ad-hoc número por número

---

## Phase 5: Veredito

- [X] T018 Registrar o veredito de H20 em `docs/research/registro-de-hipoteses.md` §4.16
- [X] T019 Registrar o achado de invariância da margem entre duas geometrias
- [X] T020 Reordenar a fila e atualizar §6.3-b
- [X] T021 Confirmar produção intacta e suíte sem redução

---

## Notes

- **A ordem das duas primeiras fases é o conteúdo da spec.** Medir antes de
  declarar a regra teria produzido os mesmos números e nenhuma evidência.
- A geometria selecionada passou por **+0,33%**, na fronteira. Com folga um
  pouco maior, nenhuma seria elegível e H20 encerraria sem avaliação de modelo —
  desfecho que FR-006 previa. O veredito seria o mesmo; a evidência, mais fraca.
