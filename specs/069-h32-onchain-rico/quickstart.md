# Quickstart: H32 — on-chain mais rico (valor transacionado)

## Rodar

```bash
python main.py onchain_volume
```

Sobre BTC/USDT (6.000 candles): calcula `onchain_txn_volume_growth_7d`
(crescimento de 7 dias do valor on-chain transacionado, USD), checa
colinearidade contra os 5 atributos de H14 e contra
`onchain_addr_growth_7d` (H17). Se colinear (≥0,80 com qualquer um),
para aí e reporta isso. Se não, compara o modelo com/sem o atributo,
isolado (mesmo par/período, nunca contra o pooled de 12 pares).

Resultado salvo em `reports/onchain_volume_<timestamp>.json`.

## Verificação

```bash
pytest tests/test_onchain_volume_hipotese.py -q
```
