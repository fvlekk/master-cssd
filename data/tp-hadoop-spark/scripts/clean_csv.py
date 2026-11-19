"""Normalise the raw BAAC CSV files so that Hive and RDD code can split them on ';'.

Removes every quote, trims the values, drops blank lines and replaces a ';' inside a value by ','.
"""
import csv
from pathlib import Path

data = Path.home() / "data"
clean = data / "clean"
clean.mkdir(exist_ok=True)

for path in sorted(data.glob("*-2024.csv")):
    rows = 0
    with path.open(newline="", encoding="utf-8") as src, (clean / path.name).open("w", encoding="utf-8") as dst:
        for row in csv.reader(src, delimiter=";"):
            if row:
                dst.write(";".join(value.replace('"', '').strip().replace(";", ",") for value in row) + "\n")
                rows += 1
    print(f"{path.name}: {rows - 1} records")
