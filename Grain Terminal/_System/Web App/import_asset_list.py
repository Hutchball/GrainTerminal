#!/usr/bin/env python3
"""
Import RSGT Asset ListV2 CSV exports into grain_terminal.db.

The Equipment sheet is treated as the hierarchy. Other sheets add component
attributes against the same asset rows.
"""

import csv
import re
import sqlite3
from datetime import datetime
from pathlib import Path


BASE = Path(__file__).parent
DB_PATH = BASE / "grain_terminal.db"
SOURCE_DIR = BASE.parents[2] / "Incoming" / "RSGT Asset ListV2"
SOURCE_FILE = "Incoming/RSGT Asset ListV2"
CREATED_AT = "2026-04-26T00:05:00"


SHEETS = {
    "equipment": "Equipment-Table 1.csv",
    "motors": "RSGT Motors-Table 1.csv",
    "gearbox": "Gearbox-Table 1.csv",
    "chains": "Chains-Table 1.csv",
    "pulleys": "Pulleys -Table 1.csv",
    "couplings": "Couplings - Flui's-Table 1.csv",
    "drive_belts": "Drive Belts-Table 1.csv",
    "bearings": "Bearings-Table 1.csv",
}


DDL = """
CREATE TABLE IF NOT EXISTS asset_list_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER REFERENCES equipment(id) ON DELETE SET NULL,
    source_section TEXT NOT NULL,
    asset_number TEXT,
    component_description TEXT NOT NULL,
    canonical_key TEXT,
    source_file TEXT NOT NULL,
    source_sheet TEXT NOT NULL,
    source_row INTEGER NOT NULL,
    imported_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_asset_list_items_equipment ON asset_list_items(equipment_id);
CREATE INDEX IF NOT EXISTS idx_asset_list_items_asset_number ON asset_list_items(asset_number);
CREATE INDEX IF NOT EXISTS idx_asset_list_items_section ON asset_list_items(source_section);
"""


def clean(value):
    return " ".join((value or "").replace("\xa0", " ").split()).strip()


def normalize(value):
    return re.sub(r"[^A-Z0-9]+", "", clean(value).upper())


def cell(row, idx):
    return clean(row[idx]) if idx < len(row) else ""


def source_path(filename):
    path = SOURCE_DIR / filename
    if not path.exists():
        raise SystemExit(f"Missing asset-list source file: {path}")
    return path


def table_rows(filename):
    with source_path(filename).open("r", encoding="utf-8-sig", newline="") as handle:
        for row_number, row in enumerate(csv.reader(handle), start=1):
            yield row_number, row


def is_header(asset_number, description):
    joined = normalize(f"{asset_number} {description}")
    return not joined or joined in {
        "ASSETNUMBERCOMPONENTDESCRIPTION",
        "MOTORINFORMATION",
        "GEARBOXINFORMATION",
        "PULLEYSINFORMATION",
        "INFORMATION",
    } or "ASSETLIST" in joined


def infer_type(label):
    text = clean(label).upper()
    if "ELEV" in text or text.startswith("ELV"):
        return "bucket_elevator"
    if "BELT" in text or re.search(r"\bR[BC]\d+\b", text) or re.search(r"\bB\.?B\.?\s*\d+\b", text):
        return "belt_conveyor"
    if "CHAIN" in text or "CONV" in text or "CC" in text:
        return "chain_conveyor"
    if "VALVE" in text or "ROTARY" in text:
        return "rotary_valve"
    if "FAN" in text or "DUST PLANT" in text or "DCE" in text or "D.C.E" in text:
        return "dust_control"
    if "COMPRESSOR" in text:
        return "compressor"
    if "TRIPPER" in text or re.search(r"\bT\d+\b", text):
        return "tripper"
    if "TURNHEAD" in text:
        return "turnhead"
    if "BIN" in text:
        return "bin"
    if "MOTOR" in text:
        return "process_equipment"
    return "process_equipment"


