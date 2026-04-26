#!/usr/bin/env python3
"""
Import dust bag stock, requirements, and last-change history into grain_terminal.db.
"""

import csv
import re
import sqlite3
from datetime import datetime
from pathlib import Path


BASE = Path(__file__).parent
DB_PATH = BASE / "grain_terminal.db"
SOURCE_DIRS = [
    BASE.parents[2] / "Incoming" / "DUST BAGS IN STOCK",
    BASE.parents[2] / "Incoming" / "Processed" / "DUST BAGS IN STOCK",
]
SOURCE_FILE = "Incoming/DUST BAGS IN STOCK"
CREATED_AT = "2026-04-26T00:35:00"


DDL = """
CREATE TABLE IF NOT EXISTS dust_bag_stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_no TEXT,
    bag_type TEXT,
    application_summary TEXT,
    stock_quantity TEXT,
    min_quantity TEXT,
    max_quantity TEXT,
    notes TEXT,
    source_file TEXT NOT NULL,
    source_row INTEGER NOT NULL,
    imported_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS equipment_dust_bags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER REFERENCES equipment(id) ON DELETE SET NULL,
    bag_type TEXT,
    application_label TEXT NOT NULL,
    quantity_required TEXT,
    total_required TEXT,
    stock_quantity TEXT,
    date_checked TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    notes TEXT,
    source_file TEXT NOT NULL,
    source_row INTEGER NOT NULL,
    imported_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dust_bag_change_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER REFERENCES equipment(id) ON DELETE SET NULL,
    application_label TEXT NOT NULL,
    year_label TEXT NOT NULL,
    change_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    notes TEXT,
    source_file TEXT NOT NULL,
    source_row INTEGER NOT NULL,
    imported_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dust_bag_stock_type ON dust_bag_stock(bag_type);
CREATE INDEX IF NOT EXISTS idx_equipment_dust_bags_equipment ON equipment_dust_bags(equipment_id);
CREATE INDEX IF NOT EXISTS idx_dust_bag_history_equipment ON dust_bag_change_history(equipment_id);
"""


SEEDED_EQUIPMENT = [
    ("RC2 DCE", "dust_control", "Receiving", "RC2 DCE dust-control asset from dust bag records.", ["R.C. 2 DCE"]),
    ("RB5 DCE", "dust_control", "Silo 1", "RB5 DCE dust-control asset from dust bag records.", ["R.B. 5 DCE"]),
    ("RB6 DCE", "dust_control", "Silo 1", "RB6 DCE dust-control asset from dust bag records.", ["R.B. 6 DCE"]),
    ("RB7 DCE", "dust_control", "Silo 1", "RB7 DCE dust-control asset from dust bag records.", ["R.B. 7 DCE"]),
    ("RB8 DCE", "dust_control", "Silo 2", "RB8 DCE dust-control asset from dust bag records.", ["R.B. 8 DCE"]),
    ("RB9 DCE", "dust_control", "Silo 2", "RB9 DCE dust-control asset from dust bag records.", ["R.B. 9 DCE"]),
    ("RB11 DCE", "dust_control", "Silo 3", "RB11 DCE dust-control asset from dust bag records.", ["R.B. 11 DCE", "DCE 11"]),
    ("RB12 DCE", "dust_control", "Silo 3", "RB12 DCE dust-control asset from dust bag records.", ["R.B. 12 DCE", "DCE 12"]),
    ("Tripper No 5 DCE", "dust_control", "Silo 1", "Tripper 5 DCE dust-control asset from dust bag records.", ["Tripper 5 DCE"]),
    ("Tripper No 6 DCE", "dust_control", "Silo 3", "Tripper 6 DCE dust-control asset from dust bag records.", ["Tripper 6 DCE"]),
    ("Tripper No 7 DCE", "dust_control", "Silo 1", "Tripper 7 DCE dust-control asset from dust bag records.", ["Tripper 7 DCE"]),
    ("MC2 Tail End DCE", "dust_control", "Mill Feed", "MC2 tail-end DCE asset from dust bag records.", ["M.C. 2 Tail End DCE"]),
    ("MC2 Drive End DCE", "dust_control", "Mill Feed", "MC2 drive-end DCE asset from dust bag records.", ["M.C. 2 Drive End DCE"]),
    ("MC3 Tail End DCE", "dust_control", "Mill Feed", "MC3 tail-end DCE asset from dust bag records.", ["M.C. 3 Tail End DCE"]),
    ("MC3 Drive End DCE", "dust_control", "Mill Feed", "MC3 drive-end DCE asset from dust bag records.", ["M.C. 3 Drive End DCE"]),
    ("BMH DCE", "dust_control", "BMH", "BMH DCE asset from dust bag records.", ["BMH Dust Control Equipment"]),
    ("Merlin AFS Hopper", "dust_control", "External Interfaces", "Merlin AFS Hopper dust-control asset from dust bag records.", ["AFS Dust Hopper", "AFS Hopper Dust"]),
    ("Merlin AFS C4", "dust_control", "External Interfaces", "Merlin AFS C4 dust-control asset from dust bag records.", ["AFS C4"]),
]


