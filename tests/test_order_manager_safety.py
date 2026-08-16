from datetime import datetime

import pytest

from execution import order_manager
from execution.order_manager import LIVE_CONFIRMATION_TEXT, OrderManager
from risk.manager import RiskLevels


def test_order_manager_does_not_initialize_exchange_in_paper(monkeypatch):
    monkeypatch.setattr(order_manager, "TRADING_MODE", "paper")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(
        order_manager,
        "get_exchange",
        lambda: pytest.fail("paper mode must not initialize live exchange"),
    )

    manager = OrderManager()

    assert manager.exchange is None


def test_live_mode_requires_explicit_confirmation(monkeypatch):
    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "fetch_balance", lambda: {"USDT": 1000.0})
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", "")
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})

    with pytest.raises(RuntimeError, match="Live trading bloqueado"):
        OrderManager()


def test_live_mode_requires_api_credentials(monkeypatch):
    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "fetch_balance", lambda: {"USDT": 1000.0})
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})

    with pytest.raises(RuntimeError, match="BINANCE_API_KEY"):
        OrderManager()


def test_generate_client_order_id_is_unique():
    ids = {order_manager._generate_client_order_id() for _ in range(200)}

    assert len(ids) == 200


def _paper_manager(monkeypatch, logged_trades=None):
    # log_trade SEMPRE mockado, mesmo quando o chamador nao quer inspecionar
    # os trades -- sem isso, qualquer teste que feche uma posicao escreve
    # de verdade em data/trades.csv (achado ao validar isolamento da spec
    # 008: a suite inteira alterava o arquivo real do bot a cada execucao).
    monkeypatch.setattr(order_manager, "TRADING_MODE", "paper")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: None)
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: None)
    monkeypatch.setattr(order_manager, "log_trade", lambda trade: (logged_trades if logged_trades is not None else []).append(trade))
    # Fee/slippage zerados por padrao (spec 010): a maioria dos testes deste
    # arquivo verifica contadores/circuit breaker/limites, nao aritmetica de
    # custo, e depende de valores exatos de entry/exit price (ex: pnl==0 num
    # trade "breakeven"). Testes que exercitam custo real sobrescrevem essas
    # duas variaveis explicitamente.
    monkeypatch.setattr(order_manager, "BACKTEST_FEE_RATE", 0.0)
    monkeypatch.setattr(order_manager, "BACKTEST_SLIPPAGE_PCT", 0.0)
    return OrderManager()


def test_paper_buy_assigns_unique_client_order_id(monkeypatch):
    manager = _paper_manager(monkeypatch)
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)

    manager.open_long("BTC/USDT", risk)

    pos = manager.get_position("BTC/USDT")
    assert pos.client_order_id
    assert pos.client_order_id.startswith("bot-")


def test_paper_sell_persists_client_order_id_on_trade(monkeypatch):
    logged_trades = []
    manager = _paper_manager(monkeypatch, logged_trades)
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)
    manager.open_long("BTC/USDT", risk)
    client_order_id = manager.get_position("BTC/USDT").client_order_id

    manager.close_position("BTC/USDT", "take_profit", current_price=110.0)

    assert logged_trades[0]["client_order_id"] == client_order_id


def test_paper_sell_removes_position_even_if_log_trade_fails(monkeypatch):
    # Regressao: contadores (total_trades, realized_pnl, daily_pnl) sao
    # incrementados antes do log_trade/log_event/telegram. Se essa ordem
    # ficasse invertida (posicao removida so depois de logar) e log_trade
    # falhasse, a posicao ficaria presa e o proximo ciclo contaria o mesmo
    # trade de novo, inflando os contadores.
    manager = _paper_manager(monkeypatch)
    monkeypatch.setattr(
        order_manager, "log_trade",
        lambda trade: (_ for _ in ()).throw(OSError("trades.csv sem espaco")),
    )
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)
    manager.open_long("BTC/USDT", risk)

    manager.close_position("BTC/USDT", "take_profit", current_price=110.0)

    assert not manager.has_position("BTC/USDT")
    assert manager.total_trades == 1

    # Uma segunda tentativa de fechar (ex: proximo ciclo re-avaliando o mesmo
    # symbol) nao deve fazer nada, pois a posicao ja nao existe mais.
    manager.close_position("BTC/USDT", "take_profit", current_price=110.0)
    assert manager.total_trades == 1


def test_paper_buy_applies_slippage_to_entry_price(monkeypatch):
    manager = _paper_manager(monkeypatch)
    monkeypatch.setattr(order_manager, "BACKTEST_SLIPPAGE_PCT", 0.0005)
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)

    manager.open_long("BTC/USDT", risk)

    pos = manager.get_position("BTC/USDT")
    assert pos.entry_price == pytest.approx(100.0 * 1.0005)


