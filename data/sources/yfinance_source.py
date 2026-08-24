"""Fonte de dados nao-cripto via yfinance (spec 023, T015).

Cobre acoes (EUA e BR), forex, futuros e indices. Escolhida por ser gratuita e
sem chave de API -- ver decisao D1 em specs/023-dados-multi-mercado/research.md,
onde a cobertura foi medida contra AAPL, PETR4.SA, EURUSD=X, ES=F e ^GSPC.

Limitacao medida e relevante: o historico intradiario tem teto de 730 dias na
fonte, o que da ~993 candles em 4h contra os 2000 de cripto. Por isso
`last_shortfall` existe -- pedir 2000 e receber 993 e normal, mas passar
silencioso desbalancearia uma comparacao cripto x acoes sem ninguem notar.
"""
from typing import Optional

import pandas as pd

from utils.logger import get_logger

log = get_logger("yfinance_source")

# Intervalos que a fonte aceita. `4h` existe (verificado), ao contrario do que
# se poderia supor -- ver D2 em research.md.
_INTERVALOS_SUPORTADOS = {"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "4h", "1d", "5d", "1wk", "1mo", "3mo"}

# Periodo pedido a fonte. `2y` e o maximo util em intradiario: acima disso a
# fonte recusa com "must be within the last 730 days".
_PERIODO_INTRADIARIO = "2y"
_PERIODO_DIARIO = "max"


def _download(symbol: str, interval: str, period: str) -> pd.DataFrame:
    """Isolado em funcao propria para ser substituivel nos testes sem tocar a rede."""
    import yfinance as yf

    return yf.Ticker(symbol).history(period=period, interval=interval)


class YFinanceSource:
    name = "yfinance"

    def __init__(self) -> None:
        # Registra a ultima lacuna entre pedido e recebido. None quando o
        # `limit` foi atendido integralmente.
        self.last_shortfall: Optional[dict] = None

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        if timeframe not in _INTERVALOS_SUPORTADOS:
            raise ValueError(
                f"intervalo '{timeframe}' nao suportado pela fonte yfinance -- "
                f"suportados: {sorted(_INTERVALOS_SUPORTADOS)}"
            )

        periodo = _PERIODO_DIARIO if timeframe.endswith(("d", "wk", "mo")) else _PERIODO_INTRADIARIO
        raw = _download(symbol, timeframe, periodo)

        if raw is None or len(raw) == 0:
            raise ValueError(
                f"nenhum candle retornado para '{symbol}' [{timeframe}] -- "
                "simbolo inexistente, sem historico, ou fora do periodo disponivel"
            )

        df = self._normalize(raw)
        df = df.iloc[-limit:]

        if len(df) < limit:
            self.last_shortfall = {"symbol": symbol, "timeframe": timeframe, "requested": limit, "received": len(df)}
            log.warning(
                f"{symbol} [{timeframe}]: pedidos {limit} candles, obtidos {len(df)} -- "
                "a fonte limita historico intradiario a 730 dias"
            )
        else:
            self.last_shortfall = None

        return df

    @staticmethod
    def _normalize(raw: pd.DataFrame) -> pd.DataFrame:
        """Converte o formato cru da fonte para o contrato do projeto.

        A normalizacao e responsabilidade da FONTE, nao do consumidor -- e o que
        permite que backtest/compare/optimize nao saibam quem respondeu.
        """
        df = raw.rename(columns={c: c.lower() for c in raw.columns})
        faltando = {"open", "high", "low", "close", "volume"} - set(df.columns)
        if faltando:
            raise ValueError(f"resposta da fonte sem as colunas obrigatorias: {sorted(faltando)}")

        df = df[["open", "high", "low", "close", "volume"]]
        df = df[~df.index.duplicated(keep="last")]
        df = df.sort_index()
        # Indice sem fuso: o resto do projeto (incluindo os indicadores e o
        # split treino/validacao) trabalha com timestamps ingenuos, e misturar
        # os dois estilos quebra comparacao de datas.
        if getattr(df.index, "tz", None) is not None:
            df.index = df.index.tz_localize(None)
        return df
