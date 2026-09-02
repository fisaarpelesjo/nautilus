# Quickstart — validação de H14

Cenários executáveis que provam que a feature faz o que a spec pede. Cada um
declara o que observar e o que significa falhar.

## Pré-requisitos

```bash
cd C:\Users\filip\OneDrive\Documents\GitHub\itgr
.venv\Scripts\activate
```

Acesso de leitura à Binance (dados públicos). Nenhuma chave de API é necessária.

---

## Cenário 1 — Rotulagem causal (US1, P1)

```bash
pytest tests/test_barreira_tripla.py -k causalidade -v
```

**Esperado:** o rótulo de um evento não muda quando preços **anteriores** a ele
são alterados, e muda quando preços dentro do seu horizonte são alterados.

**Falha se:** alterar um preço anterior ao evento mudar o rótulo dele. Seria a
rotulagem olhando para trás quando deveria olhar para frente — e o rótulo
deixaria de significar o que o nome diz.

---

## Cenário 2 — Purga remove sobreposição (US2, P1)

```bash
pytest tests/test_purga.py -k sobreposicao -v
```

**Esperado:** nenhuma amostra de treino tem `fim_horizonte` alcançando a janela
de teste.

**Falha se:** qualquer amostra sobreviver com horizonte invadindo o teste. É o
análogo, em aprendizado supervisionado, do achado M2 — e produziria o resultado
mais convincente e mais falso possível.

---

## Cenário 3 — Purga é global, não por par (US2, P1)

```bash
pytest tests/test_purga.py -k global -v
```

**Esperado:** uma amostra de BTC cujo horizonte alcança a janela de teste sai do
treino **mesmo quando a janela de teste é de ETH**.

**Falha se:** a purga for aplicada por par. Criptoativos se movem juntos —
correlação de **0,71** medida em H9 — e o modelo veria pelo BTC o desfecho que
deve prever para o ETH.

---

## Cenário 4 — Rótulos embaralhados preservam a distribuição (US3, P1)

```bash
pytest tests/test_modelo.py -k embaralhado -v
```

**Esperado:** a permutação preserva a frequência das classes e destrói a
associação entre atributo e rótulo.

**Falha se:** a distribuição mudar. Um embaralhamento que também altera as
proporções compararia duas coisas diferentes, e a linha de base perderia sentido.

---

## Cenário 5 — Modelo indistinguível do embaralhado é `sem sinal` (US3, P1)

**O cenário mais importante da spec.**

```bash
pytest tests/test_modelo.py -k sem_sinal -v
```

**Esperado:** desempenho do modelo real que não supere o do embaralhado produz
estado `sem sinal`, nunca aprovação.

**Falha se:** aparecer como melhora. Um classificador sempre encontra alguma
estrutura; sem esta guarda, capacidade do modelo seria lida como estrutura dos
dados.

---

## Cenário 6 — Sinal insuficiente é estado próprio

```bash
pytest tests/test_modelo.py -k insuficiente -v
```

**Esperado:** modelo que se distingue do embaralhado mas cuja razão de chances
no subconjunto decidido não supera **0,500** recebe estado `insuficiente`, não
`melhora` nem `sem sinal`.

**Falha se:** for colapsado em qualquer um dos dois. "Há sinal e ele não paga as
barreiras" é informação real, e é o único achado positivo que H14 pode produzir
se a hipótese não for aprovada.

---

## Cenário 7 — Falha de convergência e classe única (FR-012)

```bash
pytest tests/test_modelo.py -k "convergencia or classe_unica" -v
```

**Esperado:** estados explícitos, nunca métricas calculadas sobre uma estimação
que falhou.

**Falha se:** produzir números. Colinearidade medida de **0,959** entre
candidatos descartados mostra que este caminho de falha é real, não hipotético.

---

## Cenário 8 — Amostra insuficiente é inconclusiva

```bash
pytest tests/test_modelo.py -k amostra -v
```

**Esperado:** menos operações que o mínimo em **qualquer** versão produz
`inconclusivo`. Regra de H10, H11 e M9.

**Falha se:** produzir `piora`.

---

## Cenário 9 — Execução completa

```bash
python main.py modelo
```

**Esperado:** parâmetros declarados, distribuição de classes com a expectativa
de entrada aleatória, contagem por estado antes da tabela, diagnóstico de purga
e a declaração de executabilidade.

**Falha se:** a razão de empate `0,500` ou os cinco atributos não aparecerem na
saída — sem eles o leitor não consegue julgar o resultado.

---

## Cenário 10 — Produção intacta (FR-015, SC-006)

```bash
git diff --stat <commit-inicial-da-spec>..HEAD -- risk/ execution/ trading/ strategy/
```

**Esperado:** saída vazia.

**Falha se:** houver alteração. O bot roda em modo paper no VPS 24/7.

---

## Cenário 11 — Nenhuma dependência nova (FR-016, SC-007)

```bash
git diff <commit-inicial-da-spec>..HEAD -- requirements.txt requirements-dev.txt pyproject.toml
```

**Esperado:** saída vazia.

**Falha se:** qualquer pacote for adicionado. `scikit-learn` está ausente de
propósito: a escolha de um estimador de baixa capacidade é metodológica.

---

## Cenário 12 — Suíte completa sem regressão

```bash
pytest tests/ -q
```

**Esperado:** contagem maior que a anterior à feature, zero falhas.

---

## Critério de conclusão

Os doze cenários passam, e o veredito de H14 está registrado em
`docs/research/registro-de-hipoteses.md` com evidência, procedência, a razão de
chances observada contra a razão de empate declarada, e a declaração de
executabilidade operacional.
