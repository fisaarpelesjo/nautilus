from dotenv import load_dotenv
import os

load_dotenv()

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")

TRADING_MODE = os.getenv("TRADING_MODE", "paper")  # "paper" ou "live"
LIVE_CONFIRMATION_TEXT = "I_UNDERSTAND_LIVE_TRADING_RISK"
LIVE_TRADING_CONFIRMATION = os.getenv("LIVE_TRADING_CONFIRMATION", "")
TIMEFRAME    = os.getenv("TIMEFRAME", "4h")

_pairs_env = os.getenv("PAIRS", "ENSO/USDT,AAVE/USDT,ZEC/USDT,LDO/USDT,TON/USDT")
PAIRS      = [p.strip() for p in _pairs_env.split(",") if p.strip()]
SYMBOL     = PAIRS[0]  # compatibilidade com backtest single-pair
_blacklist_env = os.getenv("BLACKLIST_PAIRS", "")
BLACKLIST_PAIRS = {p.strip().upper() for p in _blacklist_env.split(",") if p.strip()}

DYNAMIC_PAIRS_ENABLED = os.getenv("DYNAMIC_PAIRS_ENABLED", "false").lower() in {"1", "true", "yes", "sim"}
DYNAMIC_PAIRS_TOP_N = int(os.getenv("DYNAMIC_PAIRS_TOP_N", "5"))
DYNAMIC_PAIRS_CANDIDATES = int(os.getenv("DYNAMIC_PAIRS_CANDIDATES", "20"))
MIN_VOLUME_USDT = float(os.getenv("MIN_VOLUME_USDT", "10000000"))
MIN_PRICE_USDT = float(os.getenv("MIN_PRICE_USDT", "0.001"))
MAX_SPREAD_PCT = float(os.getenv("MAX_SPREAD_PCT", "0.003"))
MIN_VOLATILITY_PCT = float(os.getenv("MIN_VOLATILITY_PCT", "1.0"))

MAX_ORDER_SIZE_USDT = float(os.getenv("MAX_ORDER_SIZE_USDT", "100.0"))
MAX_POSITIONS       = int(os.getenv("MAX_POSITIONS", "5"))
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "0.015"))
TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "0.06"))
ATR_SL_MULTIPLIER = float(os.getenv("ATR_SL_MULTIPLIER", "1.5"))
ATR_TP_MULTIPLIER = float(os.getenv("ATR_TP_MULTIPLIER", "3.0"))

VOLUME_MA_PERIOD  = int(os.getenv("VOLUME_MA_PERIOD", "20"))
VOLUME_MIN_RATIO  = float(os.getenv("VOLUME_MIN_RATIO", "1.0"))

MTF_TIMEFRAME = os.getenv("MTF_TIMEFRAME", "1d")

COOLDOWN_HOURS = int(os.getenv("COOLDOWN_HOURS", "4"))
ENTRY_COOLDOWN_CYCLES = int(os.getenv("ENTRY_COOLDOWN_CYCLES", "3"))

DAILY_DRAWDOWN_LIMIT = float(os.getenv("DAILY_DRAWDOWN_LIMIT", "0.05"))  # 5% do saldo de referencia diario
WEEKLY_DRAWDOWN_LIMIT = float(os.getenv("WEEKLY_DRAWDOWN_LIMIT", "0.10"))  # 10% do saldo de referencia semanal
MONTHLY_DRAWDOWN_LIMIT = float(os.getenv("MONTHLY_DRAWDOWN_LIMIT", "0.20"))  # 20% do saldo de referencia mensal
MAX_CONSECUTIVE_LOSSES = int(os.getenv("MAX_CONSECUTIVE_LOSSES", "3"))

# Numero minimo de trades para o veredito de aprovacao de backtest (edge/multibacktest/scan/
# backtest --validate) ser conclusivo -- amostra abaixo disso vira "inconclusivo".
EDGE_MIN_TRADES = int(os.getenv("EDGE_MIN_TRADES", "10"))

