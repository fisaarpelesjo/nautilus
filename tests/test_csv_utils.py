from data.csv_utils import ensure_csv


def test_ensure_csv_creates_file_with_header(tmp_path):
    path = tmp_path / "new.csv"

    ensure_csv(str(path), ["a", "b"])

    assert path.read_text(encoding="utf-8").splitlines()[0] == "a,b"


def test_ensure_csv_leaves_up_to_date_header_untouched(tmp_path):
    path = tmp_path / "existing.csv"
    with open(path, "w", newline="") as f:
        f.write("a,b\r\n1,2\r\n")

    ensure_csv(str(path), ["a", "b"])

    with open(path, newline="") as f:
        assert f.read() == "a,b\r\n1,2\r\n"


def test_ensure_csv_migrates_header_when_new_column_added(tmp_path):
    path = tmp_path / "trades.csv"
    with open(path, "w", newline="") as f:
        f.write("a,b\r\n1,2\r\n")

    ensure_csv(str(path), ["a", "b", "c"])

    with open(path, newline="") as f:
        lines = f.read().splitlines()
    assert lines[0] == "a,b,c"
    assert lines[1] == "1,2,"


def test_ensure_csv_self_heals_when_file_deleted_externally(tmp_path):
    # Regressao: uma versao anterior cacheava "path ja verificado" em memoria e
    # nunca mais checava o disco, entao um arquivo apagado/truncado por fora
    # (rotacao de log, crash) no meio da vida do processo ficava sem cabecalho
    # para sempre. ensure_csv deve recriar o cabecalho toda vez que o arquivo
    # nao existir, nao so na primeira chamada.
    path = tmp_path / "trades.csv"

    ensure_csv(str(path), ["a", "b"])
    path.unlink()
    ensure_csv(str(path), ["a", "b"])

    assert path.read_text(encoding="utf-8").splitlines()[0] == "a,b"
