#!/usr/bin/env python3
"""
Build a gearbox register by cross-linking gearbox lubricant assignments with
gearbox attributes imported from asset lists.
"""

import sqlite3
from datetime import datetime
from pathlib import Path


BASE = Path(__file__).parent
DB_PATH = BASE / "grain_terminal.db"


DDL = """
CREATE TABLE IF NOT EXISTS equipment_gearboxes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    gearbox_label TEXT NOT NULL,
    lubricant_id INTEGER REFERENCES lubricants(id) ON DELETE SET NULL,
    oil_supplier TEXT,
    oil_product TEXT,
    oil_application TEXT,
    gearbox_make TEXT,
    gearbox_type TEXT,
    gearbox_reduction TEXT,
    gearbox_output_speed TEXT,
    source TEXT NOT NULL,
    imported_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_equipment_gearboxes_equipment ON equipment_gearboxes(equipment_id);
CREATE INDEX IF NOT EXISTS idx_equipment_gearboxes_lubricant ON equipment_gearboxes(lubricant_id);
"""


def attr_map(cur):
    result = {}
    rows = cur.execute(
        """
        SELECT equipment_id, attribute_key, attribute_value
        FROM equipment_attributes
        WHERE attribute_category = 'gearbox'
           OR attribute_key LIKE 'gearbox_%'
           OR attribute_key IN ('reduction_gearbox', 'pony_gearbox')
        """
    ).fetchall()
    for equipment_id, key, value in rows:
        result.setdefault(equipment_id, {}).setdefault(key, [])
        if value not in result[equipment_id][key]:
            result[equipment_id][key].append(value)
    return result


def join_values(attrs, key):
    values = attrs.get(key, [])
    if not values:
        return ""
    return " / ".join(values[:4])


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(DDL)
    cur.execute("DELETE FROM equipment_gearboxes")
    attrs_by_equipment = attr_map(cur)
    now = datetime.now().isoformat(timespec="seconds")

    rows = cur.execute(
        """
        SELECT el.equipment_id, el.lubricant_id, l.supplier, l.product_description,
               el.application, el.component
        FROM equipment_lubricants el
        JOIN lubricants l ON l.id = el.lubricant_id
        WHERE el.equipment_id IS NOT NULL
          AND (
              LOWER(el.component) LIKE '%gearbox%'
              OR LOWER(el.application) LIKE '%gearbox%'
              OR LOWER(l.used_for) LIKE '%gearbox%'
          )
        ORDER BY el.equipment_id, el.application, el.id
        """
    ).fetchall()

    inserted = 0
    for equipment_id, lubricant_id, supplier, product, application, component in rows:
        attrs = attrs_by_equipment.get(equipment_id, {})
        label = application or component or "Gearbox"
        cur.execute(
            """
            INSERT INTO equipment_gearboxes
                (equipment_id, gearbox_label, lubricant_id, oil_supplier, oil_product,
                 oil_application, gearbox_make, gearbox_type, gearbox_reduction,
                 gearbox_output_speed, source, imported_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                equipment_id,
                label,
                lubricant_id,
                supplier,
                product,
                application,
                join_values(attrs, "gearbox_make"),
                join_values(attrs, "gearbox_type") or join_values(attrs, "reduction_gearbox") or join_values(attrs, "pony_gearbox"),
                join_values(attrs, "gearbox_reduction"),
                join_values(attrs, "gearbox_output_speed"),
                "Derived from equipment_lubricants and equipment_attributes",
                now,
            ),
        )
        inserted += 1

    represented_equipment = {
        row[0]
        for row in cur.execute("SELECT DISTINCT equipment_id FROM equipment_gearboxes").fetchall()
    }
    placeholder_count = 0
    for equipment_id, attrs in sorted(attrs_by_equipment.items()):
        if equipment_id in represented_equipment:
            continue
        cur.execute(
            """
            INSERT INTO equipment_gearboxes
                (equipment_id, gearbox_label, lubricant_id, oil_supplier, oil_product,
                 oil_application, gearbox_make, gearbox_type, gearbox_reduction,
                 gearbox_output_speed, source, imported_at)
            VALUES (?, ?, NULL, '', '', '', ?, ?, ?, ?, ?, ?)
            """,
            (
                equipment_id,
                "Gearbox oil to confirm",
                join_values(attrs, "gearbox_make"),
                join_values(attrs, "gearbox_type") or join_values(attrs, "reduction_gearbox") or join_values(attrs, "pony_gearbox"),
                join_values(attrs, "gearbox_reduction"),
                join_values(attrs, "gearbox_output_speed"),
                "Gearbox placeholder from equipment_attributes; oil not yet linked",
                now,
            ),
        )
        placeholder_count += 1
        inserted += 1

    conn.commit()
    linked_oil = cur.execute("SELECT COUNT(*) FROM equipment_gearboxes WHERE lubricant_id IS NOT NULL").fetchone()[0]
    conn.close()
    print(
        f"Built gearbox register: {inserted} gearbox rows; "
        f"{linked_oil} linked to lubricant/oil records; "
        f"{placeholder_count} oil placeholders."
    )


if __name__ == "__main__":
    main()