DAILY_REPORT_HOUR = int(os.getenv("DAILY_REPORT_HOUR", "0"))  # hora do relatório (0 = meia-noite)


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Estratégia EMA crossover
EMA_FAST = int(os.getenv("EMA_FAST", "9"))
EMA_SLOW = int(os.getenv("EMA_SLOW", "21"))
EMA_TREND = int(os.getenv("EMA_TREND", "50"))
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))
RSI_OVERSOLD = int(os.getenv("RSI_OVERSOLD", "35"))
RSI_OVERBOUGHT = int(os.getenv("RSI_OVERBOUGHT", "70"))
PULLBACK_ENTRY_ENABLED = os.getenv("PULLBACK_ENTRY_ENABLED", "true").lower() in {"1", "true", "yes", "sim"}
PULLBACK_RSI_MIN = int(os.getenv("PULLBACK_RSI_MIN", "45"))
PULLBACK_MAX_DISTANCE_PCT = float(os.getenv("PULLBACK_MAX_DISTANCE_PCT", "0.01"))

# Bollinger Bands
BB_PERIOD = int(os.getenv("BB_PERIOD", "20"))
BB_STD    = float(os.getenv("BB_STD", "2.0"))

# Candles para carregar
CANDLE_LIMIT = 1000

# Backtest
BACKTEST_FEE_RATE = float(os.getenv("BACKTEST_FEE_RATE", "0.001"))
BACKTEST_SLIPPAGE_PCT = float(os.getenv("BACKTEST_SLIPPAGE_PCT", "0.0005"))


