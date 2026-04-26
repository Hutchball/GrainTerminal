#!/usr/bin/env python3
"""
Import the RSGT electrical motor register CSV into grain_terminal.db.
"""

import csv
import re
import sqlite3
from datetime import datetime
from pathlib import Path


BASE = Path(__file__).parent
DB_PATH = BASE / "grain_terminal.db"
SOURCE_CANDIDATES = [
    BASE.parents[2] / "Incoming" / "RSGT ELECTRICAL MOTOR Details.csv",
    BASE.parents[2] / "Incoming" / "Processed" / "RSGT ELECTRICAL MOTOR Details.csv",
]
SOURCE_FILE = "Incoming/RSGT ELECTRICAL MOTOR Details.csv"


DDL = """
CREATE TABLE IF NOT EXISTS electrical_motors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER REFERENCES equipment(id) ON DELETE SET NULL,
    motor_reference TEXT,
    plant_label TEXT NOT NULL,
    section_name TEXT,
    source_equipment_label TEXT,
    motor_type TEXT,
    serial_number TEXT,
    make TEXT,
    volts TEXT,
    horsepower TEXT,
    amps TEXT,
    kilowatts TEXT,
    revs TEXT,
    phase TEXT,
    source_file TEXT NOT NULL,
    source_row INTEGER NOT NULL,
    imported_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_electrical_motors_equipment ON electrical_motors(equipment_id);
CREATE INDEX IF NOT EXISTS idx_electrical_motors_label ON electrical_motors(plant_label);
CREATE INDEX IF NOT EXISTS idx_electrical_motors_ref ON electrical_motors(motor_reference);
"""


CREATED_AT = "2026-04-25T23:10:00"

EXCLUDED_SECTIONS = {
    "Tower 1",
    "Tower 2",
    "Vigan",
    "Boiler Room",
}

EXCLUDED_SECTION_LABELS = {
    ("Silo 2", "D.C.E. 8"),
    ("Silo 2", "D.C.E. 9"),
    ("Silo 2", "p"),
}

SECTION_RENAMES = {
    "S-Spouts": "Shipping Spout 2",
}


