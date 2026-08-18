import pandas as pd

from risk import correlation


def _df(closes):
    return pd.DataFrame({"close": closes})


def test_check_correlated_exposure_blocks_highly_correlated_pair(monkeypatch):
    monkeypatch.setattr(correlation, "MAX_POSITION_CORRELATION", 0.7)
    monkeypatch.setattr(correlation, "CORRELATION_LOOKBACK", 20)
    # Duas series de preco quase identicas (mesmos retornos) -- correlacao ~1.0.
    prices = [100 + i + (i % 3) for i in range(25)]
    books = {"NEW/USDT": _df(prices), "OPEN/USDT": _df(prices)}
    monkeypatch.setattr(correlation, "fetch_ohlcv", lambda symbol, timeframe: books[symbol])

    result = correlation.check_correlated_exposure("NEW/USDT", "4h", ["OPEN/USDT"])

    assert result == "OPEN/USDT"


def test_check_correlated_exposure_approves_uncorrelated_pair(monkeypatch):
    monkeypatch.setattr(correlation, "MAX_POSITION_CORRELATION", 0.7)
    monkeypatch.setattr(correlation, "CORRELATION_LOOKBACK", 20)
    rising = [100 + i for i in range(25)]
    # Serie alternando pra cima/baixo -- retornos com sinal oposto/nao relacionado.
    oscillating = [100 + (5 if i % 2 == 0 else -5) for i in range(25)]
    books = {"NEW/USDT": _df(rising), "OPEN/USDT": _df(oscillating)}
    monkeypatch.setattr(correlation, "fetch_ohlcv", lambda symbol, timeframe: books[symbol])

    result = correlation.check_correlated_exposure("NEW/USDT", "4h", ["OPEN/USDT"])

    assert result is None


def test_check_correlated_exposure_approves_when_no_open_positions(monkeypatch):
    result = correlation.check_correlated_exposure("NEW/USDT", "4h", [])
    assert result is None


def test_check_correlated_exposure_ignores_the_symbol_itself(monkeypatch):
    # Se o "candidato" ja estiver na lista de abertos (nao deveria acontecer no
    # caminho real, mas a funcao nao pode comparar um symbol com ele mesmo).
    result = correlation.check_correlated_exposure("BTC/USDT", "4h", ["BTC/USDT"])
    assert result is None


def test_check_correlated_exposure_fails_open_on_network_error(monkeypatch):
    # Falha ABERTA por comparacao de proposito -- ver docstring de
    # check_correlated_exposure. Nao bloqueia a entrada so porque o historico
    # de uma posicao ja aberta (nao a que esta sendo avaliada) falhou.
    monkeypatch.setattr(
        correlation, "fetch_ohlcv",
        lambda symbol, timeframe: (_ for _ in ()).throw(RuntimeError("timeout")),
    )

    result = correlation.check_correlated_exposure("NEW/USDT", "4h", ["OPEN/USDT"])

    assert result is None
