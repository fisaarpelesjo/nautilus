# Quickstart: H24 — diferencial de funding rate entre corretoras (perp × perp)

## Pré-requisitos

- `.venv` com dependências do projeto instaladas.
- Acesso às cinco corretoras qualificadas (Binance, Bybit, OKX, KuCoin,
  Gate) para `fetch_funding_rate_history` (endpoints públicos, sem
  credencial).

## Rodar

```bash
python main.py funding_cross
```

Para BTC/USDT e ETH/USDT, sobre as 10 combinações de pares entre as 5
corretoras qualificadas: dias cobertos, diferencial bruto anualizado,
líquido sobre nocional (custo das duas corretoras), líquido sobre
**capital implantado** (igual a H8, não menor — D3) e a direção (qual
corretora vender/comprar) — comparado contra o benchmark de 5% a.a.

Resultado salvo em `reports/funding_cross_<timestamp>.json`.

## Achados de instrumentação (não presumidos, medidos)

- **Bybit e KuCoin têm histórico de funding rate mais curto que o piso
  de 90 dias** nas APIs públicas via `ccxt` (Bybit: ~67 dias reais,
  KuCoin: ~33 dias — testado diretamente, `since` mais antigo não
  produz mais dados). Combinações envolvendo essas duas corretoras
  ficam sistematicamente excluídas pelo piso de qualidade de dado
  (`MIN_DIAS_COBERTURA`) — não um defeito, um limite real da fonte.
- **Gate trunca cada chamada bem abaixo do `limit` pedido, sem erro**
  — a heurística "lote menor que o limite pedido = fim do histórico"
  (usada em `data/funding.py` para Binance) está **errada** para Gate.
  `data/funding_cross.py::fetch_funding_rate_history` não usa essa
  heurística — só para em lote vazio ou ausência de progresso.

## Resultado esperado

Dado os dois achados acima, o universo prático fica reduzido a
combinações entre Binance, OKX e Gate (as três com profundidade real
suficiente) — 3 pares de corretoras × 2 ativos = até 6 resultados,
não os 20 teóricos.

## Verificação

```bash
pytest tests/test_funding_cross.py tests/test_funding_cross_carry.py -q
```

14 testes: fetch por corretora (símbolo sem perpétuo, histórico
normal, paginação) sem rede; alinhamento com jitter de segundos;
cálculo de diferencial bruto/líquido/capital-implantado; direção
conforme o sinal; `avaliar_universo` cobre todas as combinações e pula
as sem resultado.
