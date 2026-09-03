# Quickstart: H8 — arbitragem de funding rate, revisão com universo amplo e eficiência de capital

## Pré-requisitos

- `.venv` com dependências do projeto instaladas.
- Acesso à Binance para `fetch_funding_rate_history` (endpoint público,
  sem credencial — não precisa de `BINANCE_API_KEY`).

## Rodar

```bash
python main.py funding
```

Para cada par de `UNIVERSO_AMPLO` (34 pares) com mercado perpétuo ativo
e ≥ 90 dias de histórico: dias cobertos, nº de pagamentos, % de
pagamentos negativos, retorno bruto anualizado, retorno líquido sobre
nocional (taxas atuais) e retorno líquido sobre **capital implantado**
(metade do anterior, sem alavancagem) — comparado contra o benchmark de
5% a.a. Ordenado por retorno sobre capital implantado, descendente.

Resultado salvo em `reports/funding_<timestamp>.json`.

## Resultado esperado

Ver `research.md`, seção "Hipótese declarada antes de medir". Duas
leituras possíveis: a maioria do universo fica abaixo do benchmark
(reforça REPROVADA), ou algum subconjunto supera de forma consistente
(justificaria investigar infraestrutura de execução como próximo
passo — não decidido nesta spec).

## Verificação

```bash
pytest tests/test_funding.py tests/test_funding_carry.py -q
```

12 testes: fetch de funding (símbolo sem perpétuo, histórico normal,
paginação, cache de exchange) sem rede; cálculo de
bruto/líquido/capital-implantado sobre histórico sintético, exclusão
por cobertura mínima, comparação contra benchmark, universo pula pares
sem resultado.
