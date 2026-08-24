import pytest

from config import settings


def test_validate_config_accepts_current_defaults():
    settings.validate_config()


def test_validate_config_rejects_invalid_trading_mode(monkeypatch):
    monkeypatch.setattr(settings, "TRADING_MODE", "demo")

    with pytest.raises(ValueError, match="TRADING_MODE"):
        settings.validate_config()


def test_validate_config_rejects_invalid_pair(monkeypatch):
    monkeypatch.setattr(settings, "PAIRS", ["BTCUSDT"])

    with pytest.raises(ValueError, match="PAIRS invalidos"):
        settings.validate_config()


def test_validate_config_rejects_max_consecutive_losses_below_one(monkeypatch):
    monkeypatch.setattr(settings, "MAX_CONSECUTIVE_LOSSES", 0)

    with pytest.raises(ValueError, match="MAX_CONSECUTIVE_LOSSES"):
        settings.validate_config()


def test_validate_config_rejects_edge_min_trades_below_one(monkeypatch):
    monkeypatch.setattr(settings, "EDGE_MIN_TRADES", 0)

    with pytest.raises(ValueError, match="EDGE_MIN_TRADES"):
        settings.validate_config()


def test_validate_config_rejects_weekly_limit_below_daily(monkeypatch):
    monkeypatch.setattr(settings, "DAILY_DRAWDOWN_LIMIT", 0.10)
    monkeypatch.setattr(settings, "WEEKLY_DRAWDOWN_LIMIT", 0.05)

    with pytest.raises(ValueError, match="WEEKLY_DRAWDOWN_LIMIT"):
        settings.validate_config()


def test_validate_config_rejects_monthly_limit_below_weekly(monkeypatch):
    monkeypatch.setattr(settings, "WEEKLY_DRAWDOWN_LIMIT", 0.10)
    monkeypatch.setattr(settings, "MONTHLY_DRAWDOWN_LIMIT", 0.05)

    with pytest.raises(ValueError, match="MONTHLY_DRAWDOWN_LIMIT"):
        settings.validate_config()


def test_validate_config_requires_confirmation_for_live(monkeypatch):
    monkeypatch.setattr(settings, "TRADING_MODE", "live")
    monkeypatch.setattr(settings, "LIVE_TRADING_CONFIRMATION", "")
    monkeypatch.setattr(settings, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(settings, "BINANCE_API_SECRET", "secret")

    with pytest.raises(ValueError, match="LIVE_TRADING_CONFIRMATION"):
        settings.validate_config()


# ------------------------------------------------------ spec 023: multi-mercado

def test_pairs_continua_exigindo_formato_cripto(monkeypatch):
    # A lista de OPERACAO nao pode ser afrouxada: e ela que alimenta o loop ao
    # vivo, que so sabe operar cripto. Afrouxar aqui reabriria o caminho que
    # FR-007 fecha.
    monkeypatch.setattr(settings, "PAIRS", ["BTC/USDT", "AAPL"])

    with pytest.raises(ValueError, match="PAIRS"):
        settings.validate_config()


def test_research_symbols_aceita_simbolos_de_qualquer_mercado(monkeypatch):
    # A lista de PESQUISA existe justamente para aceitar o que a de operacao
    # recusa -- avaliar acoes/forex/futuros sem nunca opera-los.
    monkeypatch.setattr(
        settings, "RESEARCH_SYMBOLS",
        ["BTC/USDT", "AAPL", "PETR4.SA", "EURUSD=X", "ES=F", "^GSPC"],
    )

    settings.validate_config()  # nao deve levantar


def test_research_symbols_recusa_simbolo_nao_resolvivel(monkeypatch):
    # Aceitar um simbolo que nenhuma fonte sabe buscar so adiaria a falha para
    # o meio da varredura.
    monkeypatch.setattr(settings, "RESEARCH_SYMBOLS", ["BTC/USDT", "!!!"])

    with pytest.raises(ValueError, match="RESEARCH_SYMBOLS"):
        settings.validate_config()


def test_research_symbols_vazia_e_valida(monkeypatch):
    # Pesquisa e opcional -- quem so opera cripto nao precisa declarar nada.
    monkeypatch.setattr(settings, "RESEARCH_SYMBOLS", [])

    settings.validate_config()
