import os

import pandas as pd

from data.paths import OHLCV_DIR


def save_ohlcv(symbol: str, timeframe: str, df):
    safe = symbol.replace("/", "")
    path = f"{OHLCV_DIR}/{safe}_{timeframe}.csv"
    if os.path.exists(path):
        existing = pd.read_csv(path, index_col="timestamp", parse_dates=True)
        df = pd.concat([existing, df])
        df = df[~df.index.duplicated(keep="last")].sort_index()
    df.to_csv(path)
