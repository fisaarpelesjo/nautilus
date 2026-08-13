import csv
import os


def ensure_csv(path: str, headers: list):
    if not os.path.exists(path):
        with open(path, "w", newline="") as f:
            csv.writer(f).writerow(headers)
        return

    with open(path, newline="") as f:
        first_line = f.readline().rstrip("\r\n")
    if not first_line or first_line == ",".join(headers):
        return

    _migrate_header(path, headers)


def _migrate_header(path: str, headers: list):
    """Reescreve o cabecalho quando `headers` ganhou colunas novas desde a
    ultima vez que o arquivo foi criado, preservando as linhas existentes
    (colunas novas ficam vazias nas linhas antigas)."""
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({h: row.get(h, "") for h in headers})
