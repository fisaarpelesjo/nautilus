from utils.display import trade_result


def test_trade_result_handles_unknown_balance_without_raising():
    # balance=None acontece quando o saldo real nao pode ser obtido (ver
    # trading/position_lifecycle.py _current_balance) -- nao pode quebrar a
    # formatacao do painel do terminal.
    trade_result("stop loss  BTC/USDT", -10.0, -2.5, None)


def test_trade_result_formats_known_balance():
    trade_result("take profit  BTC/USDT", 15.0, 3.0, 1234.5)
