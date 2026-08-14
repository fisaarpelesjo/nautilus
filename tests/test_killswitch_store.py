from data import killswitch_store


def test_load_killswitch_returns_false_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(killswitch_store, "KILLSWITCH_FILE", str(tmp_path / "missing.json"))

    assert killswitch_store.load_killswitch() is False


def test_save_and_load_killswitch_round_trip(tmp_path, monkeypatch):
    path = str(tmp_path / "killswitch.json")
    monkeypatch.setattr(killswitch_store, "KILLSWITCH_FILE", path)

    killswitch_store.save_killswitch(True)
    assert killswitch_store.load_killswitch() is True

    killswitch_store.save_killswitch(False)
    assert killswitch_store.load_killswitch() is False


def test_load_killswitch_returns_false_on_corrupted_file(tmp_path, monkeypatch):
    # Diferente de state.json (falha alto e claro), o kill switch e um flag
    # simples -- um arquivo corrompido nao deve travar o bot, so ser tratado
    # como "nao ativado".
    path = tmp_path / "killswitch.json"
    path.write_text("{nao e json valido", encoding="utf-8")
    monkeypatch.setattr(killswitch_store, "KILLSWITCH_FILE", str(path))

    assert killswitch_store.load_killswitch() is False


def test_save_killswitch_is_independent_from_state_json(tmp_path, monkeypatch):
    # A razao de existir um arquivo proprio: OrderManager reescreve
    # state.json inteiro a cada _persist_state(); se o kill switch morasse
    # la dentro, uma escrita normal do bot rodando poderia sobrescrever um
    # "kill" ativado externamente por um comando de CLI separado.
    killswitch_path = tmp_path / "killswitch.json"
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(killswitch_store, "KILLSWITCH_FILE", str(killswitch_path))

    killswitch_store.save_killswitch(True)

    assert not state_path.exists()