def area_for_asset(asset_number, section):
    asset = clean(asset_number).upper()
    if "/LL/" in asset:
        return "Lorry Loading"
    return area_for_section(section)


def area_for_section(section):
    section = clean(section)
    return {
        "BMH Ship Unloader": "BMH",
        "Silo 1": "Silo 1",
        "Silo 2": "Silo 2",
        "Silo 3": "Silo 3",
    }.get(section, section or "Unknown")


def asset_number_key(asset_number):
    asset = clean(asset_number).upper()
    if not asset:
        return ""
    last = asset.split("/")[-1]
    match = re.match(r"EL(\d+)$", last)
    if match:
        if "/JH/" in asset:
            return f"JL{match.group(1)}"
        return f"ELV{match.group(1)}"
    match = re.match(r"CC(\d+)$", last)
    if match:
        if "/LL/" in asset:
            return f"LCC{match.group(1)}"
        return f"LWCC{match.group(1)}"
    match = re.match(r"T(\d+)$", last)
    if match:
        if match.group(1) in {"8", "9"}:
            return f"Tripper No {match.group(1)}"
        return f"TR{match.group(1)}"
    return last


def description_key(description, section):
    text = clean(description).upper()
    compact = normalize(text)
    section = clean(section)

    if section == "BMH Ship Unloader":
        return f"BMH {clean(description).title()}"

    if text == "FEED ELEVATOR PONY":
        return "FE1"
    if re.match(r"^DCE\s*11$", text):
        return "RB11"
    if re.match(r"^DCE\s*12$", text):
        return "RB12"
    if re.match(r"^S3V3", text):
        return "Silo 3 Valve 3"
    if re.match(r"^S3V4", text):
        return "Silo 3 Valve 4"
    if re.search(r"(OUTLET GATE|SWEEP AUGER|BIN NO \d+ FAN|BIN \d+ OUTLET GATE)", text):
        return "Silo 3 Bins"
    match = re.match(r"^TURNHEAD NO\s*([1-9])$", text)
    if match:
        return f"TH{match.group(1)}"
    match = re.match(r"^LOWER GARNER NO\s*([1-4])$", text)
    if match:
        return f"TH{match.group(1)}"
    if text.startswith("J/H ELEVATOR 1"):
        return "JL1"
    if text.startswith("J/H ELEVATOR 2"):
        return "JL2"
    match = re.match(r"^ELEVATOR NO\s*([1-4]) PONY$", text)
    if match:
        return "Main Elevator Pony Motors"
    if text.startswith("D.C.C") or text.startswith("DIS. CHAIN"):
        return "DCC (UNUSED)"
    if text.startswith("SURGE BIN NO1") or text.startswith("SURGE BIN 1"):
        return "Surge Bin 1"
    if text.startswith("SURGE BIN NO2") or text.startswith("SURGE BIN 2"):
        return "Surge Bin 2"
    if text.startswith("MILL BIN") or text.startswith("MILL NO"):
        return "Mill Feed"
    if text.startswith("D.C.E. /R.B.1") or text.startswith("D.C.E./R.B.1"):
        return "RB1 DCE"
    if text.startswith("D.C.E./R.B.2"):
        return "RB2 DCE"
    if text.startswith("D.C.E./R.B.3"):
        return "RB3 DCE"
    if text.startswith("D.C.E./R.C.1A"):
        return "RC1 DCE2"
    if text.startswith("D.C.E./R.C.1"):
        return "RC1 DCE1"
    if text.startswith("D.C.E./R.C.2"):
        return "RC2"
    if text.startswith("D.C.E/M.C. 2"):
        return "MC2"
    if text.startswith("D.C.E./M.C. 3"):
        return "MC3"
    if text.startswith("D.C.E./M.C. 4"):
        return "MC4"
    match = re.match(r"^DUST PLANT\s*(\d+)\s*(FAN|ROTARY)", text)
    if match:
        number = match.group(1)
        return "DP12 TO DP13" if number in {"12", "13"} else "DP1 TO DP6"
    match = re.match(r"^B\.B\.\s*([1-3]).*VALVE", text)
    if match:
        return f"BB{match.group(1)}_V1"
    if text.startswith("LORRY INTAKE CHAIN"):
        return "LORRY INTAKE"
    if text.startswith("LORRY INTAKE ELEV"):
        return "LWB ELEVATOR"
    if text.startswith("RB8 DCE"):
        return "RB8"
    if text.startswith("RB9 DCE"):
        return "RB9"
    if text == "SMC":
        return "SMC"
    if text == "COMPRESSOR" and section == "Silo 3":
        return "Silo 3 Compressor"
    return compact


