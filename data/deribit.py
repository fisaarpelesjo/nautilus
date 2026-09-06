"""Volatilidade implicita (DVOL) da Deribit -- fonte de dados para H38
(specs/074-h38-dvol-gate/). API publica de opcoes, sem chave --
categoricamente diferente de qualquer fonte ja integrada (ccxt/yfinance/
blockchain.info).

Nao e consumido por trading/, execution/ nem risk/ -- inacessivel ao
caminho de execucao real por construcao.
"""
import time

import pandas as pd
import requests

BASE_URL = "https://www.deribit.com/api/v2/public/get_volatility_index_data"


def fetch_dvol_history(currency: str = "BTC", dias: int = 900, resolution: str = "86400") -> pd.DataFrame:
    """Serie do indice DVOL (colunas open/high/low/close), por padrao
    resolucao diaria. Levanta excecao em falha de rede, HTTP nao-200 ou
    resposta sem 'result' -- nunca retorna serie vazia/parcial como se
    fosse sucesso nesses casos. Serie vazia por AUSENCIA REAL de dado no
    periodo e um resultado valido, nao erro -- o chamador decide o que
    fazer."""
    agora_ms = int(time.time() * 1000)
    desde_ms = agora_ms - dias * 24 * 60 * 60 * 1000
    params = {
        "currency": currency, "start_timestamp": desde_ms,
        "end_timestamp": agora_ms, "resolution": resolution,
    }
    response = requests.get(BASE_URL, params=params, timeout=15)
    response.raise_for_status()

    body = response.json()
    if "result" not in body:
        raise RuntimeError(f"Deribit recusou get_volatility_index_data: {body}")

    pontos = body["result"].get("data") or []
    if not pontos:
        return pd.DataFrame(
            columns=["open", "high", "low", "close"],
            index=pd.DatetimeIndex([], name="date", tz="UTC"),
        )

    df = pd.DataFrame(pontos, columns=["timestamp", "open", "high", "low", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df.set_index("timestamp").sort_index()
    df.index.name = "date"
    return df[~df.index.duplicated(keep="last")]
