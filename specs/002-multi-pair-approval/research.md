# Research: Decisão de Aprovação Multi-Par

Fase 0 do `/speckit-plan`. Nenhum item do Technical Context ficou como `NEEDS CLARIFICATION` — a
stack e a base de código já existem desde a spec 001. As decisões abaixo cobrem escolhas de design
específicas desta feature.

## Local do veredito compartilhado (US1/US2)

- **Decision**: extrair `ValidationVerdict`/`evaluate_validation()` (hoje em
  `backtesting/validation.py`, spec 001 US3) para um novo módulo `backtesting/approval.py`, renomeado
  para `ApprovalVerdict`/`evaluate_approval()`. `validation.py` importa e reexporta os nomes antigos
  (`ValidationVerdict = ApprovalVerdict`, `evaluate_validation = evaluate_approval`) para não quebrar
  nada que já usa esses nomes.
- **Rationale**: `evaluate_validation()` já opera sobre um `BacktestResult` genérico — não tem nenhuma
  dependência do split treino/validação, só dos campos `total_trades`, `total_return_pct`,
  `buy_hold_return_pct`, `profit_factor`, `max_drawdown_pct` que qualquer backtest (com ou sem split)
  já produz. Chamá-la de "evaluate_validation" a partir de `multi.py`/`scanner.py`/`engine.py` (que
  não fazem split nenhum) seria um nome enganoso. Mesmo padrão de extração já usado na spec 001
  quando uma lógica ganha ≥3 pontos de chamada fora do módulo original (ex: `data/atomic_io.py`,
  `utils/logger.safe_step`).
- **Alternatives considered**: manter tudo em `validation.py` e importar de lá mesmo com o nome
  "impróprio" — rejeitado por confundir o leitor (por que `multibacktest`, que nunca faz split,
  chama algo com "validation" no nome?); duplicar a função em cada módulo consumidor — rejeitado por
  violar DRY sem ganho nenhum, os três usos são idênticos.

## Ranking de pares por qualidade (US1)

- **Decision**: reusar o `edge_score` já existente em `backtesting/engine.py` (`_edge_score`, hoje
  privado) como critério de ordenação em `multibacktest` e `scan`, tornando-o público (`edge_score`,
  mesmo padrão de `print_report` na spec 001). `scanner.py` troca seu `.score` ad hoc
  (`retorno_pct * win_rate/100`, sem profit factor nem penalidade de amostra) pelo `edge_score`
  compartilhado.
- **Rationale**: `edge_score` já combina exatamente os critérios que o `ROADMAP.md`/spec pedem para o
  ranking — retorno vs buy-and-hold, profit factor, expectativa, penalidade por sequência de perdas e
  por amostra pequena (`sample_penalty`) — não há motivo para inventar uma segunda fórmula de
  qualidade concorrente. Consolida os dois scores ad hoc que hoje existem (`ScanResult.score` e
  nenhum em `MultiResult`) numa fonte única.
- **Alternatives considered**: nova fórmula de ranking dedicada — rejeitada por duplicar o que
  `edge_score` já faz e criar duas noções de "qualidade" divergentes no mesmo relatório (o veredito
  usaria uma fórmula, o ranking usaria outra); ranking só por `total_return_pct` — rejeitado por
  ignorar profit factor/consistência, exatamente o problema que motivou este item no `ROADMAP.md`.
- **Critério de desempate**: quando dois pares empatam em `edge_score` (comparação de float com
  tolerância — ver Assumptions), desempate por `profit_factor` e, se ainda empatado, por
  `total_trades` (mais trades = amostra mais confiável).

## Faixas legíveis do `edge_score` (US3)

- **Decision**: função pura `edge_score_band(score: float) -> str` em `backtesting/engine.py`, com
  limiares fixos documentados no docstring: `score >= 20` → `"Forte"`; `0 <= score < 20` →
  `"Médio"`; `-20 <= score < 0` → `"Fraco"`; `score < -20` → `"Reprovado"`.
