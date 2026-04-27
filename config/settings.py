from dotenv import load_dotenv
import os

load_dotenv()

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")

TRADING_MODE = os.getenv("TRADING_MODE", "paper")  # "paper" ou "live"
TIMEFRAME    = os.getenv("TIMEFRAME", "4h")

_pairs_env = os.getenv("PAIRS", "ENSO/USDT,AAVE/USDT,ZEC/USDT,LDO/USDT,TON/USDT")
PAIRS      = [p.strip() for p in _pairs_env.split(",") if p.strip()]
SYMBOL     = PAIRS[0]  # compatibilidade com backtest single-pair

MAX_ORDER_SIZE_USDT = float(os.getenv("MAX_ORDER_SIZE_USDT", "100.0"))
MAX_POSITIONS       = int(os.getenv("MAX_POSITIONS", "5"))
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "0.015"))
TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "0.06"))
ATR_SL_MULTIPLIER = float(os.getenv("ATR_SL_MULTIPLIER", "1.5"))
ATR_TP_MULTIPLIER = float(os.getenv("ATR_TP_MULTIPLIER", "3.0"))

VOLUME_MA_PERIOD  = int(os.getenv("VOLUME_MA_PERIOD", "20"))
VOLUME_MIN_RATIO  = float(os.getenv("VOLUME_MIN_RATIO", "1.2"))


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Estratégia EMA crossover
EMA_FAST = 9
EMA_SLOW = 21
EMA_TREND = 50
RSI_PERIOD = 14
RSI_OVERSOLD = 35
RSI_OVERBOUGHT = 65

# Candles para carregar
CANDLE_LIMIT = 1000
