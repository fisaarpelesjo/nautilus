# Quickstart — validar a spec 033

## Pré-requisitos

- Ambiente do projeto já configurado (`pip install -r requirements.txt`).
- Acesso de rede a `api.blockchain.info` — nenhuma chave necessária.

## 1. Rodar a suite (sem rede, mockada)

```bash
pytest tests/test_onchain.py -v
```

Cobre: série válida parseada corretamente, nome inválido levanta exceção,
falha de rede levanta exceção, `status` não-ok levanta exceção, série vazia
por ausência de dado é retornada sem erro.

## 2. Confirmar contra a API real

```bash
python - <<'EOF'
from data.onchain import fetch_onchain_series
serie = fetch_onchain_series("n-unique-addresses", timespan="1years")
print(len(serie), serie.index.min(), serie.index.max())
print(serie.tail())
EOF
```

Espera-se uma série de ~365 pontos, crescente, sem exceção.

## 3. Confirmar erro explícito com métrica inválida

```bash
python -c "from data.onchain import fetch_onchain_series; fetch_onchain_series('nome-que-nao-existe')"
```

Espera-se exceção (`RuntimeError` ou equivalente), nunca uma série vazia
silenciosa.

## 4. Rodar a suite completa

```bash
pytest -q
```

Nenhuma regressão — módulo novo, sem alteração em `data/fetcher.py` nem
`data/sources/`.

## O que este quickstart não valida

Não valida H17 (a hipótese) — só a capacidade de busca. Nenhum critério de
predição, correlação ou aprovação é avaliado aqui.
