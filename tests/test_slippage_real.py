import pytest

from execution import liquidity, order_manager


def _book(asks=None, bids=None):
    return {"asks": asks or [], "bids": bids or []}


# ---------------------------------------------------------------- caminhada no book

def test_estimate_slippage_zero_when_order_fits_in_best_level(monkeypatch):
    # Ordem cabe inteira no topo do book -- preco medio == melhor preco.
    monkeypatch.setattr(liquidity, "fetch_order_book",
                        lambda s: _book(asks=[[100.0, 10.0], [101.0, 10.0]]))

    assert liquidity.estimate_slippage_pct("BTC/USDT", 500.0, "buy") == pytest.approx(0.0)


def test_estimate_slippage_grows_when_order_consumes_deeper_levels(monkeypatch):
    # $150: consome $100 a 100.0 (1 unidade) e $50 a 110.0 (0.4545 un).
    # preco medio = 150 / 1.4545 = 103.125 -> slippage 3.125%
    monkeypatch.setattr(liquidity, "fetch_order_book",
                        lambda s: _book(asks=[[100.0, 1.0], [110.0, 5.0]]))

    slip = liquidity.estimate_slippage_pct("ALT/USDT", 150.0, "buy")

    assert slip == pytest.approx(0.03125, rel=1e-3)


def test_estimate_slippage_uses_bids_when_selling(monkeypatch):
    # Venda caminha o lado bid, para baixo: $150 consome $100 a 100.0 e $50 a 90.0.
    # preco medio = 150 / (1.0 + 0.5556) = 96.43 -> slippage 3.57%
    monkeypatch.setattr(liquidity, "fetch_order_book",
                        lambda s: _book(bids=[[100.0, 1.0], [90.0, 5.0]]))

    slip = liquidity.estimate_slippage_pct("ALT/USDT", 150.0, "sell")

    assert slip == pytest.approx(0.0357, rel=1e-2)


def test_estimate_slippage_none_when_book_too_shallow(monkeypatch):
    # Book nao tem profundidade para a ordem inteira -- desconhecido, nunca 0.
    monkeypatch.setattr(liquidity, "fetch_order_book",
                        lambda s: _book(asks=[[100.0, 0.5]]))

    assert liquidity.estimate_slippage_pct("ALT/USDT", 1000.0, "buy") is None


def test_estimate_slippage_none_on_network_error(monkeypatch):
    monkeypatch.setattr(liquidity, "fetch_order_book",
                        lambda s: (_ for _ in ()).throw(RuntimeError("timeout")))

    assert liquidity.estimate_slippage_pct("BTC/USDT", 100.0, "buy") is None


# ---------------------------------------------------------------- uso em paper mode

def test_paper_slippage_uses_measured_value_when_above_floor(monkeypatch):
    monkeypatch.setattr(order_manager, "REAL_SLIPPAGE_ENABLED", True)
    monkeypatch.setattr(order_manager, "BACKTEST_SLIPPAGE_PCT", 0.0005)
    monkeypatch.setattr(order_manager, "estimate_slippage_pct",
                        lambda symbol, size, side: 0.008)   # 0.8%, book fino

    assert order_manager._paper_slippage_pct("ALT/USDT", 100.0, "buy") == 0.008


def test_paper_slippage_keeps_constant_as_floor(monkeypatch):
    # Par ultra-liquido: book mede quase zero, mas a constante representa o
    # slippage de latencia entre decidir e executar -- nao pode cair abaixo dela.
    monkeypatch.setattr(order_manager, "REAL_SLIPPAGE_ENABLED", True)
    monkeypatch.setattr(order_manager, "BACKTEST_SLIPPAGE_PCT", 0.0005)
    monkeypatch.setattr(order_manager, "estimate_slippage_pct",
                        lambda symbol, size, side: 0.00001)

    assert order_manager._paper_slippage_pct("BTC/USDT", 100.0, "buy") == 0.0005


def test_paper_slippage_falls_back_to_constant_when_unknown(monkeypatch):
    monkeypatch.setattr(order_manager, "REAL_SLIPPAGE_ENABLED", True)
    monkeypatch.setattr(order_manager, "BACKTEST_SLIPPAGE_PCT", 0.0005)
    monkeypatch.setattr(order_manager, "estimate_slippage_pct",
                        lambda symbol, size, side: None)

    assert order_manager._paper_slippage_pct("ALT/USDT", 100.0, "buy") == 0.0005


def test_paper_slippage_respects_disable_flag(monkeypatch):
    monkeypatch.setattr(order_manager, "REAL_SLIPPAGE_ENABLED", False)
    monkeypatch.setattr(order_manager, "BACKTEST_SLIPPAGE_PCT", 0.0005)
    monkeypatch.setattr(order_manager, "estimate_slippage_pct",
                        lambda symbol, size, side: pytest.fail("nao deve consultar o book"))

    assert order_manager._paper_slippage_pct("ALT/USDT", 100.0, "buy") == 0.0005