SEEDED_EQUIPMENT = [
    {
        "name": "Mill Feed",
        "equipment_type": "process_equipment",
        "area": "Mill Feed",
        "notes": "Aggregate plant record for mill feed motor-driven valves and auxiliaries from the electrical motor register.",
        "aliases": ["Mill Feed Area"],
    },
    {
        "name": "Shipping Spout 2",
        "equipment_type": "process_equipment",
        "area": "Shipping Spouts",
        "notes": "Aggregate plant record for Shipping Spout 2 motor-driven hoist, slew, telescope, and valve equipment from the electrical motor register.",
        "aliases": ["S/Spout No 2", "S Spout No 2", "Shipping Spout No 2"],
    },
    {
        "name": "Silo 3 Bins",
        "equipment_type": "bin_group",
        "area": "Silo 3",
        "notes": "Aggregate Silo 3 bin record for aeration fans, sweep augers, and outlet gates from the electrical motor register.",
        "aliases": ["Silo 3 Bin", "Silo 3 Bin Group", "Silo 3 Bins 1-9"],
    },
    {
        "name": "Silo 1 Cupola Floor DCE",
        "equipment_type": "dust_control",
        "area": "Silo 1",
        "notes": "Dust Fan No 16 / DCE asset on the Silo 1 cupola floor, from the electrical motor register.",
        "aliases": ["Dust Fan No 16", "Silo 1 DCE Dust Fan 16"],
    },
    {
        "name": "Lorry Loading Routing Valves",
        "equipment_type": "rotary_valve",
        "area": "Lorry Loading",
        "notes": "Aggregate lorry loading routing valve record covering A-F head routers and bin routing valves from the electrical motor register.",
        "aliases": ["A-F Routing Valves", "Lorry Loading Head Routers"],
    },
    {
        "name": "Lorry Loading Compressors",
        "equipment_type": "compressor",
        "area": "Lorry Loading",
        "notes": "Aggregate lorry loading compressor record for East and West compressors from the electrical motor register.",
        "aliases": ["Compressor East", "Compressor West"],
    },
    {
        "name": "LLCC2",
        "equipment_type": "chain_conveyor",
        "area": "Lorry Loading",
        "notes": "Lorry Loading Chain Conveyor 2, from the electrical motor register.",
        "aliases": ["L.L.C.C. 2", "Lorry Loading Chain Conveyor 2"],
    },
    {
        "name": "Surge Bin DCE",
        "equipment_type": "dust_control",
        "area": "Receiving",
        "notes": "Surge Bin DCE on the 4th floor, from the electrical motor register.",
        "aliases": ["Surge Bin D.C.E"],
    },
    {
        "name": "Main Elevator Pony Motors",
        "equipment_type": "process_equipment",
        "area": "Main Elevators And Distribution",
        "notes": "Aggregate main elevator pony motor record from the electrical motor register.",
        "aliases": ["ELV PONY", "Elevator Pony Motors"],
    },
    {
        "name": "Surge Bin 1",
        "equipment_type": "bin",
        "area": "Silo 1",
        "notes": "Surge Bin 1 valve motors from the electrical motor register.",
        "aliases": ["Surge Bin 1 Valve 2"],
    },
    {
        "name": "Surge Bin 2",
        "equipment_type": "bin",
        "area": "Silo 1",
        "notes": "Surge Bin 2 valve motors from the electrical motor register.",
        "aliases": ["Surge Bin 2 Valve 1", "Surge Bin 2 Valve 2"],
    },
    {
        "name": "Silo 2 Auger 8",
        "equipment_type": "process_equipment",
        "area": "Silo 2",
        "notes": "Silo 2 Auger No 8 from the electrical motor register.",
        "aliases": ["AUGER No 8"],
    },
    {
        "name": "Silo 2 Auger 9",
        "equipment_type": "process_equipment",
        "area": "Silo 2",
        "notes": "Silo 2 Auger No 9 from the electrical motor register.",
        "aliases": ["AUGER No 9"],
    },
    {
        "name": "Silo 2 Auger 9A",
        "equipment_type": "process_equipment",
        "area": "Silo 2",
        "notes": "Silo 2 Auger No 9A from the electrical motor register.",
        "aliases": ["AUGER No 9A"],
    },
    {
        "name": "Silo 3 Compressor",
        "equipment_type": "compressor",
        "area": "Silo 3",
        "notes": "Silo 3 compressor from the electrical motor register.",
        "aliases": ["Silo 3 COMPRESSOR"],
    },
    {
        "name": "Silo 3 Dust Plant 14",
        "equipment_type": "dust_control",
        "area": "Silo 3",
        "notes": "Silo 3 Dust Plant 14 from the electrical motor register.",
        "aliases": ["DUST PLANT 14"],
    },
    {
        "name": "Silo 3 Dust Plant 15",
        "equipment_type": "dust_control",
        "area": "Silo 3",
        "notes": "Silo 3 Dust Plant 15 from the electrical motor register.",
        "aliases": ["DUST PLANT 15"],
    },
    {
        "name": "Silo 3 Dust Plant Rotary Valve",
        "equipment_type": "rotary_valve",
        "area": "Silo 3",
        "notes": "Rotary Valve 14/15 for the Silo 3 dust plant from the electrical motor register.",
        "aliases": ["ROTARY VALVE 14/15"],
    },
    {
        "name": "Silo 3 Valve 3",
        "equipment_type": "rotary_valve",
        "area": "Silo 3",
        "notes": "Silo 3 valve 3 from the electrical motor register.",
        "aliases": ["S3V3"],
    },
    {
        "name": "Silo 3 Valve 4",
        "equipment_type": "rotary_valve",
        "area": "Silo 3",
        "notes": "Silo 3 valve 4 from the electrical motor register.",
        "aliases": ["S3V4"],
    },
]


def clean(value):
    return " ".join((value or "").replace("\xa0", " ").split()).strip()


def normalize(value):
    return re.sub(r"[^A-Z0-9]+", "", clean(value).upper())


def section_name(raw):
    name = clean(raw).split(":", 1)[0]
    return SECTION_RENAMES.get(name, name)


def source_path():
    for path in SOURCE_CANDIDATES:
        if path.exists():
            return path
    candidates = ", ".join(str(path) for path in SOURCE_CANDIDATES)
    raise SystemExit(f"Missing source file. Checked: {candidates}")


def is_section_row(row):
    return bool(row and clean(row[0]) and "Table" in clean(row[0]) and not clean(row[0]).upper().startswith("LG/"))