- **Rationale**: os limiares vêm da composição já existente do `edge_score`
  (`(pf - 1.0) * 10 + expectancy_pct * 5 - max_losing_streak - sample_penalty`, mais a diferença de
  retorno bruta) — um profit factor de 1.5 já contribui +5, então uma faixa de 20 pontos representa
  uma combinação real de vários fatores positivos, não um único indicador isolado. Limiares
  simétricos em torno de zero (Fraco/Reprovado espelhando Médio/Forte) mantêm a leitura intuitiva.
  Ajuste fino fica documentado como candidato a revisão após uso real (mesmo espírito de
  `MAX_CONSECUTIVE_LOSSES=3` na spec 001, marcado como "sugestão de default a validar em uso").
- **Alternatives considered**: normalizar para 0-100 — rejeitado por exigir um teto arbitrário
  (`edge_score` não tem limite superior natural) e por já existir um consumidor do valor bruto
  (edge_score é logado hoje); usar percentis calculados sobre o histórico de execuções — rejeitado
  por adicionar estado (precisaria persistir distribuição histórica) para um problema que limiares
  fixos já resolvem.

## `EDGE_MIN_TRADES` configurável (US1/US2)

- **Decision**: nova variável em `config/settings.py`, `EDGE_MIN_TRADES` (default `10`, mesmo valor
  já hardcoded em `MIN_TRADES_FOR_APPROVAL` de `backtesting/validation.py` na spec 001), lida por
  `evaluate_approval()` como default do parâmetro `min_trades` em vez da constante do módulo.
- **Rationale**: consistente com como `MAX_CONSECUTIVE_LOSSES` foi exposto na spec 001 (US2) —
  qualquer limiar que afeta uma decisão operacional (mesmo que aqui seja só de relatório, não de
  risco) vira variável de ambiente, não fica preso no código. Reaproveita o valor 10 já em uso, sem
  mudar o comportamento default.
- **Alternatives considered**: manter como constante de módulo (como está hoje) — rejeitado porque
  FR-006 pede explicitamente que seja configurável; parâmetro de linha de comando (`--min-trades`) —
  rejeitado por não haver hoje nenhum outro tunable de estratégia exposto via CLI flag (todos vivem
  em `.env`), inconsistente com o resto do projeto.

## Diagnóstico defensivo vs agressivo (US2)

- **Decision**: função `diagnose_profile(result: BacktestResult) -> Optional[str]` em
  `backtesting/approval.py`, chamada só quando o veredito é "reprovado". Retorna
  `"perfil defensivo: preservou capital, mas capturou pouco da alta"` quando
  `max_drawdown_pct <= MAX_ACCEPTABLE_DRAWDOWN_PCT` (mesmo limiar de 10% já usado no veredito),
  `expectancy > 0` e `total_return_pct < buy_hold_return_pct` (a estratégia não bateu buy-and-hold,
  senão nem seria "reprovado"). Retorna `None` (sem diagnóstico) nos demais casos de reprovação.
- **Rationale**: exemplo do próprio `ROADMAP.md` Fase 1.1 item 4. Reusa os mesmos limiares já
  definidos em `evaluate_approval()` em vez de inventar novos, evitando dois conjuntos de números
  "baixo drawdown" divergentes no mesmo relatório.
- **Alternatives considered**: classificação mais granular (defensivo/agressivo/neutro/instável) —
  rejeitada por escopo maior que o pedido no `ROADMAP.md` (só "defensivo vs agressivo" foi citado) e
  por exigir mais evidência empírica de quais faixas fazem sentido antes de formalizar; deixar como
  texto livre gerado a partir dos números — rejeitado por não ser testável de forma determinística.

## Pares com erro não somem do relatório (Edge Case)

- **Decision**: `multi.py`/`scanner.py` já capturam exceção por par (`except Exception as e:
  log.error(...)`) mas hoje simplesmente pulam o par — ele desaparece da tabela sem nenhuma indicação
  visível ao operador. Passa a adicionar uma linha "erro" (pair + mensagem curta) na tabela em vez de
  omitir, mantendo o loop resiliente (uma falha não derruba os outros pares).
- **Rationale**: era um requisito explícito do Edge Case da spec ("uma falha isolada não pode
  interromper o comando inteiro" já valia, mas "não pode desaparecer silenciosamente" é novo). Baixo
  custo — já existe o `except` e o log, só falta propagar para a saída visível.
- **Alternatives considered**: nenhuma — é a correção mínima e direta do gap identificado.
