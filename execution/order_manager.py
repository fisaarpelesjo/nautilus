import time
import uuid
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
    WEEKLY_DRAWDOWN_LIMIT,
    MONTHLY_DRAWDOWN_LIMIT,
    MAX_CONSECUTIVE_LOSSES,
)
from data.fetcher import fetch_balance, get_exchange
from data.state_store import load_state, save_state
from data.trade_store import log_trade
from risk.manager import RiskLevels
from utils.logger import get_logger, log_event, safe_step
from utils.notifier import send_telegram

log = get_logger("orders")


def _generate_client_order_id() -> str:
    """ID unico por ordem (paper e live) para idempotencia -- ver constitution P6."""
    return f"bot-{uuid.uuid4().hex[:8]}-{int(datetime.now().timestamp())}"


def _notify_safe(prefix: str, msg: str):
    """Loga e envia `msg` via Telegram, isolado (nao propaga falha) -- usado
    depois de uma ordem confirmada, onde uma falha de notificacao nao pode
    reaparecer como erro da ordem em si."""
    def _notify():
        log.info(msg)
        send_telegram(msg)
    safe_step(log, f"{prefix}, mas falha ao enviar alerta", _notify)


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
    client_order_id: Optional[str] = None
    pending_close_client_order_id: Optional[str] = None

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
        self.daily_reference_balance: float = 0.0
        self.weekly_pnl: float = 0.0
        self.weekly_reset_date: str = ""
        self.weekly_reference_balance: float = 0.0
        self.monthly_pnl: float = 0.0
        self.monthly_reset_date: str = ""
        self.monthly_reference_balance: float = 0.0
        self._reference_balance_cache: Optional[float] = None
        self._reference_balance_cache_at: float = 0.0
        self.last_reconciliation: Optional[dict] = None
        self.pending_open_client_order_ids: Dict[str, str] = {}
        self.consecutive_losses: int = 0
        self.circuit_breaker_active: bool = False
        if TRADING_MODE == "live":
            self._assert_live_trading_allowed()
            self.exchange = get_exchange()
        self._restore_state()
        self._ensure_reference_balances()

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
        self.last_reconciliation = state.get("last_reconciliation")
        self.pending_open_client_order_ids = state.get("pending_open_client_order_ids", {})
        self.consecutive_losses = state.get("consecutive_losses", 0)
        self.circuit_breaker_active = state.get("circuit_breaker_active", False)
        for symbol, ts in state.get("cooldowns", {}).items():
            self.cooldowns[symbol] = datetime.fromisoformat(ts)
        today = datetime.now().strftime("%Y-%m-%d")
        saved_date = state.get("daily_reset_date", "")
        if saved_date == today:
            self.daily_pnl        = state.get("daily_pnl", 0.0)
            self.daily_reset_date = saved_date
            self.daily_reference_balance = state.get("daily_reference_balance", 0.0)
        else:
            self.daily_pnl        = 0.0
            self.daily_reset_date = today

        current_week = datetime.now().strftime("%G-W%V")
        saved_week = state.get("weekly_reset_date", "")
        if saved_week == current_week:
            self.weekly_pnl = state.get("weekly_pnl", 0.0)
            self.weekly_reset_date = saved_week
            self.weekly_reference_balance = state.get("weekly_reference_balance", 0.0)
        else:
            self.weekly_pnl = 0.0
            self.weekly_reset_date = current_week

        current_month = datetime.now().strftime("%Y-%m")
        saved_month = state.get("monthly_reset_date", "")
        if saved_month == current_month:
            self.monthly_pnl = state.get("monthly_pnl", 0.0)
            self.monthly_reset_date = saved_month
            self.monthly_reference_balance = state.get("monthly_reference_balance", 0.0)
        else:
            self.monthly_pnl = 0.0
            self.monthly_reset_date = current_month

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
                    client_order_id = pos.get("client_order_id"),
                    pending_close_client_order_id = pos.get("pending_close_client_order_id"),
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
                "client_order_id": pos.client_order_id,
                "pending_close_client_order_id": pos.pending_close_client_order_id,
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
            "daily_reference_balance": self.daily_reference_balance,
            "weekly_pnl":         self.weekly_pnl,
            "weekly_reset_date":  self.weekly_reset_date,
            "weekly_reference_balance": self.weekly_reference_balance,
            "monthly_pnl":        self.monthly_pnl,
            "monthly_reset_date": self.monthly_reset_date,
            "monthly_reference_balance": self.monthly_reference_balance,
            "last_reconciliation": self.last_reconciliation,
            "pending_open_client_order_ids": self.pending_open_client_order_ids,
            "consecutive_losses": self.consecutive_losses,
            "circuit_breaker_active": self.circuit_breaker_active,
            "updated_at":         datetime.now().isoformat(),
        })

    def _persist_state_with_retry(self, context: str, attempts: int = 2):
        """Persiste o estado com uma tentativa extra antes de desistir.

        Usado apos uma venda ja confirmada pela exchange: se state.json nao
        for atualizado, um restart pode "ressuscitar" uma posicao ja fechada
        (client_order_id de fechamento ja usado -> proxima tentativa seria
        rejeitada pela Binance como duplicata). Isso ainda pode acontecer no
        pior caso (falha em todas as tentativas); a reconciliacao periodica
        e quem flagra essa divergencia para revisao manual.
        """
        for attempt in range(1, attempts + 1):
            try:
                self._persist_state()
                return
            except Exception as e:
                if attempt < attempts:
                    log.warning(f"Falha ao persistir estado {context} (tentativa {attempt}): {e}")
                    time.sleep(0.2)  # da uma chance real de um lock transitorio (ex: sync do OneDrive) liberar
                else:
                    log.error(f"Falha ao persistir estado {context} apos {attempts} tentativas: {e}")

    def record_reconciliation(self, status: str, checked_at: str, diffs: list):
        self.last_reconciliation = {"status": status, "checked_at": checked_at, "diffs": diffs}
        self._persist_state_with_retry("ao registrar resultado de reconciliacao")

    def _update_consecutive_losses(self, pnl: float):
        """Atualiza o contador de perdas seguidas e o circuit breaker.

        Contador GLOBAL (nao por par): perdas seguidas em pares diferentes ja
        indicam que a estrategia/regime piorou de forma geral, nao so naquele
        par -- consistente com MAX_ENTRIES_PER_CYCLE=1, que ja trata entradas
        como recurso compartilhado entre pares.
        """
        if pnl < 0:
            self.consecutive_losses += 1
            if self.consecutive_losses >= MAX_CONSECUTIVE_LOSSES:
                if not self.circuit_breaker_active:
                    self.circuit_breaker_active = True
                    log.warning(f"Circuit breaker ativado: {self.consecutive_losses} perdas seguidas")
                    safe_step(log, "Falha ao publicar evento de circuit breaker", lambda: log_event(
                        "circuit_breaker_triggered", mode=TRADING_MODE, consecutive_losses=self.consecutive_losses,
                    ))
                    safe_step(log, "Falha ao enviar alerta de circuit breaker", lambda: send_telegram(
                        f"Circuit breaker ATIVADO: {self.consecutive_losses} perdas seguidas. Novas entradas suspensas."
                    ))
        elif pnl > 0:
            if self.circuit_breaker_active:
                log.info("Circuit breaker desativado (trade positivo resetou o contador)")
            self.consecutive_losses = 0
            self.circuit_breaker_active = False

    def _reference_balance(self) -> Optional[float]:
        """Saldo real em USDT, para uso como referencia dos limites de perda
        (nao de saldo disponivel para uma ordem -- ver
        trading/position_lifecycle.py _current_balance, que tem a mesma
        bifurcacao paper/live duplicada aqui de proposito para evitar import
        circular). Retorna None quando o saldo real nao pode ser obtido -- o
        chamador MUST manter o ultimo saldo de referencia conhecido nesse
        caso, nunca zerar."""
        if TRADING_MODE == "paper":
            return self.paper_balance_usdt
        # Cache curto (segundos): dia/semana/mes podem virar juntos (ex: toda
        # segunda-feira o diario e o semanal viram no mesmo ciclo) -- sem
        # isso, is_daily_limit_hit/is_weekly_limit_hit/is_monthly_limit_hit
        # em sequencia disparariam ate 3 chamadas de rede identicas na mesma
        # checagem de entrada (achado de code-review).
        now = time.monotonic()
        if self._reference_balance_cache is not None and now - self._reference_balance_cache_at < 5.0:
            return self._reference_balance_cache
        try:
            balance = fetch_balance()
            value = float(balance.get("USDT", 0))
        except Exception:
            return None
        self._reference_balance_cache = value
        self._reference_balance_cache_at = now
        return value

    def _ensure_reference_balances(self):
        """Preenche saldos de referencia ainda nao capturados (instalacao
        nova, ou state.json de antes desta spec sem os campos) -- so roda
        uma vez por inicializacao, sem sobrescrever um valor ja restaurado."""
        if self.daily_reference_balance > 0 and self.weekly_reference_balance > 0 and self.monthly_reference_balance > 0:
            return
        ref = self._reference_balance()
        if ref is None:
            return
        if self.daily_reference_balance <= 0:
            self.daily_reference_balance = ref
        if self.weekly_reference_balance <= 0:
            self.weekly_reference_balance = ref
        if self.monthly_reference_balance <= 0:
            self.monthly_reference_balance = ref

    def _check_daily_reset(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if self.daily_reset_date != today:
            self.daily_pnl        = 0.0
            self.daily_reset_date = today
            ref = self._reference_balance()
            if ref is not None:
                self.daily_reference_balance = ref

    def _check_weekly_reset(self):
        current_week = datetime.now().strftime("%G-W%V")
        if self.weekly_reset_date != current_week:
            self.weekly_pnl        = 0.0
            self.weekly_reset_date = current_week
            ref = self._reference_balance()
            if ref is not None:
                self.weekly_reference_balance = ref

    def _check_monthly_reset(self):
        current_month = datetime.now().strftime("%Y-%m")
        if self.monthly_reset_date != current_month:
            self.monthly_pnl        = 0.0
            self.monthly_reset_date = current_month
            ref = self._reference_balance()
            if ref is not None:
                self.monthly_reference_balance = ref

    def _ensure_positive_reference(self, current: float, period_label: str) -> Optional[float]:
        """Reconsulta o saldo de referencia enquanto ele for desconhecido
        (<=0) -- sem isso, uma falha unica de fetch_balance() (ex: no
        startup) travaria o saldo de referencia em 0.0 pelo resto do
        periodo, fazendo limite = 0 e QUALQUER prejuizo parecer "limite
        atingido" silenciosamente (achado de code-review). Retorna None
        quando continua indisponivel -- o chamador MUST bloquear
        conservador nesse caso, mesmo principio ja usado para saldo
        desconhecido em handle_entry_candidate."""
        if current > 0:
            return current
        ref = self._reference_balance()
        if ref is None:
            log.warning(f"Saldo de referencia {period_label} indisponivel -- bloqueando novas entradas por seguranca")
        return ref

    def is_daily_limit_hit(self) -> bool:
        self._check_daily_reset()
        ref = self._ensure_positive_reference(self.daily_reference_balance, "diario")
        if ref is None:
            return True
        self.daily_reference_balance = ref
        limit = DAILY_DRAWDOWN_LIMIT * ref
        if self.daily_pnl < -limit:
            log.warning(f"Daily drawdown atingido: ${self.daily_pnl:.2f} (limite -${limit:.2f})")
            return True
        return False

    def is_weekly_limit_hit(self) -> bool:
        self._check_weekly_reset()
        ref = self._ensure_positive_reference(self.weekly_reference_balance, "semanal")
        if ref is None:
            return True
        self.weekly_reference_balance = ref
        limit = WEEKLY_DRAWDOWN_LIMIT * ref
        if self.weekly_pnl < -limit:
            log.warning(f"Weekly drawdown atingido: ${self.weekly_pnl:.2f} (limite -${limit:.2f})")
            return True
        return False

    def is_monthly_limit_hit(self) -> bool:
        self._check_monthly_reset()
        ref = self._ensure_positive_reference(self.monthly_reference_balance, "mensal")
        if ref is None:
            return True
        self.monthly_reference_balance = ref
        limit = MONTHLY_DRAWDOWN_LIMIT * ref
        if self.monthly_pnl < -limit:
            log.warning(f"Monthly drawdown atingido: ${self.monthly_pnl:.2f} (limite -${limit:.2f})")
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
            self._live_sell(symbol, reason, current_price)

    def _paper_buy(self, symbol: str, risk: RiskLevels):
        cost = risk.quantity * risk.entry_price
        if cost > self.paper_balance_usdt:
            log.warning(f"Saldo insuficiente para {symbol}: ${self.paper_balance_usdt:.2f}")
            return
        self.paper_balance_usdt -= cost
        client_order_id = _generate_client_order_id()
        self.positions[symbol] = Position(
            symbol        = symbol,
            side          = "long",
            entry_price   = risk.entry_price,
            quantity      = risk.quantity,
            stop_loss     = risk.stop_loss,
            take_profit   = risk.take_profit,
            atr           = risk.atr,
            highest_price = risk.entry_price,
            client_order_id = client_order_id,
        )
        self._persist_state_with_retry(f"apos comprar (paper) {symbol}")

        prefix = f"Compra paper de {symbol} confirmada"
        safe_step(log, f"{prefix}, mas falha ao registrar evento", lambda: log_event(
            "paper_order_opened",
            mode=TRADING_MODE,
            symbol=symbol,
            side="long",
            entry_price=risk.entry_price,
            quantity=risk.quantity,
            stop_loss=risk.stop_loss,
            take_profit=risk.take_profit,
            balance_after=self.paper_balance_usdt,
            client_order_id=client_order_id,
        ))

        msg = f"[PAPER] COMPRA {symbol} | ${risk.entry_price:.4f} | SL ${risk.stop_loss:.4f} | TP ${risk.take_profit:.4f}"

        _notify_safe(prefix, msg)

    def _paper_sell(self, symbol: str, reason: str, current_price: float = 0.0):
        pos = self.positions[symbol]
        exit_price = current_price or (
            pos.stop_loss if "stop" in reason.lower() else pos.take_profit
        )
        pnl     = (exit_price - pos.entry_price) * pos.quantity
        pnl_pct = (exit_price - pos.entry_price) / pos.entry_price * 100
        self.paper_balance_usdt += pos.quantity * exit_price
        self._check_daily_reset()
        self._check_weekly_reset()
        self._check_monthly_reset()
        self.total_trades += 1
        self.realized_pnl += pnl
        self.daily_pnl    += pnl
        self.weekly_pnl   += pnl
        self.monthly_pnl  += pnl
        if pnl > 0:
            self.winning_trades += 1
        self._update_consecutive_losses(pnl)

        # Remove a posicao e persiste ANTES do log/alerta: se um desses passos
        # falhar (disco cheio, etc.), a posicao nao pode ficar presa em memoria
        # com os contadores ja incrementados -- na proxima tentativa ela seria
        # contabilizada de novo. Mesmo padrao aplicado a _live_sell.
        del self.positions[symbol]
        self._persist_state_with_retry(f"apos vender (paper) {symbol}")

        prefix = f"Venda paper de {symbol} confirmada"
        safe_step(log, f"{prefix}, mas falha ao registrar trade", lambda: log_trade({
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
            "client_order_id": pos.client_order_id,
        }))

        safe_step(log, f"{prefix}, mas falha ao registrar evento", lambda: log_event(
            "paper_order_closed",
            mode=TRADING_MODE,
            symbol=pos.symbol,
            side=pos.side,
            entry_price=pos.entry_price,
            exit_price=exit_price,
            quantity=pos.quantity,
            pnl_usdt=round(pnl, 6),
            pnl_pct=round(pnl_pct, 4),
            exit_reason=reason,
            balance_after=round(self.paper_balance_usdt, 4),
            daily_pnl=round(self.daily_pnl, 6),
        ))

        msg = f"[PAPER] VENDA {symbol} | {reason} | PnL ${pnl:+.4f} ({pnl_pct:+.2f}%) | Saldo ${self.paper_balance_usdt:.2f}"

        _notify_safe(prefix, msg)

    def _live_buy(self, symbol: str, risk: RiskLevels):
        if self.exchange is None:
            raise RuntimeError("Exchange live nao inicializada.")
        # Mesmo padrao de _live_sell: reusa o client_order_id de uma tentativa
        # anterior de compra deste symbol em vez de gerar um novo a cada
        # chamada. Sem isso, um timeout depois da Binance ja ter aceitado a
        # ordem faria o proximo ciclo comprar de novo com um ID novo -- uma
        # segunda ordem de compra de verdade, exposicao dobrada de capital.
        if symbol not in self.pending_open_client_order_ids:
            self.pending_open_client_order_ids[symbol] = _generate_client_order_id()
            self._persist_state_with_retry(f"ao registrar tentativa de compra de {symbol}")
        client_order_id = self.pending_open_client_order_ids[symbol]

        try:
            order = self.exchange.create_market_buy_order(
                symbol, risk.quantity,
                params={
                    "quoteOrderQty": risk.quantity * risk.entry_price,
                    "newClientOrderId": client_order_id,
                }
            )
        except Exception as e:
            # Nao registra a posicao em caso de erro na CHAMADA: a ordem pode
            # ter sido aceita pela exchange apesar do erro (timeout, etc.).
            # pending_open_client_order_ids mantem o mesmo ID salvo para o
            # proximo retry. Reconciliacao e quem flagra divergencia real.
            error_message = str(e)  # 'e' some ao sair do except; captura antes das lambdas
            log.error(f"Erro ao comprar {symbol}: {error_message}")
            error_prefix = f"Erro ao comprar {symbol} ja registrado no log"
            safe_step(log, f"{error_prefix}, mas falha ao publicar evento", lambda: log_event(
                "live_order_error", mode=TRADING_MODE, symbol=symbol, side="buy",
                error=error_message, client_order_id=client_order_id,
            ))
            safe_step(log, f"{error_prefix}, mas falha ao enviar alerta",
                       lambda: send_telegram(f"[LIVE] ERRO ao comprar {symbol}: {error_message}"))
            return

        # A partir daqui a compra foi aceita pela exchange -- a posicao MUST
        # existir mesmo que o log/alerta abaixo falhe.
        self.pending_open_client_order_ids.pop(symbol, None)
        self.positions[symbol] = Position(
            symbol      = symbol,
            side        = "long",
            entry_price = risk.entry_price,
            quantity    = risk.quantity,
            stop_loss   = risk.stop_loss,
            take_profit = risk.take_profit,
            order_id    = order["id"],
            client_order_id = client_order_id,
        )
        self._persist_state_with_retry(f"apos comprar {symbol}")

        prefix = f"Compra de {symbol} confirmada"
        safe_step(log, f"{prefix}, mas falha ao registrar evento", lambda: log_event(
            "live_order_opened",
            mode=TRADING_MODE,
            symbol=symbol,
            side="long",
            entry_price=risk.entry_price,
            quantity=risk.quantity,
            stop_loss=risk.stop_loss,
            take_profit=risk.take_profit,
            order_id=order["id"],
            client_order_id=client_order_id,
        ))

        msg = f"[LIVE] COMPRA {symbol} | ID={order['id']} | ${risk.entry_price:.4f}"

        _notify_safe(prefix, msg)

    def _live_sell(self, symbol: str, reason: str, current_price: float = 0.0):
        if self.exchange is None:
            raise RuntimeError("Exchange live nao inicializada.")
        pos = self.positions[symbol]
        # Reusa o client_order_id de uma tentativa anterior desta MESMA posicao
        # em vez de gerar um novo a cada chamada: se a primeira tentativa deu
        # timeout mas a Binance aceitou a ordem, um retry com o mesmo ID e
        # reconhecido pela exchange como a mesma ordem (idempotencia de
        # verdade -- constitution P6). Um ID novo a cada retry, como antes,
        # nao protegia contra nada.
        if pos.pending_close_client_order_id is None:
            pos.pending_close_client_order_id = _generate_client_order_id()
            self._persist_state_with_retry(f"ao registrar tentativa de venda de {symbol}")
        client_order_id = pos.pending_close_client_order_id

        try:
            order = self.exchange.create_market_sell_order(
                symbol, pos.quantity,
                params={"newClientOrderId": client_order_id},
            )
        except Exception as e:
            # Nao remove a posicao local em caso de erro na CHAMADA: a ordem
            # pode ter sido aceita pela exchange apesar do erro (timeout,
            # etc.), e apagar o registro local aqui derrubaria SL/TP/trailing
            # de uma posicao que ainda pode estar aberta de verdade.
            # pending_close_client_order_id fica salvo para o proximo retry
            # reusar o mesmo ID. Reconciliacao e quem flagra divergencia real
            # para revisao manual.
            error_message = str(e)  # 'e' some ao sair do except; captura antes das lambdas
            log.error(f"Erro ao vender {symbol}: {error_message}")
            error_prefix = f"Erro ao vender {symbol} ja registrado no log"
            safe_step(log, f"{error_prefix}, mas falha ao publicar evento", lambda: log_event(
                "live_order_error", mode=TRADING_MODE, symbol=symbol, side="sell",
                error=error_message, client_order_id=client_order_id,
            ))
            safe_step(
                log,
                f"{error_prefix}, mas falha ao enviar alerta",
                lambda: send_telegram(
                    f"[LIVE] ERRO ao vender {symbol}: {error_message} | posicao mantida localmente para revisao"
                ),
            )
            return

        # A partir daqui a venda foi aceita pela exchange -- a posicao MUST
        # sair do estado local mesmo que o log/alerta abaixo falhe (evita um
        # "erro ao vender" falso quando a venda na verdade deu certo).
        exit_price = float(order.get("average") or order.get("price") or current_price or pos.entry_price)
        pnl     = (exit_price - pos.entry_price) * pos.quantity
        pnl_pct = (exit_price - pos.entry_price) / pos.entry_price * 100
        self._check_daily_reset()
        self._check_weekly_reset()
        self._check_monthly_reset()
        self.total_trades += 1
        self.realized_pnl += pnl
        self.daily_pnl    += pnl
        self.weekly_pnl   += pnl
        self.monthly_pnl  += pnl
        if pnl > 0:
            self.winning_trades += 1
        self._update_consecutive_losses(pnl)

        del self.positions[symbol]
        self._persist_state_with_retry(f"apos vender {symbol}")

        # A venda ja esta confirmada, a posicao ja foi removida e o PnL ja foi
        # contabilizado acima -- daqui pra baixo sao 3 acoes de observabilidade
        # independentes entre si. Cada uma isolada via safe_step para que uma
        # falhar (ex: trades.csv sem espaco em disco) nao impeca as outras
        # duas de rodar nem reapareca como se a venda tivesse falhado.
        prefix = f"Venda de {symbol} confirmada"
        safe_step(log, f"{prefix}, mas falha ao registrar trade", lambda: log_trade({
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
            "client_order_id": pos.client_order_id,
            "close_client_order_id": client_order_id,
        }))

        safe_step(log, f"{prefix}, mas falha ao registrar evento", lambda: log_event(
            "live_order_closed",
            mode=TRADING_MODE,
            symbol=symbol,
            side=pos.side,
            quantity=pos.quantity,
            exit_reason=reason,
            order_id=order["id"],
            client_order_id=client_order_id,
            pnl_usdt=round(pnl, 6),
            pnl_pct=round(pnl_pct, 4),
            daily_pnl=round(self.daily_pnl, 6),
        ))

        msg = f"[LIVE] VENDA {symbol} | {reason} | PnL ${pnl:+.4f} ({pnl_pct:+.2f}%) | ID={order['id']}"

        _notify_safe(prefix, msg)
