#!/usr/bin/env python3
"""
Create equipment-to-lubricant assignments from the lubricant register.

The CSV uses operational names such as RB1, JHEL1, EL1 and "all turnheads".
This importer links the names that already exist in the equipment database and
keeps unmatched targets as source-only records for later equipment creation.
"""

import sqlite3
from datetime import datetime
from pathlib import Path


BASE = Path(__file__).parent
DB_PATH = BASE / "grain_terminal.db"
SOURCE = "LUBRICANTS - FINAL G&B copy.csv"

DDL = """
CREATE TABLE IF NOT EXISTS equipment_lubricants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER REFERENCES equipment(id) ON DELETE CASCADE,
    lubricant_id INTEGER NOT NULL REFERENCES lubricants(id) ON DELETE CASCADE,
    source_equipment_label TEXT NOT NULL,
    application TEXT,
    component TEXT,
    notes TEXT,
    source_file TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_equipment_lubricants_equipment ON equipment_lubricants(equipment_id);
CREATE INDEX IF NOT EXISTS idx_equipment_lubricants_lubricant ON equipment_lubricants(lubricant_id);
"""


def get_id(cur, name):
    row = cur.execute("SELECT id FROM equipment WHERE name = ?", (name,)).fetchone()
    return row[0] if row else None


def get_lubricant_id(cur, product):
    row = cur.execute(
        "SELECT id FROM lubricants WHERE product_description = ? ORDER BY id LIMIT 1",
        (product,),
    ).fetchone()
    if not row:
        raise RuntimeError(f"Lubricant not found: {product}")
    return row[0]


