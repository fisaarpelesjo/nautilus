# Contrato de CLI — `python main.py modelo`

## Invocação

```
python main.py modelo
```

Alias: `ml`.

## Argumentos

Nenhum. Diferente de `volatilidade [ALVO]` e `barras [TIPO]`, aqui **nada** é
parametrizável: barreiras, atributos, limiar de correlação, embargo e universo
são todos declarados em `research.md` e fixos.

O motivo é FR-019 combinado com o achado de H13: 96 combinações produziram uma
aprovação, abaixo da expectativa do acaso. Expor qualquer eixo como flag
convidaria a varrê-lo, e um modelo tem eixos demais para que isso seja seguro.

## Saída em terminal

1. **Parâmetros declarados** — barreiras, limite de tempo, os cinco atributos
   com a correlação máxima de cada um, embargo, e a **razão de empate 0,500**.
2. **Distribuição de classes** — frequência de alvo, stop e limite de tempo, com
   a expectativa de uma entrada aleatória e a elevação relativa que o modelo
   precisa produzir.
3. **Contagem por estado antes da tabela** — avaliadas, melhora, só na busca,
   confundidas, sem vantagem, piora, insuficientes, sem sinal, inconclusivas,
   não convergiu, classe única, erro.
4. **Tabela por par** — amostras de treino e teste após purga, razão de chances
   geral e no subconjunto decidido, métricas do modelo e das regras com deltas,
   delta contra o embaralhado, operações, custo, estado.
5. **Diagnóstico de purga** — amostras removidas por sobreposição e por embargo.
   É o número que distingue "não houve vantagem" de "a purga esvaziou o treino".
6. **Legenda** — significado de `sem sinal`, `insuficiente`, `confundido`,
   `só na busca`, e por que acurácia não aparece.
7. **Executabilidade** — declaração de D6, incluindo a ausência de mecanismo de
   retreino e de detecção de degradação.

## Saída em arquivo

`reports/modelo_{timestamp}.{json,csv,md}`.

## Códigos de saída

| Código | Significado |
|---|---|
| 0 | Execução concluída, com ou sem sinal encontrado |
| 1 | Falha de configuração (universo vazio, dependência ausente) |

Ausência de sinal **não** é erro. É resultado.

## Garantias

- **Não altera o caminho de produção.** Estratégias, motor, `risk/` e
  `execution/` permanecem intactos.
- **Não adiciona dependência.**
- **Rotulagem causal.** O rótulo de um evento depende apenas de preços
  posteriores a ele; nenhum atributo usa informação posterior ao evento.
- **Purga temporal e global.** Nenhuma amostra de treino, de qualquer par, tem
  horizonte alcançando a janela de teste ou o embargo.
- **Três linhas de base declaradas** em toda avaliação: regras, buy-and-hold e
  rótulos embaralhados.
- **Não altera critério de aprovação.** Limiares vigentes.
- **Falha isolada não aborta a varredura.**
- **Amostra insuficiente resulta em `inconclusivo`**, nunca em `piora`.
- **Falha de convergência e classe única são estados explícitos**, nunca
  métricas silenciosamente inválidas.

## Não-objetivos

- Não varre hiperparâmetros, atributos, barreiras nem arquiteturas.
- Não implementa retreino periódico nem detecção de degradação (ver D6).
- Não persiste modelo treinado para uso em produção.
- Não altera o dimensionamento, o stop ou o alvo que o bot calcula.