def is_header_or_blank(row):
    joined = normalize(" ".join(row))
    if not joined:
        return True
    header_tokens = ("MOTORREFERENCE", "EQUIPNOPLANT", "PLANTTYPESERIAL", "MOTORSSTORED")
    return any(token in joined for token in header_tokens)


def cell(row, idx):
    return clean(row[idx]) if idx < len(row) else ""


def canonical_key(label, section=""):
    text = clean(label).upper()
    compact = normalize(text)
    section_text = clean(section)
    if not compact:
        return ""

    if section_text == "Dust Plants" and text == "DUST FAN NO 16":
        return "Silo 1 Cupola Floor DCE"

    if section_text == "Lorry Loading" and "ROUTING VALVE" in text:
        return "Lorry Loading Routing Valves"

    if section_text == "Lorry Loading" and text in {"COMPRESSOR EAST", "COMPRESSOR WEST"}:
        return "Lorry Loading Compressors"

    if section_text == "Lorry Loading" and text == "L.L.C.C. 2":
        return "LLCC2"

    if section_text == "Receiving":
        if text == "J/H ELEV. 1":
            return "JL1"
        if text == "J/H ELEV. 2":
            return "JL2"
        if text == "PONY 1":
            return "JL1"
        if text == "PONY 2":
            return "JL2"
        if text == "SURGE BIN D.C.E":
            return "Surge Bin DCE"

    if section_text == "Silo 1":
        if re.match(r"^DCC VALVE [1-3]$", text):
            return "DCC (UNUSED)"
        if text == "ELV PONY":
            return "Main Elevator Pony Motors"
        match = re.match(r"^L-GARNER NO([1-4])$", text)
        if match:
            return f"TH{match.group(1)}"
        if text == "L/W PONY":
            return "LWB ELEVATOR"
        if text.startswith("SURGE BIN 1 VALVE"):
            return "Surge Bin 1"
        if text.startswith("SURGE BIN 2 VALVE"):
            return "Surge Bin 2"

    if section_text == "Silo 2":
        if text == "AUGER NO 8":
            return "Silo 2 Auger 8"
        if text == "AUGER NO 9":
            return "Silo 2 Auger 9"
        if text == "AUGER NO 9A":
            return "Silo 2 Auger 9A"
        match = re.match(r"^B\.C\.C\. ([1-3])$", text)
        if match:
            return f"Basement Chain Conveyor No {match.group(1)}"

    if section_text == "Silo 3":
        if text == "COMPRESSOR":
            return "Silo 3 Compressor"
        if text == "D.C.E. 11":
            return "RB11"
        if text == "D.C.E. 12":
            return "RB12"
        if text == "DUST PLANT 14":
            return "Silo 3 Dust Plant 14"
        if text == "DUST PLANT 15":
            return "Silo 3 Dust Plant 15"
        if text == "FEED ELEVATOR":
            return "FE1"
        if text == "FEED ELEVATOR PONY":
            return "FE1"
        if text == "ROTARY VALVE 14/15":
            return "Silo 3 Dust Plant Rotary Valve"
        if text == "S3V3":
            return "Silo 3 Valve 3"
        if text == "S3V4":
            return "Silo 3 Valve 4"
        match = re.match(r"^TURNHEAD NO ([5-7])$", text)
        if match:
            return f"TH{match.group(1)}"

    if re.search(r"\bDUST\s*(?:FAN|FILTER FAN|FILTER DRIVE|ROTARY VALVE)\s*(?:NO)?\s*([1-6])\b", text):
        return "DP1 TO DP6"

    if re.search(r"\bDUST\s*(?:FAN|FILTER FAN|FILTER DRIVE|ROTARY VALVE)\s*(?:NO)?\s*(12|13)\b", text):
        return "DP12 TO DP13"

    if re.search(r"\bROTARY VALVE\s*(?:NO)?\s*([1-6])\b", text):
        return "DP1 TO DP6"

    if re.search(r"\bROTARY VALVE\s*(?:NO)?\s*(12|13)\b", text):
        return "DP12 TO DP13"

    if "DUST CHAIN 12" in text or "DUST ELEVATOR 12" in text or "DUST CHAIN 12 + 13" in text or "DUST ELEVATOR 12 + 13" in text:
        return "DP12 TO DP13"

    if text.startswith("MAIN DUST CHAIN"):
        return "DP1 TO DP6"

    if re.search(r"\bMILL\s*(?:BIN\s*)?\d*\s*(?:ROUTING\s*)?VALVE\b", text) or text.startswith("MILL BIN"):
        return "Mill Feed"

    if text == "COMPRESSOR 3":
        return "Mill Feed"

    if text.startswith("S/SPOUT") or text.startswith("S SPOUT"):
        return "Shipping Spout 2"

    if re.search(r"\b(?:AERATION FAN|SWEEP AUGER|OUTLET GATE)\s*(?:NO)?\s*\d+\b", text):
        return "Silo 3 Bins"

    match = re.search(r"\bELV(?:ATOR)?\s*(?:NO)?\s*(\d+)\b", text)
    if match:
        return f"ELV{match.group(1)}"

    match = re.search(r"\bT[-\s]*HEAD\s*(?:NO)?\s*(\d+)\b", text)
    if match:
        return f"TH{match.group(1)}"

    match = re.search(r"\bTRIPPER\s*(\d+)\b", text)
    if match:
        return f"TR{match.group(1)}"

    match = re.search(r"\b(?:R\.?\s*B\.?|RB)\s*(\d+)\b", text)
    if match:
        return f"RB{match.group(1)}"

    match = re.search(r"\b(?:B\.?\s*B\.?|BB)\s*(\d+)\b", text)
    if match:
        return f"BB{match.group(1)}"

    match = re.search(r"\b(?:R\.?\s*C\.?|RC)\s*(\d+)\b", text)
    if match:
        return f"RC{match.group(1)}"

    match = re.search(r"\b(?:M\.?\s*C\.?|MC)\s*(\d+)\b", text)
    if match:
        return f"MC{match.group(1)}"

    match = re.search(r"\b(?:F\.?\s*B\.?|FB)\s*(\d+)\b", text)
    if match:
        return f"FB{match.group(1)}"

    match = re.search(r"\b(?:F\.?\s*E\.?|FE)\s*(\d+)\b", text)
    if match:
        return f"FE{match.group(1)}"

    match = re.search(r"\b(?:L/?W|L\.?W\.?)\s*CHAIN\s*(\d+)?\b", text)
    if match:
        return f"LWCC{match.group(1) or '1'}"

    if "L/W ELEVATOR" in text or "L.W ELEVATOR" in text or "ELEVATOR" in text and "PONY" not in text:
        if text.startswith("L/") or text.startswith("L.") or "L/W" in text:
            return "LWB ELEVATOR"

    match = re.search(r"\bDUST\s*(?:FAN|FILTER FAN|FILTER DRIVE|ROTARY VALVE)\s*(?:NO)?\s*(\d+)\b", text)
    if match:
        number = match.group(1)
        if number in {"12", "13"}:
            if "FAN" in text:
                return f"Dust Plant {number} - Fan"
            if "CHAIN" in text:
                return f"Dust Plant {number} - Chain Conveyor"
            if "ELEVATOR" in text:
                return f"Dust Plant {number} - Elevator"

    if compact in {"DCC", "DCCUNUSED"}:
        return "DCC (UNUSED)"

    for key in ("SMC", "LGS1", "LGS2"):
        if compact.startswith(key):
            return key

    return compact


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
        VALUES (?, ?, 'legacy_name', ?, ?)
        """,
        (equipment_id, alias, SOURCE_FILE, notes),
    )


def ensure_seed_equipment(cur):
    for item in SEEDED_EQUIPMENT:
        row = cur.execute("SELECT id FROM equipment WHERE UPPER(name) = ?", (item["name"].upper(),)).fetchone()
        if row:
            equipment_id = row[0]
            cur.execute(
                """
                UPDATE equipment
                SET equipment_type = COALESCE(equipment_type, ?),
                    area = COALESCE(area, ?),
                    notes = COALESCE(notes, ?)
                WHERE id = ?
                """,
                (item["equipment_type"], item["area"], item["notes"], equipment_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO equipment
                    (name, equipment_type, area, mcc, drawing_refs, manufacturer, model, notes, created_at, location_description)
                VALUES (?, ?, ?, NULL, '[]', NULL, NULL, ?, ?, ?)
                """,
                (
                    item["name"],
                    item["equipment_type"],
                    item["area"],
                    item["notes"],
                    CREATED_AT,
                    item["area"],
                ),
            )
            equipment_id = cur.lastrowid
        for alias in item.get("aliases", []):
            add_alias(cur, equipment_id, alias, f"Alias added during {SOURCE_FILE} motor linking.")


