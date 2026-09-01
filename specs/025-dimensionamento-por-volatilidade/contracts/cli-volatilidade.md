# Contrato de CLI — `python main.py volatilidade`

## Invocação

```
python main.py volatilidade [ALVO]
```

Alias: `voltarget`.

## Argumentos

| Posição | Obrigatório | Padrão | Descrição |
|---|---|---|---|
| `ALVO` | não | `0.02` | Volatilidade-alvo do dimensionamento |

O argumento existe para reprodutibilidade e inspeção manual, **não** para
varredura. O relatório declara o alvo usado, e a avaliação registrada no
registro de hipóteses usa o padrão. Executar com alvos diferentes até um passar
é o problema de testes múltiplos que a metodologia existe para conter — a spec
registra isso em Assumptions.

## Universo e estratégias

Não parametrizáveis por CLI, pelo mesmo motivo do comando `horizonte`: os mesmos
12 pares e as mesmas 4 estratégias das avaliações anteriores, para que o
resultado seja comparável.

## Saída em terminal

1. **Parâmetros** — alvo, fator médio aplicado, exposição média das duas versões.
2. **Contagem antes da tabela** — comparações avaliadas, com melhora, sem
   vantagem, piora, inconclusivas.
3. **Tabela pareada** — por combinação: drawdown base e dimensionado com delta,
   retorno base e dimensionado com delta, delta de exposição, delta de ganho de
   timing, operações de cada versão, status.
4. **Legenda** — `sem vantagem` significa que o ganho desapareceu ao descontar
   exposição; `inconclusivo` significa amostra insuficiente, não ausência de
   vantagem.

## Saída em arquivo

`reports/volatilidade_{timestamp}.{json,csv,md}`.

## Códigos de saída

| Código | Significado |
|---|---|
| 0 | Execução concluída, com ou sem melhora encontrada |
| 1 | Falha de configuração (alvo inválido, universo vazio) |

Ausência de melhora **não** é erro. É resultado.

## Garantias

- **Não altera o caminho de produção.** `risk/manager.py` não é tocado; o
  dimensionamento vive atrás de parâmetro opcional cujo default reproduz o
  comportamento atual.
- **Nunca amplia posição.** O fator é limitado a 1,0 na fórmula.
- **Não altera critério de aprovação.** Limiares vigentes.
- **Falha isolada não aborta a varredura.**
- **Amostra insuficiente resulta em `inconclusivo`**, nunca em `piora`.

## Não-objetivos

- Não varre alvos nem janelas.
- Não implementa estratégia nova.
- Não sugere mudança de configuração operacional.
