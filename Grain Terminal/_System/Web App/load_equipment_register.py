#!/usr/bin/env python3
"""
load_equipment_register.py
==========================
Max (Mechanical Engineer) — parses Silo Layout PH CSV.csv and loads:
  1. Equipment records (INSERT OR IGNORE — won't overwrite existing data)
  2. Component attribute rows (value='TBC', marks known components awaiting spec data)
  3. Equipment relationships (valve → elevator feed chains)

Run from project root:  python3 load_equipment_register.py
"""

import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path

BASE    = Path(__file__).parent
DB_PATH = BASE / "grain_terminal.db"
CSV_PATH = BASE / "Drag Raw Data" / "Silo Layout PH CSV.csv"

# ── Component → attribute category mapping ────────────────────────────────────
COMPONENT_CATEGORIES = {
    "LV MOTOR":                   ("motor",        "lv_motor"),
    "HV MOTOR":                   ("motor",        "hv_motor"),
    "PONY MOTOR":                 ("motor",        "pony_motor"),
    "FAN MOTOR":                  ("motor",        "fan_motor"),
    "FLUID COUPLING":             ("fluid_coupling","fluid_coupling"),
    "FLUID COUPLING DRIVE":       ("fluid_coupling","fluid_coupling_drive"),
    "REDUCTION GEARBOX":          ("gearbox",      "reduction_gearbox"),
    "PONY GEARBOX":               ("gearbox",      "pony_gearbox"),
    "COUPLING":                   ("coupling",     "coupling"),
    "PONY COUPLING":              ("coupling",     "pony_coupling"),
    "ANTI RUN BACK GEAR":         ("drive",        "anti_runback"),
    "DRIVE CHAIN":                ("drive",        "drive_chain"),
    "DRIVE SPROCKET":             ("drive",        "drive_sprocket"),
    "DRIVEN SPROCKET":            ("drive",        "driven_sprocket"),
    "GTU":                        ("drive",        "gravity_take_up"),
    "DRIVE PULLEY":               ("roller",       "drive_pulley"),
    "SNUB PULLEYS":               ("roller",       "snub_pulleys"),
    "BEND PULLEYS":               ("roller",       "bend_pulleys"),
    "WING ROLLERS":               ("roller",       "wing_rollers"),
    "TROUGH ROLLERS":             ("roller",       "trough_rollers"),
    "RETURN ROLLERS":             ("roller",       "return_rollers"),
    "BELT ALIGNMENT SWITCHES":    ("safety",       "belt_alignment_switches"),
    "PULL CORDS":                 ("safety",       "pull_cords"),
    "STOP BUTTONS":               ("safety",       "stop_buttons"),
    "STOP BUTTON":                ("safety",       "stop_buttons"),
    "SPEED SENSOR":               ("safety",       "speed_sensor"),
    "LOWER CHUTE BLOCK":          ("safety",       "lower_chute_block"),
    "UPPER CHUTE BLOCK":          ("safety",       "upper_chute_block"),
    "CHUTE BLOCK":                ("safety",       "chute_block"),
    "HIGHER CHUTE BLOCK":         ("safety",       "higher_chute_block"),
    "SOUNDER":                    ("safety",       "sounder"),
    "HAND CONTROL":               ("control",      "hand_control"),
    "LOCAL ISOLATOR":             ("control",      "local_isolator"),
    "DUST BAGS (NUMBER AND TYPE)": ("dust_control", "dust_bags"),
    "PULSE AIR SOLENOIDS":        ("dust_control", "pulse_air_solenoids"),
}

# Components that are informational notes, not real attributes
SKIP_COMPONENTS = {
    "MAKE AND MODEL", "MORE INFO REQUIRED",
}

# ── Equipment type detection ───────────────────────────────────────────────────
def detect_type(name: str) -> str:
    n = name.upper()
    if "MAIN ELEVATOR" in n or "JUNCTION HOUSE ELEVATOR" in n:
        return "bucket_elevator"
    if n.endswith(" DCE") or "DCE" in n.split():
        return "dust_control"
    if "BELT" in n and "VALVE" not in n:
        return "belt_conveyor"
    if n.startswith("RB") and "MAGNET" not in n and "DCE" not in n:
        return "belt_conveyor"
    if n.startswith("RC") and "DCE" not in n:
        return "chain_conveyor"
    if "COMPRESSOR" in n:
        return "compressor"
    if "MAGNET" in n:
        return "magnetic_separator"
    if "VALVE" in n:
        return "rotary_valve"
    return "conveyor"

# ── CSV parsing ───────────────────────────────────────────────────────────────
def parse_csv(path: Path) -> list[dict]:
    """
    Returns a list of equipment dicts:
      {name, area, type, components:[str], relationship_note:str|None}
    """
    rows = []
    current_area = "Unknown"

    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for raw in reader:
            # Strip all cells
            cells = [c.strip() for c in raw]
            # Skip blank rows or header rows
            if not any(cells):
                continue
            if cells[0] == "Table 1" or (cells[0] == "Location" and cells[1] == ""):
                continue

            # Area header row: first cell non-empty, second cell is empty or area label
            if cells[0] and not cells[1]:
                continue  # pure area separator with no equipment

            # Area assignment: first cell non-empty, second cell has equipment name
            if cells[0] and cells[1]:
                current_area = cells[0].rstrip()
                equip_name   = cells[1]
                components   = [c for c in cells[2:] if c]
            elif not cells[0] and cells[1]:
                equip_name   = cells[1]
                components   = [c for c in cells[2:] if c]
            else:
                continue

            # Detect relationship note (e.g. "FEEDS MAIN ELEVATORS 1 AND 2")
            rel_note = None
            real_components = []
            for comp in components:
                if comp.startswith("FEEDS "):
                    rel_note = comp
                elif comp not in SKIP_COMPONENTS:
                    real_components.append(comp)

            rows.append({
                "name":              equip_name,
                "area":              current_area,
                "type":              detect_type(equip_name),
                "components":        real_components,
                "relationship_note": rel_note,
            })

    return rows