def canonical_key(asset_number, description, section):
    return asset_number_key(asset_number) or description_key(description, section)


def find_equipment(cur, key):
    key = clean(key)
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
           OR UPPER(REPLACE(REPLACE(REPLACE(alias_name, ' ', ''), '.', ''), '/', '')) = ?
        LIMIT 1
        """,
        (key.upper(), normalize(key)),
    ).fetchone()
    return row[0] if row else None


def add_alias(cur, equipment_id, alias_name, notes):
    alias = clean(alias_name)
    if not alias:
        return
    exists = cur.execute(
        """
        SELECT 1 FROM equipment_aliases
        WHERE equipment_id = ? AND UPPER(alias_name) = ?
        LIMIT 1
        """,
        (equipment_id, alias.upper()),
    ).fetchone()
    if exists:
        return
    cur.execute(
        """
        INSERT INTO equipment_aliases (equipment_id, alias_name, alias_type, source, notes)
        VALUES (?, ?, 'asset_list', ?, ?)
        """,
        (equipment_id, alias, SOURCE_FILE, notes),
    )


def ensure_equipment(cur, key, asset_number, description, section):
    equipment_id = find_equipment(cur, key)
    if equipment_id:
        add_alias(cur, equipment_id, asset_number, "Asset number from RSGT Asset ListV2.")
        add_alias(cur, equipment_id, description, "Component description from RSGT Asset ListV2.")
        return equipment_id, False

    name = key if key.startswith("BMH ") else clean(description) or key
    cur.execute(
        """
        INSERT INTO equipment
            (name, equipment_type, area, mcc, drawing_refs, manufacturer, model, notes, created_at, location_description)
        VALUES (?, ?, ?, NULL, '[]', NULL, NULL, ?, ?, ?)
        """,
        (
            name,
            infer_type(name),
            area_for_asset(asset_number, section),
            "Placeholder created from RSGT Asset ListV2. Additional technical information can be added as it becomes available.",
            CREATED_AT,
            section,
        ),
    )
    equipment_id = cur.lastrowid
    add_alias(cur, equipment_id, asset_number, "Asset number from RSGT Asset ListV2.")
    add_alias(cur, equipment_id, description, "Component description from RSGT Asset ListV2.")
    return equipment_id, True


def add_relationship(cur, parent_id, child_id, notes):
    if not parent_id or not child_id or parent_id == child_id:
        return
    exists = cur.execute(
        """
        SELECT 1 FROM equipment_relationships
        WHERE parent_equipment_id = ? AND child_equipment_id = ? AND relationship_type = 'contains'
        LIMIT 1
        """,
        (parent_id, child_id),
    ).fetchone()
    if exists:
        return
    cur.execute(
        """
        INSERT INTO equipment_relationships
            (parent_equipment_id, child_equipment_id, relationship_type, notes)
        VALUES (?, ?, 'contains', ?)
        """,
        (parent_id, child_id, notes),
    )


def import_equipment_sheet(cur):
    current_section = ""
    section_parent_id = None
    imported = 0
    created = 0
    now = datetime.now().isoformat(timespec="seconds")
    bmh_parent = find_equipment(cur, "BMH Ship Unloader")
    for row_number, row in table_rows(SHEETS["equipment"]):
        asset_number = cell(row, 1)
        description = cell(row, 2)
        if is_header(asset_number, description):
            continue
        if asset_number and not description:
            current_section = clean(asset_number)
            section_parent_id = bmh_parent if current_section == "BMH Ship Unloader" else None
            continue
        if not description:
            continue
        key = canonical_key(asset_number, description, current_section)
        equipment_id, was_created = ensure_equipment(cur, key, asset_number, description, current_section)
        created += int(was_created)
        if section_parent_id:
            add_relationship(cur, section_parent_id, equipment_id, "BMH child asset from RSGT Asset ListV2.")
        cur.execute(
            """
            INSERT INTO asset_list_items
                (equipment_id, source_section, asset_number, component_description,
                 canonical_key, source_file, source_sheet, source_row, imported_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                equipment_id,
                current_section,
                asset_number,
                description,
                key,
                SOURCE_FILE,
                "Equipment",
                row_number,
                now,
            ),
        )
        imported += 1
    return imported, created


