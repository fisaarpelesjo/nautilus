# Contrato de CLI — `python main.py horizonte`

Interface pública desta feature. O projeto é uma ferramenta de linha de comando;
o contrato exposto é o comando, não uma API.

## Invocação

```
python main.py horizonte [HORIZONTES...]
```

Aliases aceitos, seguindo o padrão PT-BR do projeto (`comparar`, `multimercado`,
`desempenho`): `horizontes`.

## Argumentos

| Posição | Obrigatório | Padrão | Descrição |
|---|---|---|---|
| `HORIZONTES...` | não | `4h 1d 1w` | Escalas temporais a avaliar |

Sem argumento, avalia os três horizontes de referência. Com argumentos, avalia
apenas os informados — útil para reexecutar só a escala diária.

## Universo e estratégias

Não parametrizáveis por CLI nesta feature, de propósito. O universo de pares e o
conjunto de estratégias vêm das mesmas fontes já usadas por `compare`, para que
o resultado seja comparável às hipóteses anteriores. Expor os dois como flag
convidaria a varrer combinações até achar uma que passe — que é o mecanismo de
testes múltiplos que a confirmação fora da amostra existe para conter.

## Saída em terminal

Uma seção por horizonte, contendo:

1. **Contexto de dado** — candles medianos obtidos, aquecimento em dias, pares
   marcados como histórico curto.
2. **Contagem em destaque, antes da tabela** — combinações avaliadas,
   confirmadas fora da amostra, inconclusivas. A contagem precede a tabela
   porque ler a tabela sem ela convida à leitura errada.
3. **Tabela por combinação** — estratégia, par, operações, retorno,
   buy-and-hold, profit factor, drawdown, ganho de timing, status.
4. **Legenda** — `so na busca` NÃO é aprovação; `inconclusivo` significa amostra
   insuficiente, não ausência de vantagem.

Ao final, um quadro comparativo entre horizontes.

## Saída em arquivo

`reports/horizonte_{timestamp}.{json,csv,md}` via `utils/report_export.py`,
seguindo o padrão de `backtest`, `scan`, `multibacktest` e `optimize`.

## Códigos de saída

| Código | Significado |
|---|---|
| 0 | Execução concluída, com ou sem combinação confirmada |
| 1 | Falha de configuração (horizonte inválido, universo vazio) |

Ausência de combinação aprovada **não** é erro. É resultado.

## Garantias

- **Não altera o horizonte de produção.** O comando lê `TIMEFRAME` apenas para
  exibir a linha de base; nunca escreve em `.env` nem em estado do bot.
- **Não interrompe por falha isolada.** Par que falha ao buscar dados vira
  entrada de erro; os demais seguem, como já faz `multimarket.run_scan`.
- **Não altera critério de aprovação.** Usa `evaluate_approval` com os limiares
  vigentes.
- **Combinação sem amostra suficiente resulta em `inconclusivo`**, nunca em
  `reprovado`.

## Não-objetivos

- Não otimiza parâmetros por horizonte.
- Não implementa estratégia nova.
- Não decide nem sugere mudança de configuração operacional.