def equipment_id_for(cur, label, section=""):
    key = canonical_key(label, section)
    if not key:
        return None, ""

    row = cur.execute("SELECT id FROM equipment WHERE UPPER(name) = ?", (key.upper(),)).fetchone()
    if row:
        return row[0], key

    row = cur.execute(
        """
        SELECT equipment_id
        FROM equipment_aliases
        WHERE UPPER(alias_name) = ?
           OR UPPER(REPLACE(REPLACE(alias_name, ' ', ''), '.', '')) = ?
        LIMIT 1
        """,
        (key.upper(), normalize(key)),
    ).fetchone()
    if row:
        return row[0], key

    return None, key


def parse_motor_row(row, current_section):
    if is_header_or_blank(row):
        return None

    first = cell(row, 0)
    second = cell(row, 1)
    equip_mode = first.upper().startswith("LG/") or (not first and second)

    if equip_mode:
        motor_reference = first
        plant_label = second
        values = [cell(row, idx) for idx in range(2, 11)]
    else:
        motor_reference = ""
        plant_label = first
        values = [cell(row, idx) for idx in range(1, 10)]

    if not plant_label and motor_reference:
        plant_label = f"Stored spare motor {motor_reference}"

    if not plant_label:
        return None

    while len(values) < 9:
        values.append("")

    return {
        "motor_reference": motor_reference,
        "plant_label": plant_label,
        "section_name": current_section,
        "motor_type": values[0],
        "serial_number": values[1],
        "make": values[2],
        "volts": values[3],
        "horsepower": values[4],
        "amps": values[5],
        "kilowatts": values[6],
        "revs": values[7],
        "phase": values[8],
    }


