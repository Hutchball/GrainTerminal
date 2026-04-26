#!/usr/bin/env python3
"""
Import pulley register CSV exports into grain_terminal.db.
"""

import csv
import re
import sqlite3
from datetime import datetime
from pathlib import Path


BASE = Path(__file__).parent
DB_PATH = BASE / "grain_terminal.db"
INCOMING = BASE.parents[2] / "Incoming" / "PULLEYS LIST"
SOURCE_MAIN = "Incoming/PULLEYS LIST/Pulley List-Table 1.csv"
SOURCE_COMPAT = "Incoming/PULLEYS LIST/Sheet4-Table 1.csv"


DDL = """
CREATE TABLE IF NOT EXISTS equipment_pulleys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER REFERENCES equipment(id) ON DELETE SET NULL,
    source_equipment_label TEXT NOT NULL,
    pulley_label TEXT NOT NULL,
    pulley_type TEXT,
    stock_number TEXT,
    pulley_diameter TEXT,
    face_width TEXT,
    shaft_diameter TEXT,
    shaft_length TEXT,
    length_from_face TEXT,
    bearing_centre TEXT,
    bearing_details TEXT,
    quantity TEXT,
    notes TEXT,
    source_file TEXT NOT NULL,
    source_sheet TEXT NOT NULL,
    source_row INTEGER NOT NULL,
    record_type TEXT NOT NULL DEFAULT 'register',
    imported_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_equipment_pulleys_equipment ON equipment_pulleys(equipment_id);
CREATE INDEX IF NOT EXISTS idx_equipment_pulleys_label ON equipment_pulleys(source_equipment_label);
"""


def clean(value):
    return " ".join((value or "").replace("\xa0", " ").split()).strip()


def is_empty(row):
    return not any(clean(v) for v in row)


def get_col(row, idx):
    return clean(row[idx]) if idx < len(row) else ""


def first_nonempty(row, indexes):
    for idx in indexes:
        value = get_col(row, idx)
        if value:
            return value
    return ""


def equipment_key(label):
    text = clean(label).upper().replace(".", "")
    match = re.match(r"^(ELV)\s*(\d+)\b", text)
    if match:
        return f"ELV{match.group(2)}"
    match = re.match(r"^([A-Z]+)(\d+)\b", text)
    if match:
        prefix, number = match.groups()
        if prefix in {"RB", "RC", "BB", "MC", "FB", "FE", "UG", "TH", "ELV", "LWCC"}:
            return f"{prefix}{number}"
        if prefix == "JHEL":
            return f"JL{number}"
    if text.startswith("SMC"):
        return "SMC"
    return text.split()[0] if text else ""


def pulley_type(label):
    key = equipment_key(label)
    rest = clean(label)
    if key and rest.upper().startswith(key):
        rest = rest[len(key):]
    rest = rest.replace(".", "").strip()
    return rest or None


def equipment_id_for(cur, label):
    key = equipment_key(label)
    if not key:
        return None
    row = cur.execute("SELECT id FROM equipment WHERE UPPER(name) = ?", (key.upper(),)).fetchone()
    if row:
        return row[0]
    row = cur.execute(
        """
        SELECT equipment_id
        FROM equipment_aliases
        WHERE UPPER(alias_name) = ?
        LIMIT 1
        """,
        (key.upper(),),
    ).fetchone()
    return row[0] if row else None


def insert_row(cur, row, row_number, source_file, source_sheet, record_type):
    stock_number = get_col(row, 0) if record_type == "register" else ""
    label = get_col(row, 1) if record_type == "register" else get_col(row, 0)
    if not label:
        return False
    label_upper = label.upper()
    if label_upper.startswith(("STOCK NO", "PULLEY", "THIS PULLEY", "RECEIVING", "SILO", "MILL FEED")):
        return False
    if not re.search(r"\b(DRIVE|SNUB|TAIL|BEND|GTU|TENS|HEAD|BOOT)\b", label_upper):
        return False

    offset = 0 if record_type == "compatibility" else 1
    values = {
        "pulley_diameter": first_nonempty(row, [offset + 2, offset + 3]),
        "face_width": first_nonempty(row, [offset + 4, offset + 5]),
        "shaft_diameter": first_nonempty(row, [offset + 6, offset + 7]),
        "shaft_length": first_nonempty(row, [offset + 8, offset + 9]),
        "length_from_face": first_nonempty(row, [offset + 10, offset + 11]),
        "bearing_centre": first_nonempty(row, [offset + 12, offset + 13]),
        "bearing_details": first_nonempty(row, [offset + 14, offset + 15]),
    }
    quantity = first_nonempty(row, [17, 18]) if record_type == "register" else ""
    notes = " | ".join(clean(v) for v in row[18:] if clean(v)) if record_type == "register" else ""

    cur.execute(
        """
        INSERT INTO equipment_pulleys
            (equipment_id, source_equipment_label, pulley_label, pulley_type, stock_number,
             pulley_diameter, face_width, shaft_diameter, shaft_length, length_from_face,
             bearing_centre, bearing_details, quantity, notes, source_file, source_sheet,
             source_row, record_type, imported_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            equipment_id_for(cur, label),
            equipment_key(label),
            label,
            pulley_type(label),
            stock_number,
            values["pulley_diameter"],
            values["face_width"],
            values["shaft_diameter"],
            values["shaft_length"],
            values["length_from_face"],
            values["bearing_centre"],
            values["bearing_details"],
            quantity,
            notes,
            source_file,
            source_sheet,
            row_number,
            record_type,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    return True


def import_file(cur, path, source_file, source_sheet, record_type):
    count = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        for row_number, row in enumerate(reader, start=1):
            if is_empty(row):
                continue
            if insert_row(cur, row, row_number, source_file, source_sheet, record_type):
                count += 1
    return count


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(DDL)
    cur = conn.cursor()
    cur.execute("DELETE FROM equipment_pulleys WHERE source_file LIKE 'Incoming/PULLEYS LIST/%'")

    main_count = import_file(
        cur,
        INCOMING / "Pulley List-Table 1.csv",
        SOURCE_MAIN,
        "Pulley List",
        "register",
    )
    compat_count = import_file(
        cur,
        INCOMING / "Sheet4-Table 1.csv",
        SOURCE_COMPAT,
        "Suitable For",
        "compatibility",
    )

    conn.commit()
    linked = cur.execute("SELECT COUNT(*) FROM equipment_pulleys WHERE equipment_id IS NOT NULL").fetchone()[0]
    total = cur.execute("SELECT COUNT(*) FROM equipment_pulleys").fetchone()[0]
    conn.close()
    print(f"Imported {main_count} pulley register rows and {compat_count} compatibility rows.")
    print(f"Total pulley records: {total}; linked to equipment: {linked}.")


if __name__ == "__main__":
    main()
