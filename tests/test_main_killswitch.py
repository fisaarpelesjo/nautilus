import main
from data import killswitch_store


def test_cmd_kill_activates_and_notifies(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(killswitch_store, "KILLSWITCH_FILE", str(tmp_path / "killswitch.json"))
    events = []
    messages = []
    monkeypatch.setattr("utils.logger.log_event", lambda event, **kwargs: events.append((event, kwargs)))
    monkeypatch.setattr("utils.notifier.send_telegram", lambda msg: messages.append(msg))

    main.cmd_kill()

    assert killswitch_store.load_killswitch() is True
    assert events[0][0] == "killswitch_toggled"
    assert events[0][1]["active"] is True
    assert any("ATIVADO" in m for m in messages)
    assert "ativado" in capsys.readouterr().out


def test_cmd_resume_deactivates_and_notifies(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(killswitch_store, "KILLSWITCH_FILE", str(tmp_path / "killswitch.json"))
    killswitch_store.save_killswitch(True)
    events = []
    messages = []
    monkeypatch.setattr("utils.logger.log_event", lambda event, **kwargs: events.append((event, kwargs)))
    monkeypatch.setattr("utils.notifier.send_telegram", lambda msg: messages.append(msg))

    main.cmd_resume()

    assert killswitch_store.load_killswitch() is False
    assert events[0][1]["active"] is False
    assert any("DESATIVADO" in m for m in messages)
    assert "desativado" in capsys.readouterr().out


def test_toggle_killswitch_survives_notification_failure(tmp_path, monkeypatch):
    # A ativacao do kill switch (a parte critica) nao pode ficar refem de
    # uma falha ao publicar evento/alerta.
    monkeypatch.setattr(killswitch_store, "KILLSWITCH_FILE", str(tmp_path / "killswitch.json"))
    monkeypatch.setattr(
        "utils.logger.log_event",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("disk full")),
    )
    monkeypatch.setattr("utils.notifier.send_telegram", lambda msg: (_ for _ in ()).throw(RuntimeError("sem rede")))

    main.cmd_kill()  # nao deve levantar

    assert killswitch_store.load_killswitch() is True
