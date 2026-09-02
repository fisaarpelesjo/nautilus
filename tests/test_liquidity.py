import pytest

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


def test_check_liquidity_blocks_on_corrupted_best_ask(monkeypatch):
    # Achado de auditoria: so bids[0][0] <= 0 era validado -- um best_ask
    # corrompido (0 ou negativo) fazia spread_pct sair negativo, passando
    # trivialmente pelo limite de spread em vez de virar "liquidez indisponivel"
    # como a corrupcao equivalente do lado bid ja tratava.
    monkeypatch.setattr(liquidity, "MAX_SPREAD_PCT_ENTRY", 0.005)
    monkeypatch.setattr(liquidity, "MIN_ORDERBOOK_DEPTH_USDT", 100.0)
    monkeypatch.setattr(liquidity, "fetch_order_book", lambda symbol, limit=20: _book(bid=100.0, ask=0.0))

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


def _book_multi_level(bid, levels):
    """Livro com varios niveis no lado ask -- `levels` e uma lista de
    (preco, qtd)."""
    return {"bids": [[bid, 10.0]], "asks": [list(level) for level in levels]}


def test_check_liquidity_no_regression_when_depth_concentrated_near_price(monkeypatch):
    # US2 -- profundidade toda perto do topo (padrao ja aprovado hoje):
    # continua aprovando, e depth_usdt reflete a soma dos niveis proximos.
    monkeypatch.setattr(liquidity, "MAX_SPREAD_PCT_ENTRY", 0.005)
    monkeypatch.setattr(liquidity, "MIN_ORDERBOOK_DEPTH_USDT", 1000.0)
    niveis = [(100.1, 4000.0), (100.15, 4000.0), (100.2, 4000.0)]  # todos < 0,5% de 100.1
    monkeypatch.setattr(liquidity, "fetch_order_book",
                         lambda symbol, limit=20: _book_multi_level(100.0, niveis))

    result = liquidity.check_liquidity("BTC/USDT", order_size_usdt=100.0)

    assert result.approved is True
    assert result.depth_usdt == pytest.approx(sum(p * q for p, q in niveis), rel=1e-6)


def test_check_liquidity_blocks_on_phantom_depth_far_from_price(monkeypatch):
    # US1 -- profundidade TOTAL acima do requisito, mas quase toda a mais de
    # MAX_SPREAD_PCT_ENTRY do melhor ask (padrao medido para ORCA/USDT em
    # research.md: ~90% da soma bruta fora da banda de 0,5%).
    monkeypatch.setattr(liquidity, "MAX_SPREAD_PCT_ENTRY", 0.005)
    monkeypatch.setattr(liquidity, "MIN_ORDERBOOK_DEPTH_USDT", 1000.0)
    niveis = [
        (100.1, 1.0),       # perto: ~100 USDT, bem abaixo do requisito de 1000
        (105.0, 1000.0),    # +4,9% do melhor ask -- fantasma, fora da banda
        (110.0, 1000.0),    # +9,8% -- fantasma
    ]
    monkeypatch.setattr(liquidity, "fetch_order_book",
                         lambda symbol, limit=20: _book_multi_level(100.0, niveis))

    result = liquidity.check_liquidity("BTC/USDT", order_size_usdt=100.0)

    assert result.approved is False
    assert "perto do preco" in result.reason
    assert "spread" not in result.reason
    assert result.depth_usdt < 1000.0  # so a perna perto do preco conta


def test_check_liquidity_and_slippage_agree_on_reachable_depth(monkeypatch):
    # US3 -- mesmo book de test_check_liquidity_blocks_on_phantom_depth_far_from_price:
    # check_liquidity so conta a perna perto do preco, e estimate_slippage_pct
    # nao trata a perna distante como imediatamente utilizavel (retorna
    # slippage acima da banda aceita para um volume que so cabe nela).
    monkeypatch.setattr(liquidity, "MAX_SPREAD_PCT_ENTRY", 0.005)
    monkeypatch.setattr(liquidity, "MIN_ORDERBOOK_DEPTH_USDT", 1000.0)
    niveis = [(100.1, 1.0), (105.0, 1000.0), (110.0, 1000.0)]
    monkeypatch.setattr(liquidity, "fetch_order_book",
                         lambda symbol, limit=20: _book_multi_level(100.0, niveis))

    liquidez = liquidity.check_liquidity("BTC/USDT", order_size_usdt=100.0)
    slippage = liquidity.estimate_slippage_pct("BTC/USDT", order_size_usdt=50_000.0, side="buy")

    assert liquidez.approved is False
    assert slippage is not None and slippage > liquidity.MAX_SPREAD_PCT_ENTRY