def test_paper_sell_applies_slippage_to_exit_price_with_current_price(monkeypatch):
    logged_trades = []
    manager = _paper_manager(monkeypatch, logged_trades)
    monkeypatch.setattr(order_manager, "BACKTEST_SLIPPAGE_PCT", 0.0005)
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)
    manager.open_long("BTC/USDT", risk)

    manager.close_position("BTC/USDT", "sinal de venda", current_price=110.0)

    assert logged_trades[0]["exit_price"] == pytest.approx(110.0 * (1 - 0.0005))


def test_paper_sell_applies_slippage_to_fallback_stop_take_price(monkeypatch):
    # backtesting/engine.py aplica slippage tambem quando a saida e por
    # stop/take (nao so por sinal com current_price explicito) -- mesmo
    # tratamento aqui, senao a paridade com o backtest fica so parcial.
    logged_trades = []
    manager = _paper_manager(monkeypatch, logged_trades)
    monkeypatch.setattr(order_manager, "BACKTEST_SLIPPAGE_PCT", 0.0005)
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)
    manager.open_long("BTC/USDT", risk)

    manager.close_position("BTC/USDT", "take_profit")  # sem current_price -> usa pos.take_profit

    assert logged_trades[0]["exit_price"] == pytest.approx(110.0 * (1 - 0.0005))


def test_paper_buy_sell_price_unchanged_when_slippage_zero(monkeypatch):
    # FR-008: BACKTEST_SLIPPAGE_PCT=0 (ja o default de _paper_manager) nao
    # pode mudar o preco de entrada/saida em relacao ao comportamento anterior
    # a esta spec.
    logged_trades = []
    manager = _paper_manager(monkeypatch, logged_trades)
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)

    manager.open_long("BTC/USDT", risk)
    assert manager.get_position("BTC/USDT").entry_price == 100.0

    manager.close_position("BTC/USDT", "sinal de venda", current_price=110.0)
    assert logged_trades[0]["exit_price"] == 110.0


def test_paper_buy_deducts_fee_from_balance(monkeypatch):
    manager = _paper_manager(monkeypatch)
    monkeypatch.setattr(order_manager, "BACKTEST_FEE_RATE", 0.001)
    saldo_inicial = manager.paper_balance_usdt
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)

    manager.open_long("BTC/USDT", risk)

    notional = 1.0 * 100.0
    custo_esperado = notional + notional * 0.001
    assert manager.paper_balance_usdt == pytest.approx(saldo_inicial - custo_esperado)


def test_paper_sell_deducts_fee_from_proceeds_and_pnl(monkeypatch):
    logged_trades = []
    manager = _paper_manager(monkeypatch, logged_trades)
    monkeypatch.setattr(order_manager, "BACKTEST_FEE_RATE", 0.001)
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)
    manager.open_long("BTC/USDT", risk)
    saldo_apos_compra = manager.paper_balance_usdt

    manager.close_position("BTC/USDT", "sinal de venda", current_price=110.0)

    gross_exit = 1.0 * 110.0
    proceeds_esperado = gross_exit - gross_exit * 0.001
    assert manager.paper_balance_usdt == pytest.approx(saldo_apos_compra + proceeds_esperado)

    entrada_custo = 100.0 + 100.0 * 0.001
    pnl_esperado = proceeds_esperado - entrada_custo
    assert logged_trades[0]["pnl_usdt"] == pytest.approx(pnl_esperado)


def test_paper_buy_blocks_when_balance_covers_notional_but_not_fee(monkeypatch):
    manager = _paper_manager(monkeypatch)
    monkeypatch.setattr(order_manager, "BACKTEST_FEE_RATE", 0.001)
    manager.paper_balance_usdt = 100.0  # cobre so o nocional, nao a taxa
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)

    manager.open_long("BTC/USDT", risk)

    assert not manager.has_position("BTC/USDT")
    assert manager.paper_balance_usdt == 100.0  # nada foi debitado


def test_paper_buy_sell_cost_unchanged_when_fee_zero(monkeypatch):
    # FR-008: BACKTEST_FEE_RATE=0 (ja o default de _paper_manager) nao pode
    # mudar o custo/proceeds em relacao ao comportamento anterior a esta spec.
    manager = _paper_manager(monkeypatch)
    saldo_inicial = manager.paper_balance_usdt
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)

    manager.open_long("BTC/USDT", risk)

    assert manager.paper_balance_usdt == pytest.approx(saldo_inicial - 100.0)


