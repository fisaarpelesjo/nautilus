# CLI Contract: Comandos Afetados

Fase 1 do `/speckit-plan`. Nenhum comando novo é criado nesta feature — os três já existentes
(`multibacktest`, `scan`, `edge`) ganham uma seção nova na saída. `backtest` (sem flag) e
`backtest --validate` (spec 001) continuam idênticos (FR-011).

## `python main.py multibacktest`

- **Input**: nenhum argumento (igual hoje).
- **Efeito**: para cada par × timeframe já testado, calcula o veredito de aprovação sobre o
  resultado do backtest (janela única, sem split — critérios idênticos aos de
  `backtest --validate`, mas sem a divisão treino/validação).
- **Output (stdout)**: tabela por timeframe passa a incluir colunas de veredito (aprovado/reprovado/
  inconclusivo) e `edge_score`/faixa; dentro de cada timeframe, as linhas passam a vir ordenadas por
  qualidade (`edge_score` desc, desempate por profit factor e depois por nº de trades) em vez da
  ordem de `PAIRS`. Um par que falhar (erro de rede, símbolo inválido) aparece como uma linha de erro
  em vez de sumir silenciosamente da tabela.
- **Efeito colateral observável**: nenhum — comando de leitura, não persiste nem envia alerta.

## `python main.py scan`

- **Input**: nenhum argumento (igual hoje).
- **Efeito**: mesmo tratamento de `multibacktest` — veredito + `edge_score` por par.
- **Output (stdout)**: o ranking que hoje usa `ScanResult.score` (retorno × win rate, sem profit
  factor) passa a usar o `edge_score` compartilhado; a separação atual "melhores oportunidades" vs
  "evitar" passa a refletir também o veredito (ex: um par com veredito `aprovado` não deveria cair em
  "evitar" mesmo com retorno bruto baixo, se profit factor/drawdown forem bons — critério final
  definido na implementação, documentado em `tasks.md`). Par com erro aparece marcado, não some.
- **Efeito colateral observável**: nenhum.

## `python main.py edge`

- **Input**: nenhum argumento (igual hoje — usa `SYMBOL`/`TIMEFRAME` do `.env`, mesmo padrão de
  `backtest`).
- **Efeito**: hoje `cmd_edge` é um alias literal de `cmd_backtest` (mesma chamada a `run_backtest`).
  Passa a chamar uma função própria que roda o backtest de janela única e calcula o veredito de
  aprovação sobre o resultado — sem split treino/validação (isso é `backtest --validate`, spec 001).
- **Output (stdout)**: relatório de backtest já existente (inalterado), seguido de uma seção nova:
  `VEREDITO: APROVADO|REPROVADO|INCONCLUSIVO`, lista de motivos quando reprovado/inconclusivo, e o
  diagnóstico "perfil defensivo" quando aplicável (ver `data-model.md`). `edge_score` exibido junto
  com sua faixa legível (Forte/Médio/Fraco/Reprovado).
- **Efeito colateral observável**: nenhum — comando de leitura.

## `python main.py backtest` e `python main.py backtest --validate`

- Sem mudança de comportamento nesta spec (FR-011). `evaluate_approval()` generalizada é usada
  internamente por `backtest --validate` (via o alias de compatibilidade em `validation.py`), mas a
  saída observável do comando não muda.
