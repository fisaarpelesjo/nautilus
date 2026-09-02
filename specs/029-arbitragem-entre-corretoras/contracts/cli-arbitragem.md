# Contrato de CLI — `python main.py arbitragem`

## Invocação

```
python main.py arbitragem [PAR]
```

`PAR` é opcional, default `BTC/USDT`. Sem alias — comando novo, sem
precedente a manter compatível.

## Argumentos

Um único par, mesmo padrão de `volatilidade [ALVO]` e `barras [TIPO]`. As seis
corretoras (D1), o volume por perna (D2, US$ 10.000) e o teto de latência
(D4, 2.000 ms) **não são parametrizáveis** — são declarados em
`backtesting/arbitragem.py`, mesmo motivo de `modelo` não expor eixo nenhum:
são decisões de pesquisa (research.md), não configuração de produto, e expor
como flag convidaria a variá-las até achar uma combinação favorável.

## O que a execução faz

1. Consulta o livro de ofertas de `PAR` nas seis corretoras (público, sem
   chave — FR-013), falha isolada por corretora (FR-011).
2. Monta uma `Comparacao` para cada par de corretoras que respondeu (até 15,
   C(6,2)) — nunca envia ordem (FR-012).
3. Persiste todas as `Comparacao` do ciclo em `data/arbitragem.jsonl`,
   acrescentando à amostra já acumulada (D5, FR-008).
4. Agrega **todo** o histórico persistido — não só o ciclo atual — em
   `RelatorioH15` (FR-009).

## Saída em terminal

1. **Tabela do ciclo atual** — uma linha por combinação de corretoras:
   diferencial bruto, custo, diferencial líquido, volume preenchido,
   intervalo em ms, estado.
2. **Corretoras indisponíveis neste ciclo**, se houver (FR-011) — nunca
   omitido silenciosamente.
3. **Agregado histórico** — período coberto (primeira/última observação),
   N total, N por combinação, e `estado_agregado`
   (`inconclusivo`/`amostra_suficiente` — ver `data-model.md`). Quando
   `inconclusivo`, declara quanto falta para `MIN_OBSERVACOES_AGREGACAO`.
4. **Executabilidade (D6)** — declaração estática: inexecutável hoje, com os
   três motivos (capital pré-posicionado, chaves múltiplas, execução
   simultânea). Aparece em toda execução, independente do resultado medido.
5. **Nenhum veredito de aprovação/reprovação.** Este comando nunca imprime
   "aprovada"/"reprovada" para H15 — só quando uma fase futura, com amostra
   suficiente, definir o critério (ver `plan.md`, Fase 4).

## Saída em arquivo

- `data/arbitragem.jsonl` — acrescido, nunca sobrescrito (D5).
- `reports/arbitragem_{timestamp}.{json,csv,md}` via `export_report`, mesmo
  padrão de `scan`/`multibacktest`/`optimize`/`barras`/`modelo` — snapshot do
  ciclo atual mais o agregado histórico no momento da execução.

## Códigos de saída

| Código | Significado |
|---|---|
| 0 | Execução concluída — inclui o caso de todas as corretoras indisponíveis, que produz `comparacoes_ciclo` vazio mas não é erro de configuração |
| 1 | Falha de configuração (par inválido em todas as corretoras) |

## Garantias

- **Não altera o caminho de produção.** `trading/runner.py`,
  `execution/order_manager.py`, `risk/manager.py` intocados — FR-014.
- **Não exige chave de API** em nenhuma das seis corretoras — FR-013.
- **Nenhuma ordem é enviada**, em nenhuma corretora — FR-012.
- **Comparação nunca mistura moeda de cotação.** Só entra na tabela quando as
  duas pontas cotam na mesma moeda — FR-003.
- **Custo desconhecido nunca vira zero.** Estado `custo_desconhecido`
  explícito — FR-006.
- **Falha de uma corretora não aborta o ciclo.** As demais são medidas e
  reportadas — FR-011.
- **Amostra insuficiente nunca vira reprovação.** Estado `inconclusivo` com o
  N declarado — FR-010.

## Não-objetivos

- Não envia ordem, não abre posição, não gerencia capital.
- Não decide se H15 é aprovada ou reprovada — essa decisão espera amostra
  (Assumptions da spec).
- Não implementa transferência de capital entre corretoras, gestão de chaves
  múltiplas ou execução simultânea de duas pernas — D6 já declara os três
  como pré-requisitos não atendidos, independente do resultado medido.
- Não agenda execuções periódicas — cada execução é manual; agendamento é
  decisão de operação, fora do escopo desta spec.