def test_paper_sell_uses_fee_actually_paid_at_entry_not_current_rate(monkeypatch):
    # Achado de code-review (spec 010): BACKTEST_FEE_RATE e uma constante de
    # modulo lida no processo -- se o operador editar o .env e reiniciar o bot
    # com uma posicao ja aberta, a taxa "atual" no momento da venda pode nao
    # ser mais a taxa realmente paga na compra. pos.entry_fee (persistido em
    # Position/state.json) precisa ser reusado, nao recalculado com a taxa nova.
    logged_trades = []
    manager = _paper_manager(monkeypatch, logged_trades)
    monkeypatch.setattr(order_manager, "BACKTEST_FEE_RATE", 0.001)
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)
    manager.open_long("BTC/USDT", risk)

    # Simula reinicio do bot com a taxa mudada no .env (0.001 -> 0.01) antes
    # da posicao fechar.
    monkeypatch.setattr(order_manager, "BACKTEST_FEE_RATE", 0.01)
    manager.close_position("BTC/USDT", "sinal de venda", current_price=110.0)

    gross_exit = 1.0 * 110.0
    proceeds_com_taxa_nova = gross_exit - gross_exit * 0.01  # taxa de saida usa a taxa atual mesmo
    entrada_custo_taxa_original = 100.0 + 100.0 * 0.001  # mas a taxa de entrada tem que ser a original
    pnl_esperado = proceeds_com_taxa_nova - entrada_custo_taxa_original
    assert logged_trades[0]["pnl_usdt"] == pytest.approx(pnl_esperado)


def test_paper_trade_pnl_pct_matches_backtest_engine_for_same_price_pair(monkeypatch):
    # SC-001: paridade percentual com simulate_backtest() para o mesmo par de
    # precos de mercado e mesmos fee_rate/slippage_pct -- ver research.md
    # sobre por que a comparacao e percentual, nao em dolar absoluto (as duas
    # convencoes de sizing -- nocional fixo no backtest, quantidade fixa aqui
    # -- produzem o mesmo pnl_pct, nao o mesmo pnl em dolar).
    from backtesting.engine import _close_trade

    fee_rate, slippage_pct = 0.001, 0.0005
    market_entry, market_exit = 100.0, 110.0

    logged_trades = []
    manager = _paper_manager(monkeypatch, logged_trades)
    monkeypatch.setattr(order_manager, "BACKTEST_FEE_RATE", fee_rate)
    monkeypatch.setattr(order_manager, "BACKTEST_SLIPPAGE_PCT", slippage_pct)
    risk = RiskLevels(entry_price=market_entry, stop_loss=90.0, take_profit=120.0, quantity=1.0, risk_usdt=5.0)
    manager.open_long("BTC/USDT", risk)
    manager.close_position("BTC/USDT", "sinal de venda", current_price=market_exit)

    paper_entry_cost = market_entry * (1 + slippage_pct) * (1 + fee_rate)
    paper_pnl_pct = logged_trades[0]["pnl_usdt"] / paper_entry_cost * 100

    # backtesting/engine.py fixa um valor nocional em dolar (order_size) e deriva
    # a quantidade a partir dele (quantity = order_size / entry_price_com_slippage)
    # -- convencao diferente da do paper (quantidade fixa, nocional deriva), mas
    # pnl_pct e invariante a essa escolha (fee/slippage sao proporcionais). Usar
    # order_size=100 aqui e so um valor de conveniencia, nao precisa bater com
    # market_entry.
    order_size = 100.0
    backtest_entry_price = market_entry * (1 + slippage_pct)
    backtest_quantity = order_size / backtest_entry_price
    backtest_entry_fee = order_size * fee_rate
    backtest_entry_cost = order_size + backtest_entry_fee
    _, backtest_trade = _close_trade(
        capital=1000.0, entry_price=backtest_entry_price, exit_price=market_exit * (1 - slippage_pct),
        quantity=backtest_quantity, entry_cost=backtest_entry_cost, entry_fee=backtest_entry_fee,
        entry_time=None, exit_time=None, exit_reason="teste", fee_rate=fee_rate,
    )

    assert paper_pnl_pct == pytest.approx(backtest_trade.pnl_pct, rel=1e-6)


def _open_and_close(manager, symbol, entry_price, exit_price, reason="stop_loss"):
    risk = RiskLevels(entry_price=entry_price, stop_loss=entry_price * 0.9, take_profit=entry_price * 1.1,
                       quantity=1.0, risk_usdt=5.0)
    manager.open_long(symbol, risk)
    manager.close_position(symbol, reason, current_price=exit_price)


