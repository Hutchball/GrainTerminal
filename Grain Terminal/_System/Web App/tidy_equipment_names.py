#!/usr/bin/env python3
"""Add short/long naming structure and normalise obvious coded equipment."""

import re
import sqlite3
from pathlib import Path


BASE = Path(__file__).parent
DB_PATH = BASE / "grain_terminal.db"


def ensure_column(cur, table, column, ddl):
    columns = [row[1] for row in cur.execute(f"PRAGMA table_info({table})")]
    if column not in columns:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def add_alias(cur, equipment_id, alias_name, alias_type="normalised_name", source="manual tidy 2026-04-26", notes=None):
    if not alias_name:
        return
    exists = cur.execute(
        """
        SELECT 1
        FROM equipment_aliases
        WHERE equipment_id = ? AND lower(alias_name) = lower(?)
        """,
        (equipment_id, alias_name),
    ).fetchone()
    if exists:
        return
    cur.execute(
        """
        INSERT INTO equipment_aliases (equipment_id, alias_name, alias_type, source, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (equipment_id, alias_name, alias_type, source, notes),
    )


def title_for_name(name, equipment_type):
    patterns = [
        (r"^RB(\d+)$", "Receiving Belt {n}"),
        (r"^RB(\d+) DCE$", "Receiving Belt {n} DCE"),
        (r"^RB(\d+) MAGNET$", "Receiving Belt {n} Magnet"),
        (r"^BB(\d+)$", "Basement Belt {n}"),
        (r"^BB(\d+)_V(\d+)$", "Basement Belt {n} Valve {m}"),
        (r"^RC(\d+)$", "Receiving Chain Conveyor {n}"),
        (r"^RC(\d+) DCE(\d+)$", "Receiving Chain Conveyor {n} DCE {m}"),
        (r"^RC(\d+) DCE$", "Receiving Chain Conveyor {n} DCE"),
        (r"^ELV(\d+)$", "Elevator {n}"),
        (r"^ME(\d+)$", "Main Elevator {n}"),
        (r"^JL(\d+)$", "Junction House Elevator {n}"),
        (r"^LLCC(\d+)$", "Lorry Loading Chain Conveyor {n}"),
        (r"^LWCC(\d+)$", "Lorry Weighback Chain Conveyor {n}"),
        (r"^MC(\d+)$", "Mill Conveyor {n}"),
        (r"^FB(\d+)$", "Feed Belt {n}"),
        (r"^FE(\d+)$", "Feed Elevator {n}"),
        (r"^TH(\d+)$", "Turnhead {n}"),
        (r"^UG(\d+)$", "Upper Garner {n}"),
        (r"^SUB (\d+)$", "Substation {n}"),
    ]
    for pattern, template in patterns:
        match = re.match(pattern, name)
        if not match:
            continue
        groups = match.groups()
        return template.format(n=groups[0], m=groups[1] if len(groups) > 1 else "")

    if equipment_type == "tripper":
        match = re.match(r"^TR(\d+)$", name)
        if match:
            return f"Tripper {match.group(1)}"
    return None


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    ensure_column(cur, "equipment", "long_name", "long_name TEXT")

    rows = cur.execute("SELECT id, name, equipment_type, long_name FROM equipment ORDER BY id").fetchall()
    updated = 0
    for equipment_id, name, equipment_type, current_long in rows:
        long_name = title_for_name(name, equipment_type)
        if not long_name:
            continue
        if current_long != long_name:
            cur.execute("UPDATE equipment SET long_name = ? WHERE id = ?", (long_name, equipment_id))
            updated += 1
        add_alias(
            cur,
            equipment_id,
            long_name,
            notes=f"Long name for short equipment code {name}.",
        )

    # A few already-long canonical names still benefit from explicit long_name values.
    explicit = {
        "Simons Bin": "Simons Bin",
        "Shipping Spout 2": "Shipping Spout 2",
        "Silo 3 Bins": "Silo 3 Bins 1-9",
        "Mill Feed": "Mill Feed",
    }
    for short_name, long_name in explicit.items():
        row = cur.execute("SELECT id, long_name FROM equipment WHERE name = ?", (short_name,)).fetchone()
        if not row:
            continue
        equipment_id, current_long = row
        if current_long != long_name:
            cur.execute("UPDATE equipment SET long_name = ? WHERE id = ?", (long_name, equipment_id))
            updated += 1

    conn.commit()
    alias_count = cur.execute("SELECT COUNT(*) FROM equipment_aliases").fetchone()[0]
    long_count = cur.execute("SELECT COUNT(*) FROM equipment WHERE long_name IS NOT NULL AND long_name != ''").fetchone()[0]
    conn.close()
    print(f"Equipment naming tidy complete: {updated} long names set/changed; {long_count} equipment rows have long names; {alias_count} aliases total.")


if __name__ == "__main__":
    main()