ATTRIBUTE_MAPS = {
    "motors": {
        "sheet": "RSGT Motors",
        "category": "motor",
        "columns": {
            3: ("motor_make", None),
            4: ("motor_serial_number", None),
            5: ("motor_type", None),
            6: ("motor_weight", "kg"),
            7: ("motor_voltage", "V"),
            8: ("motor_power", "kW"),
            9: ("motor_efficiency", "%"),
            10: ("motor_current", "A"),
            11: ("motor_speed", "RPM"),
            12: ("motor_nde_bearing", None),
            13: ("motor_de_bearing", None),
        },
    },
    "gearbox": {
        "sheet": "Gearbox",
        "category": "gearbox",
        "columns": {
            3: ("gearbox_make", None),
            4: ("gearbox_serial_number", None),
            5: ("gearbox_type", None),
            6: ("gearbox_weight", "kg"),
            7: ("gearbox_input_speed", "RPM"),
            8: ("gearbox_output_speed", "RPM"),
            9: ("gearbox_reduction", None),
            10: ("gearbox_power", "kW"),
            11: ("gearbox_oil_type", None),
            12: ("gearbox_oil_litres", "litres"),
            13: ("gearbox_input_shaft", "mm"),
            14: ("gearbox_output_shaft", "mm"),
        },
    },
    "chains": {
        "sheet": "Chains",
        "category": "chain",
        "columns": {
            3: ("chain_length_pitches", "pitches"),
            4: ("chain_pitch", "inch"),
            5: ("chain_type", None),
            6: ("chain_model_number", None),
            7: ("chain_comment", None),
        },
    },
    "drive_belts": {
        "sheet": "Drive Belts",
        "category": "belt",
        "offset": 0,
        "columns": {
            2: ("drive_belt_number", None),
            3: ("drive_belt_quantity", None),
            4: ("drive_belt_comment", None),
        },
    },
    "bearings": {
        "sheet": "Bearings",
        "category": "bearing",
        "columns": {
            3: ("bearing_shaft_size", None),
            4: ("bearing_make", None),
            5: ("bearing_housing", None),
            6: ("bearing", None),
            7: ("bearing_seals", None),
            8: ("bearing_sleeve", None),
            9: ("bearing_lock_nut", None),
            10: ("bearing_tools", None),
        },
    },
    "pulleys": {
        "sheet": "Asset Pulleys",
        "category": "pulley",
        "columns": {
            3: ("pulley_make", None),
            4: ("pulley_serial_number", None),
            5: ("pulley_type", None),
            6: ("pulley_weight", "kg"),
            7: ("pulley_input_speed", "RPM"),
            8: ("pulley_output_speed", "RPM"),
            9: ("pulley_reduction", None),
            10: ("pulley_power", "kW"),
            11: ("pulley_oil_type", None),
            12: ("pulley_oil_litres", "litres"),
            13: ("pulley_input_shaft", "mm"),
            14: ("pulley_output_shaft", "mm"),
        },
    },
    "couplings": {
        "sheet": "Couplings / Fluids",
        "category": "coupling",
        "columns": {
            3: ("coupling_make", None),
            4: ("coupling_serial_number", None),
            5: ("coupling_type", None),
            6: ("coupling_weight", "kg"),
            7: ("fluid_drive_make", None),
            8: ("fluid_drive_serial_number", None),
            9: ("fluid_drive_type", None),
            10: ("fluid_drive_weight", "kg"),
            11: ("fluid_drive_oil_type", None),
            12: ("fluid_drive_oil_litres", "litres"),
        },
    },
}