# ── Database loading ──────────────────────────────────────────────────────────
def load(rows: list[dict]):
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    now  = datetime.now().isoformat()

    stats = {"new_equipment": 0, "updated_equipment": 0,
             "attributes_added": 0, "relationships_added": 0}

    # Name → id map (built as we go)
    def get_or_create_equipment(name: str, area: str, etype: str) -> int:
        row = conn.execute(
            "SELECT id FROM equipment WHERE name=?", (name,)
        ).fetchone()
        if row:
            # Update area/type if blank
            conn.execute(
                "UPDATE equipment SET area=COALESCE(NULLIF(area,''),?), "
                "equipment_type=COALESCE(NULLIF(equipment_type,''),?) WHERE id=?",
                (area, etype, row["id"])
            )
            stats["updated_equipment"] += 1
            return row["id"]
        else:
            conn.execute(
                "INSERT INTO equipment (name, equipment_type, area, drawing_refs, created_at) "
                "VALUES (?,?,?,?,?)",
                (name, etype, area, "[]", now)
            )
            stats["new_equipment"] += 1
            return conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def add_attribute(equip_id: int, key: str, category: str):
        # Only add if this key doesn't already exist for this equipment
        exists = conn.execute(
            "SELECT 1 FROM equipment_attributes WHERE equipment_id=? AND attribute_key=?",
            (equip_id, key)
        ).fetchone()
        if not exists:
            conn.execute(
                """INSERT INTO equipment_attributes
                   (equipment_id, attribute_key, attribute_value, attribute_category,
                    source, confidence_level, added_by, added_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (equip_id, key, "TBC", category,
                 "Silo Layout PH CSV", "VERIFIED", "Max", now)
            )
            stats["attributes_added"] += 1

    def add_relationship(parent_id: int, child_id: int, rel_type: str):
        exists = conn.execute(
            "SELECT 1 FROM equipment_relationships "
            "WHERE parent_equipment_id=? AND child_equipment_id=?",
            (parent_id, child_id)
        ).fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO equipment_relationships "
                "(parent_equipment_id, child_equipment_id, relationship_type) VALUES (?,?,?)",
                (parent_id, child_id, rel_type)
            )
            stats["relationships_added"] += 1

    # First pass: create all equipment records and attributes
    equip_ids = {}
    for item in rows:
        eid = get_or_create_equipment(item["name"], item["area"], item["type"])
        equip_ids[item["name"]] = eid

        for comp in item["components"]:
            mapping = COMPONENT_CATEGORIES.get(comp)
            if mapping:
                category, attr_key = mapping
                add_attribute(eid, attr_key, category)

    # Second pass: add relationships from valve/feed notes
    for item in rows:
        if not item["relationship_note"]:
            continue
        parent_id = equip_ids.get(item["name"])
        if not parent_id:
            continue
        # Parse "FEEDS MAIN ELEVATORS 1 AND 2" → ["MAIN ELEVATOR 1", "MAIN ELEVATOR 2"]
        note = item["relationship_note"]
        if "FEEDS" in note and "ELEVATOR" in note:
            import re
            nums = re.findall(r'\d+', note)
            for n in nums:
                target = f"MAIN ELEVATOR {n}"
                child_id = equip_ids.get(target)
                if child_id:
                    add_relationship(parent_id, child_id, "feeds_into")

    conn.commit()
    conn.close()
    return stats


# ── File the source documents ─────────────────────────────────────────────────
def file_documents():
    import shutil
    dest_dir = BASE / "Grain Terminal" / "Equipment Register"
    dest_dir.mkdir(parents=True, exist_ok=True)

    for filename in ["Silo Layout PH CSV.csv", "Silo Layout PH.numbers"]:
        src = BASE / "Drag Raw Data" / filename
        dst = dest_dir / filename
        if src.exists() and not dst.exists():
            shutil.copy2(str(src), str(dst))
            print(f"  Adam: Filed → Grain Terminal/Equipment Register/{filename}")

    # Register in documents table
    conn = sqlite3.connect(str(DB_PATH))
    now  = datetime.now().isoformat()
    for filename, category in [
        ("Silo Layout PH CSV.csv",    "manual"),
        ("Silo Layout PH.numbers",    "manual"),
    ]:
        rel_path = f"Equipment Register/{filename}"
        conn.execute("""
            INSERT INTO documents
              (filename, title, file_path, category, area, status, imported_at, updated_at, assignee)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(file_path) DO NOTHING
        """, (filename, "Silo Layout — Equipment Register (partial)",
              rel_path, category, "All Areas", "active", now, now, "Adam (Administrator)"))
    conn.commit()
    conn.close()


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if not DB_PATH.exists():
        print("ERROR: grain_terminal.db not found. Run init_db.py first.")
        return
    if not CSV_PATH.exists():
        print(f"ERROR: CSV not found at {CSV_PATH}")
        return

    print("Max: Parsing equipment register CSV...")
    rows = parse_csv(CSV_PATH)
    print(f"  Found {len(rows)} equipment entries")

    print("Max: Loading into database...")
    stats = load(rows)
    print(f"  New equipment:      {stats['new_equipment']}")
    print(f"  Updated equipment:  {stats['updated_equipment']}")
    print(f"  Attributes added:   {stats['attributes_added']}")
    print(f"  Relationships added:{stats['relationships_added']}")

    print("Adam: Filing source documents...")
    file_documents()

    print("Done. Run export_to_json.py to update the web portal.")


if __name__ == "__main__":
    main()
