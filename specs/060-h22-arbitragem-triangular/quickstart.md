# Quickstart: H22 — arbitragem triangular intra-corretora

## Pré-requisitos

- `.venv` com dependências do projeto instaladas.
- Acesso à Binance para `fetch_order_book` (endpoint público, sem
  credencial).

## Rodar um ciclo

```bash
python main.py triangular [INTERMEDIARIA] [BASE] [COTACAO]
```

Padrão (sem argumentos): `BTC/USDT` × `ETH/BTC` × `ETH/USDT`. Mede as
duas direções do ciclo (direto e inverso), imprime diferencial bruto,
custo de 3 pernas (0,30%), diferencial líquido, volume final,
intervalo de latência e estado. Persiste em
`data/arbitragem_triangular.jsonl` e `reports/triangular_<timestamp>.json`.

## Rodar uma campanha (evidência real, não um ciclo isolado)

```bash
for i in $(seq 1 40); do
  python main.py triangular
  sleep 30
done
```

Mesma disciplina de H15 — o veredito exige amostra acumulada (≥ 30
observações por direção), nunca um único ciclo.

## Resultado esperado

Ver `research.md`, seção "Hipótese declarada antes de medir". A leitura
mais provável é diferencial líquido negativo ou muito próximo de zero
na maioria das observações — mas a ausência de obstáculo de latência
entre corretoras (diferente de H15) é uma diferença estrutural real,
não uma garantia de resultado.

## Verificação

```bash
pytest tests/test_arbitragem_triangular.py -q
```

13 testes: `_comprar`/`_vender` puros, ciclo balanceado (sem
oportunidade após custo), ciclo desbalanceado (detecta oportunidade),
perna indisponível aborta sem medição parcial, profundidade
insuficiente, persistência, agregação por (triângulo, direção).
