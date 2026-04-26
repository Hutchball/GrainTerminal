#!/usr/bin/env python3
"""
Import lubricant register rows from the Incoming CSV into grain_terminal.db.
"""

import csv
import sqlite3
from datetime import datetime
from pathlib import Path


BASE = Path(__file__).parent
DB_PATH = BASE / "grain_terminal.db"
CSV_PATH = BASE.parents[2] / "Incoming" / "LUBRICANTS - FINAL G&B copy.csv"
SOURCE_FILE = "Incoming/LUBRICANTS - FINAL G&B copy.csv"


DDL = """
CREATE TABLE IF NOT EXISTS lubricants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier TEXT,
    product_description TEXT NOT NULL,
    stock_quantity INTEGER,
    ordering_instructions TEXT,
    used_for TEXT,
    source_file TEXT,
    imported_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_lubricants_product ON lubricants(product_description);
CREATE INDEX IF NOT EXISTS idx_lubricants_supplier ON lubricants(supplier);
"""


def normalise(value):
    return " ".join((value or "").replace("\xa0", " ").split())


def main():
    if not CSV_PATH.exists():
        raise SystemExit(f"Missing CSV: {CSV_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(DDL)
    cur = conn.cursor()
    cur.execute("DELETE FROM lubricants WHERE source_file = ?", (SOURCE_FILE,))

    imported_at = datetime.now().isoformat(timespec="seconds")
    inserted = 0
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            supplier = normalise(row.get("SUPPLIER"))
            product = normalise(row.get("PRODUCT DESCRIPTION"))
            qty_raw = normalise(row.get("QTY TO HOLD IN STOCK"))
            ordering = normalise(row.get("SPECIAL ORDERING INSTRUCTIONS"))
            used_for = normalise(row.get("MACHINE ITEMS USED FOR OR PRODUCT USED FOR?"))
            if not any([supplier, product, qty_raw, ordering, used_for]):
                continue
            qty = int(qty_raw) if qty_raw.isdigit() else None
            cur.execute(
                """
                INSERT INTO lubricants
                    (supplier, product_description, stock_quantity, ordering_instructions,
                     used_for, source_file, imported_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (supplier, product, qty, ordering, used_for, SOURCE_FILE, imported_at),
            )
            inserted += 1

    conn.commit()
    conn.close()
    print(f"Imported {inserted} lubricant rows.")


if __name__ == "__main__":
    main()
