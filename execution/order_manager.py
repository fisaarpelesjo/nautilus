from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict
import ccxt
from config.settings import (
    BINANCE_API_KEY,
    BINANCE_API_SECRET,
    LIVE_CONFIRMATION_TEXT,
    LIVE_TRADING_CONFIRMATION,
    TRADING_MODE,
    COOLDOWN_HOURS,
    DAILY_DRAWDOWN_LIMIT,
)
from data.fetcher import get_exchange
from data.trade_logger import log_trade, save_state, load_state
from risk.manager import RiskLevels
from utils.logger import get_logger
from utils.notifier import send_telegram

log = get_logger("orders")

@dataclass
class Position:
    symbol: str
    side: str
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: float
    atr: float = 0.0
    highest_price: float = 0.0
    opened_at: datetime = field(default_factory=datetime.now)
    order_id: Optional[str] = None

class OrderManager:
    def __init__(self):
        self.exchange: Optional[ccxt.binance] = None
        self.positions: Dict[str, Position] = {}
        self.paper_balance_usdt: float = 1000.0
        self.total_trades: int   = 0
        self.winning_trades: int = 0
        self.realized_pnl: float = 0.0
        self.cooldowns: Dict[str, datetime] = {}
        self.daily_pnl: float = 0.0
        self.daily_reset_date: str = ""
        if TRADING_MODE == "live":
            self._assert_live_trading_allowed()
            self.exchange = get_exchange()
        self._restore_state()

    def _assert_live_trading_allowed(self):
        if LIVE_TRADING_CONFIRMATION != LIVE_CONFIRMATION_TEXT:
            raise RuntimeError(
                "Live trading bloqueado: defina "
                f"LIVE_TRADING_CONFIRMATION={LIVE_CONFIRMATION_TEXT} no .env para operar com dinheiro real."
            )
        if not BINANCE_API_KEY or not BINANCE_API_SECRET:
            raise RuntimeError("Live trading bloqueado: BINANCE_API_KEY e BINANCE_API_SECRET sao obrigatorios.")

    def _restore_state(self):
        state = load_state()
        if not state:
            return
        self.paper_balance_usdt = state.get("paper_balance_usdt", 1000.0)
        self.total_trades       = state.get("total_trades", 0)
        self.winning_trades     = state.get("winning_trades", 0)
        self.realized_pnl       = state.get("realized_pnl", 0.0)
        for symbol, ts in state.get("cooldowns", {}).items():
            self.cooldowns[symbol] = datetime.fromisoformat(ts)
        today = datetime.now().strftime("%Y-%m-%d")
        saved_date = state.get("daily_reset_date", "")
        if saved_date == today:
            self.daily_pnl        = state.get("daily_pnl", 0.0)
            self.daily_reset_date = saved_date
        else:
            self.daily_pnl        = 0.0
            self.daily_reset_date = today
        for symbol, pos in state.get("positions", {}).items():
            if pos:
                self.positions[symbol] = Position(
                    symbol        = pos["symbol"],
                    side          = pos["side"],
                    entry_price   = pos["entry_price"],
                    quantity      = pos["quantity"],
                    stop_loss     = pos["stop_loss"],
                    take_profit   = pos["take_profit"],
                    atr           = pos.get("atr", 0.0),
                    highest_price = pos.get("highest_price", pos["entry_price"]),
                    opened_at     = datetime.fromisoformat(pos["opened_at"]),
                    order_id      = pos.get("order_id"),
                )
        if self.positions:
            log.info(f"Posicoes restauradas: {list(self.positions.keys())}")

    def _persist_state(self):
        pos_data = {}
        for symbol, pos in self.positions.items():
            pos_data[symbol] = {
                "symbol":        pos.symbol,
                "side":          pos.side,
                "entry_price":   pos.entry_price,
                "quantity":      pos.quantity,
                "stop_loss":     pos.stop_loss,
                "take_profit":   pos.take_profit,
                "atr":           pos.atr,
                "highest_price": pos.highest_price,
                "opened_at":     pos.opened_at.isoformat(),
                "order_id":      pos.order_id,
            }
        save_state({
            "paper_balance_usdt": self.paper_balance_usdt,
            "total_trades":       self.total_trades,
            "winning_trades":     self.winning_trades,
            "realized_pnl":       self.realized_pnl,
            "positions":          pos_data,
            "cooldowns":          {s: dt.isoformat() for s, dt in self.cooldowns.items()},
            "daily_pnl":          self.daily_pnl,
            "daily_reset_date":   self.daily_reset_date,
            "updated_at":         datetime.now().isoformat(),
        })

    def _check_daily_reset(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if self.daily_reset_date != today:
            self.daily_pnl        = 0.0
            self.daily_reset_date = today

    def is_daily_limit_hit(self) -> bool:
        self._check_daily_reset()
        limit = DAILY_DRAWDOWN_LIMIT * 1000.0
        if self.daily_pnl < -limit:
            log.warning(f"Daily drawdown atingido: ${self.daily_pnl:.2f} (limite -${limit:.2f})")
            return True
        return False

    def set_cooldown(self, symbol: str):
        self.cooldowns[symbol] = datetime.now()
        log.info(f"Cooldown ativado: {symbol} por {COOLDOWN_HOURS}h")

    def is_in_cooldown(self, symbol: str) -> bool:
        if symbol not in self.cooldowns:
            return False
        return datetime.now() - self.cooldowns[symbol] < timedelta(hours=COOLDOWN_HOURS)

    def has_position(self, symbol: str) -> bool:
        return symbol in self.positions

    def get_position(self, symbol: str) -> Optional[Position]:
        return self.positions.get(symbol)

    def win_rate(self) -> float:
        return (self.winning_trades / self.total_trades * 100) if self.total_trades else 0

    def pnl(self) -> float:
        return self.realized_pnl

    def open_long(self, symbol: str, risk: RiskLevels):
        if self.has_position(symbol):
            return
        if TRADING_MODE == "paper":
            self._paper_buy(symbol, risk)
        else:
            self._live_buy(symbol, risk)

    def close_position(self, symbol: str, reason: str, current_price: float = 0.0):
        if not self.has_position(symbol):
            return
        if TRADING_MODE == "paper":
            self._paper_sell(symbol, reason, current_price)
        else:
            self._live_sell(symbol, reason)

    def _paper_buy(self, symbol: str, risk: RiskLevels):
        cost = risk.quantity * risk.entry_price
        if cost > self.paper_balance_usdt:
            log.warning(f"Saldo insuficiente para {symbol}: ${self.paper_balance_usdt:.2f}")
            return
        self.paper_balance_usdt -= cost
        self.positions[symbol] = Position(
            symbol        = symbol,
            side          = "long",
            entry_price   = risk.entry_price,
            quantity      = risk.quantity,
            stop_loss     = risk.stop_loss,
            take_profit   = risk.take_profit,
            atr           = risk.atr,
            highest_price = risk.entry_price,
        )
        self._persist_state()
        msg = f"[PAPER] COMPRA {symbol} | ${risk.entry_price:.4f} | SL ${risk.stop_loss:.4f} | TP ${risk.take_profit:.4f}"
        log.info(msg)
        send_telegram(msg)

    def _paper_sell(self, symbol: str, reason: str, current_price: float = 0.0):
        pos = self.positions[symbol]
        exit_price = current_price or (
            pos.stop_loss if "stop" in reason.lower() else pos.take_profit
        )
        pnl     = (exit_price - pos.entry_price) * pos.quantity
        pnl_pct = (exit_price - pos.entry_price) / pos.entry_price * 100
        self.paper_balance_usdt += pos.quantity * exit_price
        self._check_daily_reset()
        self.total_trades += 1
        self.realized_pnl += pnl
        self.daily_pnl    += pnl
        if pnl > 0:
            self.winning_trades += 1

        log_trade({
            "opened_at":     pos.opened_at,
            "closed_at":     datetime.now(),
            "symbol":        pos.symbol,
            "side":          pos.side,
            "entry_price":   pos.entry_price,
            "exit_price":    exit_price,
            "quantity":      pos.quantity,
            "pnl_usdt":      round(pnl, 6),
            "pnl_pct":       round(pnl_pct, 4),
            "exit_reason":   reason,
            "balance_after": round(self.paper_balance_usdt, 4),
        })

        msg = f"[PAPER] VENDA {symbol} | {reason} | PnL ${pnl:+.4f} ({pnl_pct:+.2f}%) | Saldo ${self.paper_balance_usdt:.2f}"
        log.info(msg)
        send_telegram(msg)
        del self.positions[symbol]
        self._persist_state()

    def _live_buy(self, symbol: str, risk: RiskLevels):
        if self.exchange is None:
            raise RuntimeError("Exchange live nao inicializada.")
        try:
            order = self.exchange.create_market_buy_order(
                symbol, risk.quantity,
                params={"quoteOrderQty": risk.quantity * risk.entry_price}
            )
            self.positions[symbol] = Position(
                symbol      = symbol,
                side        = "long",
                entry_price = risk.entry_price,
                quantity    = risk.quantity,
                stop_loss   = risk.stop_loss,
                take_profit = risk.take_profit,
                order_id    = order["id"],
            )
            self._persist_state()
            msg = f"[LIVE] COMPRA {symbol} | ID={order['id']} | ${risk.entry_price:.4f}"
            log.info(msg)
            send_telegram(msg)
        except Exception as e:
            log.error(f"Erro ao comprar {symbol}: {e}")

    def _live_sell(self, symbol: str, reason: str):
        if self.exchange is None:
            raise RuntimeError("Exchange live nao inicializada.")
        pos = self.positions[symbol]
        try:
            order = self.exchange.create_market_sell_order(symbol, pos.quantity)
            msg = f"[LIVE] VENDA {symbol} | {reason} | ID={order['id']}"
            log.info(msg)
            send_telegram(msg)
        except Exception as e:
            log.error(f"Erro ao vender {symbol}: {e}")
        finally:
            del self.positions[symbol]
            self._persist_state()