OBSOLETE_LABELS = {"VIGAN", "VIGAN BB 3", "TOWER BELTLOADERS", "WEIGHTOWER"}


def clean(value):
    return " ".join((value or "").replace("\xa0", " ").split()).strip()


def normalize(value):
    return re.sub(r"[^A-Z0-9]+", "", clean(value).upper())


def cell(row, idx):
    return clean(row[idx]) if idx < len(row) else ""


def read_csv(filename):
    path = next((candidate / filename for candidate in SOURCE_DIRS if (candidate / filename).exists()), None)
    if not path:
        checked = ", ".join(str(candidate / filename) for candidate in SOURCE_DIRS)
        raise SystemExit(f"Missing dust bag source file. Checked: {checked}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        yield from enumerate(csv.reader(handle), start=1)


def add_alias(cur, equipment_id, alias_name, notes):
    alias = clean(alias_name)
    if not alias:
        return
    exists = cur.execute(
        "SELECT 1 FROM equipment_aliases WHERE equipment_id = ? AND UPPER(alias_name) = ? LIMIT 1",
        (equipment_id, alias.upper()),
    ).fetchone()
    if exists:
        return
    cur.execute(
        """
        INSERT INTO equipment_aliases (equipment_id, alias_name, alias_type, source, notes)
        VALUES (?, ?, 'dust_bag_label', ?, ?)
        """,
        (equipment_id, alias, SOURCE_FILE, notes),
    )


def ensure_equipment(cur, name, equipment_type, area, notes, aliases):
    row = cur.execute("SELECT id FROM equipment WHERE UPPER(name) = ?", (name.upper(),)).fetchone()
    if row:
        equipment_id = row[0]
    else:
        cur.execute(
            """
            INSERT INTO equipment
                (name, equipment_type, area, mcc, drawing_refs, manufacturer, model, notes, created_at, location_description)
            VALUES (?, ?, ?, NULL, '[]', NULL, NULL, ?, ?, ?)
            """,
            (name, equipment_type, area, notes, CREATED_AT, area),
        )
        equipment_id = cur.lastrowid
    for alias in aliases:
        add_alias(cur, equipment_id, alias, f"Alias from {SOURCE_FILE}.")
    return equipment_id


def ensure_seed_equipment(cur):
    for item in SEEDED_EQUIPMENT:
        ensure_equipment(cur, *item)


def find_equipment(cur, key):
    key = clean(key)
    if not key:
        return None
    row = cur.execute("SELECT id FROM equipment WHERE UPPER(name) = ?", (key.upper(),)).fetchone()
    if row:
        return row[0]
    row = cur.execute(
        """
        SELECT equipment_id FROM equipment_aliases
        WHERE UPPER(alias_name) = ?
           OR UPPER(REPLACE(REPLACE(REPLACE(alias_name, ' ', ''), '.', ''), '/', '')) = ?
        LIMIT 1
        """,
        (key.upper(), normalize(key)),
    ).fetchone()
    return row[0] if row else None


def equipment_key(label):
    text = clean(label).upper()
    compact = normalize(text)
    if not compact:
        return ""
    if text in {"RB 1 & RB 2", "RB1 & RB2"}:
        return "DP1 TO DP6"
    if text in {"RB 5, 6, 7", "RB5,6,7"}:
        return "DP1 TO DP6"
    if text in {"MC 1- 4", "MC 1 - 4"}:
        return "Mill Feed"
    if text in {"TRIPPER 5, 6, 7", "TRIPPER 5,6,7"}:
        return "Tripper No 5 DCE"
    if text in {"RB8 & 9", "RB8 & RB9"}:
        return "DP12 TO DP13"
    if text == "SILO 3":
        return "Silo 3 Dust Plant Rotary Valve"
    if re.match(r"^NO\s*1$", text) or text == "NO1":
        return "DP1 TO DP6"
    if re.match(r"^NO\s*2$", text) or text == "NO2":
        return "DP1 TO DP6"
    if re.match(r"^NO\s*3$", text) or text == "NO3":
        return "DP1 TO DP6"
    if re.match(r"^NO\s*4$", text) or text == "NO4":
        return "DP1 TO DP6"
    if re.match(r"^NO\s*5$", text) or text == "NO5":
        return "DP1 TO DP6"
    if re.match(r"^NO\s*12$", text):
        return "Dust Plant 12 - Fan"
    if re.match(r"^NO\s*13$", text) or text == "NO13":
        return "Dust Plant 13 - Fan"
    if re.match(r"^NO\s*14", text):
        return "Silo 3 Dust Plant 14"
    if text.startswith("BELT LOADER RB 1"):
        return "RB1 DCE"
    if text.startswith("BELT LOADER RB 2"):
        return "RB2 DCE"
    if text == "MAIN DUSTPLANTS":
        return "DP1 TO DP6"
    if text.startswith("NO "):
        return f"DP{text.split()[-1]}"
    match = re.match(r"NO\s*(\d+)", text)
    if match:
        return "Silo 3 Dust Plant 14" if match.group(1) == "14" else f"DP{match.group(1)}"
    match = re.match(r"RB\s*(\d+)$", text)
    if match:
        number = match.group(1)
        return f"RB{number} DCE" if number in {"5", "6", "7", "8", "9", "11", "12"} else f"RB{number} DCE"
    match = re.match(r"R\.B\.\s*(\d+)\s*DCE", text)
    if match:
        return f"RB{match.group(1)} DCE"
    match = re.match(r"R\.C\.\s*(\d+)\s*DCE", text)
    if match:
        return f"RC{match.group(1)} DCE" if match.group(1) == "2" else "RC1 DCE1"
    if text.startswith("RC 1"):
        return "RC1 DCE1"
    if text.startswith("RC 2"):
        return "RC2 DCE"
    if text.startswith("RB3"):
        return "RB3 DCE"
    if text.startswith("RB4"):
        return "RB4 DCE"
    if text.startswith("SURGE BIN"):
        return "Surge Bin DCE"
    if text.startswith("BMH"):
        return "BMH DCE"
    if "AFS C4" in text:
        return "Merlin AFS C4"
    if "AFS DUST HOPPER" in text or "AFS HOPPER" in text:
        return "Merlin AFS Hopper"
    if "DUST PLANT 14" in text or "DP14" in text:
        return "Silo 3 Dust Plant 14"
    if "DUST PLANT 15" in text or "DP15" in text:
        return "Silo 3 Dust Plant 15"
    if re.match(r"^DUST PLANT\s*[1-6]$", text):
        return "DP1 TO DP6"
    if "DUST PLANT 12" in text or "NO 12" in text:
        return "Dust Plant 12 - Fan"
    if "DUST PLANT 13" in text or "NO13" in text:
        return "Dust Plant 13 - Fan"
    if "DUST PLANT 1" in text:
        return "DP1 TO DP6"
    if "DUST PLANT 2" in text or "DUST PLANT 3" in text or "DUST PLANT 5" in text or "DUST PLANT 6" in text:
        return "DP1 TO DP6"
    if text.startswith("M.C. 2 TAIL"):
        return "MC2 Tail End DCE"
    if text.startswith("M.C. 2 DRIVE"):
        return "MC2 Drive End DCE"
    if text.startswith("M.C. 3 TAIL"):
        return "MC3 Tail End DCE"
    if text.startswith("M.C. 3 DRIVE"):
        return "MC3 Drive End DCE"
    if text.startswith("TRIPPER NO 5"):
        return "Tripper No 5 DCE"
    if text.startswith("TRIPPER NO 6"):
        return "Tripper No 6 DCE"
    if text.startswith("TRIPPER NO 7"):
        return "Tripper No 7 DCE"
    if "MT" in text:
        return ""
    return compact


def status_for(label):
    return "obsolete" if clean(label).upper() in OBSOLETE_LABELS else "active"


def import_stock(cur):
    now = datetime.now().isoformat(timespec="seconds")
    count = 0
    for row_number, row in read_csv("Stocks-Table 1.csv"):
        item_no = cell(row, 0)
        bag_type = cell(row, 2)
        if not item_no or not re.match(r"^\d+$", item_no):
            continue
        cur.execute(
            """
            INSERT INTO dust_bag_stock
                (item_no, bag_type, application_summary, stock_quantity, min_quantity,
                 max_quantity, notes, source_file, source_row, imported_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_no,
                bag_type or cell(row, 3),
                cell(row, 3),
                "",
                "",
                "",
                "Historic stock quantities intentionally not imported; use as stock placeholder only.",
                f"{SOURCE_FILE}/Stocks-Table 1.csv",
                row_number,
                now,
            ),
        )
        count += 1
    return count


def import_requirements(cur):
    now = datetime.now().isoformat(timespec="seconds")
    count = 0
    current_bag = ""
    current_family = ""
    pending_ids = []
    for row_number, row in read_csv("Required-Table 1.csv"):
        bag_type = cell(row, 0)
        descriptor = cell(row, 1)
        application = cell(row, 3)
        quantity = cell(row, 5)
        total_required = cell(row, 6)
        stock_quantity = ""
        date_checked = cell(row, 8)

        if bag_type and not application and not quantity and not total_required:
            current_family = bag_type
            current_bag = "" if bag_type.isupper() and len(bag_type) > 6 else bag_type
            continue
        if bag_type:
            current_bag = f"{bag_type} {descriptor}".strip()
        if application and quantity:
            status = status_for(application)
            equipment_id = find_equipment(cur, equipment_key(application))
            cur.execute(
                """
                INSERT INTO equipment_dust_bags
                    (equipment_id, bag_type, application_label, quantity_required,
                     total_required, stock_quantity, date_checked, status, notes,
                     source_file, source_row, imported_at)
                VALUES (?, ?, ?, ?, NULL, NULL, NULL, ?, ?, ?, ?, ?)
                """,
                (
                    equipment_id,
                    current_bag or current_family,
                    application,
                    quantity,
                    status,
                    current_family,
                    f"{SOURCE_FILE}/Required-Table 1.csv",
                    row_number,
                    now,
                ),
            )
            pending_ids.append(cur.lastrowid)
            count += 1
        if total_required or stock_quantity or date_checked:
            for req_id in pending_ids:
                cur.execute(
                    """
                    UPDATE equipment_dust_bags
                    SET total_required = COALESCE(NULLIF(?, ''), total_required),
                        stock_quantity = COALESCE(NULLIF(?, ''), stock_quantity),
                        date_checked = COALESCE(NULLIF(?, ''), date_checked)
                    WHERE id = ?
                    """,
                    (total_required, stock_quantity, date_checked, req_id),
                )
            pending_ids = []
    return count


def import_change_history(cur):
    rows = list(read_csv("date last change-Table 1.csv"))
    if len(rows) < 2:
        return 0
    header = rows[1][1]
    years = {idx: clean(value) for idx, value in enumerate(header) if clean(value)}
    now = datetime.now().isoformat(timespec="seconds")
    count = 0
    for row_number, row in rows[2:]:
        label = cell(row, 0)
        if not label:
            continue
        status = status_for(label)
        equipment_id = find_equipment(cur, equipment_key(label))
        for idx, year in years.items():
            change_date = cell(row, idx)
            if not change_date:
                continue
            cur.execute(
                """
                INSERT INTO dust_bag_change_history
                    (equipment_id, application_label, year_label, change_date, status,
                     notes, source_file, source_row, imported_at)
                VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?)
                """,
                (
                    equipment_id,
                    label,
                    year,
                    change_date,
                    status,
                    f"{SOURCE_FILE}/date last change-Table 1.csv",
                    row_number,
                    now,
                ),
            )
            count += 1
    return count


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(DDL)
    cur = conn.cursor()
    ensure_seed_equipment(cur)
    cur.execute("DELETE FROM dust_bag_stock WHERE source_file LIKE ?", (f"{SOURCE_FILE}/%",))
    cur.execute("DELETE FROM equipment_dust_bags WHERE source_file LIKE ?", (f"{SOURCE_FILE}/%",))
    cur.execute("DELETE FROM dust_bag_change_history WHERE source_file LIKE ?", (f"{SOURCE_FILE}/%",))
    stock = import_stock(cur)
    requirements = import_requirements(cur)
    history = import_change_history(cur)
    conn.commit()
    linked_requirements = cur.execute("SELECT COUNT(*) FROM equipment_dust_bags WHERE equipment_id IS NOT NULL").fetchone()[0]
    linked_history = cur.execute("SELECT COUNT(*) FROM dust_bag_change_history WHERE equipment_id IS NOT NULL").fetchone()[0]
    total_equipment = cur.execute("SELECT COUNT(*) FROM equipment").fetchone()[0]
    conn.close()
    print(f"Imported {stock} stock rows, {requirements} requirement rows, {history} change-history rows.")
    print(f"Linked requirements: {linked_requirements}; linked change-history entries: {linked_history}.")
    print(f"Equipment records now: {total_equipment}.")


if __name__ == "__main__":
    main()