def import_attribute_sheet(cur, key_name, item_lookup):
    spec = ATTRIBUTE_MAPS[key_name]
    current_section = ""
    count = 0
    for row_number, row in table_rows(SHEETS[key_name]):
        offset = spec.get("offset", 1)
        asset_number = cell(row, offset)
        description = cell(row, offset + 1)
        if is_header(asset_number, description):
            continue
        if asset_number and not description and key_name != "drive_belts":
            current_section = clean(asset_number)
            continue
        if key_name == "drive_belts":
            asset_number = cell(row, 0)
            description = cell(row, 1)
        if not description:
            continue
        lookup_key = (normalize(asset_number), normalize(description))
        equipment_id = item_lookup.get(lookup_key)
        if not equipment_id:
            candidate_key = canonical_key(asset_number, description, current_section)
            equipment_id = find_equipment(cur, candidate_key)
        if not equipment_id:
            continue
        for idx, (attr_key, unit) in spec["columns"].items():
            value = cell(row, idx)
            if not value:
                continue
            cur.execute(
                """
                INSERT INTO equipment_attributes
                    (equipment_id, attribute_key, attribute_value, attribute_unit,
                     attribute_category, source, confidence_level, added_by, notes)
                VALUES (?, ?, ?, ?, ?, ?, 'LIKELY', 'Codex', ?)
                """,
                (
                    equipment_id,
                    attr_key,
                    value,
                    unit,
                    spec["category"],
                    f"{SOURCE_FILE}/{SHEETS[key_name]}",
                    f"Imported from {spec['sheet']} row {row_number}. Verify before relying on this value.",
                ),
            )
            count += 1
    return count


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(DDL)
    cur = conn.cursor()
    cur.execute("DELETE FROM asset_list_items WHERE source_file = ?", (SOURCE_FILE,))
    cur.execute("DELETE FROM equipment_attributes WHERE source LIKE ?", (f"{SOURCE_FILE}/%",))

    imported_items, created_equipment = import_equipment_sheet(cur)
    item_lookup = {}
    for row in cur.execute(
        """
        SELECT equipment_id, asset_number, component_description
        FROM asset_list_items
        WHERE source_file = ?
        """,
        (SOURCE_FILE,),
    ):
        item_lookup[(normalize(row[1]), normalize(row[2]))] = row[0]

    attribute_count = 0
    for key_name in ATTRIBUTE_MAPS:
        attribute_count += import_attribute_sheet(cur, key_name, item_lookup)

    conn.commit()
    total_equipment = cur.execute("SELECT COUNT(*) FROM equipment").fetchone()[0]
    total_items = cur.execute("SELECT COUNT(*) FROM asset_list_items WHERE source_file = ?", (SOURCE_FILE,)).fetchone()[0]
    conn.close()
    print(f"Imported {imported_items} asset-list hierarchy rows ({total_items} stored).")
    print(f"Created {created_equipment} new equipment placeholders.")
    print(f"Imported {attribute_count} component attributes.")
    print(f"Equipment records now: {total_equipment}.")


if __name__ == "__main__":
    main()