def add(cur, equipment_id, lubricant_id, label, application, component="Gearbox", notes=None):
    cur.execute(
        """
        INSERT INTO equipment_lubricants
            (equipment_id, lubricant_id, source_equipment_label, application,
             component, notes, source_file, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            equipment_id,
            lubricant_id,
            label,
            application,
            component,
            notes,
            SOURCE,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    conn.executescript(DDL)
    cur.execute("DELETE FROM equipment_lubricants WHERE source_file = ?", (SOURCE,))

    lubricant_ids = {
        "CISIDA GREASE EPS2": get_lubricant_id(cur, "CISIDA GREASE EPS2"),
        "CASSIDA FLUID GL 220": get_lubricant_id(cur, "CASSIDA FLUID GL 220"),
        "CASSIDA FLUID HF 46": get_lubricant_id(cur, "CASSIDA FLUID HF 46"),
        "RENOLIN CLP GEAR OIL 460": get_lubricant_id(cur, "RENOLIN CLP GEAR OIL 460"),
        "RENOLIN CLP GEAR OIL 220": get_lubricant_id(cur, "RENOLIN CLP GEAR OIL 220"),
        "RENOLIN CLP GEAR OIL 150": get_lubricant_id(cur, "RENOLIN CLP GEAR OIL 150"),
        "RENOLIN CLP GEAR OIL 320": get_lubricant_id(cur, "RENOLIN CLP GEAR OIL 320"),
        "RENOLIN UNISYN CLP 320": get_lubricant_id(cur, "RENOLIN UNISYN CLP 320"),
        "RENOFLUID TF 1500 Oil": get_lubricant_id(cur, "RENOFLUID TF 1500 Oil"),
        "RENOLIT EP-X1-PBF": get_lubricant_id(cur, "RENOLIT EP-X1-PBF"),
        "INTERFLON SPRAY": get_lubricant_id(cur, "INTERFLON SPRAY"),
    }

    bmh_id = get_id(cur, "BMH Ship Unloader")
    add(cur, bmh_id, lubricant_ids["CISIDA GREASE EPS2"], "BMH Ship Unloader Main Grease Pump", "Main grease pump", "Grease pump")
    add(cur, bmh_id, lubricant_ids["CISIDA GREASE EPS2"], "BMH Ship Unloader inlet head", "Inlet head", "Grease point")
    for label in [
        "BMH Inlet Head feeder gearbox (bottom)",
        "BMH Inlet Head Machinery gearbox (top)",
        "BMH Horizontal gearbox",
        "BMH Vertical gearbox",
        "BMH Slew gearboxes",
        "BMH Auto Lubrication unit",
    ]:
        add(cur, bmh_id, lubricant_ids["CASSIDA FLUID GL 220"], label, label.replace("BMH ", ""), "Gearbox/lubrication unit")
    add(cur, bmh_id, lubricant_ids["CASSIDA FLUID HF 46"], "BMH Hydraulic oil tank", "Hydraulic oil tank", "Hydraulic system")
    add(cur, bmh_id, lubricant_ids["RENOLIN UNISYN CLP 320"], "BMH Travelling drive gears", "Travelling drive gears", "Drive gears")

    for label in ["AFS C1", "C2", "C3A", "C3B", "C4 Gearbox"]:
        add(cur, None, lubricant_ids["RENOLIN CLP GEAR OIL 460"], label, "Gearbox", notes="Equipment record not yet created.")

    for label in [
        "CC3 Drive gearbox", "Shuttle 1 drive gearboxes", "Bridge 1 chain conveyor drive gearbox",
        "Shuttle 2 drive gearboxes", "Bridge 2 chain conveyor drive gearbox", "CC4 Drive gearbox",
        "Shuttle 3 drive gearboxes", "Bridge 3 (CC5) chain conveyor drive gearbox",
        "Shuttle 4 drive gearboxes", "Bridge 4 (CC6) chain conveyor drive gearbox",
    ]:
        add(cur, None, lubricant_ids["RENOLIN CLP GEAR OIL 220"], label, "Drive gearbox", notes="Equipment record not yet created.")

    clp150_names = (
        [f"RB{i}" for i in range(1, 10)]
        + [f"RC{i}" for i in range(1, 5)]
        + [f"BB{i}" for i in range(1, 8)]
        + [f"MC{i}" for i in range(1, 5)]
        + ["JL1", "JL2", "ELV1", "ELV2", "ELV3", "ELV4", "LC1", "LCC3", "DCC (UNUSED)", "LWCC1", "LWCC2", "SMC"]
        + [f"TH{i}" for i in range(1, 10)]
    )
    clp150_source_label = {
        "JL1": "JHEL1 Drive gearbox",
        "JL2": "JHEL2 Drive gearbox",
        "ELV1": "EL1 Drive gearbox",
        "ELV2": "EL2 Drive gearbox",
        "ELV3": "EL3 Drive gearbox",
        "ELV4": "EL4 Drive gearbox",
        "LC1": "LLCC1 Drive gearbox",
        "LCC3": "LLCC3 Drive gearbox",
        "DCC (UNUSED)": "DCC Drive gearbox",
        "SMC": "SMC1 Drive gearbox",
    }
    for name in clp150_names:
        label = clp150_source_label.get(name, f"{name} Drive gearbox")
        add(cur, get_id(cur, name), lubricant_ids["RENOLIN CLP GEAR OIL 150"], label, "Drive gearbox")

    for name in ["JL1", "JL2", "ELV1", "ELV2", "ELV3", "ELV4"]:
        label = clp150_source_label.get(name, name).replace("Drive", "Pony drive")
        add(cur, get_id(cur, name), lubricant_ids["RENOLIN CLP GEAR OIL 150"], label, "Pony drive gearbox")

    for label in ["BCC1 Drive gearbox", "BCC2 Drive gearbox", "BCC3 Drive gearbox", "LWEL1 Drive gearbox"]:
        add(cur, None, lubricant_ids["RENOLIN CLP GEAR OIL 150"], label, "Drive gearbox", notes="Equipment record not yet created.")

    for name in [f"BB{i}" for i in range(8, 13)] + [f"RB{i}" for i in range(10, 13)] + ["FB1", "FB2", "FE1"]:
        add(cur, get_id(cur, name), lubricant_ids["RENOLIN CLP GEAR OIL 320"], f"{name} Drive gearbox", "Drive gearbox")
    add(cur, None, lubricant_ids["RENOLIN CLP GEAR OIL 320"], "BC5 Drive gearbox", "Drive gearbox", notes="Equipment record not yet created.")

    for row in cur.execute("SELECT id, name FROM equipment WHERE equipment_type IN ('belt_conveyor','chain_conveyor','bucket_elevator','tripper')").fetchall():
        add(cur, row[0], lubricant_ids["RENOFLUID TF 1500 Oil"], row[1], "Fluid drive coupling", "Fluid coupling")
        add(cur, row[0], lubricant_ids["RENOLIT EP-X1-PBF"], row[1], "Conveyor gear coupling grease", "Gear coupling")

    for row in cur.execute("SELECT id, name FROM equipment WHERE equipment_type IN ('belt_conveyor','chain_conveyor')").fetchall():
        add(cur, row[0], lubricant_ids["INTERFLON SPRAY"], row[1], "Drive chain lubrication", "Drive chain")

    conn.commit()
    count = cur.execute("SELECT COUNT(*) FROM equipment_lubricants").fetchone()[0]
    linked = cur.execute("SELECT COUNT(*) FROM equipment_lubricants WHERE equipment_id IS NOT NULL").fetchone()[0]
    conn.close()
    print(f"Created {count} lubricant assignments ({linked} linked to equipment records).")


if __name__ == "__main__":
    main()
