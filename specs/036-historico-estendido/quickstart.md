# Quickstart — validar a spec 036

## Pré-requisitos

- Ambiente configurado, acesso de rede à Binance.

## 1. Confirmar zero regressão nos testes existentes

```bash
pytest tests/test_modelo.py tests/test_onchain_hipotese.py tests/test_horizonte.py -v
```

A maioria já passa `df`/candles sintéticos diretamente (não depende do
valor de `2000`/`6000`) — MUST continuar passando sem alteração.

## 2. Reavaliar H17

```bash
python main.py onchain
```

Espera-se `n_treino`/`n_teste` maiores que os publicados (1.342/586) e a
linha de base de regras com mais que 10 operações — o bloqueio específico
de hoje (7 operações).

## 3. Reavaliar H14

```bash
python main.py modelo
```

Comparar `n_treino`/`n_teste` por par contra os já publicados.

## 4. Reavaliar H11 (4h/1d)

```bash
python main.py horizonte 4h 1d
```

Comparar candles obtidos/cobertura por par contra o já publicado.

## 5. Rodar a suite completa

```bash
pytest -q
```

Nenhuma regressão fora dos três arquivos tocados.

## O que este quickstart não valida

Não reavalia H10 (fora do escopo, `spec.md` FR-007) nem H11 em 1w
(limitação de listing date, não de `limit` pedido).
