"""
import_silo3_bins.py
Adds Silo 3 Bins 1-9, each with Sweep Auger, Aeration Fan, and Outlet Gate.
Safe to re-run (skips bins that already exist).
"""

from db_config import get_connection
from datetime import datetime

NOW = datetime.utcnow().isoformat()
AREA = "Silo 3"
SOURCE = "user_confirmed"
CONFIDENCE = "UNKNOWN"

AUGER_ATTRS = [
    ("motor",       "Motor",       "motor"),
    ("coupling",    "Coupling",    "drive"),
    ("gearbox",     "Gearbox",     "gearbox"),
    ("screw",       "Screw",       "general"),
    ("drive_wheel", "Drive Wheel", "drive"),
]


def get_or_create_equipment(conn, name, equipment_type, area):
    row = conn.execute(
        "SELECT id FROM equipment WHERE name = ?", (name,)
    ).fetchone()
    if row:
        return row["id"], False
    conn.execute(
        "INSERT INTO equipment (name, equipment_type, area, created_at) VALUES (?,?,?,?)",
        (name, equipment_type, area, NOW),
    )
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0], True


def add_alias(conn, equipment_id, alias_name):
    exists = conn.execute(
        "SELECT 1 FROM equipment_aliases WHERE equipment_id=? AND alias_name=?",
        (equipment_id, alias_name),
    ).fetchone()
    if not exists:
        conn.execute(
            "INSERT INTO equipment_aliases (equipment_id, alias_name, alias_type, source) VALUES (?,?,?,?)",
            (equipment_id, alias_name, "legacy_name", SOURCE),
        )


def add_relationship(conn, parent_id, child_id, rel_type):
    exists = conn.execute(
        "SELECT 1 FROM equipment_relationships WHERE parent_equipment_id=? AND child_equipment_id=? AND relationship_type=?",
        (parent_id, child_id, rel_type),
    ).fetchone()
    if not exists:
        conn.execute(
            "INSERT INTO equipment_relationships (parent_equipment_id, child_equipment_id, relationship_type) VALUES (?,?,?)",
            (parent_id, child_id, rel_type),
        )


def add_attr(conn, equipment_id, key, value, category):
    exists = conn.execute(
        "SELECT 1 FROM equipment_attributes WHERE equipment_id=? AND attribute_key=?",
        (equipment_id, key),
    ).fetchone()
    if not exists:
        conn.execute(
            """INSERT INTO equipment_attributes
               (equipment_id, attribute_key, attribute_value, attribute_category,
                source, confidence_level, added_by, added_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (equipment_id, key, "TBC", category, SOURCE, CONFIDENCE, "Paul", NOW),
        )


def main():
    conn = get_connection()

    for n in range(1, 10):
        bin_name   = f"Silo 3 Bin {n}"
        auger_name = f"Silo 3 Bin {n} Sweep Auger"
        fan_name   = f"Silo 3 Bin {n} Aeration Fan"
        gate_name  = f"Silo 3 Bin {n} Outlet Gate"

        bin_id,   bin_new   = get_or_create_equipment(conn, bin_name,   "bin",         AREA)
        auger_id, auger_new = get_or_create_equipment(conn, auger_name, "sweep_auger", AREA)
        fan_id,   fan_new   = get_or_create_equipment(conn, fan_name,   "fan",         AREA)
        gate_id,  gate_new  = get_or_create_equipment(conn, gate_name,  "gate",        AREA)

        add_alias(conn, bin_id,   f"Bin {n}")
        add_alias(conn, auger_id, f"Silo 3 Bin {n} Auger")
        add_alias(conn, fan_id,   f"Bin {n} Aeration Fan")
        add_alias(conn, gate_id,  f"Bin {n} Outlet Gate")

        add_relationship(conn, bin_id, auger_id, "contains")
        add_relationship(conn, bin_id, fan_id,   "contains")
        add_relationship(conn, bin_id, gate_id,  "contains")

        for key, label, category in AUGER_ATTRS:
            add_attr(conn, auger_id, key, "TBC", category)

        status = "created" if bin_new else "already exists"
        print(f"  Bin {n}: {status}")

    conn.commit()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
