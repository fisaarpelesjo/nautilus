# Contrato de CLI — `python main.py barras`

## Invocação

```
python main.py barras [TIPO]
```

Alias: `bars`.

## Argumentos

| Posição | Obrigatório | Padrão | Descrição |
|---|---|---|---|
| `TIPO` | não | ambos | `dollar`, `cusum`, ou omitido para avaliar as duas variantes |

O argumento existe para inspeção manual e reprodutibilidade. O limiar **não** é
parametrizável: é calibrado por D2 sobre a contagem de barras, nunca escolhido
por desempenho. Expor o limiar como flag convidaria a varrê-lo até um passar,
que é o problema de testes múltiplos que a metodologia existe para conter.

## Universo, estratégias e base

Não parametrizáveis por CLI, pelo mesmo motivo de `horizonte` e `volatilidade`:
os mesmos 12 pares e as mesmas 4 estratégias das avaliações anteriores, para que
o resultado seja comparável. Base fixa em `1h × 8.000` candles (D1).

## Saída em terminal

1. **Parâmetros** — base, candles, janela de calendário, alvo de barras,
   tolerância de calibração; e a declaração de que produção não é tocada.
2. **Contagem por estado antes da tabela** — avaliadas, melhora, só na busca,
   confundidas, sem vantagem, piora, inconclusivas, inertes, erro.
3. **Tabela pareada** — por combinação: observações de cada versão e sua razão,
   drawdown de cada versão com delta, retorno de cada versão com delta, delta de
   exposição, delta de timing, operações de cada versão, delta de custo, estado.
4. **Diagnóstico da reamostragem** — candles por barra (mediana e p90) e
   percentual de barras de um candle só, por variante. É o número que distingue
   "não houve vantagem" de "a reamostragem não atuou".
5. **Legenda** — significado de `inerte`, `confundido`, `só na busca`,
   `inconclusivo`, e o que `dTiming` desconta.
6. **Executabilidade** — declaração de D6, incluindo a ressalva de que o limiar
   exigiria recalibração periódica em operação real.

## Saída em arquivo

`reports/barras_{timestamp}.{json,csv,md}`.

## Códigos de saída

| Código | Significado |
|---|---|
| 0 | Execução concluída, com ou sem melhora encontrada |
| 1 | Falha de configuração (tipo inválido, universo vazio) |

Ausência de melhora **não** é erro. É resultado.

## Garantias

- **Não altera o caminho de produção.** `TIMEFRAME`, ciclo de decisão,
  `risk/manager.py` e `execution/` permanecem intactos.
- **Construção causal.** Nenhuma barra usa informação posterior ao seu
  fechamento; barras incompletas não aparecem na saída.
- **Janela de calendário comum.** As duas versões cobrem o mesmo intervalo, e o
  intervalo é exibido.
- **Contagem de observações pareada** dentro da tolerância declarada, e exibida
  em toda combinação.
- **Não altera critério de aprovação.** `evaluate_approval` e os limiares
  vigentes permanecem.
- **Falha isolada não aborta a varredura.**
- **Amostra insuficiente resulta em `inconclusivo`**, nunca em `piora`.
- **Reamostragem que não agrupa resulta em `inerte`**, nunca em `piora`.

## Não-objetivos

- Não varre limiares nem granularidades.
- Não implementa estratégia nova.
- Não altera o timeframe operacional do bot.
- Não implementa recalibração periódica de limiar (ver D6).
