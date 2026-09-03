# Quickstart: H31 — viabilidade de dados alternativos (sentimento social/notícia)

## O que esta spec é

Uma checagem de viabilidade de fonte de dado, não uma hipótese medida.
Não há comando `python main.py ...` para rodar — o resultado é a
investigação documentada em `research.md`.

## Como reproduzir a checagem

**GitHub (sem autenticação, sem dependência nova):**

```bash
curl -s https://api.github.com/repos/bitcoin/bitcoin/stats/commit_activity | python -c "import json,sys; d=json.load(sys.stdin); print(len(d), 'semanas')"
curl -s https://api.github.com/rate_limit
```

Esperado: 52 semanas, rate limit 60/hora não-autenticado.

**Google Trends (`pytrends`, instalação isolada — NÃO instalar no
`.venv` do projeto):**

```bash
pip install --target=/tmp/h31_check pytrends
PYTHONPATH=/tmp/h31_check python -c "
from pytrends.request import TrendReq
p = TrendReq(hl='en-US', tz=360)
p.build_payload(['bitcoin'], timeframe='today 5-y')
print(p.interest_over_time().shape)
"
```

Esperado: uma primeira chamada bem-sucedida (262 semanas), qualquer
chamada seguinte tem alta chance de falhar com HTTP 400.

## Resultado

Viabilidade **negativa** para as duas fontes — ver `research.md` D1-D2
para os números completos e o motivo específico de cada uma.

## Se isto for reaberto no futuro

Precisaria de uma fonte gratuita nova, com granularidade diária (ou
melhor) sobre uma janela de pelo menos ~2 anos, e confiabilidade
suficiente para uma campanha real de 12 pares sem bloqueio. Nenhuma
das duas candidatas originais atende.
