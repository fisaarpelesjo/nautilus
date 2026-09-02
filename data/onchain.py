"""Fonte de dados on-chain do Bitcoin (spec 033).

Infraestrutura de pesquisa -- entrega so a capacidade de busca, nao decide
qual metrica nenhuma hipotese usa (ver specs/033-fonte-dados-onchain/spec.md
FR-007). So Bitcoin: api.blockchain.info nao cobre os demais pares do bot
(Assumptions da spec).

Nao e consumido por trading/, execution/ nem risk/ -- inacessivel ao
caminho de execucao real por construcao.
"""

import pandas as pd
import requests

BASE_URL = "https://api.blockchain.info/charts"


def fetch_onchain_series(metric: str, timespan: str = "3years") -> pd.DataFrame:
    """Serie diaria de uma metrica on-chain do Bitcoin, por nome.

    `sampled=false` evita que a API subamostre janelas longas (D1,
    research.md) -- sem isso um pedido de anos podia devolver menos de um
    ponto por dia sem aviso.

    Levanta excecao em falha de rede, HTTP nao-200 ou `status` != "ok" no
    corpo (nome de metrica invalido) -- nunca retorna serie vazia ou
    parcial como se fosse sucesso nesses casos (FR-003). Serie vazia por
    AUSENCIA REAL de dado no periodo (status "ok", `values: []`) e um
    resultado valido, nao erro (FR-004) -- o chamador decide o que fazer.
    """
    url = f"{BASE_URL}/{metric}?timespan={timespan}&format=json&sampled=false"
    response = requests.get(url, timeout=15)
    response.raise_for_status()

    body = response.json()
    if body.get("status") != "ok":
        raise RuntimeError(f"blockchain.info recusou a metrica '{metric}': {body}")

    valores = body.get("values") or []
    if not valores:
        return pd.DataFrame(columns=["value"], index=pd.DatetimeIndex([], name="date"))

    index = pd.to_datetime([v["x"] for v in valores], unit="s", utc=True)
    serie = pd.DataFrame({"value": [v["y"] for v in valores]}, index=index)
    serie.index.name = "date"
    serie = serie[~serie.index.duplicated(keep="last")].sort_index()
    return serie
