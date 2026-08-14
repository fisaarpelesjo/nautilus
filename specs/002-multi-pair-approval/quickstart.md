# Quickstart: Validando a Decisão de Aprovação Multi-Par

Fase 1 do `/speckit-plan`. Roteiro para validar manualmente cada User Story — todo comando aqui usa
só dados públicos da Binance (mesma confirmação já feita na spec 001), sem exigir `.env`/API key.

Pré-requisitos: ambiente Python configurado (`.venv`), dependências instaladas.

## US1 — Veredito multi-par em `multibacktest`/`scan`

1. Rodar `pytest tests/test_backtesting_approval.py tests/test_multi_backtest.py
   tests/test_scanner.py -v` e confirmar que os testes de veredito/ranking/erro passam.
2. Rodar `python main.py multibacktest` e confirmar que cada linha da tabela mostra um veredito
   (aprovado/reprovado/inconclusivo) e que a ordem dentro de cada timeframe reflete `edge_score`
   decrescente, não a ordem de `PAIRS` em `backtesting/multi.py`.
3. Rodar `python main.py scan` e confirmar o mesmo veredito/ranking, e que o ranking não é mais
   idêntico ao `.score` antigo (retorno × win rate) — comparar contra o comportamento anterior a esta
   spec se houver dúvida.
4. Forçar um erro num par (ex: symbol inválido temporário na lista de teste) e confirmar que ele
   aparece como linha de erro na tabela, não desaparece silenciosamente.

## US2 — Motivos e diagnóstico em `edge`

1. Rodar `pytest tests/test_backtesting_approval.py -v` (mesmo arquivo da US1 — os testes de
   `diagnose_profile`/motivos ficam junto) e confirmar que passam.
2. Rodar `python main.py edge` sobre `PAIRS[0]` e confirmar que a saída agora é diferente de
   `python main.py backtest` (hoje são idênticas) — deve aparecer a seção de veredito com motivos.
3. Encontrar (ou construir com dados sintéticos em teste) um cenário de baixo drawdown + expectativa
   positiva + retorno abaixo do buy-and-hold, e confirmar que o diagnóstico "perfil defensivo"
   aparece nesse caso específico, não em qualquer reprovação.

## US3 — Faixas legíveis do `edge_score`

1. Rodar `pytest tests/test_backtesting_approval.py -v` (função `edge_score_band` testada no mesmo
   arquivo) e confirmar que os limiares documentados em `research.md` batem com o teste.
2. Rodar `python main.py edge` sobre dois pares com resultados bem diferentes e confirmar que a
   faixa exibida (Forte/Médio/Fraco/Reprovado) muda de forma consistente com o valor numérico.

## Checklist final antes de qualquer go-live

Esta spec não altera `risk/`, `execution/` nem `trading/position_lifecycle.py` — é só relatório de
backtest. Não há checklist de go-live novo; o checklist já existente em
`specs/001-hardening-incremental/tasks.md` (T037) continua sendo o de referência para
`TRADING_MODE=live`.
