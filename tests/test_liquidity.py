from execution import liquidity


def _book(bid=100.0, ask=100.5, ask_qty=1000.0):
    return {"bids": [[bid, 10.0]], "asks": [[ask, ask_qty]]}


def test_check_liquidity_blocks_on_high_spread(monkeypatch):
    monkeypatch.setattr(liquidity, "MAX_SPREAD_PCT_ENTRY", 0.005)
    monkeypatch.setattr(liquidity, "MIN_ORDERBOOK_DEPTH_USDT", 100.0)
    # spread de 2% (100 -> 102), bem acima do limite de 0.5%
    monkeypatch.setattr(liquidity, "fetch_order_book", lambda symbol, limit=20: _book(bid=100.0, ask=102.0))

    result = liquidity.check_liquidity("BTC/USDT", order_size_usdt=50.0)

    assert result.approved is False
    assert "spread" in result.reason


def test_check_liquidity_blocks_on_low_depth(monkeypatch):
    monkeypatch.setattr(liquidity, "MAX_SPREAD_PCT_ENTRY", 0.005)
    monkeypatch.setattr(liquidity, "MIN_ORDERBOOK_DEPTH_USDT", 1000.0)
    # spread ok (0.1%), mas profundidade do ask muito baixa
    monkeypatch.setattr(liquidity, "fetch_order_book", lambda symbol, limit=20: _book(bid=100.0, ask=100.1, ask_qty=1.0))

    result = liquidity.check_liquidity("BTC/USDT", order_size_usdt=50.0)

    assert result.approved is False
    assert "profundidade" in result.reason


def test_check_liquidity_treats_network_failure_as_blocked(monkeypatch):
    monkeypatch.setattr(
        liquidity, "fetch_order_book",
        lambda symbol, limit=20: (_ for _ in ()).throw(RuntimeError("timeout")),
    )

    result = liquidity.check_liquidity("BTC/USDT", order_size_usdt=50.0)

    assert result.approved is False
    assert result.reason == "liquidez indisponivel"


def test_check_liquidity_approves_within_limits(monkeypatch):
    monkeypatch.setattr(liquidity, "MAX_SPREAD_PCT_ENTRY", 0.005)
    monkeypatch.setattr(liquidity, "MIN_ORDERBOOK_DEPTH_USDT", 100.0)
    monkeypatch.setattr(liquidity, "fetch_order_book", lambda symbol, limit=20: _book(bid=100.0, ask=100.1, ask_qty=1000.0))

    result = liquidity.check_liquidity("BTC/USDT", order_size_usdt=50.0)

    assert result.approved is True
    assert result.reason is None
    assert result.spread_pct > 0
    assert result.depth_usdt > 0
