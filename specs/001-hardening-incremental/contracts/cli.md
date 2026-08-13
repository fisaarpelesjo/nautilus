# CLI Contract: Novos Comandos

Fase 1 do `/speckit-plan`. O bot expõe sua única interface externa via CLI (`python main.py
<comando>`); não há API HTTP nem outra integração externa nesta feature, então este é o único
"contrato" a documentar.

## `python main.py kill`

- **Input**: nenhum argumento.
- **Efeito**: seta `killswitch_active=true` em `state.json`. Idempotente — rodar de novo com o kill
  switch já ativo não é erro, apenas confirma o estado.
- **Output (stdout)**: confirmação humana de que o kill switch foi ativado, incluindo timestamp.
- **Efeito colateral observável**: próximo ciclo do bot (`python main.py bot`, se estiver rodando)
  para de abrir novas posições; posições já abertas continuam sendo geridas normalmente. Evento
  `killswitch_toggled` gravado em `logs/events-YYYY-MM-DD.jsonl` e alerta enviado ao Telegram (se
  configurado).

## `python main.py resume`

- **Input**: nenhum argumento.
- **Efeito**: seta `killswitch_active=false` em `state.json`. Idempotente — rodar de novo com o kill
  switch já inativo não é erro.
- **Output (stdout)**: confirmação humana de que novas entradas foram retomadas.
- **Efeito colateral observável**: mesmo pipeline de evento/alerta do comando `kill`.

## Reconciliação (não é um comando novo — estende `python main.py bot` e `python main.py status`)

- Na inicialização de `python main.py bot` (`TRADING_MODE=live`), o bot roda uma reconciliação antes
  de entrar no loop principal. Se houver divergência, o bot MUST logar/alertar mas MUST NOT recusar
  iniciar — a decisão de agir sobre a divergência é do operador.
- `python main.py status` (comando já existente) passa a incluir, quando `TRADING_MODE=live`, o
  resultado da última reconciliação (status `ok`/`mismatch` e timestamp) na saída exibida.
