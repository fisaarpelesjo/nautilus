import csv
import os


def ensure_csv(path: str, headers: list):
    if not os.path.exists(path):
        with open(path, "w", newline="") as f:
            csv.writer(f).writerow(headers)
