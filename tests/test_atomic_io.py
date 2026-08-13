import os

from data.atomic_io import atomic_write


def test_atomic_write_creates_file_with_content(tmp_path):
    path = tmp_path / "out.txt"

    atomic_write(str(path), lambda f: f.write("conteudo"))

    assert path.read_text(encoding="utf-8") == "conteudo"
    assert not os.path.exists(f"{path}.tmp")


def test_atomic_write_replaces_existing_file(tmp_path):
    path = tmp_path / "out.txt"
    path.write_text("antigo", encoding="utf-8")

    atomic_write(str(path), lambda f: f.write("novo"))

    assert path.read_text(encoding="utf-8") == "novo"


def test_atomic_write_does_not_touch_original_if_write_fn_raises(tmp_path):
    path = tmp_path / "out.txt"
    path.write_text("original", encoding="utf-8")

    def _boom(f):
        f.write("parcial")
        raise OSError("disco cheio")

    try:
        atomic_write(str(path), _boom)
    except OSError:
        pass

    assert path.read_text(encoding="utf-8") == "original"
    assert not os.path.exists(f"{path}.tmp")  # nao deixa lixo para tras