def test_consecutive_losses_increments_on_loss_and_resets_on_win(monkeypatch):
    manager = _paper_manager(monkeypatch)

    _open_and_close(manager, "BTC/USDT", 100.0, 90.0)  # prejuizo
    assert manager.consecutive_losses == 1

    _open_and_close(manager, "BTC/USDT", 100.0, 90.0)  # prejuizo
    assert manager.consecutive_losses == 2

    _open_and_close(manager, "BTC/USDT", 100.0, 110.0)  # lucro
    assert manager.consecutive_losses == 0


def test_consecutive_losses_unaffected_by_breakeven_trade(monkeypatch):
    manager = _paper_manager(monkeypatch)

    _open_and_close(manager, "BTC/USDT", 100.0, 90.0)  # prejuizo
    assert manager.consecutive_losses == 1

    _open_and_close(manager, "BTC/USDT", 100.0, 100.0)  # pnl == 0, nao e vitoria
    assert manager.consecutive_losses == 1
    assert manager.circuit_breaker_active is False


def test_circuit_breaker_activates_at_max_consecutive_losses(monkeypatch):
    monkeypatch.setattr(order_manager, "MAX_CONSECUTIVE_LOSSES", 2)
    manager = _paper_manager(monkeypatch)

    _open_and_close(manager, "BTC/USDT", 100.0, 90.0)
    assert manager.circuit_breaker_active is False

    _open_and_close(manager, "BTC/USDT", 100.0, 90.0)
    assert manager.circuit_breaker_active is True


def test_circuit_breaker_deactivates_when_counter_resets(monkeypatch):
    monkeypatch.setattr(order_manager, "MAX_CONSECUTIVE_LOSSES", 2)
    manager = _paper_manager(monkeypatch)

    _open_and_close(manager, "BTC/USDT", 100.0, 90.0)
    _open_and_close(manager, "BTC/USDT", 100.0, 90.0)
    assert manager.circuit_breaker_active is True

    _open_and_close(manager, "BTC/USDT", 100.0, 110.0)  # lucro reseta
    assert manager.circuit_breaker_active is False
    assert manager.consecutive_losses == 0


def _freeze_current_periods(manager):
    # _restore_state() sai cedo quando load_state() retorna {} (instalacao
    # nova), deixando *_reset_date="" -- na producao isso e inofensivo (a
    # primeira chamada de _check_*_reset so reseta um pnl que ja e 0), mas
    # testes que setam pnl manualmente ANTES de chamar is_*_limit_hit()
    # precisam fixar a data do periodo corrente, senao o reset dispara e
    # zera o pnl que acabamos de setar antes da comparacao rodar.
    manager.daily_reset_date = datetime.now().strftime("%Y-%m-%d")
    manager.weekly_reset_date = datetime.now().strftime("%G-W%V")
    manager.monthly_reset_date = datetime.now().strftime("%Y-%m")


def test_is_daily_limit_hit_uses_real_reference_balance_not_hardcoded_1000(monkeypatch):
    # Regressao: is_daily_limit_hit() usava DAILY_DRAWDOWN_LIMIT * 1000.0 (saldo
    # paper default hardcoded), nao o saldo real da conta. Com saldo de
    # referencia real de $5000 e limite de 5%, o limite deve ser $250, nao $50.
    monkeypatch.setattr(order_manager, "DAILY_DRAWDOWN_LIMIT", 0.05)
    manager = _paper_manager(monkeypatch)
    _freeze_current_periods(manager)
    manager.daily_reference_balance = 5000.0

    manager.daily_pnl = -100.0  # acima de $50 (bug antigo) mas abaixo de $250 (correto)
    assert manager.is_daily_limit_hit() is False

    manager.daily_pnl = -260.0
    assert manager.is_daily_limit_hit() is True


def test_weekly_and_monthly_limit_hit_use_their_own_reference_balance(monkeypatch):
    monkeypatch.setattr(order_manager, "WEEKLY_DRAWDOWN_LIMIT", 0.10)
    monkeypatch.setattr(order_manager, "MONTHLY_DRAWDOWN_LIMIT", 0.20)
    manager = _paper_manager(monkeypatch)
    _freeze_current_periods(manager)
    manager.weekly_reference_balance = 5000.0
    manager.monthly_reference_balance = 5000.0

    manager.weekly_pnl = -400.0
    assert manager.is_weekly_limit_hit() is False
    manager.weekly_pnl = -600.0
    assert manager.is_weekly_limit_hit() is True

    manager.monthly_pnl = -900.0
    assert manager.is_monthly_limit_hit() is False
    manager.monthly_pnl = -1100.0
    assert manager.is_monthly_limit_hit() is True


