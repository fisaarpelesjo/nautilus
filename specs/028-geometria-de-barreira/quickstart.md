# Quickstart — validação de H20

## Cenário 1 — A regra foi declarada antes da medição

```bash
git log --oneline --reverse -- specs/028-geometria-de-barreira/research.md
```

**Esperado:** `7cc19e0` (regra, com D2/D3 marcados pendentes) **antes** de
`19a40e1` (veredito com os números).

**Falha se:** a ordem for inversa, ou os dois estiverem no mesmo commit. É a
única evidência de que a regra não foi ajustada ao resultado, e sem ela H20 é
indistinguível de uma varredura de parâmetro.

---

## Cenário 2 — A regra exibida é a regra aplicada

```bash
pytest tests/test_geometria.py -k regra_exibida -v
```

**Esperado:** o texto de `regra_declarada()` contém as constantes que a seleção
usa.

**Falha se:** divergirem. O relatório passaria a descrever um critério diferente
do aplicado.

---

## Cenário 3 — A seleção não consulta desempenho de modelo

```bash
pytest tests/test_geometria.py -k nao_importa_nada_de_modelo -v
```

**Esperado:** `backtesting/geometria.py` não importa `backtesting.modelo`.

**Falha se:** importar. É a porta pela qual H20 viraria varredura.

---

## Cenário 4 — As constantes são as commitadas em `7cc19e0`

```bash
pytest tests/test_geometria.py -k constantes_da_regra -v
```

**Esperado:** `ELEVACAO_H14 = 1.318`, `FOLGA = 1.09`, `TETO_PCT_TEMPO = 25.0`,
`MIN_DESFECHOS = 1000`, `SL_FIXO = 1.5`.

**Falha se:** qualquer uma tiver mudado. Alterá-las depois da medição
invalidaria a procedência.

---

## Cenário 5 — Seleciona a mais conservadora, não a melhor

```bash
pytest tests/test_geometria.py -k menor_tp_e_nao_a_de_maior_margem -v
```

**Esperado:** com `tp = 4,0` de margem folgada e `tp = 2,0` raspando, a regra
escolhe `tp = 2,0`.

**Falha se:** escolher a de maior margem. Seria otimizar sobre o conjunto, e o
problema de testes múltiplos voltaria por outra porta.

---

## Cenário 6 — Nenhuma elegível é desfecho, não erro

```bash
pytest tests/test_geometria.py -k nenhuma_elegivel -v
```

**Esperado:** `selecionar()` devolve `None` e a regra não é relaxada. FR-006.

---

## Cenário 7 — Limite de tempo não conta como desfecho

```bash
pytest tests/test_geometria.py -k limite_de_tempo -v
```

**Esperado:** `n_desfechos` conta apenas alvo e stop. FR-009 — com alvo mais
distante, mais eventos terminam por tempo, e a razão de chances passaria a
descrever uma fatia menor da amostra sem que isso aparecesse.

---

## Cenário 8 — A medição reproduz o que foi registrado

```bash
python -c "from backtesting.geometria import run_geometria_scan; r = run_geometria_scan(); [print(f'tp={p.tp_mult} razao={p.razao_base:.4f}') for p in r.perfis]; print('sel:', r.selecionada.tp_mult)"
```

**Esperado:** os valores de `research.md` D2 — `tp = 2,0` com razão 0,6223 até
`tp = 6,0` com 0,1076 — e `tp = 2,0` selecionada.

**Falha se:** divergirem. O veredito foi registrado a partir desses números.

---

## Cenário 9 — Produção intacta e sem dependência nova

```bash
git diff --stat f486cfe~1..HEAD -- risk/ execution/ trading/ requirements.txt requirements-dev.txt pyproject.toml
```

**Esperado:** saída vazia.

---

## Cenário 10 — Suíte completa

```bash
pytest tests/ -q
```

**Esperado:** 668 testes, zero falhas.

---

## Critério de conclusão

Os dez cenários passam, e o veredito de H20 está registrado em §4.16 com o
achado de invariância da margem entre as duas geometrias avaliadas.