def import_rows(cur):
    imported = 0
    linked = 0
    current_section = ""
    now = datetime.now().isoformat(timespec="seconds")
    with source_path().open("r", encoding="utf-8-sig", newline="") as handle:
        for row_number, row in enumerate(csv.reader(handle), start=1):
            if is_section_row(row):
                current_section = section_name(row[0])
                continue
            if current_section in EXCLUDED_SECTIONS:
                continue
            parsed = parse_motor_row(row, current_section)
            if not parsed:
                continue
            if (parsed["section_name"], parsed["plant_label"]) in EXCLUDED_SECTION_LABELS:
                continue
            equipment_id, source_label = equipment_id_for(cur, parsed["plant_label"], parsed["section_name"])
            cur.execute(
                """
                INSERT INTO electrical_motors
                    (equipment_id, motor_reference, plant_label, section_name, source_equipment_label,
                     motor_type, serial_number, make, volts, horsepower, amps, kilowatts, revs, phase,
                     source_file, source_row, imported_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    equipment_id,
                    parsed["motor_reference"],
                    parsed["plant_label"],
                    parsed["section_name"],
                    source_label,
                    parsed["motor_type"],
                    parsed["serial_number"],
                    parsed["make"],
                    parsed["volts"],
                    parsed["horsepower"],
                    parsed["amps"],
                    parsed["kilowatts"],
                    parsed["revs"],
                    parsed["phase"],
                    SOURCE_FILE,
                    row_number,
                    now,
                ),
            )
            imported += 1
            if equipment_id:
                linked += 1
    return imported, linked


def main():
    source_path()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(DDL)
    cur = conn.cursor()
    ensure_seed_equipment(cur)
    cur.execute("DELETE FROM electrical_motors WHERE source_file = ?", (SOURCE_FILE,))
    imported, linked = import_rows(cur)
    conn.commit()
    total = cur.execute("SELECT COUNT(*) FROM electrical_motors").fetchone()[0]
    sections = cur.execute("SELECT COUNT(DISTINCT section_name) FROM electrical_motors").fetchone()[0]
    conn.close()
    print(f"Imported {imported} electrical motor rows from {SOURCE_FILE}.")
    print(f"Total electrical motor records: {total}; linked to equipment: {linked}; sections: {sections}.")


if __name__ == "__main__":
    main()
