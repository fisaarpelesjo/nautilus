# Quickstart: H36 — Hash Ribbons: capitulação de mineradores (BTC-only)

## Pré-requisitos

- `.venv` com dependências do projeto instaladas.
- Acesso à Binance para `fetch_ohlcv` e a `api.blockchain.info` para o
  hashrate (mesmo requisito de `python main.py onchain`).

## Rodar

```bash
python main.py hashribbons
```

Sobre `BTC/USDT` (candles cobrindo a janela real do hashrate disponível,
~2023-09 em diante): calcula médias móveis de 30/60 dias do hashrate,
detecta cruzamentos de alta/baixa, alinha ao candle por forward-fill
causal (D-1), e roda a bateria completa E1-E6
(`backtesting/bateria_hipotese.py`) usando o cruzamento como sinal de
entrada/saída (sem SL/TP artificial — o ATR do motor permanece ativo).
Imprime o status de cada etapa.

## Resultado esperado

Ver `research.md`, seção "Hipótese declarada antes de medir". Leituras
possíveis: o sinal sobrevive às seis etapas (achado positivo real, dado
mecanismo de oferta nunca testado antes), reprova com amostra suficiente
para a leitura ter peso, ou fica inconclusivo por amostra pequena
(esperado dado D5 — no máximo ~16 eventos possíveis na série completa).

## Verificação

```bash
pytest tests/test_hash_ribbons.py -q
```

Cobre: detecção de cruzamento de alta/baixa sobre série sintética com
posições conhecidas, alinhamento causal D-1, `teste_sanidade` devolve
zero trades sobre série de hashrate monotônica (sem cruzamento),
descarte de candles anteriores ao início real do hashrate, `gerar_resultado`
aplica custo zero corretamente.
