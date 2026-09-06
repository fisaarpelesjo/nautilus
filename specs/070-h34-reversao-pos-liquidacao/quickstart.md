# Quickstart: H34 — Reversão pós-liquidação (padrão de vela: pavio + pico de volume)

## Pré-requisitos

- `.venv` com dependências do projeto instaladas.
- Acesso à Binance para `fetch_ohlcv` (mesmo requisito de `python main.py horizonte`).

## Rodar

```bash
python main.py liquidacao
```

Sobre `UNIVERSO_H11` (12 pares, 4h, ~2000 candles cada): para cada par,
roda a bateria completa E1-E6 (`backtesting/bateria_hipotese.py`) sobre o
sinal de entrada "pavio ≥ 50% do range + volume ≥ 3x a média + fechamento
de recuperação". Imprime, por par, o status de cada etapa (sanidade, janela
única, busca/confirmação fora da amostra, walk-forward, desconto de
exposição, sensibilidade a custo).

## Resultado esperado

Ver `research.md`, seção "Hipótese declarada antes de medir". Duas leituras
possíveis: o excesso sobrevive às seis etapas em pelo menos alguns pares de
forma consistente (aponta para o mecanismo de liquidação como real, mesmo
via proxy), ou reprova em alguma etapa de forma sistemática — em particular,
se o padrão de reprovação for indistinguível do já visto em H3 (mesma
família de reversão à média), o registro deve dizer isso explicitamente
(FR-005), não reportar como achado novo isolado.

## Verificação

```bash
pytest tests/test_reversao_pos_liquidacao.py -q
```

Cobre: detecção do padrão (bate os três critérios / erra cada um
isoladamente / candle em warmup sem média de volume completa), `gerar_resultado`
aplica custo zero corretamente (E6), `teste_sanidade` devolve zero trades
sobre série sintética sem pavio nem pico de volume (E1), `avaliar_par`/
`avaliar_universo` funcionam com `fetch_ohlcv` mockado (sem rede).