def test_is_daily_limit_hit_blocks_conservatively_when_reference_balance_never_captured(monkeypatch):
    # Achado de code-review: se fetch_balance() falhar uma vez (ex: no
    # startup), o saldo de referencia ficava travado em 0.0 pelo resto do
    # periodo -- limite = 0 faz QUALQUER prejuizo parecer "limite atingido",
    # silenciosamente. Deve reconsultar a cada chamada enquanto for
    # desconhecido, e bloquear conservador (nao limite=0) se continuar
    # indisponivel. fetch_balance ja falha DESDE a construcao, para o cache
    # de saldo (ver _reference_balance_cache) nunca ser populado.
    manager = _live_manager(
        monkeypatch, exchange=object(),
        fetch_balance_fn=lambda: (_ for _ in ()).throw(RuntimeError("timeout")),
    )
    _freeze_current_periods(manager)

    assert manager.is_daily_limit_hit() is True

    monkeypatch.setattr(order_manager, "fetch_balance", lambda: {"USDT": 5000.0})
    manager.daily_pnl = -10.0
    assert manager.is_daily_limit_hit() is False
    assert manager.daily_reference_balance == 5000.0


def test_reference_balance_fetch_is_cached_across_coincident_period_rollovers(monkeypatch):
    # Achado de code-review: numa segunda-feira (diario + semanal viram
    # juntos), is_daily_limit_hit/is_weekly_limit_hit/is_monthly_limit_hit
    # cada um chamava fetch_balance() de novo -- ate 3 chamadas de rede na
    # mesma checagem de entrada quando uma so bastaria.
    manager = _live_manager(monkeypatch, exchange=object())
    calls = []
    monkeypatch.setattr(order_manager, "fetch_balance", lambda: (calls.append(1), {"USDT": 3000.0})[1])
    manager._reference_balance_cache = None  # invalida o cache aquecido na construcao

    # Forca os 3 periodos a virarem juntos.
    manager.daily_reset_date = "2000-01-01"
    manager.weekly_reset_date = "1999-W01"
    manager.monthly_reset_date = "1999-01"

    manager.is_daily_limit_hit()
    manager.is_weekly_limit_hit()
    manager.is_monthly_limit_hit()

    assert len(calls) == 1


def test_daily_weekly_monthly_counters_reset_independently(monkeypatch):
    manager = _paper_manager(monkeypatch)
    _freeze_current_periods(manager)
    manager.daily_pnl = -10.0
    manager.weekly_pnl = -20.0
    manager.monthly_pnl = -30.0

    # Forca virada so do dia -- semana e mes continuam no periodo corrente.
    manager.daily_reset_date = "2000-01-01"

    manager._check_daily_reset()

    assert manager.daily_pnl == 0.0
    assert manager.weekly_pnl == -20.0
    assert manager.monthly_pnl == -30.0


def test_sell_accumulates_weekly_and_monthly_pnl_alongside_daily(monkeypatch):
    manager = _paper_manager(monkeypatch)

    _open_and_close(manager, "BTC/USDT", 100.0, 90.0)  # prejuizo de 10

    assert manager.daily_pnl == -10.0
    assert manager.weekly_pnl == -10.0
    assert manager.monthly_pnl == -10.0


def test_record_reconciliation_persists_and_is_restored(monkeypatch):
    saved_states = []
    monkeypatch.setattr(order_manager, "TRADING_MODE", "paper")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: saved_states.append(state))

    manager = OrderManager()
    manager.record_reconciliation("mismatch", "2026-08-13T00:00:00", ["BTC/USDT: divergente"])

    assert manager.last_reconciliation["status"] == "mismatch"
    assert saved_states[-1]["last_reconciliation"]["status"] == "mismatch"

    monkeypatch.setattr(order_manager, "load_state", lambda: saved_states[-1])
    restored = OrderManager()
    assert restored.last_reconciliation["status"] == "mismatch"


def test_live_sell_keeps_local_position_when_exchange_call_fails(monkeypatch):
    class _FailingExchange:
        def create_market_sell_order(self, symbol, quantity, params=None):
            raise RuntimeError("network timeout")

    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "fetch_balance", lambda: {"USDT": 1000.0})
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: None)
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: None)
    monkeypatch.setattr(order_manager, "get_exchange", lambda: _FailingExchange())

    manager = OrderManager()
    manager.positions["BTC/USDT"] = order_manager.Position(
        symbol="BTC/USDT", side="long", entry_price=100.0, quantity=1.0,
        stop_loss=95.0, take_profit=110.0,
    )

    manager.close_position("BTC/USDT", "stop_loss")

    assert manager.has_position("BTC/USDT")


