# Quickstart: H37 — Mean reversion em par de stablecoin (USDC/USDT)

## Pré-requisitos

- `.venv` com dependências do projeto instaladas.
- Acesso à Binance para `fetch_ohlcv` (mesmo requisito de `python main.py liquidacao`).

## Rodar

```bash
python main.py stablecoin
```

Sobre `USDC/USDT` (2000 candles de 4h, ~11 meses): roda a bateria completa
E1-E6 (`backtesting/bateria_hipotese.py`) usando
`strategy/mean_reversion.py::MeanReversionStrategy` (H3) sem nenhuma
alteração. Imprime o status de cada etapa (sanidade, janela única,
busca/confirmação fora da amostra, walk-forward, desconto de exposição,
sensibilidade a custo).

## Resultado esperado

Ver `research.md`, seção "Hipótese declarada antes de medir". Duas
leituras possíveis: a estratégia captura reversão real mesmo no horizonte
de 4h, ou o resultado é ruído em torno de um preço estruturalmente
estável — sem sinal capturável nesse horizonte (diferente de H3 nos
outros pares, que teve sinal mensurável, só ruim).

## Verificação

```bash
pytest tests/test_mean_reversion_stablecoin.py -q
```

Cobre: `teste_sanidade` devolve zero trades sobre série de preço
constante (E1), `gerar_resultado` aplica custo zero corretamente (E6),
`avaliar()` funciona com `fetch_ohlcv` mockado (sem rede).