def validate_config():
    errors = []

    if TRADING_MODE not in {"paper", "live"}:
        errors.append("TRADING_MODE deve ser 'paper' ou 'live'.")
    if not PAIRS:
        errors.append("PAIRS deve conter ao menos um par.")
    invalid_pairs = [pair for pair in PAIRS if "/" not in pair or not pair.endswith("/USDT")]
    if invalid_pairs:
        errors.append(f"PAIRS invalidos: {', '.join(invalid_pairs)}. Use o formato BASE/USDT.")
    invalid_blacklist = [pair for pair in BLACKLIST_PAIRS if "/" not in pair and not pair.isalpha()]
    if invalid_blacklist:
        errors.append(f"BLACKLIST_PAIRS invalido: {', '.join(invalid_blacklist)}.")
    if not TIMEFRAME.strip():
        errors.append("TIMEFRAME nao pode ficar vazio.")
    if MAX_ORDER_SIZE_USDT <= 0:
        errors.append("MAX_ORDER_SIZE_USDT deve ser maior que zero.")
    if DYNAMIC_PAIRS_TOP_N < 1 or DYNAMIC_PAIRS_CANDIDATES < 1:
        errors.append("DYNAMIC_PAIRS_TOP_N e DYNAMIC_PAIRS_CANDIDATES devem ser maiores que zero.")
    if MIN_VOLUME_USDT < 0 or MAX_SPREAD_PCT < 0 or MIN_VOLATILITY_PCT < 0:
        errors.append("Filtros dinamicos de mercado nao podem ser negativos.")
    if MIN_PRICE_USDT < 0:
        errors.append("MIN_PRICE_USDT nao pode ser negativo.")
    if MAX_POSITIONS < 1:
        errors.append("MAX_POSITIONS deve ser pelo menos 1.")
    if STOP_LOSS_PCT <= 0 or TAKE_PROFIT_PCT <= 0:
        errors.append("STOP_LOSS_PCT e TAKE_PROFIT_PCT devem ser maiores que zero.")
    if ATR_SL_MULTIPLIER <= 0 or ATR_TP_MULTIPLIER <= 0:
        errors.append("ATR_SL_MULTIPLIER e ATR_TP_MULTIPLIER devem ser maiores que zero.")
    if VOLUME_MA_PERIOD < 1 or VOLUME_MIN_RATIO <= 0:
        errors.append("Configuracao de volume invalida.")
    if not (EMA_FAST > 0 and EMA_SLOW > 0 and EMA_TREND > 0 and EMA_FAST < EMA_SLOW):
        errors.append("EMAs invalidas. Use valores positivos com EMA_FAST menor que EMA_SLOW.")
    if RSI_PERIOD < 1 or not (0 <= RSI_OVERSOLD < RSI_OVERBOUGHT <= 100):
        errors.append("Configuracao de RSI invalida.")
    if not (0 <= PULLBACK_RSI_MIN < RSI_OVERBOUGHT <= 100):
        errors.append("Configuracao de RSI para pullback invalida.")
    if PULLBACK_MAX_DISTANCE_PCT < 0:
        errors.append("PULLBACK_MAX_DISTANCE_PCT nao pode ser negativo.")
    if COOLDOWN_HOURS < 0:
        errors.append("COOLDOWN_HOURS nao pode ser negativo.")
    if ENTRY_COOLDOWN_CYCLES < 0:
        errors.append("ENTRY_COOLDOWN_CYCLES nao pode ser negativo.")
    if not 0 < DAILY_DRAWDOWN_LIMIT <= 1:
        errors.append("DAILY_DRAWDOWN_LIMIT deve estar entre 0 e 1.")
    if not 0 < WEEKLY_DRAWDOWN_LIMIT <= 1:
        errors.append("WEEKLY_DRAWDOWN_LIMIT deve estar entre 0 e 1.")
    if not 0 < MONTHLY_DRAWDOWN_LIMIT <= 1:
        errors.append("MONTHLY_DRAWDOWN_LIMIT deve estar entre 0 e 1.")
    if WEEKLY_DRAWDOWN_LIMIT < DAILY_DRAWDOWN_LIMIT:
        errors.append("WEEKLY_DRAWDOWN_LIMIT deve ser maior ou igual a DAILY_DRAWDOWN_LIMIT.")
    if MONTHLY_DRAWDOWN_LIMIT < WEEKLY_DRAWDOWN_LIMIT:
        errors.append("MONTHLY_DRAWDOWN_LIMIT deve ser maior ou igual a WEEKLY_DRAWDOWN_LIMIT.")
    if MAX_CONSECUTIVE_LOSSES < 1:
        errors.append("MAX_CONSECUTIVE_LOSSES deve ser pelo menos 1.")
    if EDGE_MIN_TRADES < 1:
        errors.append("EDGE_MIN_TRADES deve ser pelo menos 1.")
    if not 0 <= DAILY_REPORT_HOUR <= 23:
        errors.append("DAILY_REPORT_HOUR deve estar entre 0 e 23.")
    if BB_PERIOD < 1 or BB_STD <= 0:
        errors.append("Configuracao de Bollinger Bands invalida.")
    if CANDLE_LIMIT < 50:
        errors.append("CANDLE_LIMIT deve ser pelo menos 50.")
    if BACKTEST_FEE_RATE < 0 or BACKTEST_SLIPPAGE_PCT < 0:
        errors.append("BACKTEST_FEE_RATE e BACKTEST_SLIPPAGE_PCT nao podem ser negativos.")

    if TRADING_MODE == "live":
        if LIVE_TRADING_CONFIRMATION != LIVE_CONFIRMATION_TEXT:
            errors.append(f"LIVE_TRADING_CONFIRMATION deve ser {LIVE_CONFIRMATION_TEXT} para modo live.")
        if not BINANCE_API_KEY or not BINANCE_API_SECRET:
            errors.append("BINANCE_API_KEY e BINANCE_API_SECRET sao obrigatorios no modo live.")

    if errors:
        raise ValueError("Config invalida:\n- " + "\n- ".join(errors))


validate_config()