def test_live_sell_error_alert_still_sent_when_log_event_fails(monkeypatch):
    # Regressao: no ramo de erro (a chamada a exchange falhou), log_event e
    # send_telegram tambem precisam estar isolados um do outro -- nao so no
    # caminho de sucesso.
    class _FailingExchange:
        def create_market_sell_order(self, symbol, quantity, params=None):
            raise RuntimeError("network timeout")

    sent_messages = []
    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "fetch_balance", lambda: {"USDT": 1000.0})
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: None)
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: sent_messages.append(msg))
    monkeypatch.setattr(order_manager, "get_exchange", lambda: _FailingExchange())
    monkeypatch.setattr(
        order_manager, "log_event",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("disk full")),
    )

    manager = OrderManager()
    manager.positions["BTC/USDT"] = order_manager.Position(
        symbol="BTC/USDT", side="long", entry_price=100.0, quantity=1.0,
        stop_loss=95.0, take_profit=110.0,
    )

    manager.close_position("BTC/USDT", "stop_loss")  # nao deve levantar

    assert manager.has_position("BTC/USDT")
    assert any("ERRO ao vender" in m for m in sent_messages)


def test_live_buy_error_alert_still_sent_when_log_event_fails(monkeypatch):
    # Espelha test_live_sell_error_alert_still_sent_when_log_event_fails: o
    # mesmo isolamento no ramo de erro se aplica a _live_buy.
    class _FailingExchange:
        def create_market_buy_order(self, symbol, quantity, params=None):
            raise RuntimeError("network timeout")

    sent_messages = []
    manager = _live_manager(monkeypatch, _FailingExchange())
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: sent_messages.append(msg))
    monkeypatch.setattr(
        order_manager, "log_event",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("disk full")),
    )
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)

    manager.open_long("BTC/USDT", risk)  # nao deve levantar

    assert not manager.has_position("BTC/USDT")
    assert any("ERRO ao comprar" in m for m in sent_messages)


def _live_manager(monkeypatch, exchange, log_trade=None, fetch_balance_fn=lambda: {"USDT": 1000.0}):
    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "fetch_balance", fetch_balance_fn)
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: None)
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: None)
    monkeypatch.setattr(order_manager, "get_exchange", lambda: exchange)
    # log_trade SEMPRE mockado (mesmo padrao de _paper_manager acima) --
    # sem isso, um teste que fecha posicao escreve de verdade em
    # data/trades.csv.
    monkeypatch.setattr(order_manager, "log_trade", log_trade if log_trade is not None else (lambda trade: None))
    return OrderManager()


def test_live_buy_does_not_create_position_when_exchange_call_fails(monkeypatch):
    class _FailingExchange:
        def create_market_buy_order(self, symbol, quantity, params=None):
            raise RuntimeError("network timeout")

    manager = _live_manager(monkeypatch, _FailingExchange())
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)

    manager.open_long("BTC/USDT", risk)

    assert not manager.has_position("BTC/USDT")


def test_live_buy_reuses_client_order_id_across_retries(monkeypatch):
    calls = []

    class _FailingExchange:
        def create_market_buy_order(self, symbol, quantity, params=None):
            calls.append(params.get("newClientOrderId"))
            raise RuntimeError("network timeout")

    manager = _live_manager(monkeypatch, _FailingExchange())
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)

    manager.open_long("BTC/USDT", risk)
    manager.open_long("BTC/USDT", risk)

    assert len(calls) == 2
    assert calls[0] is not None
    assert calls[0] == calls[1]


def test_live_buy_clears_pending_id_and_creates_position_on_success(monkeypatch):
    class _SucceedingExchange:
        def create_market_buy_order(self, symbol, quantity, params=None):
            return {"id": "abc123"}

    manager = _live_manager(monkeypatch, _SucceedingExchange())
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)

    manager.open_long("BTC/USDT", risk)

    assert manager.has_position("BTC/USDT")
    assert "BTC/USDT" not in manager.pending_open_client_order_ids
    assert manager.get_position("BTC/USDT").client_order_id is not None


def test_persist_state_with_retry_succeeds_on_second_attempt(monkeypatch):
    calls = []

    def _flaky_save_state(state):
        calls.append(state)
        if len(calls) == 1:
            raise OSError("disk busy")

    monkeypatch.setattr(order_manager, "TRADING_MODE", "paper")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", _flaky_save_state)

    manager = OrderManager()
    manager._persist_state_with_retry("teste")

    assert len(calls) == 2


