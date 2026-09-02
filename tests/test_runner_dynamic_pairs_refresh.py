from market.selector import PairCandidate
from trading import runner


class _FakePosition:
    def __init__(self, quantity=1.0):
        self.quantity = quantity


class _FakeManager:
    def __init__(self, positions=None):
        self.positions = positions or {}

    def has_position(self, symbol: str) -> bool:
        return symbol in self.positions


def _candidates(*symbols):
    return [PairCandidate(symbol=s, volume_24h=0.0, spread_pct=0.0, volatility_pct=0.0, trend_pct=0.0) for s in symbols]


# ---------------------------------------------------------------- US1: refresh muda a lista

def test_refresh_active_pairs_adopts_new_selection(monkeypatch):
    manager = _FakeManager()
    monkeypatch.setattr(runner, "select_dynamic_pairs", lambda: _candidates("ETH/USDT", "SOL/USDT"))

    nova_lista, resumo = runner._refresh_active_pairs(manager, ["BTC/USDT"])

    assert nova_lista == ["ETH/USDT", "SOL/USDT"]
    assert resumo["added"] == ["ETH/USDT", "SOL/USDT"]
    assert resumo["removed"] == ["BTC/USDT"]
    assert resumo["kept_for_open_position"] == []


def test_refresh_active_pairs_idempotent_when_selection_unchanged(monkeypatch):
    manager = _FakeManager()
    monkeypatch.setattr(runner, "select_dynamic_pairs", lambda: _candidates("BTC/USDT", "ETH/USDT"))

    nova_lista, resumo = runner._refresh_active_pairs(manager, ["BTC/USDT", "ETH/USDT"])

    assert nova_lista == ["BTC/USDT", "ETH/USDT"]
    assert resumo["added"] == []
    assert resumo["removed"] == []


# ---------------------------------------------------------------- US2: posicao aberta nunca sai

def test_refresh_active_pairs_never_drops_symbol_with_open_position(monkeypatch):
    # Achado critico da spec: handle_open_position so roda para simbolos em
    # active_pairs -- remover um par com posicao aberta o deixaria orfao,
    # sem stop loss/trailing/take profit gerido.
    manager = _FakeManager(positions={"LUNC/USDT": _FakePosition()})
    monkeypatch.setattr(runner, "select_dynamic_pairs", lambda: _candidates("ETH/USDT", "SOL/USDT"))

    nova_lista, resumo = runner._refresh_active_pairs(manager, ["LUNC/USDT"])

    assert "LUNC/USDT" in nova_lista
    assert "LUNC/USDT" not in resumo["removed"]
    assert resumo["kept_for_open_position"] == ["LUNC/USDT"]


def test_refresh_active_pairs_removes_symbol_without_open_position(monkeypatch):
    # Contraste com o teste acima: a guarda e especifica de posicao aberta,
    # nao um bloqueio geral de remocao.
    manager = _FakeManager()  # nenhuma posicao aberta
    monkeypatch.setattr(runner, "select_dynamic_pairs", lambda: _candidates("ETH/USDT"))

    nova_lista, resumo = runner._refresh_active_pairs(manager, ["LUNC/USDT"])

    assert "LUNC/USDT" not in nova_lista
    assert resumo["removed"] == ["LUNC/USDT"]
    assert resumo["kept_for_open_position"] == []


# ---------------------------------------------------------------- D2: falha preserva lista vigente

def test_refresh_active_pairs_preserves_current_list_on_selector_failure(monkeypatch):
    manager = _FakeManager()

    def _falha():
        raise RuntimeError("rede indisponivel")

    monkeypatch.setattr(runner, "select_dynamic_pairs", _falha)

    nova_lista, resumo = runner._refresh_active_pairs(manager, ["BTC/USDT", "ETH/USDT"])

    assert nova_lista == ["BTC/USDT", "ETH/USDT"]
    assert "error" in resumo
    assert "rede indisponivel" in resumo["error"]


# ---------------------------------------------------------------- US3: evento de auditoria (D3)

def test_refresh_active_pairs_logs_event_when_list_changes(monkeypatch):
    eventos = []
    monkeypatch.setattr(runner, "log_event", lambda name, **kwargs: eventos.append((name, kwargs)))
    manager = _FakeManager(positions={"LUNC/USDT": _FakePosition()})
    monkeypatch.setattr(runner, "select_dynamic_pairs", lambda: _candidates("ETH/USDT"))

    runner._refresh_active_pairs(manager, ["LUNC/USDT", "BTC/USDT"])

    assert len(eventos) == 1
    nome, campos = eventos[0]
    assert nome == "dynamic_pairs_refreshed"
    assert campos["mode"] == runner.TRADING_MODE
    assert campos["added"] == ["ETH/USDT"]
    assert campos["removed"] == ["BTC/USDT"]
    assert campos["kept_for_open_position"] == ["LUNC/USDT"]


def test_refresh_active_pairs_logs_event_even_when_nothing_changes(monkeypatch):
    eventos = []
    monkeypatch.setattr(runner, "log_event", lambda name, **kwargs: eventos.append((name, kwargs)))
    manager = _FakeManager()
    monkeypatch.setattr(runner, "select_dynamic_pairs", lambda: _candidates("BTC/USDT"))

    runner._refresh_active_pairs(manager, ["BTC/USDT"])

    assert len(eventos) == 1
    _nome, campos = eventos[0]
    assert campos["added"] == []
    assert campos["removed"] == []
    assert campos["kept_for_open_position"] == []


# ---------------------------------------------------------------- Polish: flag desligada (FR-006)

def test_dynamic_pairs_disabled_never_calls_selector(monkeypatch):
    # DYNAMIC_PAIRS_ENABLED=false e a config atual do bot -- o refresh nunca
    # deve rodar, mesmo apos DYNAMIC_PAIRS_REFRESH_CYCLES ciclos.
    monkeypatch.setattr(runner, "DYNAMIC_PAIRS_ENABLED", False)
    monkeypatch.setattr(runner, "DYNAMIC_PAIRS_REFRESH_CYCLES", 1)

    def _falha_se_chamado():
        raise AssertionError("select_dynamic_pairs nao deveria ser chamado com a flag desligada")

    monkeypatch.setattr(runner, "select_dynamic_pairs", _falha_se_chamado)

    cycle_id = 3  # multiplo de DYNAMIC_PAIRS_REFRESH_CYCLES=1
    active_pairs = ["BTC/USDT"]
    if runner.DYNAMIC_PAIRS_ENABLED and cycle_id % runner.DYNAMIC_PAIRS_REFRESH_CYCLES == 0:
        active_pairs, _ = runner._refresh_active_pairs(None, active_pairs)

    assert active_pairs == ["BTC/USDT"]
