#!/usr/bin/env python3
"""
Import Fike dust suppression documents/assets into grain_terminal.db.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


BASE = Path(__file__).parent
DB_PATH = BASE / "grain_terminal.db"
SOURCE_ROOT = BASE.parents[1] / "Fike" / "Fike"
SOURCE_PREFIX = "Fike/Fike"
CREATED_AT = "2026-04-26T01:20:00"


ASSETS = [
    {
        "name": "Fike Dust Suppression System",
        "type": "dust_suppression",
        "area": "Main Elevators And Distribution",
        "notes": "Fike dust suppression system attached to main elevators, Junction House elevators, and lorry intake chains.",
        "aliases": ["Fike System", "FIKES EPC"],
    },
    {
        "name": "Fike Main Elevators Panel",
        "type": "control_panel",
        "area": "Switchrooms",
        "notes": "Fike panel for main elevators; source folder labels this as 8th Floor Main Elevators Fike Panel.",
        "aliases": ["8th Floor Main Elevators Fike Panel", "Fike Cabinet 3", "EPACO Multi Stream Cabinet 3"],
    },
    {
        "name": "Fike Junction House Panel",
        "type": "control_panel",
        "area": "Switchrooms",
        "notes": "Placeholder Fike panel serving Junction House elevators; user identified panels in switchrooms 1 and 2.",
        "aliases": ["Fike Switchroom 1 Panel", "Fike Switchroom 2 Panel"],
    },
    {
        "name": "Fike Scale Room Panel",
        "type": "control_panel",
        "area": "Scale Room",
        "notes": "Placeholder Fike panel located in the Scale Room.",
        "aliases": ["Scale Room Fike Panel"],
    },
]


PROTECTED_EQUIPMENT = [
    "ELV1", "ELV2", "ELV3", "ELV4",
    "JL1", "JL2",
    "LWCC1", "LWCC2", "LCC1", "LCC3",
    "LORRY INTAKE",
]


def clean(value):
    return " ".join((value or "").replace("_", " ").split()).strip()


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
        VALUES (?, ?, 'fike_document', ?, ?)
        """,
        (equipment_id, alias, SOURCE_PREFIX, notes),
    )


def ensure_equipment(cur, item):
    row = cur.execute("SELECT id FROM equipment WHERE UPPER(name) = ?", (item["name"].upper(),)).fetchone()
    if row:
        equipment_id = row[0]
    else:
        cur.execute(
            """
            INSERT INTO equipment
                (name, equipment_type, area, mcc, drawing_refs, manufacturer, model, notes, created_at, location_description)
            VALUES (?, ?, ?, NULL, '[]', 'Fike', NULL, ?, ?, ?)
            """,
            (item["name"], item["type"], item["area"], item["notes"], CREATED_AT, item["area"]),
        )
        equipment_id = cur.lastrowid
    for alias in item.get("aliases", []):
        add_alias(cur, equipment_id, alias, f"Alias from {SOURCE_PREFIX}.")
    return equipment_id


def find_equipment(cur, name):
    row = cur.execute("SELECT id FROM equipment WHERE UPPER(name) = ?", (name.upper(),)).fetchone()
    return row[0] if row else None


def add_relationship(cur, parent_id, child_id, relation, notes):
    if not parent_id or not child_id or parent_id == child_id:
        return
    exists = cur.execute(
        """
        SELECT 1 FROM equipment_relationships
        WHERE parent_equipment_id = ? AND child_equipment_id = ? AND relationship_type = ?
        LIMIT 1
        """,
        (parent_id, child_id, relation),
    ).fetchone()
    if exists:
        return
    cur.execute(
        """
        INSERT INTO equipment_relationships
            (parent_equipment_id, child_equipment_id, relationship_type, notes)
        VALUES (?, ?, ?, ?)
        """,
        (parent_id, child_id, relation, notes),
    )


def description_for(path):
    name = path.name
    lower = name.lower()
    if "160737" in lower:
        return "Fike EPACO multi-stream electrical drawings, project 160737-3-3"
    if lower.endswith(".docx"):
        return "Fike EPC fault-finding procedure"
    if "e06-053" in lower:
        return "Fike annunciator module E10-0068 installation and operation instructions"
    return clean(path.stem)


def category_for(path):
    return "electrical_drawing" if path.suffix.lower() == ".pdf" and "160737" in path.name else "manual"


def equipment_ids_for(path, system_id, main_panel_id, junction_panel_id, scale_panel_id):
    ids = [system_id]
    lower = str(path).lower()
    if "8th floor" in lower or "160737" in lower:
        ids.append(main_panel_id)
    if "fault finding" in lower or "e06-053" in lower:
        ids.extend([main_panel_id, junction_panel_id, scale_panel_id])
    return sorted(set(ids))


def insert_document(cur, path, system_id, main_panel_id, junction_panel_id, scale_panel_id):
    rel = path.relative_to(BASE.parents[1]).as_posix()
    now = datetime.now().isoformat(timespec="seconds")
    size_kb = max(1, int(path.stat().st_size / 1024))
    equipment_ids = equipment_ids_for(path, system_id, main_panel_id, junction_panel_id, scale_panel_id)
    description = description_for(path)
    cur.execute(
        """
        INSERT INTO documents
            (filename, title, file_path, category, area, mcc, drawing_ref, drawing_type,
             description, assignee, status, file_size_kb, imported_at, updated_at, equipment_ids)
        VALUES (?, ?, ?, ?, 'Fike', NULL, ?, NULL, ?, NULL, 'active', ?, ?, ?, ?)
        ON CONFLICT(file_path) DO UPDATE SET
            title = excluded.title,
            category = excluded.category,
            area = excluded.area,
            drawing_ref = excluded.drawing_ref,
            description = excluded.description,
            status = excluded.status,
            file_size_kb = excluded.file_size_kb,
            updated_at = excluded.updated_at,
            equipment_ids = excluded.equipment_ids
        """,
        (
            path.name,
            description,
            rel,
            category_for(path),
            "160737-3-3" if "160737" in path.name else None,
            description,
            size_kb,
            now,
            now,
            json.dumps(equipment_ids),
        ),
    )
    return 1


def main():
    if not SOURCE_ROOT.exists():
        raise SystemExit(f"Missing Fike source folder: {SOURCE_ROOT}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    system_id, main_panel_id, junction_panel_id, scale_panel_id = [ensure_equipment(cur, item) for item in ASSETS]

    for child_name in PROTECTED_EQUIPMENT:
        child_id = find_equipment(cur, child_name)
        if child_id:
            add_relationship(cur, system_id, child_id, "protects", "Fike dust suppression coverage identified by user.")

    for panel_id in (main_panel_id, junction_panel_id, scale_panel_id):
        add_relationship(cur, system_id, panel_id, "controlled_by", "Fike panel linked to dust suppression system.")

    count = 0
    for path in sorted(SOURCE_ROOT.rglob("*")):
        if path.name == ".DS_Store" or not path.is_file():
            continue
        if path.suffix.lower() not in {".pdf", ".docx"}:
            continue
        count += insert_document(cur, path, system_id, main_panel_id, junction_panel_id, scale_panel_id)

    conn.commit()
    total_docs = cur.execute("SELECT COUNT(*) FROM documents WHERE file_path LIKE 'Fike/Fike/%'").fetchone()[0]
    conn.close()
    print(f"Imported/updated {count} Fike documents.")
    print(f"Fike documents registered: {total_docs}.")
    print(f"Fike equipment ids: system={system_id}, main_panel={main_panel_id}, junction_panel={junction_panel_id}, scale_panel={scale_panel_id}.")


if __name__ == "__main__":
    main()
