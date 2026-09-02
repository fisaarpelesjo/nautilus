# Quickstart — validar a spec 037 (motor de carteira, H14)

## Pré-requisitos

- Ambiente configurado (`pip install -r requirements.txt`).
- Acesso de rede à Binance (candles).

## 1. Rodar a suite (sem rede, mockada)

```bash
pytest tests/test_modelo.py tests/test_portfolio_h14.py -v
```

Cobre: `avaliar_par(retornar_previsao=True)` devolve a mesma probabilidade
já usada internamente, e não muda nada no caminho default (D2, regressão);
caixa nunca abre posição além do disponível; teto de `MAX_POSITIONS`
respeitado; desempate por maior probabilidade quando sinais excedem
slots/caixa (D4); saída exatamente por take-profit ATR + stop trailing
(D7, mesmo mecanismo do backtest publicado de H14);
posição aberta no fim do histórico fecha a mercado; `BacktestResult`
produzido passa por `evaluate_approval()` sem erro.

## 2. Rodar a avaliação real

```bash
python main.py carteira
```

Espera-se:

- Curva de capital agregada (um valor de patrimônio por candle, não 12).
- `max_drawdown_pct` agregado — a medição que faltava desde `specs/
  036-historico-estendido/` §4.15.
- Veredito (`evaluate_approval`): aprovado/reprovado/inconclusivo.
- O maior drawdown por par isolado (já registrado em H14), lado a lado
  com o agregado, para comparação direta (SC-003).

## 3. Confirmar que o resultado é resultado de carteira, não soma de resultados isolados

Sobre um trecho curto do histórico (poucos candles), verificar manualmente
que o número de posições abertas simultaneamente nunca excede
`MAX_POSITIONS`, e que o caixa disponível antes de cada abertura reflete
posições ainda abertas em OUTROS pares — não capital independente por par.

## 4. Rodar a suite completa

```bash
pytest -q
```

Nenhuma regressão — `backtesting/engine.py`, `backtesting/approval.py`
não são alterados; `backtesting/modelo.py` só ganha um parâmetro opt-in
com default testado como idêntico ao comportamento atual.

## O que este quickstart não valida

Não decide se H14 deveria virar a estratégia operada pelo bot — o bot só
opera `strategy/ema_rsi.py` (regras), nunca o classificador. O quickstart
valida a medição de risco de carteira que faltava para completar o
veredito de aprovação de H14 no registro de hipóteses.
