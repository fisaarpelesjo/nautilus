# Research: H31 — viabilidade de dados alternativos (sentimento social/notícia)

## D1 — as duas fontes candidatas, testadas com chamadas reais (2026-09-03)

### GitHub — atividade de desenvolvimento (`stats/commit_activity`)

Chamada real, sem autenticação:

```
GET https://api.github.com/repos/bitcoin/bitcoin/stats/commit_activity
status: 200
```

**Resultado:** 52 registros (semanas), do timestamp `1757203200`
(2025-09-07) ao `1788048000` (2026-08-24) — **exatamente 1 ano de
histórico, granularidade semanal**. Este é o teto do endpoint de
estatísticas agregadas do GitHub — não é um limite de paginação
contornável.

**Rate limit não-autenticado, verificado:**

```
GET https://api.github.com/rate_limit
{'limit': 60, 'remaining': 59, 'used': 1}
```

60 requisições/hora. Suficiente para 1 chamada por par de
`UNIVERSO_H11` (12), mas não para reconstruir histórico mais longo via
paginação de commits individuais (que consumiria muitas chamadas por
repositório e ainda teria a mesma granularidade grosseira de eventos
discretos, não uma série contínua).

**Contra a barra declarada (spec.md):** falha em histórico (1 ano
contra ~2,7 anos de referência) e falha em granularidade (semanal
contra candles de 4h — um forward-fill de valor semanal sobre ~42
candles de 4h é informação quase constante dentro de cada semana,
grosseiro demais para ser um atributo por candle com o mesmo espírito
dos 5 atributos de H14).

### Google Trends (`pytrends`, não-oficial)

**Instalado isolado** via `pip install --target=/tmp/h31_feasibility
pytrends` — nunca adicionado ao `.venv` compartilhado do projeto
(FR-003), removido ao final desta investigação.

**Primeira chamada, sucesso:**

```python
pytrends.build_payload(['bitcoin'], timeframe='today 5-y')
df = pytrends.interest_over_time()
# (262, 2) -- 262 semanas (~5 anos), 2021-08-29 a 2026-08-30
# frequência inferida: 7 dias (semanal)
```

262 semanas de histórico real — mais longo que o necessário, mas
**também semanal**, mesma limitação de granularidade do GitHub (o
Google Trends automaticamente aumenta a granularidade só para janelas
curtas — dias para janelas de meses, horas para janelas de dias — mas
uma janela curta o bastante para granularidade diária perde a maior
parte do histórico de 2,7 anos que os outros atributos deste registro
usam).

**Segunda chamada (mesmo processo, nova sessão `TrendReq`, 20s de
espera antes), falha:**

```
pytrends.exceptions.ResponseError: The request failed:
Google returned a response with code 400
```

**Repetido com backoff explícito — falha persistente, não transiente.**
O rate limit agressivo já citado na entrada da fila (§6.2) se confirma
na prática: mesmo uma segunda chamada, com uma pausa real entre elas e
uma sessão nova, falha. Uma campanha real precisaria de pelo menos 12
chamadas (uma por par de `UNIVERSO_H11`) — com a taxa de falha
observada aqui (1 de 2 chamadas falhou mesmo com backoff), o resultado
esperado é uma campanha que não consegue nem terminar de coletar dado
para todos os pares, quanto mais de forma repetível.

## D2 — nenhuma fonte passa a barra de viabilidade declarada

| Critério (barra declarada em spec.md) | GitHub | Google Trends |
|---|---|---|
| Histórico ~2,7 anos | **Falha** (1 ano, teto do endpoint) | Passa (5 anos disponíveis) |
| Granularidade compatível com candles de 4h | **Falha** (semanal) | **Falha** (semanal na janela longa) |
| Confiabilidade para campanha multi-par sem infra paga | Passa (rate limit generoso, 60/h) | **Falha** (bloqueio já na 2ª chamada) |

**Nenhuma das duas passa nos três critérios simultaneamente.** GitHub
falha por histórico e granularidade; Google Trends falha por
granularidade e confiabilidade. Contornar qualquer uma das falhas
exigiria infraestrutura fora do escopo declarado (proxy rotation ou
API paga para Google Trends; token de autenticação não resolve o teto
de 52 semanas do GitHub, que é do próprio endpoint, não do rate
limit).

## Conclusão

**H31 permanece com viabilidade negativa.** Não é um veredito
REPROVADA (nada foi medido quanto a sentimento predizer retorno) — é a
constatação de que, hoje, com fontes gratuitas e sem infraestrutura
nova, a pergunta não é testável com o mesmo rigor do resto do
registro. Fica registrada como tal, reabrível se uma fonte gratuita
com histórico/granularidade adequados aparecer no futuro (ex.: um
provedor com tier gratuito que ofereça granularidade diária sobre
janela longa, ou uma mudança na política de rate limit do Google
Trends).

## Reprodução

Nenhum comando de produção — a checagem foi ad-hoc, documentada acima
com os números reais obtidos em 2026-09-03. Repetível chamando os dois
endpoints diretamente (GitHub sem autenticação; `pytrends` via
instalação isolada, não faz parte das dependências do projeto).