def test_persist_state_with_retry_gives_up_after_all_attempts(monkeypatch, caplog):
    monkeypatch.setattr(order_manager, "TRADING_MODE", "paper")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})

    def _always_fails(state):
        raise OSError("disk full")

    monkeypatch.setattr(order_manager, "save_state", _always_fails)

    manager = OrderManager()
    manager._persist_state_with_retry("teste")  # nao deve levantar


def test_live_sell_does_not_abort_when_first_persist_fails(monkeypatch):
    calls = []

    class _SucceedingExchange:
        def create_market_sell_order(self, symbol, quantity, params=None):
            calls.append(params.get("newClientOrderId"))
            return {"id": "abc123", "average": 100.0}

    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "fetch_balance", lambda: {"USDT": 1000.0})
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: (_ for _ in ()).throw(OSError("disk busy")))
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: None)
    monkeypatch.setattr(order_manager, "get_exchange", lambda: _SucceedingExchange())
    monkeypatch.setattr(order_manager, "log_trade", lambda trade: None)

    manager = OrderManager()
    manager.positions["BTC/USDT"] = order_manager.Position(
        symbol="BTC/USDT", side="long", entry_price=100.0, quantity=1.0,
        stop_loss=95.0, take_profit=110.0,
    )

    manager.close_position("BTC/USDT", "stop_loss")  # nao deve levantar

    assert len(calls) == 1
    assert not manager.has_position("BTC/USDT")


def test_live_sell_reuses_client_order_id_across_retries(monkeypatch):
    calls = []

    class _FailingExchange:
        def create_market_sell_order(self, symbol, quantity, params=None):
            calls.append(params.get("newClientOrderId"))
            raise RuntimeError("network timeout")

    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "fetch_balance", lambda: {"USDT": 1000.0})
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: None)
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: None)
    monkeypatch.setattr(order_manager, "get_exchange", lambda: _FailingExchange())

    manager = OrderManager()
    manager.positions["BTC/USDT"] = order_manager.Position(
        symbol="BTC/USDT", side="long", entry_price=100.0, quantity=1.0,
        stop_loss=95.0, take_profit=110.0,
    )

    manager.close_position("BTC/USDT", "stop_loss")
    manager.close_position("BTC/USDT", "stop_loss")

    assert len(calls) == 2
    assert calls[0] is not None
    assert calls[0] == calls[1]


def test_live_sell_updates_pnl_and_trade_counters(monkeypatch):
    class _SucceedingExchange:
        def create_market_sell_order(self, symbol, quantity, params=None):
            return {"id": "abc123", "average": 90.0}

    logged_trades = []
    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "fetch_balance", lambda: {"USDT": 1000.0})
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: None)
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: None)
    monkeypatch.setattr(order_manager, "get_exchange", lambda: _SucceedingExchange())
    monkeypatch.setattr(order_manager, "log_trade", lambda trade: logged_trades.append(trade))

    manager = OrderManager()
    manager.positions["BTC/USDT"] = order_manager.Position(
        symbol="BTC/USDT", side="long", entry_price=100.0, quantity=1.0,
        stop_loss=90.0, take_profit=110.0,
    )

    manager.close_position("BTC/USDT", "Stop Loss", current_price=90.0)

    # entrada 100, saida 90 (do fill da ordem), qty 1 -> prejuizo de 10
    assert manager.total_trades == 1
    assert manager.winning_trades == 0
    assert manager.realized_pnl == -10.0
    assert manager.daily_pnl == -10.0
    assert logged_trades[0]["pnl_usdt"] == -10.0
    assert logged_trades[0]["exit_price"] == 90.0


def test_live_sell_records_distinct_open_and_close_client_order_ids(monkeypatch):
    class _SucceedingExchange:
        def create_market_sell_order(self, symbol, quantity, params=None):
            return {"id": "abc123", "average": 90.0}

    logged_trades = []
    manager = _live_manager(monkeypatch, _SucceedingExchange(), log_trade=logged_trades.append)
    manager.positions["BTC/USDT"] = order_manager.Position(
        symbol="BTC/USDT", side="long", entry_price=100.0, quantity=1.0,
        stop_loss=90.0, take_profit=110.0, client_order_id="bot-open-id",
    )

    manager.close_position("BTC/USDT", "Stop Loss", current_price=90.0)

    assert logged_trades[0]["client_order_id"] == "bot-open-id"
    assert logged_trades[0]["close_client_order_id"] is not None
    assert logged_trades[0]["close_client_order_id"] != "bot-open-id"


