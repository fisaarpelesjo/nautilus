# Quickstart — validar a spec 034 (H17)

## Pré-requisitos

- Ambiente configurado (`pip install -r requirements.txt`).
- Acesso de rede à Binance (candles) e `api.blockchain.info` (spec 033).

## 1. Confirmar que H14 não mudou (regressão, sem rede)

```bash
pytest tests/test_modelo.py -v
```

Todos os testes existentes de `avaliar_par`/`run_modelo_scan` MUST
continuar passando sem alteração — é a garantia de D4 (research.md).

## 2. Rodar a suite nova (sem rede, mockada)

```bash
pytest tests/test_onchain_hipotese.py -v
```

Cobre: `onchain_addr_growth_7d` calculado corretamente sobre uma série
sintética; `_merge_causal` nunca usa o dia corrente do candle; `avaliar_par`
com os parâmetros novos aceita um conjunto de 6 atributos.

## 3. Rodar a comparação real (BTC/USDT)

```bash
python main.py onchain
```

Espera-se, em segundos (não minutos — um par, não doze):

- O atributo declarado (`onchain_addr_growth_7d`) e sua correlação contra
  os 5 existentes (research.md: máxima 0,304).
- `n_treino`/`n_teste` de ambas as avaliações (research.md: 1.342/586).
- Razão de chances no subconjunto decidido, lado a lado (com e sem
  on-chain).
- Estado de cada avaliação, nos mesmos termos já usados por H14
  (`sem_sinal`, `insuficiente`, `melhora`, etc.).

## 4. Rodar a suite completa

```bash
pytest -q
```

Nenhuma regressão fora dos arquivos tocados.

## O que este quickstart não valida

Não valida se H17 deveria mudar a operação do bot — o bot só opera a
estratégia de regras (`strategy/ema_rsi.py`), nunca o modelo supervisionado
de H14/H17, aprovado ou não. O quickstart valida a medição, não uma decisão
de deploy que esta linha de pesquisa nunca propôs.
