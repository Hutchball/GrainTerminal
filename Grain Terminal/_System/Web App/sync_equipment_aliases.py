#!/usr/bin/env python3
"""
Load canonical/legacy alias mappings from the terminal structure folder into the
equipment_aliases table. This does not delete equipment records; it only attaches
aliases to the chosen canonical records.
"""

import json
import sqlite3
from pathlib import Path

BASE = Path(__file__).parent
DB_PATH = BASE / "grain_terminal.db"
ALIAS_MAP_PATH = BASE.parent / "Terminal Structure" / "CANONICAL_ALIAS_MAP_2026-04-25.json"

CANONICAL_NAME_TO_EQUIPMENT_ID = {
    "RB1": 43,
    "RB2": 44,
    "RC1": 45,
    "RC2": 46,
    "JH_ELEVATOR_1": 51,
    "JH_ELEVATOR_2": 52,
    "BB1": 61,
    "BB2": 62,
    "BB3": 63,
    "BB1_V1": 64,
    "BB2_V1": 65,
    "BB3_V1": 66,
    "ME1": 67,
    "ME2": 68,
    "ME3": 69,
    "ME4": 70,
}


def main():
    payload = json.loads(ALIAS_MAP_PATH.read_text(encoding="utf-8"))
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    inserted = 0

    for row in payload["aliases"]:
        equipment_id = CANONICAL_NAME_TO_EQUIPMENT_ID.get(row["canonical_name"])
        if not equipment_id:
            continue
        for alias in row["legacy_aliases"]:
            cur.execute(
                """
                INSERT INTO equipment_aliases (equipment_id, alias_name, alias_type, source, notes)
                SELECT ?, ?, 'legacy_name', ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM equipment_aliases WHERE equipment_id = ? AND alias_name = ?
                )
                """,
                (
                    equipment_id,
                    alias,
                    "CANONICAL_ALIAS_MAP_2026-04-25.json",
                    f"Canonical merge alias for {row['canonical_asset_id']}",
                    equipment_id,
                    alias,
                ),
            )
            inserted += cur.rowcount

    conn.commit()
    conn.close()
    print(f"Inserted {inserted} equipment alias rows.")


if __name__ == "__main__":
    main()