def test_live_sell_records_balance_after_in_logged_trade(monkeypatch):
    # Regressao (achado de code-review): _live_sell nao incluia
    # balance_after no log_trade (diferente de _paper_sell, que ja
    # incluia) -- backtesting/performance_charts.py depende desse campo
    # para a curva de capital/drawdown; sem ele, todo trade live vira
    # $0.0 na curva, silenciosamente.
    class _SucceedingExchange:
        def create_market_sell_order(self, symbol, quantity, params=None):
            return {"id": "abc123", "average": 90.0}

    logged_trades = []
    manager = _live_manager(
        monkeypatch, _SucceedingExchange(), log_trade=logged_trades.append,
        fetch_balance_fn=lambda: {"USDT": 950.0},
    )
    manager.positions["BTC/USDT"] = order_manager.Position(
        symbol="BTC/USDT", side="long", entry_price=100.0, quantity=1.0,
        stop_loss=90.0, take_profit=110.0,
    )

    manager.close_position("BTC/USDT", "Stop Loss", current_price=90.0)

    assert logged_trades[0]["balance_after"] == 950.0


def test_live_sell_falls_back_to_current_price_when_order_has_no_fill_price(monkeypatch):
    class _SucceedingExchangeNoFillPrice:
        def create_market_sell_order(self, symbol, quantity, params=None):
            return {"id": "abc123"}  # sem "average"/"price"

    logged_trades = []
    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "fetch_balance", lambda: {"USDT": 1000.0})
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: None)
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: None)
    monkeypatch.setattr(order_manager, "get_exchange", lambda: _SucceedingExchangeNoFillPrice())
    monkeypatch.setattr(order_manager, "log_trade", lambda trade: logged_trades.append(trade))

    manager = OrderManager()
    manager.positions["BTC/USDT"] = order_manager.Position(
        symbol="BTC/USDT", side="long", entry_price=100.0, quantity=1.0,
        stop_loss=90.0, take_profit=110.0,
    )

    manager.close_position("BTC/USDT", "Take Profit", current_price=115.0)

    assert logged_trades[0]["exit_price"] == 115.0
    assert logged_trades[0]["pnl_usdt"] == 15.0


def test_live_sell_removes_position_even_if_post_success_logging_fails(monkeypatch):
    class _SucceedingExchange:
        def create_market_sell_order(self, symbol, quantity, params=None):
            return {"id": "abc123"}

    sent_messages = []
    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "fetch_balance", lambda: {"USDT": 1000.0})
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: None)
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: sent_messages.append(msg))
    monkeypatch.setattr(order_manager, "get_exchange", lambda: _SucceedingExchange())
    monkeypatch.setattr(order_manager, "log_trade", lambda trade: None)
    monkeypatch.setattr(
        order_manager, "log_event",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("disk full")),
    )

    manager = OrderManager()
    manager.positions["BTC/USDT"] = order_manager.Position(
        symbol="BTC/USDT", side="long", entry_price=100.0, quantity=1.0,
        stop_loss=95.0, take_profit=110.0,
    )

    manager.close_position("BTC/USDT", "stop_loss")

    assert not manager.has_position("BTC/USDT")
    assert not any("ERRO ao vender" in m for m in sent_messages)
    # log_event falhou (isolado no seu proprio try/except), mas isso nao pode
    # impedir o alerta de telegram de rodar -- sao acoes independentes.
    assert any("VENDA BTC/USDT" in m for m in sent_messages)


def test_live_sell_log_trade_failure_does_not_block_event_and_alert(monkeypatch):
    class _SucceedingExchange:
        def create_market_sell_order(self, symbol, quantity, params=None):
            return {"id": "abc123", "average": 90.0}

    sent_messages = []
    logged_events = []
    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "fetch_balance", lambda: {"USDT": 1000.0})
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: None)
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: sent_messages.append(msg))
    monkeypatch.setattr(order_manager, "get_exchange", lambda: _SucceedingExchange())
    monkeypatch.setattr(
        order_manager, "log_trade",
        lambda trade: (_ for _ in ()).throw(OSError("trades.csv sem espaco")),
    )
    monkeypatch.setattr(order_manager, "log_event", lambda event, **kwargs: logged_events.append(event))

    manager = OrderManager()
    manager.positions["BTC/USDT"] = order_manager.Position(
        symbol="BTC/USDT", side="long", entry_price=100.0, quantity=1.0,
        stop_loss=95.0, take_profit=110.0,
    )

    manager.close_position("BTC/USDT", "stop_loss")

    assert not manager.has_position("BTC/USDT")
    assert "live_order_closed" in logged_events
    assert any("VENDA BTC/USDT" in m for m in sent_messages)
